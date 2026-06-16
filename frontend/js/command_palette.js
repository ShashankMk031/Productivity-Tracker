import { fetchAPI } from './api.js';
import { toast } from './ui.js';

// Inject CSS styles for Command Palette items
const style = document.createElement("style");
style.textContent = `
  .command-palette-item {
    padding: 12px 16px;
    font-size: 14px;
    color: var(--text);
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: background 0.1s;
    background: transparent;
    border: none;
    width: 100%;
    text-align: left;
    outline: none;
  }
  .command-palette-item:hover, .command-palette-item--selected {
    background: rgba(255, 255, 255, 0.08);
  }
  .command-palette-item__title {
    font-weight: 500;
  }
  .command-palette-item__shortcut {
    font-size: 11px;
    color: var(--muted);
    font-family: monospace;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border);
    padding: 1px 5px;
    border-radius: 3px;
  }
`;
document.head.appendChild(style);

let modal;
let overlay;
let input;
let resultsContainer;
let selectedIndex = 0;
let filteredItems = [];

// Static navigation / shortcut actions
const STATIC_COMMANDS = [
  { title: "📅 Go to Calendar", action: () => window.location.href = "/calendar", shortcut: "G C" },
  { title: "📈 Go to Reports Dashboard", action: () => window.location.href = "/reports", shortcut: "G R" },
  { title: "⚙️ Go to Settings", action: () => window.location.href = "/settings", shortcut: "G S" },
  { title: "🎯 Create New Goal", action: () => { document.getElementById("btn-add-goal")?.click(); }, shortcut: "N G" },
  { title: "🏁 Create New Project", action: () => { document.getElementById("btn-add-project")?.click(); }, shortcut: "N P" }
];

function initCommandPalette() {
  modal = document.getElementById("command-palette-modal");
  overlay = document.getElementById("command-palette-overlay");
  input = document.getElementById("command-palette-input");
  resultsContainer = document.getElementById("command-palette-results");

  if (!modal || !input || !resultsContainer) return;

  // Global Key listener for Cmd+K / Ctrl+K
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      openPalette();
    }
  });

  // Modal key controls
  input.addEventListener("keydown", handleInputKeydown);
  input.addEventListener("input", filterAndRender);

  if (overlay) {
    overlay.addEventListener("click", closePalette);
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initCommandPalette);
} else {
  initCommandPalette();
}

function openPalette() {
  modal.classList.add("modal--open");
  input.value = "";
  selectedIndex = 0;
  filterAndRender();
  setTimeout(() => input.focus(), 50);
}

function closePalette() {
  modal.classList.remove("modal--open");
  input.blur();
}

function filterAndRender() {
  const query = input.value.trim();
  filteredItems = [];

  // Parse Slash commands
  if (query.startsWith("/")) {
    if (query.startsWith("/focus ")) {
      const desc = query.slice(7).trim();
      filteredItems.push({
        title: `⏱️ Start Focus Session: "${desc || '...'}"`,
        action: () => triggerStartFocus(desc)
      });
    } else if (query.startsWith("/task ")) {
      const taskTitle = query.slice(6).trim();
      filteredItems.push({
        title: `✅ Add Habit: "${taskTitle || '...'}"`,
        action: () => triggerAddTask(taskTitle)
      });
    } else if (query.startsWith("/remind ")) {
      const remindText = query.slice(8).trim();
      // Regex search for " at HH:MM"
      const match = remindText.match(/(.+?)\s+at\s+(\d{1,2}:\d{2})/i);
      if (match) {
        const title = match[1].trim();
        const time = match[2].trim();
        filteredItems.push({
          title: `🔔 Add Reminder: "${title}" at ${time}`,
          action: () => triggerAddReminder(title, time)
        });
      } else {
        filteredItems.push({
          title: `🔔 Add Reminder: "${remindText || '...'}" (type "at HH:MM" to schedule)`,
          action: () => toast("Please suffix with 'at HH:MM' to schedule reminder", "error")
        });
      }
    } else {
      // General slash helper
      filteredItems.push({ title: "⏱️ /focus [description] - Start focus session", action: () => { input.value = "/focus "; filterAndRender(); } });
      filteredItems.push({ title: "✅ /task [title] - Quick add habit", action: () => { input.value = "/task "; filterAndRender(); } });
      filteredItems.push({ title: "🔔 /remind [title] at [HH:MM] - Add reminder", action: () => { input.value = "/remind "; filterAndRender(); } });
    }
  } else {
    // General text filtering on static navigation commands
    STATIC_COMMANDS.forEach(cmd => {
      if (!query || cmd.title.toLowerCase().includes(query.toLowerCase())) {
        filteredItems.push(cmd);
      }
    });

    // Offer slash shortcuts as helpers if query is empty
    if (!query) {
      filteredItems.push({ title: "⏱️ Type /focus to start focus session...", action: () => { input.value = "/focus "; filterAndRender(); } });
      filteredItems.push({ title: "✅ Type /task to add a habit...", action: () => { input.value = "/task "; filterAndRender(); } });
      filteredItems.push({ title: "🔔 Type /remind to add a reminder...", action: () => { input.value = "/remind "; filterAndRender(); } });
    }
  }

  renderItems();
}

function renderItems() {
  resultsContainer.innerHTML = "";
  
  if (filteredItems.length === 0) {
    resultsContainer.innerHTML = `<div style="padding:16px; font-size:12px; color:var(--muted); text-align:center;">No matching commands found.</div>`;
    return;
  }

  // Bound index
  if (selectedIndex >= filteredItems.length) selectedIndex = filteredItems.length - 1;
  if (selectedIndex < 0) selectedIndex = 0;

  filteredItems.forEach((item, index) => {
    const el = document.createElement("button");
    el.type = "button";
    el.className = "command-palette-item";
    if (index === selectedIndex) {
      el.classList.add("command-palette-item--selected");
    }

    const titleSpan = document.createElement("span");
    titleSpan.className = "command-palette-item__title";
    titleSpan.textContent = item.title;
    el.appendChild(titleSpan);

    if (item.shortcut) {
      const shortcutSpan = document.createElement("span");
      shortcutSpan.className = "command-palette-item__shortcut";
      shortcutSpan.textContent = item.shortcut;
      el.appendChild(shortcutSpan);
    }

    el.addEventListener("click", () => {
      executeItem(item);
    });

    resultsContainer.appendChild(el);
  });
}

function handleInputKeydown(e) {
  if (e.key === "Escape") {
    e.preventDefault();
    closePalette();
  } else if (e.key === "ArrowDown") {
    e.preventDefault();
    selectedIndex = (selectedIndex + 1) % filteredItems.length;
    renderItems();
    scrollSelectedIntoView();
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    selectedIndex = (selectedIndex - 1 + filteredItems.length) % filteredItems.length;
    renderItems();
    scrollSelectedIntoView();
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (filteredItems[selectedIndex]) {
      executeItem(filteredItems[selectedIndex]);
    }
  }
}

function executeItem(item) {
  closePalette();
  item.action();
}

function scrollSelectedIntoView() {
  const selectedEl = resultsContainer.querySelector(".command-palette-item--selected");
  if (selectedEl) {
    selectedEl.scrollIntoView({ block: "nearest" });
  }
}

// ── Command Trigger Actions ─────────────────────────────────────────────────

async function triggerStartFocus(description) {
  const title = description ? description.trim() : "";
  if (!title) {
    toast("Please specify what you are focusing on!", "error");
    return;
  }
  try {
    await fetchAPI('/focus/start', {
      method: 'POST',
      body: JSON.stringify({ title })
    });
    toast(`Focus Session started: "${title}" 🎯`);
    window.location.reload();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function triggerAddTask(titleText) {
  const title = titleText ? titleText.trim() : "";
  if (!title) {
    toast("Habit title is required!", "error");
    return;
  }
  try {
    await fetchAPI('/tasks', {
      method: 'POST',
      body: JSON.stringify({
        title,
        recurring: 1,
        active_days: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
      })
    });
    toast(`Habit "${title}" created successfully!`);
    window.location.reload();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function triggerAddReminder(titleText, timeStr) {
  const title = titleText ? titleText.trim() : "";
  if (!title || !timeStr) {
    toast("Title and time are required!", "error");
    return;
  }
  
  // Format full YYYY-MM-DDTHH:MM:00 ISO string using system date
  const now = new Date();
  const dateStr = now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, '0') + "-" + String(now.getDate()).padStart(2, '0');
  const datetime = `${dateStr}T${timeStr}:00`;
  
  try {
    await fetchAPI('/reminders', {
      method: 'POST',
      body: JSON.stringify({
        title,
        datetime,
        recurring: 'none'
      })
    });
    toast(`Reminder "${title}" scheduled at ${timeStr}! 🔔`);
    window.location.reload();
  } catch (err) {
    toast(err.message, "error");
  }
}
