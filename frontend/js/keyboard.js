import { toast } from './ui.js';

let selectedIndex = -1;

export function initKeyboardNav(state, loadAll, renderTracker, handleToggle, getLogicalToday) {
  // Inject visual selected row highlight styles
  const style = document.createElement("style");
  style.textContent = `
    .task-matrix-row--selected {
      outline: 2px solid var(--green) !important;
      outline-offset: -2px;
      background: rgba(84, 209, 79, 0.04) !important;
      box-shadow: 0 0 10px rgba(84, 209, 79, 0.1);
    }
  `;
  document.head.appendChild(style);

  document.addEventListener("keydown", async (e) => {
    // 1. Guard input focus
    const active = document.activeElement;
    if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.tagName === "SELECT" || active.isContentEditable)) {
      return;
    }

    // 2. Guard modal open
    if (document.querySelector(".modal--open")) {
      return;
    }

    const rows = Array.from(document.querySelectorAll(".task-matrix-row"));
    if (rows.length === 0) return;

    if (e.key === "j" || e.key === "ArrowDown") {
      e.preventDefault();
      clearSelection(rows);
      selectedIndex = (selectedIndex + 1) % rows.length;
      highlightRow(rows[selectedIndex]);
    } else if (e.key === "k" || e.key === "ArrowUp") {
      e.preventDefault();
      clearSelection(rows);
      selectedIndex = (selectedIndex - 1 + rows.length) % rows.length;
      highlightRow(rows[selectedIndex]);
    } else if (e.key === " " && selectedIndex !== -1) {
      e.preventDefault();
      const selectedRow = rows[selectedIndex];
      const taskId = parseInt(selectedRow.dataset.taskId);
      const todayStr = getLogicalToday();
      
      if (taskId && todayStr) {
        await handleToggle(taskId, todayStr);
        toast("Habit completion toggled");
      }
    } else if (e.key === "n" && selectedIndex !== -1) {
      e.preventDefault();
      const selectedRow = rows[selectedIndex];
      const taskId = parseInt(selectedRow.dataset.taskId);
      const todayStr = getLogicalToday();
      
      if (taskId && todayStr) {
        // Set active note state in app.js and trigger re-render
        state.activeNoteTaskId = taskId;
        state.activeNoteDate = todayStr;
        renderTracker();
      }
    }
  });
}

function clearSelection(rows) {
  rows.forEach(r => r.classList.remove("task-matrix-row--selected"));
}

function highlightRow(row) {
  if (row) {
    row.classList.add("task-matrix-row--selected");
    row.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
}
