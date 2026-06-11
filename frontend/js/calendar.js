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
        const entries = monthData.entries || {}; // key: date key, value: dictionary of task completion state
        
        // 2. Fetch Projects
        const projects = await fetchAPI('/projects');
        
        // 3. Fetch Goals
        const goals = await fetchAPI('/goals');
        
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
            tasks.forEach(task => {
                let scheduled = false;
                try {
                    const days = JSON.parse(task.active_days);
                    scheduled = days.includes(currentWk);
                } catch (e) {
                    scheduled = true; // Default fallback
                }
                
                if (scheduled) {
                    const taskEntry = entries[dayDateStr]?.find(e => e.task_id === task.id);
                    const completed = taskEntry?.completed === 1;
                    
                    const pill = document.createElement("div");
                    pill.className = `calendar-item-pill ${completed ? 'calendar-item-pill--task-done' : 'calendar-item-pill--task-pending'}`;
                    pill.innerHTML = `${completed ? '✓' : '○'} ${task.title}`;
                    dayCell.appendChild(pill);
                }
            });
            
            // B. Add project deadlines
            projects.forEach(proj => {
                if (proj.deadline === dayDateStr) {
                    const pill = document.createElement("div");
                    pill.className = "calendar-item-pill calendar-item-pill--project";
                    pill.innerHTML = `🏁 Deadline: ${proj.title}`;
                    dayCell.appendChild(pill);
                    
                    // Display Project Milestones/ToDos inside parent deadline cell
                    if (proj.milestones && proj.milestones.length > 0) {
                        proj.milestones.forEach(m => {
                            const mPill = document.createElement("div");
                            mPill.className = "calendar-item-pill calendar-item-pill--milestone";
                            mPill.innerHTML = `${m.completed ? '☑' : '☐'} ToDo: ${m.title}`;
                            dayCell.appendChild(mPill);
                        });
                    }
                }
            });
            
            // C. Add goal targets
            goals.forEach(goal => {
                if (goal.target_date === dayDateStr) {
                    const pill = document.createElement("div");
                    pill.className = "calendar-item-pill calendar-item-pill--goal";
                    pill.innerHTML = `🎯 Goal Target: ${goal.title}`;
                    dayCell.appendChild(pill);
                }
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
