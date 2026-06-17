// Shared Navigation Module for Productivity Tracker MPA

// Global Error & Promise Rejection handler to diagnose loading screen locks
window.addEventListener('error', function(e) {
  console.error("[Global Error Exception]", e);
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.remove('hidden');
    overlay.style.background = 'rgba(30, 5, 5, 0.98)';
    overlay.style.zIndex = '99999';
    overlay.innerHTML = `<pre style="color: #ff5b5b; padding: 30px; font-family: monospace; font-size: 14px; white-space: pre-wrap; word-break: break-all; max-width: 90%; line-height: 1.5; border: 1px solid #ff3333; background: #0c0202; border-radius: 8px;">❌ [JS Runtime Error]\n\n${e.message}\n\nFile: ${e.filename}\nLine: ${e.lineno}:${e.colno}\n\nStack:\n${e.error ? e.error.stack : 'N/A'}</pre>`;
  }
});

window.addEventListener('unhandledrejection', function(e) {
  console.error("[Unhandled Promise Rejection]", e);
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.remove('hidden');
    overlay.style.background = 'rgba(30, 5, 5, 0.98)';
    overlay.style.zIndex = '99999';
    overlay.innerHTML = `<pre style="color: #ff5b5b; padding: 30px; font-family: monospace; font-size: 14px; white-space: pre-wrap; word-break: break-all; max-width: 90%; line-height: 1.5; border: 1px solid #ff3333; background: #0c0202; border-radius: 8px;">❌ [Unhandled Rejection]\n\n${e.reason && e.reason.message ? e.reason.message : e.reason}\n\nStack:\n${e.reason && e.reason.stack ? e.reason.stack : 'N/A'}</pre>`;
  }
});

const PAGE_INFOS = {
  '/': {
    title: '⚡ Today\'s Execution Center',
    breadcrumb: 'Dashboard / Overview',
    description: 'Track daily consistency scores, active focus sessions, habit schedules, and log daily thoughts.'
  },
  '/dashboard': {
    title: '⚡ Today\'s Execution Center',
    breadcrumb: 'Dashboard / Overview',
    description: 'Track daily consistency scores, active focus sessions, habit schedules, and log daily thoughts.'
  },
  '/tasks': {
    title: '✅ Active Tasks & Habits',
    breadcrumb: 'Tasks / Habits Matrix',
    description: 'Manage recurring habits, view monthly progress charts, and schedule active execution days.'
  },
  '/goals': {
    title: '🎯 Strategic Goals',
    breadcrumb: 'Goals / Strategic Timeline',
    description: 'Set and track key strategic long-term, short-term, and step-up milestones.'
  },
  '/projects': {
    title: '🏁 Deadline Projects',
    breadcrumb: 'Projects / Deliverables',
    description: 'Plan project structures, link parent goals, check off milestones, and observe progress.'
  },
  '/calendar': {
    title: '📅 Monthly Calendar Log',
    breadcrumb: 'Calendar / Monthly View',
    description: 'Review historically logged habits, completed projects, timers, and consolidated journal notes.'
  },
  '/reports': {
    title: '📈 Performance Analytics',
    breadcrumb: 'Reports / Analytics Dashboard',
    description: 'Generate weekly or monthly productivity reports, view macro trends, and compare cycles.'
  },
  '/insights': {
    title: '🧠 Intelligence & Foresight',
    breadcrumb: 'Insights / Foresight Engine',
    description: 'View burnout warnings, accuracy dashboards, and predictive consistency analytics.'
  },
  '/board': {
    title: '📝 Sticky Notes Board',
    breadcrumb: 'Board / Whiteboard Canvas',
    description: 'A freeform canvas for brainstorming, organizing ideas, and auto-saving quick thoughts.'
  },
  '/settings': {
    title: '⚙️ System Settings & Health',
    breadcrumb: 'Settings / Configuration',
    description: 'Manage local data backups, execute startup integrity checks, and view database size.'
  }
};

function injectSidebar() {
  const container = document.getElementById("sidebar-nav-container");
  if (!container) return;

  const currentPath = window.location.pathname;

  container.innerHTML = `
    <div class="sidebar-nav">
      <div class="sidebar-brand">
        🚀 Productivity Tracker
      </div>
      <ul class="sidebar-menu">
        <li class="sidebar-menu-item ${currentPath === '/dashboard' || currentPath === '/' ? 'active' : ''}"><a href="/dashboard">⚡ Dashboard</a></li>
        <li class="sidebar-menu-item ${currentPath === '/tasks' ? 'active' : ''}"><a href="/tasks">✅ Active Tasks</a></li>
        <li class="sidebar-menu-item ${currentPath === '/goals' ? 'active' : ''}"><a href="/goals">🎯 Strategic Goals</a></li>
        <li class="sidebar-menu-item ${currentPath === '/projects' ? 'active' : ''}"><a href="/projects">🏁 Deadline Projects</a></li>
        <li class="sidebar-menu-item ${currentPath === '/board' ? 'active' : ''}"><a href="/board">📝 Sticky Board</a></li>
        <li class="sidebar-menu-item ${currentPath === '/calendar' ? 'active' : ''}"><a href="/calendar">📅 Monthly Calendar</a></li>
        <li class="sidebar-menu-item ${currentPath === '/reports' ? 'active' : ''}"><a href="/reports">📈 Reports Dashboard</a></li>
        <li class="sidebar-menu-item ${currentPath === '/insights' ? 'active' : ''}"><a href="/insights">🧠 Intelligence Insights</a></li>
        <li class="sidebar-menu-item ${currentPath === '/settings' ? 'active' : ''}"><a href="/settings">⚙️ System Settings</a></li>
      </ul>
      <div class="sidebar-footer">
        <span>local-first · no auth</span>
        <span>v1.3.0</span>
      </div>
    </div>
  `;
}

function injectPageHeader() {
  const mainArea = document.querySelector(".main-content-area");
  if (!mainArea) return;

  if (document.getElementById("ui-dynamic-page-header")) return;

  const currentPath = window.location.pathname;
  const info = PAGE_INFOS[currentPath] || PAGE_INFOS['/dashboard'];

  const headerDiv = document.createElement("div");
  headerDiv.id = "ui-dynamic-page-header";
  headerDiv.className = "ui-page-header";
  headerDiv.style.marginBottom = "var(--space-lg)";
  headerDiv.style.borderBottom = "1px solid var(--border)";
  headerDiv.style.paddingBottom = "var(--space-md)";
  
  headerDiv.innerHTML = `
    <div class="ui-breadcrumb" style="font-size: 11px; text-transform: uppercase; color: var(--muted); letter-spacing: 0.5px; margin-bottom: var(--space-xs); font-weight: 600;">
      ${info.breadcrumb}
    </div>
    <h1 class="ui-page-title" style="font-size: 24px; font-weight: 700; color: var(--text); margin-bottom: 4px;">
      ${info.title}
    </h1>
    <p class="ui-page-description" style="font-size: 13px; color: var(--muted); margin: 0; line-height: 1.4;">
      ${info.description}
    </p>
  `;

  mainArea.insertBefore(headerDiv, mainArea.firstChild);
}

function injectCommandPaletteModal() {
  if (document.getElementById("command-palette-modal")) return;

  const modalHTML = `
    <div class="modal-backdrop" id="command-palette-modal">
      <div id="command-palette-overlay" style="position:absolute;inset:0;z-index:-1;"></div>
      <div class="modal-box" style="max-width: 600px; width: 95%; background: rgba(11, 19, 24, 0.98); backdrop-filter: blur(10px); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: 0 20px 50px rgba(0,0,0,0.6); overflow: hidden; padding: 0;">
        <div style="display:flex; align-items:center; border-bottom: 1px solid var(--border); padding: 12px 16px; background: rgba(255,255,255,0.02);">
          <span style="font-size: 18px; margin-right: 12px; color: var(--muted);">🔍</span>
          <input type="text" id="command-palette-input" placeholder="Type a command (e.g. /focus, /task, /remind) or search..." style="background:transparent; border:none; color:var(--text); font-size:16px; width:100%; outline:none;" autocomplete="off" />
          <kbd style="background: rgba(255,255,255,0.1); border-radius: 4px; padding: 2px 6px; font-size: 10px; font-family: monospace; color: var(--muted); border: 1px solid var(--border);">ESC</kbd>
        </div>
        <div id="command-palette-results" style="max-height: 300px; overflow-y: auto; padding: 8px 0; display:flex; flex-direction:column;">
          <!-- Command items loaded dynamically -->
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; background: rgba(0,0,0,0.2); padding: 8px 16px; border-top: 1px solid var(--border); font-size: 11px; color: var(--muted);">
          <div>Use <kbd>↑</kbd> <kbd>↓</kbd> to navigate, <kbd>Enter</kbd> to select</div>
          <div>Close with <kbd>Esc</kbd></div>
        </div>
      </div>
    </div>
  `;

  const div = document.createElement("div");
  div.innerHTML = modalHTML;
  while (div.firstChild) {
    document.body.appendChild(div.firstChild);
  }

  // Dynamically load the command palette script
  const script = document.createElement("script");
  script.type = "module";
  script.src = "/static/js/command_palette.js";
  document.body.appendChild(script);
}

function ensureToastContainer() {
  if (!document.getElementById("toast")) {
    const toastDiv = document.createElement("div");
    toastDiv.id = "toast";
    toastDiv.setAttribute("role", "status");
    toastDiv.setAttribute("aria-live", "polite");
    document.body.appendChild(toastDiv);
  }
}

function dismissLoadingOverlay() {
  const overlay = document.getElementById("loading-overlay");
  if (overlay) {
    overlay.classList.add("hidden");
  }
}

// Initialize
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    injectSidebar();
    injectPageHeader();
    injectCommandPaletteModal();
    ensureToastContainer();
    dismissLoadingOverlay();
  });
} else {
  injectSidebar();
  injectPageHeader();
  injectCommandPaletteModal();
  ensureToastContainer();
  dismissLoadingOverlay();
}
