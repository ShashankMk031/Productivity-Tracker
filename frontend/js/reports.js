import { fetchAPI } from './api.js';
import { toast } from './ui.js';

let reports = [];

// DOM Elements
const generateBtn = document.getElementById("generate-report-btn");

const historyModal = document.getElementById("report-history-modal");
const historyCloseBtn = document.getElementById("report-history-close-btn");
const historyOverlay = document.getElementById("report-history-modal-overlay");
const historyList = document.getElementById("report-history-list");

const previewContainer = document.getElementById("report-preview-container");
const previewContent = document.getElementById("report-preview-content");
const previewBackBtn = document.getElementById("report-preview-back-btn");

let canGenerate = false;
let weeklyChartInstance = null;
let tasksChartInstance = null;

export async function initReports() {
  setupEventListeners();
  await loadStatus();
}

function setupEventListeners() {
  const toggleBtn = document.getElementById("report-dropdown-toggle");
  const menuEl = document.getElementById("report-dropdown-menu");
  
  if (generateBtn) {
    generateBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (menuEl) menuEl.classList.add("hidden");
      // Default action: smart generate or open current weekly report
      triggerSmartGenerate("weekly");
    });
  }
  
  if (toggleBtn && menuEl) {
    toggleBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      menuEl.classList.toggle("hidden");
    });
    
    document.addEventListener("click", () => {
      menuEl.classList.add("hidden");
    });
  }
  
  const btnWeekly = document.getElementById("btn-dropdown-weekly");
  const btnMonthly = document.getElementById("btn-dropdown-monthly");
  const btnHistory = document.getElementById("btn-dropdown-history");
  
  if (btnWeekly) {
    btnWeekly.addEventListener("click", (e) => {
      e.stopPropagation();
      if (menuEl) menuEl.classList.add("hidden");
      triggerSmartGenerate("weekly");
    });
  }
  
  if (btnMonthly) {
    btnMonthly.addEventListener("click", (e) => {
      e.stopPropagation();
      if (menuEl) menuEl.classList.add("hidden");
      triggerSmartGenerate("monthly");
    });
  }
  
  if (btnHistory) {
    btnHistory.addEventListener("click", (e) => {
      e.stopPropagation();
      if (menuEl) menuEl.classList.add("hidden");
      openHistoryModal();
    });
  }
  
  if (historyCloseBtn) historyCloseBtn.addEventListener("click", closeHistoryModal);
  if (historyOverlay) historyOverlay.addEventListener("click", closeHistoryModal);
  
  if (previewBackBtn) {
    previewBackBtn.addEventListener("click", () => {
      previewContainer.classList.add("hidden");
      historyList.classList.remove("hidden");
    });
  }
}

async function loadStatus() {
  // Always active under the single button philosophy
  canGenerate = true;
}

async function triggerSmartGenerate(type) {
  try {
    const data = await fetchAPI(`/reports/smart-generate?type=${type}`, { method: 'POST' });
    
    if (data.status === "existing") {
      toast("Report already exists. Opening saved report.");
    } else {
      toast(data.message || 'Report generated successfully');
    }
    
    await openHistoryModal();
    showPreview(data.id, data.markdown_content);
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function openHistoryModal() {
  historyModal.classList.add("modal--open");
  previewContainer.classList.add("hidden");
  historyList.classList.remove("hidden");
  historyList.innerHTML = '<div style="color:var(--muted); font-size:13px;">Loading reports...</div>';
  
  try {
    reports = await fetchAPI('/reports/history');
    renderHistory();
  } catch (err) {
    historyList.innerHTML = `<div style="color:var(--red); font-size:13px;">Failed to load history: ${err.message}</div>`;
  }
}

function renderHistory() {
  historyList.innerHTML = '';
  if (reports.length === 0) {
    historyList.innerHTML = '<div style="color:var(--muted); font-size:13px;">No reports generated yet.</div>';
    return;
  }
  
  reports.forEach(r => {
    const el = document.createElement('div');
    el.className = 'report-card';
    el.style = 'background: rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; cursor: pointer; display: flex; justify-content: space-between; align-items: center;';
    
    const dateStr = new Date(r.generated_at).toLocaleDateString();
    
    el.innerHTML = `
      <div>
        <div style="font-weight: 500; font-size: 14px; text-transform: capitalize;">${r.type} Report</div>
        <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">${r.summary || ''}</div>
      </div>
      <div style="font-size: 12px; color: var(--muted);">${dateStr}</div>
    `;
    
    el.addEventListener('click', () => loadPreview(r.id));
    historyList.appendChild(el);
  });
}

async function loadPreview(id) {
  try {
    const data = await fetchAPI(`/reports/${id}`);
    showPreview(id, data.markdown);
  } catch (err) {
    toast(`Failed to load preview: ${err.message}`, 'error');
  }
}

async function showPreview(id, markdown) {
  historyList.classList.add("hidden");
  previewContainer.classList.remove("hidden");
  
  previewContent.innerHTML = `<div style="font-weight:700; font-size:18px; color:var(--text); margin-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">Report Details</div>\n${markdown}`;

  try {
    const analytics = await fetchAPI('/reports/analytics');
    if (analytics.charts) {
      renderCharts(analytics.charts);
    }
  } catch (err) {
    console.warn("Failed to load charts:", err);
  }
}

function renderCharts(chartData) {
  if (weeklyChartInstance) weeklyChartInstance.destroy();
  if (tasksChartInstance) tasksChartInstance.destroy();
  
  const weeklyCtx = document.getElementById('preview-chart-weekly');
  const tasksCtx = document.getElementById('preview-chart-tasks');
  
  if (weeklyCtx && chartData.weekly_completion) {
    weeklyChartInstance = new Chart(weeklyCtx, {
      type: 'line',
      data: {
        labels: chartData.weekly_completion.labels,
        datasets: [{
          label: 'Completion %',
          data: chartData.weekly_completion.data,
          borderColor: '#46b846',
          backgroundColor: 'rgba(70, 184, 70, 0.1)',
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: true, text: 'Weekly Completion Trend', color: '#cdd5db' }
        },
        scales: {
          y: { beginAtZero: true, max: 100, ticks: { color: '#88929b' } },
          x: { ticks: { color: '#88929b' } }
        }
      }
    });
  }
  
  if (tasksCtx && chartData.task_performance) {
    tasksChartInstance = new Chart(tasksCtx, {
      type: 'bar',
      data: {
        labels: chartData.task_performance.labels,
        datasets: [{
          label: 'Performance %',
          data: chartData.task_performance.data,
          backgroundColor: '#3c9e3c'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: true, text: 'Task Performance (Last 30 Days)', color: '#cdd5db' }
        },
        scales: {
          y: { beginAtZero: true, max: 100, ticks: { color: '#88929b' } },
          x: { ticks: { color: '#88929b' } }
        }
      }
    });
  }
}

function closeHistoryModal() {
  historyModal.classList.remove("modal--open");
}

// Auto-init
try {
  console.log("Reports module loaded, initializing...");
  initReports().catch(err => console.error("Reports init async error:", err));
} catch (e) {
  console.error("Reports init sync error:", e);
}
