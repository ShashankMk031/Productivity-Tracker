/**
 * app.js — Main application controller.
 * Renders a schedule-aware monthly matrix with inline notes and a persistent sidebar.
 */

import * as api from "./api.js";
import { initProductivityOS } from "./productivity_os.js";
import {
  getDayKey,
  getLogicalDateIST,
  getLogicalTodayIST,
  getMonthFromDateKey,
  formatMonthLabel,
  formatNoteDate,
  isFutureLogicalDate,
  isLogicalTodayIST,
} from "./date.js";
import { DAY_ORDER, PRESET_OPTIONS, getPresetLabel, normalizeActiveDays, sameSchedule } from "./schedule.js";
import { confirm as uiConfirm, initTaskModal, openTaskModal, toast } from "./ui.js";

const initialLogicalDate = getLogicalDateIST();
const initialMonth = getMonthFromDateKey(initialLogicalDate);

const state = {
  year: initialMonth.year,
  month: initialMonth.month,
  data: null,
  selectedTaskId: null,
  scheduleDrafts: {},
  openActionMenuTaskId: null,
  archivedExpanded: false,
  activeNoteTaskId: null,
  activeNoteDate: null,
};

async function init() {
  initTaskModal(handleSaveTask);

  const addTaskBtn = document.getElementById("add-task-btn");
  if (addTaskBtn) {
    addTaskBtn.addEventListener("click", (e) => { e.preventDefault(); openTaskModal(); });
  }
  document.getElementById("add-task-btn-bottom").addEventListener("click", () => openTaskModal());
  
  const prevMonthBtn = document.getElementById("prev-month-btn");
  const nextMonthBtn = document.getElementById("next-month-btn");
  const todayBtn = document.getElementById("today-btn");
  const settingsBtn = document.getElementById("settings-btn");

  if (prevMonthBtn) {
    prevMonthBtn.addEventListener("click", () => {
      changeMonth(-1);
    });
  }

  if (nextMonthBtn) {
    nextMonthBtn.addEventListener("click", () => {
      changeMonth(1);
    });
  }

  if (todayBtn) {
    todayBtn.addEventListener("click", () => {
      jumpToToday();
    });
  }

  if (settingsBtn) {
    settingsBtn.addEventListener("click", () => {
      window.location.href = "/settings";
    });
  }

  document.getElementById("completed-toggle-btn").addEventListener("click", () => {
    state.archivedExpanded = !state.archivedExpanded;
    renderArchivedVisibility();
  });
  document.addEventListener("click", handleDocumentClick);

  await loadAll();
  initProductivityOS();
}

async function loadAll() {
  showLoading(true);
  try {
    const monthData = await api.getMonthData(state.year, state.month);
    state.data = monthData;
    syncSelectedTask();
    renderHeader();
    renderTracker();
    await renderArchived();
  } catch (error) {
    toast(`Failed to load data: ${error.message}`, "error");
    console.error(error);
  } finally {
    showLoading(false);
  }
}

function syncSelectedTask() {
  const tasks = state.data?.tasks || [];
  const taskIds = new Set(tasks.map((task) => task.id));

  if (!taskIds.has(state.selectedTaskId)) {
    state.selectedTaskId = tasks[0]?.id ?? null;
  }
  if (!taskIds.has(state.openActionMenuTaskId)) {
    state.openActionMenuTaskId = null;
  }

  for (const taskId of Object.keys(state.scheduleDrafts)) {
    if (!taskIds.has(Number(taskId))) delete state.scheduleDrafts[taskId];
  }

  if (state.activeNoteTaskId !== null && !taskIds.has(state.activeNoteTaskId)) {
    state.activeNoteTaskId = null;
    state.activeNoteDate = null;
  }
}

function getLogicalToday() {
  return state.data?.meta?.logical_today || getLogicalTodayIST();
}

function changeMonth(delta) {
  state.month += delta;
  if (state.month > 12) {
    state.month = 1;
    state.year += 1;
  }
  if (state.month < 1) {
    state.month = 12;
    state.year -= 1;
  }
  loadAll();
}

function jumpToToday() {
  const today = getMonthFromDateKey(getLogicalTodayIST());
  state.year = today.year;
  state.month = today.month;
  loadAll();
}

function renderHeader() {
  const { data, year, month } = state;
  document.getElementById("month-label").textContent = formatMonthLabel(year, month);
  document.getElementById("day-reset-indicator").textContent = data.meta?.day_reset_label || "Day count resets at 04:00 AM (IST)";
}

function renderTracker() {
  const container = document.getElementById("tracker-body");
  container.innerHTML = "";

  const tasks = state.data?.tasks || [];
  if (!tasks.length) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No tasks yet. Click <strong>+ Add Task</strong> to get started.</p>
      </div>
    `;
    return;
  }

  container.appendChild(buildCalendarHeader());
  tasks.forEach((task) => container.appendChild(buildTaskRow(task)));
}

function buildCalendarHeader() {
  const header = document.createElement("div");
  header.className = "calendar-header-row";
  header.innerHTML = `
    <div class="calendar-header-row__spacer"></div>
    <div class="calendar-header-days">${buildDayHeaderCells()}</div>
    <div class="calendar-header-row__actions"> </div>
  `;
  return header;
}

function buildDayHeaderCells() {
  return Object.keys(state.data.tasks[0].days).map((dateValue) => `
    <div class="calendar-day-head ${isLogicalTodayIST(dateValue, getLogicalToday()) ? "calendar-day-head--today" : ""}">
      <span class="calendar-day-head__date">${Number(dateValue.slice(8))}</span>
      <span class="calendar-day-head__weekday">${esc(getDayKey(dateValue))}</span>
    </div>
  `).join("");
}

function buildTaskRow(task) {
  const row = document.createElement("article");
  row.className = "task-matrix-row";

  row.appendChild(buildTaskInfo(task));
  row.appendChild(buildTaskDayArea(task));
  row.appendChild(buildTaskActions(task));

  return row;
}

function buildTaskInfo(task) {
  const info = document.createElement("button");
  info.type = "button";
  info.className = "task-matrix-info";

  info.innerHTML = `
    <div class="task-matrix-info__title-row">
      <span class="task-matrix-info__title">${esc(task.title)}</span>
      <span class="task-matrix-info__status ${task.recurring ? "task-matrix-info__status--active" : "task-matrix-info__status--muted"}">
        ${task.recurring ? "◔" : "•"}
      </span>
    </div>
    <div class="task-matrix-info__schedule">${esc(getPresetLabel(task.active_days))}</div>
    <div class="task-matrix-info__stats">
      <span class="task-stat" title="Current Streak">🔥 ${task.streak || 0}</span>
      <span class="task-stat" title="Month Completion">✓ ${task.completion_pct || 0}%</span>
    </div>
    <div class="task-matrix-info__notes-label">Notes:</div>
  `;

  return info;
}

function buildTaskDayArea(task) {
  const area = document.createElement("div");
  area.className = "task-matrix-days";

  const checkStrip = document.createElement("div");
  checkStrip.className = "task-day-check-strip";

  const notesStrip = document.createElement("div");
  notesStrip.className = "task-day-notes-strip";

  Object.entries(task.days).forEach(([dateValue, entry]) => {
    checkStrip.appendChild(buildDaySquareWrapper(task, dateValue, entry));

    if (entry.note || (state.activeNoteTaskId === task.id && state.activeNoteDate === dateValue)) {
      notesStrip.appendChild(buildNoteCard(task, dateValue, entry));
    }
  });

  area.appendChild(checkStrip);
  area.appendChild(notesStrip);
  return area;
}

function buildDaySquareWrapper(task, dateValue, entry) {
  const logicalToday = getLogicalToday();
  const dayState = getDayState(dateValue, entry, logicalToday);
  const interactive = isInteractiveDay(dayState);

  const wrapper = document.createElement("div");
  wrapper.className = "task-day-square-wrapper";
  if (isLogicalTodayIST(dateValue, logicalToday)) {
    wrapper.classList.add("task-day-square-wrapper--today");
  }
  wrapper.dataset.tooltip = buildDayTooltip(dateValue, entry, dayState);

  const square = document.createElement("button");
  square.type = "button";
  square.className = ["task-day-square", `task-day-square--${dayState}`].join(" ");
  square.disabled = !interactive;
  if (dayState === "completed") square.textContent = "";

  if (interactive) {
    square.addEventListener("click", async () => {
      state.activeNoteTaskId = task.id;
      state.activeNoteDate = dateValue;
      await handleToggle(task.id, dateValue);
    });
  }

  wrapper.appendChild(square);
  return wrapper;
}

function buildNoteCard(task, dateValue, entry) {
  const dayState = getDayState(dateValue, entry, getLogicalToday());
  const interactive = isInteractiveDay(dayState);

  const card = document.createElement("div");
  card.className = "task-note-card";
  
  const header = document.createElement("div");
  header.className = "task-note-card__header";
  header.textContent = formatNoteDate(dateValue);

  const note = document.createElement("textarea");
  note.className = "task-note-card__input";
  note.rows = 2;
  note.maxLength = 240;
  note.value = entry.note || "";
  note.dataset.savedValue = entry.note || "";
  note.disabled = !interactive;
  note.placeholder = "Add note...";

  if (interactive) {
    note.addEventListener("blur", async () => {
      const nextValue = note.value.trim();
      if (nextValue === note.dataset.savedValue) {
        if (!nextValue && state.activeNoteDate === dateValue) {
          state.activeNoteTaskId = null;
          state.activeNoteDate = null;
          renderTracker();
        }
        return;
      }
      const saved = await saveNote(task.id, dateValue, nextValue);
      if (saved) {
        note.dataset.savedValue = nextValue;
        state.activeNoteTaskId = null;
        state.activeNoteDate = null;
        renderTracker();
      }
    });
    note.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        note.blur();
      }
    });
  }

  if (state.activeNoteTaskId === task.id && state.activeNoteDate === dateValue) {
    setTimeout(() => note.focus(), 0);
  }

  card.append(header, note);
  return card;
}

function buildTaskActions(task) {
  const actions = document.createElement("div");
  actions.className = "task-matrix-actions";

  const button = document.createElement("button");
  button.type = "button";
  button.className = "task-matrix-actions__toggle";
  button.textContent = "⋯";
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    state.openActionMenuTaskId = state.openActionMenuTaskId === task.id ? null : task.id;
    renderTracker();
  });

  actions.appendChild(button);

  if (state.openActionMenuTaskId === task.id) {
    const menu = document.createElement("div");
    menu.className = "task-action-menu";
    menu.addEventListener("click", (event) => event.stopPropagation());
    menu.append(
      buildActionMenuItem("Edit Task", () => {
        state.openActionMenuTaskId = null;
        renderTracker();
        openTaskModal(task);
      }),
      buildActionMenuItem("Move to completed", async () => {
        await handleArchive(task.id);
      }),
      buildActionMenuItem("Delete task", async () => {
        await handleDelete(task.id);
      }, "task-action-menu__item--danger"),
    );
    actions.appendChild(menu);
  }

  return actions;
}

function buildActionMenuItem(label, onClick, extraClass = "") {
  const button = document.createElement("button");
  button.type = "button";
  button.className = ["task-action-menu__item", extraClass].filter(Boolean).join(" ");
  button.textContent = label;
  button.addEventListener("click", async (event) => {
    event.stopPropagation();
    state.openActionMenuTaskId = null;
    await onClick();
  });
  return button;
}


async function saveSchedule(taskId) {
  const nextDays = normalizeActiveDays(state.scheduleDrafts[taskId]);
  try {
    await api.updateTask(taskId, { active_days: nextDays });
    toast("Schedule updated");
    delete state.scheduleDrafts[taskId];
    await loadAll();
  } catch (error) {
    toast(`Schedule update failed: ${error.message}`, "error");
  }
}

async function handleToggle(taskId, dateValue) {
  try {
    const result = await api.toggleEntry(taskId, dateValue);
    updateEntryInState(taskId, dateValue, {
      completed: result.completed,
      note: result.note,
      active: true,
    });
    
    const task = state.data?.tasks.find((item) => item.id === taskId);
    if (task && result.streak !== undefined) {
      task.streak = result.streak;
    }
    
    recomputeStats();
    renderTracker();
  } catch (error) {
    toast(`Toggle failed: ${error.message}`, "error");
  }
}

async function saveNote(taskId, dateValue, note) {
  try {
    const result = await api.updateNote(taskId, dateValue, note);
    updateEntryInState(taskId, dateValue, {
      completed: result.completed,
      note: result.note,
      active: result.active,
    });
    renderTracker();
    return true;
  } catch (error) {
    toast(`Note save failed: ${error.message}`, "error");
    return false;
  }
}

function updateEntryInState(taskId, dateValue, patch) {
  const task = state.data?.tasks.find((item) => item.id === taskId);
  if (!task) return;
  task.days[dateValue] = {
    ...task.days[dateValue],
    ...patch,
  };
}

async function handleSaveTask(title, recurring, activeDays, existingTaskId) {
  try {
    if (existingTaskId) {
      await api.updateTask(existingTaskId, title, recurring, activeDays);
      toast(`"${title}" updated`);
    } else {
      await api.addTask(title, recurring, activeDays);
      toast(`"${title}" added`);
    }
    await loadAll();
  } catch (error) {
    toast(`Failed to save task: ${error.message}`, "error");
    throw error;
  }
}

async function handleDelete(taskId) {
  if (!uiConfirm("Delete this task and all its history permanently?")) return;
  try {
    await api.deleteTask(taskId);
    toast("Task deleted");
    await loadAll();
  } catch (error) {
    toast(`Delete failed: ${error.message}`, "error");
  }
}

async function handleArchive(taskId) {
  if (!uiConfirm("Mark this task as permanently completed?")) return;
  try {
    await api.archiveTask(taskId);
    toast("Moved to Completed Goals");
    await loadAll();
  } catch (error) {
    toast(`Archive failed: ${error.message}`, "error");
  }
}

async function handleRestore(taskId) {
  try {
    await api.restoreTask(taskId);
    toast("Task restored");
    await loadAll();
  } catch (error) {
    toast(`Restore failed: ${error.message}`, "error");
  }
}

async function renderArchived() {
  const section = document.getElementById("archived-section");
  const list = document.getElementById("archived-list");
  const tasks = await api.getArchivedTasks().catch(() => []);

  list.innerHTML = "";
  if (!tasks.length) {
    section.classList.add("hidden");
    return;
  }

  section.classList.remove("hidden");
  tasks.forEach((task) => {
    const item = document.createElement("div");
    item.className = "archived-item";
    item.innerHTML = `
      <div class="archived-info">
        <span class="archived-title">${esc(task.title)}</span>
        <span class="archived-date">Completed · ${task.created_at}</span>
      </div>
      <button class="archive-restore-btn" title="Restore to active">Restore</button>
    `;
    item.querySelector(".archive-restore-btn").addEventListener("click", () => handleRestore(task.id));
    list.appendChild(item);
  });
  renderArchivedVisibility();
}

function renderArchivedVisibility() {
  const section = document.getElementById("archived-section");
  const toggle = document.getElementById("completed-toggle-btn");
  if (section.classList.contains("hidden")) return;
  section.style.display = state.archivedExpanded ? "block" : "none";
  toggle.textContent = state.archivedExpanded ? "🏆 Completed Tasks ▲" : "🏆 Completed Tasks ▼";
}

function handleDocumentClick() {
  if (state.openActionMenuTaskId !== null) {
    state.openActionMenuTaskId = null;
    renderTracker();
  }
}

function recomputeStats() {
  if (!state.data) return;
  const logicalToday = getLogicalToday();
  const monthEnd = dateStr(state.year, state.month, state.data.days_in_month);
  const until = logicalToday < monthEnd ? logicalToday : monthEnd;

  state.data.tasks.forEach((task) => {
    let taskTotal = 0;
    let taskDone = 0;
    Object.entries(task.days).forEach(([dateValue, entry]) => {
      if (entry.active && dateValue <= until) {
        taskTotal += 1;
        if (entry.completed) taskDone += 1;
      }
    });
    task.completion_pct = taskTotal ? +(taskDone / taskTotal * 100).toFixed(1) : 0;
  });
}

function isFutureDay(dateValue, logicalToday = getLogicalToday()) {
  return isFutureLogicalDate(dateValue, logicalToday);
}

function isScheduledDay(entry) {
  return !!entry?.active;
}

function getDayState(dateValue, entry, logicalToday = getLogicalToday()) {
  if (isFutureDay(dateValue, logicalToday)) return "future";
  if (!isScheduledDay(entry)) return "not-scheduled";
  if (entry?.completed) return "completed";
  return "not-done";
}

function isInteractiveDay(dayState) {
  return dayState === "completed" || dayState === "not-done";
}

function getNotePlaceholder(dayState) {
  if (dayState === "future") return "";
  if (dayState === "not-scheduled") return "";
  return "";
}

function buildDayTooltip(dateValue, entry, dayState) {
  const parts = [dateValue, getDayKey(dateValue), dayState.replace("-", " ")];
  if (entry.note) parts.push(entry.note);
  return parts.join(" · ");
}

function dateStr(year, month, day) {
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function esc(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function showLoading(visible) {
  document.getElementById("loading-overlay").classList.toggle("hidden", !visible);
}

document.addEventListener("DOMContentLoaded", init);
