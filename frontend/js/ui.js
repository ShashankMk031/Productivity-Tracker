/**
 * ui.js — Shared UI helpers: toast notifications and task modal.
 */

let toastTimer;

export function toast(msg, type = "success") {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    document.body.appendChild(el);
  }

  el.textContent = msg;
  el.className = `toast toast--${type} toast--visible`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("toast--visible"), 2800);
}

export function confirm(msg) {
  return window.confirm(msg);
}

const PRESET_OPTIONS = [
  { key: "everyday", days: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] },
  { key: "weekdays", days: ["Mon", "Tue", "Wed", "Thu", "Fri"] },
  { key: "weekends", days: ["Sat", "Sun"] },
  { key: "saturday", days: ["Sat"] },
  { key: "sunday", days: ["Sun"] }
];

let editingTaskId = null;

export function openTaskModal(task = null) {
  const modal = document.getElementById("task-modal");
  const titleEl = document.getElementById("task-modal-title");
  const inputEl = document.getElementById("task-modal-input");
  const recurringEl = document.getElementById("task-modal-recurring");
  const scheduleSection = document.getElementById("task-modal-schedule-section");
  
  scheduleSection.style.display = "none";
  
  if (task) {
    editingTaskId = task.id;
    titleEl.textContent = "Edit Task";
    inputEl.value = task.title;
    recurringEl.checked = !!task.recurring;
    setScheduleUI(task.active_days);
  } else {
    editingTaskId = null;
    titleEl.textContent = "New Task";
    inputEl.value = "";
    recurringEl.checked = true;
    setScheduleUI(PRESET_OPTIONS[0].days); // everyday
  }
  
  modal.classList.add("modal--open");
  inputEl.focus();
}

function setScheduleUI(activeDays) {
  const checks = document.querySelectorAll('#task-modal-custom-days input[type="checkbox"]');
  checks.forEach(check => {
    check.checked = activeDays.includes(check.value);
  });
}

function getScheduleUI() {
  const checks = document.querySelectorAll('#task-modal-custom-days input[type="checkbox"]:checked');
  return Array.from(checks).map(c => c.value);
}

export function closeTaskModal() {
  document.getElementById("task-modal").classList.remove("modal--open");
}

export function initTaskModal(onSave) {
  const saveBtn = document.getElementById("task-modal-save-btn");
  const closeBtn = document.getElementById("task-modal-close-btn");
  const overlay = document.getElementById("task-modal-overlay");
  const cancelBtn = document.getElementById("task-modal-cancel-btn");
  const optionsBtn = document.getElementById("task-modal-options-btn");
  
  optionsBtn.addEventListener("click", () => {
    const section = document.getElementById("task-modal-schedule-section");
    section.style.display = section.style.display === "none" ? "block" : "none";
  });
  


  saveBtn.addEventListener("click", async () => {
    const title = document.getElementById("task-modal-input").value.trim();
    const recurring = document.getElementById("task-modal-recurring").checked;
    const activeDays = getScheduleUI();
    
    if (!title) {
      toast("Task name cannot be empty", "error");
      return;
    }
    if (activeDays.length === 0) {
      toast("Choose at least one active day", "error");
      return;
    }

    try {
      await onSave(title, recurring, activeDays, editingTaskId);
      closeTaskModal();
    } catch {
      // Caller surfaces error
    }
  });

  closeBtn.addEventListener("click", closeTaskModal);
  cancelBtn.addEventListener("click", closeTaskModal);
  overlay.addEventListener("click", closeTaskModal);

  document.getElementById("task-modal-input").addEventListener("keydown", (event) => {
    if (event.key === "Enter") saveBtn.click();
    if (event.key === "Escape") closeTaskModal();
  });
}
