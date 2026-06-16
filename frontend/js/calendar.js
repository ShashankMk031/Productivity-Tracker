import { fetchAPI } from './api.js';
import { toast } from './ui.js';
import { getLogicalTodayIST } from './date.js';

let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth() + 1; // 1-indexed

const gridBody = document.getElementById("calendar-grid-body");
const monthLabel = document.getElementById("cal-month-label");
const prevBtn = document.getElementById("cal-prev-month");
const nextBtn = document.getElementById("cal-next-month");
const loadingOverlay = document.getElementById("loading-overlay");

function showLoading(show) {
    if (loadingOverlay) {
        if (show) loadingOverlay.classList.remove("hidden");
        else loadingOverlay.classList.add("hidden");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Parse current month from logical date if possible
    const todayStr = getLogicalTodayIST();
    const dateObj = new Date(todayStr);
    currentYear = dateObj.getFullYear();
    currentMonth = dateObj.getMonth() + 1;
    
    // Bind listeners
    if (prevBtn) prevBtn.addEventListener("click", () => changeMonth(-1));
    if (nextBtn) nextBtn.addEventListener("click", () => changeMonth(1));
    
    // Close Day Detail Modal
    const modal = document.getElementById("day-detail-modal");
    const closeBtn = document.getElementById("day-detail-close-btn");
    const overlay = document.getElementById("day-detail-modal-overlay");
    if (closeBtn) closeBtn.addEventListener("click", () => modal.classList.remove("modal--open"));
    if (overlay) overlay.addEventListener("click", () => modal.classList.remove("modal--open"));
    
    renderCalendar();
});

function changeMonth(delta) {
    currentMonth += delta;
    if (currentMonth > 12) {
        currentMonth = 1;
        currentYear += 1;
    } else if (currentMonth < 1) {
        currentMonth = 12;
        currentYear -= 1;
    }
    renderCalendar();
}

async function renderCalendar() {
    showLoading(true);
    if (!gridBody || !monthLabel) return;
    
    gridBody.innerHTML = "";
    
    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];
    monthLabel.textContent = `${monthNames[currentMonth - 1]} ${currentYear}`;
    
    try {
        // 1. Fetch Month Tasks & Entries
        const monthData = await fetchAPI(`/entries/${currentYear}/${currentMonth}`);
        const tasks = monthData.tasks || [];
        
        // 2. Fetch Projects
        const projects = await fetchAPI('/projects') || [];
        
        // 3. Fetch Goals
        const goals = await fetchAPI('/goals') || [];
        
        // 4. Fetch Focus sessions
        const focusSessions = await fetchAPI('/focus/history') || [];
        
        // 5. Fetch Reminders
        const reminders = await fetchAPI('/reminders') || [];
        
        // Compute calendar math
        const firstDayDate = new Date(currentYear, currentMonth - 1, 1);
        let firstDayIndex = firstDayDate.getDay(); // 0 = Sunday, 1 = Monday
        // Convert to Mon-Sun indexed (0 = Monday, 6 = Sunday)
        firstDayIndex = firstDayIndex === 0 ? 6 : firstDayIndex - 1;
        
        const totalDays = new Date(currentYear, currentMonth, 0).getDate();
        
        // 4. Pad preceding days from previous month
        for (let i = 0; i < firstDayIndex; i++) {
            const pad = document.createElement("div");
            pad.className = "calendar-day-cell calendar-day-cell--empty";
            gridBody.appendChild(pad);
        }
        
        // 5. Render days of the month
        const todayStr = getLogicalTodayIST();
        
        for (let day = 1; day <= totalDays; day++) {
            const dayCell = document.createElement("div");
            dayCell.className = "calendar-day-cell";
            dayCell.style.cursor = "pointer";
            
            // Format YYYY-MM-DD date key
            const dayDateStr = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dateObj = new Date(dayDateStr);
            const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
            const currentWk = weekdays[dateObj.getDay()];
            
            if (dayDateStr === todayStr) {
                dayCell.classList.add("calendar-day-cell--today");
            }
            
            // Add day number
            const numEl = document.createElement("div");
            numEl.className = "calendar-day-number";
            numEl.textContent = day;
            dayCell.appendChild(numEl);
            
            // A. Add scheduled habits/tasks for this weekday
            const scheduledTodayHabits = [];
            tasks.forEach(task => {
                let scheduled = false;
                try {
                    const days = Array.isArray(task.active_days) ? task.active_days : JSON.parse(task.active_days);
                    scheduled = days.includes(currentWk);
                } catch (e) {
                    scheduled = true; // Default fallback
                }
                
                if (scheduled) {
                    scheduledTodayHabits.push(task);
                    const completed = task.days?.[dayDateStr]?.completed === 1;
                    
                    const pill = document.createElement("div");
                    pill.className = `calendar-item-pill ${completed ? 'calendar-item-pill--task-done' : 'calendar-item-pill--task-pending'}`;
                    pill.innerHTML = `${completed ? '✓' : '○'} ${task.title}`;
                    dayCell.appendChild(pill);
                }
            });
            
            // B. Add project deadlines
            const dayProjects = [];
            projects.forEach(proj => {
                if (proj.deadline === dayDateStr) {
                    dayProjects.push(proj);
                    const pill = document.createElement("div");
                    pill.className = "calendar-item-pill calendar-item-pill--project";
                    pill.innerHTML = `🏁 Deadline: ${proj.title}`;
                    dayCell.appendChild(pill);
                }
            });
            
            // C. Add goal targets
            const dayGoals = [];
            goals.forEach(goal => {
                if (goal.target_date === dayDateStr) {
                    dayGoals.push(goal);
                    const pill = document.createElement("div");
                    pill.className = "calendar-item-pill calendar-item-pill--goal";
                    pill.innerHTML = `🎯 Goal Target: ${goal.title}`;
                    dayCell.appendChild(pill);
                }
            });
            
            // D. Add focus sessions executed on this day
            const dayFocus = focusSessions.filter(fs => fs.start_time.startsWith(dayDateStr));
            dayFocus.forEach(fs => {
                const pill = document.createElement("div");
                pill.className = "calendar-item-pill calendar-item-pill--focus";
                const min = Math.round(fs.duration / 60);
                pill.innerHTML = `⏱️ Focus: ${min}m - ${fs.title}`;
                dayCell.appendChild(pill);
            });
            
            // E. Add reminders scheduled for this day
            const dayReminders = reminders.filter(r => r.datetime.startsWith(dayDateStr));
            dayReminders.forEach(r => {
                const pill = document.createElement("div");
                pill.className = "calendar-item-pill calendar-item-pill--reminder";
                const timeStr = new Date(r.datetime).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
                pill.innerHTML = `🔔 ${timeStr}: ${r.title}`;
                dayCell.appendChild(pill);
            });
            
            // Click listener to open modal
            dayCell.addEventListener("click", (e) => {
                openDayDetailModal(dayDateStr, scheduledTodayHabits, dayFocus, dayReminders, dayProjects, dayGoals);
            });
            
            gridBody.appendChild(dayCell);
        }
    } catch (err) {
        toast(`Failed to load calendar events: ${err.message}`, "error");
        console.error(err);
    } finally {
        showLoading(false);
    }
}

async function openDayDetailModal(dateStr, habits, focus, reminders, projects, goals) {
    const modal = document.getElementById("day-detail-modal");
    const title = document.getElementById("day-detail-title");
    const body = document.getElementById("day-detail-body");
    if (!modal || !title || !body) return;
    
    // Format friendly date
    const dateObj = new Date(dateStr + "T00:00:00");
    const formattedDate = dateObj.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    title.textContent = formattedDate;
    
    let html = "";
    
    // 1. Scheduled Habits
    html += `<div><h4 style="margin: 0 0 10px 0; font-size: 13px; color: var(--green); border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">🎯 Habits & Tasks</h4>`;
    if (habits.length === 0) {
        html += `<div style="font-size:12px; color:var(--muted); padding:4px 0;">No habits scheduled for this day.</div>`;
    } else {
        habits.forEach(h => {
            const completed = h.days?.[dateStr]?.completed === 1;
            const note = h.days?.[dateStr]?.note || "";
            const statusIcon = completed ? "✅" : "❌";
            const statusText = completed ? "Completed" : "Pending";
            
            html += `<div style="background: rgba(255,255,255,0.02); padding: 10px; border-radius: 6px; border: 1px solid var(--border); margin-bottom: 8px;">
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px;">
                    <strong style="color:var(--text);">${h.title}</strong>
                    <span style="font-size:10px; color:${completed ? 'var(--green)' : 'var(--danger)'}; font-weight:700;">${statusIcon} ${statusText}</span>
                </div>`;
            if (note) {
                html += `<div style="font-size:11px; color:var(--muted); margin-top: 6px; padding-top: 6px; border-top: 1px dashed rgba(255,255,255,0.08); font-style: italic;">
                    📝 Note: "${note}"
                </div>`;
            }
            html += `</div>`;
        });
    }
    html += `</div>`;
    
    // 2. Daily Notes Context (Consolidated tracker notes entered that day)
    const dayNotes = [];
    habits.forEach(h => {
        const note = h.days?.[dateStr]?.note;
        if (note) {
            dayNotes.push({ source: `Habit: ${h.title}`, note });
        }
    });
    focus.forEach(fs => {
        if (fs.notes) {
            dayNotes.push({ source: `Focus Session: ${fs.title}`, note: fs.notes });
        }
    });

    // Fetch daily note for the date
    try {
        const res = await fetchAPI(`/daily-notes/${dateStr}`);
        if (res && res.content) {
            dayNotes.push({ source: `Daily Journal Note`, note: res.content });
        }
    } catch (err) {
        console.warn("Failed to load daily note in calendar detail:", err);
    }
    
    html += `<div><h4 style="margin: 14px 0 10px 0; font-size: 13px; color: #ff00aa; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">📝 Notes Entered Today</h4>`;
    if (dayNotes.length === 0) {
        html += `<div style="font-size:12px; color:var(--muted); padding:4px 0;">No notes entered on this day.</div>`;
    } else {
        dayNotes.forEach(dn => {
            html += `<div style="background: rgba(255,255,255,0.02); padding: 10px; border-radius: 6px; border: 1px solid var(--border); margin-bottom: 8px;">
                <div style="font-size: 10px; color: #ff00aa; font-weight: bold; margin-bottom: 4px;">${dn.source}</div>
                <div style="font-size: 11px; color: var(--text); font-style: italic; white-space: pre-wrap;">"${dn.note}"</div>
            </div>`;
        });
    }
    html += `</div>`;
    
    // 3. Focus Sessions
    html += `<div><h4 style="margin: 14px 0 10px 0; font-size: 13px; color: #4a90e2; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">⏱️ Focus Sessions</h4>`;
    if (focus.length === 0) {
        html += `<div style="font-size:12px; color:var(--muted); padding:4px 0;">No focus sessions recorded on this day.</div>`;
    } else {
        focus.forEach(fs => {
            const start = new Date(fs.start_time).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
            const end = fs.end_time ? new Date(fs.end_time).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' }) : "Ongoing";
            const min = Math.round(fs.duration / 60);
            
            html += `<div style="background: rgba(255,255,255,0.02); padding: 10px; border-radius: 6px; border: 1px solid var(--border); margin-bottom: 8px; font-size: 12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="color:var(--text);">${fs.title}</strong>
                    <span style="font-weight:bold; color:var(--green);">${min} mins</span>
                </div>
                <div style="font-size: 10px; color:var(--muted); margin-top: 4px;">
                    Time: ${start} – ${end}
                </div>`;
            if (fs.notes) {
                html += `<div style="font-size:11px; color:var(--muted); margin-top: 6px; font-style: italic; border-top: 1px dashed rgba(255,255,255,0.08); padding-top: 6px;">
                    📝 Note: "${fs.notes}"
                </div>`;
            }
            html += `</div>`;
        });
    }
    html += `</div>`;
    
    // 4. Reminders
    html += `<div><h4 style="margin: 14px 0 10px 0; font-size: 13px; color: #ffaa00; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">🔔 Reminders</h4>`;
    if (reminders.length === 0) {
        html += `<div style="font-size:12px; color:var(--muted); padding:4px 0;">No reminders scheduled for this day.</div>`;
    } else {
        reminders.forEach(r => {
            const time = new Date(r.datetime).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
            const completed = r.completed === 1;
            
            html += `<div style="display:flex; justify-content:space-between; align-items:center; background: rgba(255,255,255,0.02); padding: 10px; border-radius: 6px; border: 1px solid var(--border); margin-bottom: 8px; font-size: 12px;">
                <span style="color:var(--text); font-weight: 500;">${r.title}</span>
                <div style="display:flex; gap: 8px; align-items:center;">
                    <span style="font-family:monospace; color:var(--muted); font-size:10px;">${time}</span>
                    <span style="font-size:10px; font-weight:700; color:${completed ? 'var(--green)' : '#ffaa00'};">${completed ? '✓ Done' : 'Pending'}</span>
                </div>
            </div>`;
        });
    }
    html += `</div>`;
    
    // 5. Deadlines & Targets
    html += `<div><h4 style="margin: 14px 0 10px 0; font-size: 13px; color: var(--danger); border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">🏁 Deadlines & Target Goals</h4>`;
    if (projects.length === 0 && goals.length === 0) {
        html += `<div style="font-size:12px; color:var(--muted); padding:4px 0;">No deadlines or target goals due today.</div>`;
    } else {
        projects.forEach(p => {
            html += `<div style="background: rgba(255,122,112,0.03); border:1px solid rgba(255,122,112,0.2); padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 12px;">
                <strong style="color:var(--danger);">🏁 Project Deadline: ${p.title}</strong>
                <div style="font-size:10px; color:var(--muted); margin-top:4px;">Progress: ${p.progress}%</div>
            </div>`;
        });
        goals.forEach(g => {
            html += `<div style="background: rgba(74,144,226,0.03); border:1px solid rgba(74,144,226,0.2); padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 12px;">
                <strong style="color:#4a90e2;">🎯 Goal Target Date: ${g.title}</strong>
                <div style="font-size:10px; color:var(--muted); margin-top:4px;">Category: ${g.category} | Progress: ${g.progress}%</div>
            </div>`;
        });
    }
    html += `</div>`;
    
    body.innerHTML = html;
    modal.classList.add("modal--open");
}
