import { fetchAPI } from './api.js';
import { toast } from './ui.js';
import { getLogicalTodayIST } from './date.js';

let activeFocusSession = null;
let focusInterval = null;
let reminderCheckInterval = null;
let scoresInterval = null;

export async function initProductivityOS() {
    console.log("[Productivity OS] Initializing core modules...");
    
    // Request notification permission on startup
    requestNotificationPermission();
    
    // Set today logical indicator date label
    const dateIndicator = document.getElementById("today-logical-date-indicator");
    if (dateIndicator) {
        const todayStr = getLogicalTodayIST();
        dateIndicator.textContent = `Logical Date: ${todayStr}`;
    }

    // Bind Focus events
    const startFocusBtn = document.getElementById("btn-start-focus");
    const stopFocusBtn = document.getElementById("btn-stop-focus");
    if (startFocusBtn) startFocusBtn.addEventListener("click", handleStartFocus);
    if (stopFocusBtn) stopFocusBtn.addEventListener("click", handleStopFocus);
    
    // Bind Reminders events
    const addReminderBtn = document.getElementById("btn-add-reminder");
    if (addReminderBtn) addReminderBtn.addEventListener("click", handleAddReminder);

    // Initial load of all modules
    await refreshAllOSModules();
    await initDailyNotesJournal();

    // Start 60-second background ticking daemon for Reminders
    if (reminderCheckInterval) clearInterval(reminderCheckInterval);
    reminderCheckInterval = setInterval(checkRemindersDaemon, 60000);
    // Run immediately on startup
    await checkRemindersDaemon();
    
    // Refresh scores and widgets every 30 seconds
    if (scoresInterval) clearInterval(scoresInterval);
    scoresInterval = setInterval(async () => {
        await refreshScores();
        await refreshTodaySchedule();
        await refreshRemindersList();
    }, 30000);
}

export async function refreshAllOSModules() {
    await refreshScores();
    await checkActiveFocusSession();
    await refreshTodaySchedule();
    await refreshRemindersList();
}

// ── 1. SCORING SYSTEM ──────────────────────────────────────────────────────────
async function refreshScores() {
    try {
        const res = await fetchAPI('/scores/today');
        const consistencyEl = document.getElementById("score-consistency");
        const executionEl = document.getElementById("score-execution");
        const progressEl = document.getElementById("score-goal-progress");
        
        if (consistencyEl) consistencyEl.textContent = res.consistency;
        if (executionEl) executionEl.textContent = res.execution;
        if (progressEl) progressEl.textContent = res.goal_progress;
    } catch (err) {
        console.warn("Failed to load daily scores", err);
    }
}

// ── 2. FOCUS SESSIONS ────────────────────────────────────────────────────────
async function checkActiveFocusSession() {
    try {
        const session = await fetchAPI('/focus/active');
        if (session) {
            activeFocusSession = session;
            enterActiveFocusState();
        } else {
            activeFocusSession = null;
            enterIdleFocusState();
        }
    } catch (err) {
        console.warn("Failed to fetch active focus session", err);
    }
}

function enterActiveFocusState() {
    const idleState = document.getElementById("focus-idle-state");
    const activeState = document.getElementById("focus-active-state");
    const activeTitle = document.getElementById("focus-active-title");
    
    if (idleState) idleState.classList.add("hidden");
    if (activeState) activeState.classList.remove("hidden");
    
    if (activeTitle) {
        activeTitle.textContent = `Focusing on: "${activeFocusSession.title}"`;
    }
    
    // Start Ticking Timer
    if (focusInterval) clearInterval(focusInterval);
    focusInterval = setInterval(updateFocusTimerUI, 1000);
    updateFocusTimerUI();
}

function enterIdleFocusState() {
    const idleState = document.getElementById("focus-idle-state");
    const activeState = document.getElementById("focus-active-state");
    const titleInput = document.getElementById("focus-session-title-input");
    const notesInput = document.getElementById("focus-session-notes-input");
    
    if (idleState) idleState.classList.remove("hidden");
    if (activeState) activeState.classList.add("hidden");
    
    if (titleInput) titleInput.value = "";
    if (notesInput) notesInput.value = "";
    
    if (focusInterval) {
        clearInterval(focusInterval);
        focusInterval = null;
    }
}

function updateFocusTimerUI() {
    if (!activeFocusSession) return;
    const timerEl = document.getElementById("focus-active-timer");
    if (!timerEl) return;
    
    const start = new Date(activeFocusSession.start_time);
    const now = new Date();
    const diff = Math.max(0, Math.floor((now - start) / 1000));
    
    const h = String(Math.floor(diff / 3600)).padStart(2, '0');
    const m = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
    const s = String(diff % 60).padStart(2, '0');
    
    timerEl.textContent = `${h}:${m}:${s}`;
}

async function handleStartFocus(e) {
    e.preventDefault();
    const titleInput = document.getElementById("focus-session-title-input");
    const title = titleInput ? titleInput.value.trim() : "";
    
    if (!title) {
        toast("Please describe what you are focusing on!", "error");
        return;
    }
    
    try {
        const res = await fetchAPI('/focus/start', {
            method: 'POST',
            body: JSON.stringify({ title })
        });
        activeFocusSession = res;
        enterActiveFocusState();
        toast("Focus Session started! Stay dedicated! 🎯");
        refreshScores();
    } catch (err) {
        toast(err.message, "error");
    }
}

async function handleStopFocus(e) {
    e.preventDefault();
    const notesInput = document.getElementById("focus-session-notes-input");
    const notes = notesInput ? notesInput.value.trim() : "";
    
    try {
        const res = await fetchAPI('/focus/stop', {
            method: 'POST',
            body: JSON.stringify({ notes })
        });
        
        const h = Math.floor(res.duration / 3600);
        const m = Math.floor((res.duration % 3600) / 60);
        toast(`Focus Session completed! Duration: ${h}h ${m}m. Saved! 🎉`);
        
        activeFocusSession = null;
        enterIdleFocusState();
        refreshScores();
    } catch (err) {
        toast(err.message, "error");
    }
}

// ── 3. TODAY'S SCHEDULE & DEADLINES ──────────────────────────────────────────
async function refreshTodaySchedule() {
    try {
        // Today logical date and weekday
        const todayStr = getLogicalTodayIST();
        const dateObj = new Date(todayStr);
        const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        const todayWk = weekdays[dateObj.getDay()];
        
        // Fetch active habits from API
        const tasksListEl = document.getElementById("today-tasks-list");
        if (tasksListEl) {
            tasksListEl.innerHTML = "";
            const monthData = await fetchAPI(`/entries/${dateObj.getFullYear()}/${dateObj.getMonth() + 1}`);
            const tasks = monthData.tasks || [];
            
            const scheduledToday = tasks.filter(t => {
                try {
                    const days = Array.isArray(t.active_days) ? t.active_days : JSON.parse(t.active_days);
                    return days.includes(todayWk);
                } catch (e) {
                    return true;
                }
            });
            
            if (scheduledToday.length === 0) {
                tasksListEl.innerHTML = '<div style="color:var(--muted); font-size:11px;">No habits scheduled for today.</div>';
            } else {
                scheduledToday.forEach(task => {
                    const el = document.createElement('div');
                    el.style = 'display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:6px 10px; border-radius:4px; border:1px solid var(--border);';
                    el.innerHTML = `
                        <span style="font-size:12px; color:var(--text); font-weight:500;">${task.title}</span>
                        <span style="font-size:10px; padding:2px 6px; border-radius:10px; background:rgba(84,209,79,0.1); color:var(--green); font-weight:700;">Active Today</span>
                    `;
                    tasksListEl.appendChild(el);
                });
            }
        }
        
        // Fetch upcoming project deadlines countdowns
        const deadlinesListEl = document.getElementById("today-deadlines-list");
        if (deadlinesListEl) {
            deadlinesListEl.innerHTML = "";
            const projects = await fetchAPI('/projects');
            const activeProjects = projects.filter(p => p.completed === 0);
            
            if (activeProjects.length === 0) {
                deadlinesListEl.innerHTML = '<div style="color:var(--muted); font-size:11px;">No active deadline projects.</div>';
            } else {
                activeProjects.forEach(proj => {
                    const diffDays = getDaysRemaining(proj.deadline);
                    let badgeColor = "var(--green)";
                    let badgeBg = "rgba(84, 209, 79, 0.15)";
                    
                    if (diffDays <= 3) {
                        badgeColor = "var(--danger)";
                        badgeBg = "rgba(255, 122, 112, 0.15)";
                    } else if (diffDays <= 7) {
                        badgeColor = "#ffaa00";
                        badgeBg = "rgba(255, 170, 0, 0.15)";
                    }
                    
                    const alertLabel = diffDays < 0 ? "Overdue" : diffDays === 0 ? "Due Today" : `${diffDays} days left`;
                    
                    const el = document.createElement('div');
                    el.style = 'display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:6px 10px; border-radius:4px; border:1px solid var(--border);';
                    el.innerHTML = `
                        <span style="font-size:12px; color:var(--text); text-overflow:ellipsis; overflow:hidden; white-space:nowrap; max-width:180px;">${proj.title}</span>
                        <span style="font-size:10px; padding:2px 6px; border-radius:10px; background:${badgeBg}; color:${badgeColor}; font-weight:700; white-space:nowrap;">${alertLabel}</span>
                    `;
                    deadlinesListEl.appendChild(el);
                });
            }
        }
    } catch (err) {
        console.warn("Failed to refresh Today Schedule UI", err);
    }
}

function getDaysRemaining(deadlineStr) {
    const today = new Date(getLogicalTodayIST());
    const target = new Date(deadlineStr);
    const diffTime = target - today;
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

// ── 4. REMINDERS SYSTEM ───────────────────────────────────────────────────────
function formatDateLabel(dateStr) {
    if (!dateStr) return "";
    const [year, month, day] = dateStr.split("-");
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function formatTimeLabel(timeStr) {
    if (!timeStr) return "";
    const [hours, minutes] = timeStr.split(":");
    const dummyDate = new Date();
    dummyDate.setHours(parseInt(hours), parseInt(minutes));
    return dummyDate.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
}

async function refreshRemindersList() {
    const listEl = document.getElementById("today-reminders-list");
    if (!listEl) return;
    
    try {
        const reminders = await fetchAPI('/reminders/active');
        listEl.innerHTML = "";
        
        if (reminders.length === 0) {
            listEl.innerHTML = '<div style="color:var(--muted); font-size:11px; text-align:center; padding-top:20px;">No active reminders. Add one above!</div>';
            return;
        }
        
        reminders.forEach(rem => {
            const el = document.createElement('div');
            el.style = 'display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:8px 10px; border-radius:6px; border:1px solid var(--border);';
            if (rem.is_overdue) {
                el.style.borderLeft = '3px solid var(--danger)';
            }
            
            let label = "";
            if (rem.due_date && rem.due_time) {
                label = `${formatDateLabel(rem.due_date)} @ ${formatTimeLabel(rem.due_time)}`;
            } else if (rem.due_date) {
                label = `Due: ${formatDateLabel(rem.due_date)}`;
            } else if (rem.due_time) {
                label = `At: ${formatTimeLabel(rem.due_time)}`;
            } else {
                label = "";
            }
            
            el.innerHTML = `
                <div style="display:flex; align-items:center; gap:8px; min-width:0; flex:1;">
                    <input type="checkbox" class="reminder-complete-check" data-id="${rem.id}" style="cursor:pointer;" />
                    <span style="font-size:12px; color:var(--text); text-overflow:ellipsis; overflow:hidden; white-space:nowrap; ${rem.is_overdue ? 'color: var(--danger); font-weight: 500;' : ''}">${rem.title}</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px; white-space:nowrap;">
                    <span style="font-size:10px; color:${rem.is_overdue ? 'var(--danger)' : 'var(--muted)'}; font-family:monospace;">${label}</span>
                    <button class="reminder-delete-btn" data-id="${rem.id}" style="background:transparent; border:none; color:var(--muted-2); cursor:pointer; font-size:10px; padding:2px;">✕</button>
                </div>
            `;
            
            // Toggle complete listener
            const check = el.querySelector(".reminder-complete-check");
            check.addEventListener("change", () => handleToggleReminder(rem.id));
            
            // Delete listener
            const delBtn = el.querySelector(".reminder-delete-btn");
            delBtn.addEventListener("click", () => handleDeleteReminder(rem.id));
            
            listEl.appendChild(el);
        });
    } catch (err) {
        console.warn("Failed to load active reminders", err);
    }
}

async function handleAddReminder(e) {
    e.preventDefault();
    const titleInput = document.getElementById("reminder-title-input");
    const dateInput = document.getElementById("reminder-date-input");
    const timeInput = document.getElementById("reminder-time-input");
    
    const title = titleInput ? titleInput.value.trim() : "";
    const dateVal = dateInput ? dateInput.value : "";
    const timeVal = timeInput ? timeInput.value : "";
    
    if (!title) {
        toast("Please provide a reminder title!", "error");
        return;
    }
    
    try {
        await fetchAPI('/reminders', {
            method: 'POST',
            body: JSON.stringify({
                title,
                due_date: dateVal || null,
                due_time: timeVal || null,
                recurring: 'none'
            })
        });
        
        toast("Reminder added successfully! 🔔");
        titleInput.value = "";
        if (dateInput) dateInput.value = "";
        if (timeInput) timeInput.value = "";
        
        await refreshRemindersList();
        refreshScores();
    } catch (err) {
        toast(err.message, "error");
    }
}

async function handleToggleReminder(id) {
    try {
        await fetchAPI(`/reminders/${id}/toggle`, { method: 'POST' });
        toast("Reminder completed! Great job! 🎉");
        await refreshRemindersList();
        refreshScores();
    } catch (err) {
        toast(err.message, "error");
    }
}

async function handleDeleteReminder(id) {
    try {
        await fetchAPI(`/reminders/${id}`, { method: 'DELETE' });
        toast("Reminder removed.");
        await refreshRemindersList();
        refreshScores();
    } catch (err) {
        toast(err.message, "error");
    }
}

// ── 5. NOTIFICATION DAEMON ────────────────────────────────────────────────────
const alertedOverdueReminders = new Set();

function requestNotificationPermission() {
    if ("Notification" in window) {
        if (Notification.permission === "default") {
            Notification.requestPermission();
        }
    }
}

async function checkRemindersDaemon() {
    const isNotificationGranted = ("Notification" in window) && Notification.permission === "granted";
    
    try {
        const reminders = await fetchAPI('/reminders/active');
        const now = new Date();
        const nowMinutes = now.getHours() * 60 + now.getMinutes();
        const todayStr = getLogicalTodayIST();
        
        const overdueList = [];
        
        reminders.forEach(rem => {
            // Push notification checks for time-exact notifications:
            const isToday = !rem.due_date || rem.due_date === todayStr;
            if (isToday && rem.due_time) {
                const [dueH, dueM] = rem.due_time.split(":");
                const dueMinutes = parseInt(dueH) * 60 + parseInt(dueM);
                
                if (dueMinutes === nowMinutes) {
                    if (isNotificationGranted) {
                        new Notification(`🔔 Productivity Reminder: "${rem.title}"`, {
                            body: `It's time to execute: ${rem.title}. Keep up the momentum!`,
                            icon: '/static/favicon.svg'
                        });
                    } else {
                        toast(`🔔 Reminder: "${rem.title}"`, "info");
                    }
                    
                    // Auto toggle completed on backend to avoid double alerts
                    fetchAPI(`/reminders/${rem.id}/toggle`, { method: 'POST' }).then(() => {
                        refreshRemindersList();
                    });
                    return;
                }
            }
            
            // Check overdue using the backend-calculated is_overdue property
            if (rem.is_overdue) {
                if (!alertedOverdueReminders.has(rem.id)) {
                    overdueList.push(rem);
                    alertedOverdueReminders.add(rem.id);
                }
            }
        });
        
        // Alert user about overdue reminders
        if (overdueList.length > 0) {
            if (overdueList.length === 1) {
                toast(`⚠️ Overdue Reminder: "${overdueList[0].title}" is past due!`, "warning");
            } else {
                toast(`⚠️ You have ${overdueList.length} overdue reminders (e.g. "${overdueList[0].title}").`, "warning");
            }
        }
        
        // Also check project deadline countdowns daily for 7, 3, or 1 days
        const projects = await fetchAPI('/projects');
        const activeProjects = projects.filter(p => p.completed === 0);
        
        activeProjects.forEach(proj => {
            const diffDays = getDaysRemaining(proj.deadline);
            // Alert exactly at 9:00 AM local time to avoid repeated noise
            if (now.getHours() === 9 && now.getMinutes() === 0) {
                if (diffDays === 7 || diffDays === 3 || diffDays === 1) {
                    if (isNotificationGranted) {
                        new Notification(`⚠️ Project Deadline approaching!`, {
                            body: `"${proj.title}" has ${diffDays} day(s) left! Adhere to your milestones.`,
                            icon: '/static/favicon.svg'
                        });
                    } else {
                        toast(`⚠️ Project Deadline: "${proj.title}" has ${diffDays} day(s) left!`, "warning");
                    }
                }
            }
        });
    } catch (err) {
        console.warn("[Notification Daemon] Background check failed", err);
    }
}

// ── 6. DAILY NOTES JOURNAL ───────────────────────────────────────────────────
async function initDailyNotesJournal() {
    const journalInput = document.getElementById("today-journal-input");
    const saveStatus = document.getElementById("journal-save-status");
    if (!journalInput) return;

    const todayStr = getLogicalTodayIST();
    
    // Load today's note
    try {
        const res = await fetchAPI(`/daily-notes/${todayStr}`);
        journalInput.value = res.content || "";
        if (saveStatus) saveStatus.textContent = "Saved.";
    } catch (err) {
        console.warn("Failed to load today's daily note", err);
    }

    // Save logic
    const saveNoteAction = async () => {
        if (saveStatus) saveStatus.textContent = "Saving...";
        try {
            await fetchAPI(`/daily-notes/${todayStr}`, {
                method: "PUT",
                body: JSON.stringify({ content: journalInput.value })
            });
            if (saveStatus) saveStatus.textContent = "Saved.";
        } catch (err) {
            console.error("Failed to save daily note", err);
            if (saveStatus) saveStatus.textContent = "Save failed.";
        }
    };

    journalInput.addEventListener("blur", saveNoteAction);
    journalInput.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            journalInput.blur();
        }
    });
}
