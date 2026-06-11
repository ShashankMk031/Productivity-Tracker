import { fetchAPI } from './api.js';
import { toast } from './ui.js';

let reports = [];
let comparisonChartInstance = null;
let generalChartInstance = null;
let weeklyChartInstance = null;
let monthlyChartInstance = null;

// DOM Elements
const loadingOverlay = document.getElementById("loading-overlay");
const kpiWeeklyCompletion = document.getElementById("kpi-weekly-completion");
const kpiWeeklyPeriod = document.getElementById("kpi-weekly-period");
const kpiMonthlyCompletion = document.getElementById("kpi-monthly-completion");
const kpiMonthlyPeriod = document.getElementById("kpi-monthly-period");
const kpiTotalReports = document.getElementById("kpi-total-reports");
const kpiReportsRatio = document.getElementById("kpi-reports-ratio");

// Comparison DOM
const scopeWeeklyBtn = document.getElementById("scope-weekly");
const scopeMonthlyBtn = document.getElementById("scope-monthly");
const comparePeriodA = document.getElementById("compare-period-a");
const comparePeriodB = document.getElementById("compare-period-b");
const btnRunComparison = document.getElementById("btn-run-comparison");
const comparisonResultArea = document.getElementById("comparison-result-area");

// Scorecard values & deltas
const compCompletionVal = document.getElementById("comp-completion-val");
const compCompletionDelta = document.getElementById("comp-completion-delta");
const compStreakVal = document.getElementById("comp-streak-val");
const compStreakDelta = document.getElementById("comp-streak-delta");

// Generation Dropdown DOM
const generateBtn = document.getElementById("generate-report-btn");
const toggleBtn = document.getElementById("report-dropdown-toggle");
const menuEl = document.getElementById("report-dropdown-menu");
const btnWeekly = document.getElementById("btn-dropdown-weekly");
const btnMonthly = document.getElementById("btn-dropdown-monthly");
const btnHistory = document.getElementById("btn-dropdown-history");

// History Modal DOM
const historyModal = document.getElementById("report-history-modal");
const historyCloseBtn = document.getElementById("report-history-close-btn");
const historyOverlay = document.getElementById("report-history-modal-overlay");
const historyList = document.getElementById("report-history-list");
const previewContainer = document.getElementById("report-preview-container");
const previewContent = document.getElementById("report-preview-content");
const previewBackBtn = document.getElementById("report-preview-back-btn");

let currentComparisonScope = "weekly"; // weekly or monthly

// Helper to show/hide loading spinner
function showLoading(show) {
  if (loadingOverlay) {
    if (show) loadingOverlay.classList.remove("hidden");
    else loadingOverlay.classList.add("hidden");
  }
}

// Format period dates beautifully
function formatPeriod(r) {
  const start = new Date(r.period_start);
  const end = new Date(r.period_end);
  if (r.type === 'monthly') {
    return end.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
  } else {
    const startStr = start.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    const endStr = end.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    return `${startStr} - ${endStr}`;
  }
}

// Parse completion rate and streak from summary string
function parseReportMetrics(summaryStr) {
  if (!summaryStr) return { completion: 0, streak: 0 };
  const compMatch = summaryStr.match(/Completion:\s*([0-9.]+)/);
  const streakMatch = summaryStr.match(/Streak:\s*([0-9]+)/);
  
  return {
    completion: compMatch ? parseFloat(compMatch[1]) : 0,
    streak: streakMatch ? parseInt(streakMatch[1]) : 0
  };
}

// Initialize Dashboard
export async function initDashboard() {
  showLoading(true);
  setupDropdownListeners();
  setupHistoryModalListeners();
  setupComparisonListeners();
  await loadDashboardData();
  showLoading(false);
}

// Setup generate dropdown split menu listeners
function setupDropdownListeners() {
  if (generateBtn) {
    generateBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (menuEl) menuEl.classList.add("hidden");
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
}

// Setup report history viewing modals
function setupHistoryModalListeners() {
  if (historyCloseBtn) historyCloseBtn.addEventListener("click", closeHistoryModal);
  if (historyOverlay) historyOverlay.addEventListener("click", closeHistoryModal);
  
  if (previewBackBtn) {
    previewBackBtn.addEventListener("click", () => {
      previewContainer.classList.add("hidden");
      historyList.classList.remove("hidden");
    });
  }
}

// Setup Comparison Selector Listeners
function setupComparisonListeners() {
  scopeWeeklyBtn.addEventListener("click", () => {
    if (currentComparisonScope === "weekly") return;
    currentComparisonScope = "weekly";
    scopeWeeklyBtn.classList.add("scope-option--active");
    scopeMonthlyBtn.classList.remove("scope-option--active");
    populateComparisonDropdowns();
  });
  
  scopeMonthlyBtn.addEventListener("click", () => {
    if (currentComparisonScope === "monthly") return;
    currentComparisonScope = "monthly";
    scopeMonthlyBtn.classList.add("scope-option--active");
    scopeWeeklyBtn.classList.remove("scope-option--active");
    populateComparisonDropdowns();
  });
  
  btnRunComparison.addEventListener("click", runComparison);
}

// Fetch history and draw/populate elements
async function loadDashboardData() {
  try {
    reports = await fetchAPI('/reports/history');
    
    // Sort reports chronologically ascending for the progression charts
    const chronologicalReports = [...reports].sort((a, b) => new Date(a.period_end) - new Date(b.period_end));
    
    updateKPIs();
    drawGeneralRelationChart(chronologicalReports);
    drawWeeklyTrendChart(chronologicalReports);
    drawMonthlyTrendChart(chronologicalReports);
    populateComparisonDropdowns();
    renderEmbeddedReportList();
    
    // Auto-select first report by default in the embedded viewer
    if (reports.length > 0) {
      loadEmbeddedPreview(reports[0].id);
      setTimeout(() => {
        const firstCard = document.querySelector('.report-card-embedded');
        if (firstCard) {
          firstCard.style.borderColor = 'var(--green)';
          firstCard.style.background = 'rgba(84, 209, 79, 0.05)';
        }
      }, 150);
    }
    
    // Run comparison automatically on first load if we have data
    if (reports.length >= 2) {
      runComparison();
    }
  } catch (err) {
    console.error("Failed to load dashboard data", err);
    toast("Failed to load analytics data", "error");
  }
}

// Trigger smart report generation
async function triggerSmartGenerate(type) {
  showLoading(true);
  try {
    const data = await fetchAPI(`/reports/smart-generate?type=${type}`, { method: 'POST' });
    
    if (data.status === "existing") {
      toast("Report already exists. Opening saved report.");
    } else {
      toast(data.message || 'Report generated successfully! 🎉');
    }
    
    // Hot reload dashboard in real-time
    await loadDashboardData();
    
    // Open preview inside the modal
    openHistoryModal();
    showPreview(data.id, data);
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

// Update Overview Scorecards
function updateKPIs() {
  const weeklyReports = reports.filter(r => r.type === "weekly");
  const monthlyReports = reports.filter(r => r.type === "monthly");
  
  // Total Counts
  kpiTotalReports.textContent = reports.length;
  kpiReportsRatio.textContent = `Weekly: ${weeklyReports.length} · Monthly: ${monthlyReports.length}`;
  
  // Latest Weekly
  if (weeklyReports.length > 0) {
    const latestW = weeklyReports[0]; // Already ordered DESC in DB
    const metrics = parseReportMetrics(latestW.summary);
    kpiWeeklyCompletion.textContent = `${metrics.completion}%`;
    kpiWeeklyPeriod.textContent = `Week: ${formatPeriod(latestW)}`;
  } else {
    kpiWeeklyCompletion.textContent = "--%";
    kpiWeeklyPeriod.textContent = "No weekly reports yet";
  }
  
  // Latest Monthly
  if (monthlyReports.length > 0) {
    const latestM = monthlyReports[0];
    const metrics = parseReportMetrics(latestM.summary);
    kpiMonthlyCompletion.textContent = `${metrics.completion}%`;
    kpiMonthlyPeriod.textContent = `Month of ${formatPeriod(latestM)}`;
  } else {
    kpiMonthlyCompletion.textContent = "--%";
    kpiMonthlyPeriod.textContent = "No monthly reports yet";
  }
}

// Draw General Combined Progression Line Chart
function drawGeneralRelationChart(chronoData) {
  if (generalChartInstance) generalChartInstance.destroy();
  
  const ctx = document.getElementById('chart-general-relation').getContext('2d');
  
  // X axis timeline (all distinct period end dates)
  const timelineDates = [...new Set(chronoData.map(r => r.period_end))].sort();
  
  const weeklyCompletionDataset = new Array(timelineDates.length).fill(null);
  const monthlyCompletionDataset = new Array(timelineDates.length).fill(null);
  
  chronoData.forEach(r => {
    const idx = timelineDates.indexOf(r.period_end);
    if (idx !== -1) {
      const metrics = parseReportMetrics(r.summary);
      if (r.type === 'weekly') {
        weeklyCompletionDataset[idx] = metrics.completion;
      } else {
        monthlyCompletionDataset[idx] = metrics.completion;
      }
    }
  });
  
  const xLabels = timelineDates.map(dateStr => {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  });

  generalChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: xLabels,
      datasets: [
        {
          label: 'Weekly Completion Rate (%)',
          data: weeklyCompletionDataset,
          borderColor: '#54d14f',
          backgroundColor: 'rgba(84, 209, 79, 0.05)',
          borderWidth: 2.5,
          tension: 0.3,
          spanGaps: true,
          pointBackgroundColor: '#54d14f',
          fill: true
        },
        {
          label: 'Monthly Completion Rate (%)',
          data: monthlyCompletionDataset,
          borderColor: '#4a90e2',
          backgroundColor: 'rgba(74, 144, 226, 0.05)',
          borderWidth: 2.5,
          tension: 0.3,
          spanGaps: true,
          pointBackgroundColor: '#4a90e2',
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: { color: '#cdd5db', font: { size: 11, family: 'inherit' } }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#88929b' }
        },
        x: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#88929b' }
        }
      }
    }
  });
}

// Draw Weekly Progression Line Chart
function drawWeeklyTrendChart(chronoData) {
  if (weeklyChartInstance) weeklyChartInstance.destroy();
  
  const ctx = document.getElementById('chart-weekly-trend').getContext('2d');
  
  const weeklyReports = chronoData.filter(r => r.type === 'weekly');
  const labels = weeklyReports.map(r => formatPeriod(r));
  const data = weeklyReports.map(r => parseReportMetrics(r.summary).completion);
  
  weeklyChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Weekly Rate',
        data: data,
        borderColor: '#54d14f',
        backgroundColor: 'rgba(84, 209, 79, 0.1)',
        fill: true,
        borderWidth: 2,
        tension: 0.25,
        pointBackgroundColor: '#54d14f'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#88929b', font: { size: 10 } } },
        x: { grid: { display: false }, ticks: { color: '#88929b', font: { size: 9 } } }
      }
    }
  });
}

// Draw Monthly Progression Bar Chart
function drawMonthlyTrendChart(chronoData) {
  if (monthlyChartInstance) monthlyChartInstance.destroy();
  
  const ctx = document.getElementById('chart-monthly-trend').getContext('2d');
  
  const monthlyReports = chronoData.filter(r => r.type === 'monthly');
  const labels = monthlyReports.map(r => formatPeriod(r));
  const data = monthlyReports.map(r => parseReportMetrics(r.summary).completion);
  
  monthlyChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Monthly Rate',
        data: data,
        backgroundColor: '#4a90e2',
        borderRadius: 4,
        barPercentage: 0.5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#88929b', font: { size: 10 } } },
        x: { grid: { display: false }, ticks: { color: '#88929b', font: { size: 9 } } }
      }
    }
  });
}

// Populate comparison dropdown options
function populateComparisonDropdowns() {
  comparePeriodA.innerHTML = "";
  comparePeriodB.innerHTML = "";
  
  const filtered = reports.filter(r => r.type === currentComparisonScope);
  
  if (filtered.length === 0) {
    const opt = document.createElement("option");
    opt.textContent = "No data available";
    opt.disabled = true;
    comparePeriodA.appendChild(opt);
    
    const optB = document.createElement("option");
    optB.textContent = "No data available";
    optB.disabled = true;
    comparePeriodB.appendChild(optB);
    return;
  }
  
  filtered.forEach((r, index) => {
    const name = `${r.type === 'weekly' ? 'Week' : 'Month'} ending ${formatPeriod(r)}`;
    
    const optA = document.createElement("option");
    optA.value = r.id;
    optA.textContent = name;
    comparePeriodA.appendChild(optA);
    
    const optB = document.createElement("option");
    optB.value = r.id;
    optB.textContent = name;
    comparePeriodB.appendChild(optB);
  });
  
  // Set defaults: Period A is latest (index 0), Period B is second latest (index 1) if available
  if (filtered.length >= 2) {
    comparePeriodA.selectedIndex = 0;
    comparePeriodB.selectedIndex = 1;
  }
}

// Run side-by-side comparison
function runComparison() {
  const idA = parseInt(comparePeriodA.value);
  const idB = parseInt(comparePeriodB.value);
  
  if (isNaN(idA) || isNaN(idB)) {
    toast("Please select two valid periods to compare");
    return;
  }
  
  const reportA = reports.find(r => r.id === idA);
  const reportB = reports.find(r => r.id === idB);
  
  if (!reportA || !reportB) return;
  
  const nameA = formatPeriod(reportA);
  const nameB = formatPeriod(reportB);
  
  const metricsA = parseReportMetrics(reportA.summary);
  const metricsB = parseReportMetrics(reportB.summary);
  
  // Update Scorecards
  compCompletionVal.textContent = `${metricsA.completion}% vs ${metricsB.completion}%`;
  compStreakVal.textContent = `${metricsA.streak} days vs ${metricsB.streak} days`;
  
  // Render Deltas
  const compDiff = metricsB.completion - metricsA.completion;
  const streakDiff = metricsB.streak - metricsA.streak;
  
  renderDeltaPill(compCompletionDelta, compDiff, "%");
  renderDeltaPill(compStreakDelta, streakDiff, " days");
  
  // Show results area
  comparisonResultArea.classList.remove("hidden");
  
  // Render Comparison Chart
  drawComparisonChart(nameA, nameB, metricsA, metricsB);
}

// Format scorecard progress delta pills
function renderDeltaPill(element, diff, unit) {
  element.className = "delta-pill";
  const abs = Math.abs(diff).toFixed(1).replace(/\.0$/, '');
  
  if (diff > 0) {
    element.classList.add("delta-pill--positive");
    element.textContent = `▲ +${abs}${unit}`;
  } else if (diff < 0) {
    element.classList.add("delta-pill--negative");
    element.textContent = `▼ -${abs}${unit}`;
  } else {
    element.classList.add("delta-pill--neutral");
    element.textContent = `● 0${unit}`;
  }
}

// Draw side-by-side double bars
function drawComparisonChart(nameA, nameB, metricsA, metricsB) {
  if (comparisonChartInstance) comparisonChartInstance.destroy();
  
  const ctx = document.getElementById('chart-comparison-bars').getContext('2d');
  
  comparisonChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Completion Rate (%)', 'Max Streak (days)'],
      datasets: [
        {
          label: `Period A (${nameA})`,
          data: [metricsA.completion, metricsA.streak],
          backgroundColor: '#4a90e2',
          borderRadius: 4,
          barPercentage: 0.7,
          categoryPercentage: 0.6
        },
        {
          label: `Period B (${nameB})`,
          data: [metricsB.completion, metricsB.streak],
          backgroundColor: '#54d14f',
          borderRadius: 4,
          barPercentage: 0.7,
          categoryPercentage: 0.6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: { color: '#cdd5db', font: { size: 11 } }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255,255,255,0.03)' },
          ticks: { color: '#88929b' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#88929b' }
        }
      }
    }
  });
}

// --- History Modal Functionality (Reused for consistent experience) ---

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
    showPreview(id, data);
  } catch (err) {
    toast(`Failed to load preview: ${err.message}`, 'error');
  }
}

let weeklyPreviewChartInstance = null;
let tasksPreviewChartInstance = null;

async function showPreview(id, data) {
  historyList.classList.add("hidden");
  previewContainer.classList.remove("hidden");
  
  const markdownText = data.markdown || data.markdown_content || "";
  const aiText = data.ai_reflection || "No raw AI reflection backup found for this report period.";
  
  previewContent.innerHTML = `
    <div style="font-weight:700; font-size:18px; color:var(--text); margin-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">Report Details</div>
    
    <div style="display: flex; gap: 8px; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px;">
      <button id="modal-toggle-standard" style="background: var(--green); color: white; border: 1px solid var(--border); padding: 6px 12px; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s;">📄 Standard Report</button>
      <button id="modal-toggle-ai" style="background: rgba(255,255,255,0.05); color: var(--muted); border: 1px solid var(--border); padding: 6px 12px; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s;">🤖 Raw AI Reflection</button>
    </div>
    
    <div id="modal-report-text-container" style="background: rgba(0,0,0,0.2); padding: 16px; border-radius: 6px; font-size: 14px; line-height: 1.5; white-space: pre-wrap; font-family: monospace; color: #d9e0e6;">${markdownText}</div>
  `;
  
  const textContainer = document.getElementById("modal-report-text-container");
  const toggleStandard = document.getElementById("modal-toggle-standard");
  const toggleAi = document.getElementById("modal-toggle-ai");
  
  function setTab(tab) {
    if (tab === "standard") {
      toggleStandard.style.background = "var(--green)";
      toggleStandard.style.color = "white";
      toggleAi.style.background = "rgba(255,255,255,0.05)";
      toggleAi.style.color = "var(--muted)";
      textContainer.textContent = markdownText;
    } else {
      toggleAi.style.background = "var(--green)";
      toggleAi.style.color = "white";
      toggleStandard.style.background = "rgba(255,255,255,0.05)";
      toggleStandard.style.color = "var(--muted)";
      textContainer.textContent = aiText;
    }
  }
  
  toggleStandard.addEventListener("click", () => setTab("standard"));
  toggleAi.addEventListener("click", () => setTab("ai"));

  try {
    const analytics = await fetchAPI('/reports/analytics');
    if (analytics.charts) {
      renderPreviewCharts(analytics.charts);
    }
  } catch (err) {
    console.warn("Failed to load charts:", err);
  }
}

function renderPreviewCharts(chartData) {
  if (weeklyPreviewChartInstance) weeklyPreviewChartInstance.destroy();
  if (tasksPreviewChartInstance) tasksPreviewChartInstance.destroy();
  
  const weeklyCtx = document.getElementById('preview-chart-weekly');
  const tasksCtx = document.getElementById('preview-chart-tasks');
  
  if (weeklyCtx && chartData.weekly_completion) {
    weeklyPreviewChartInstance = new Chart(weeklyCtx, {
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
    tasksPreviewChartInstance = new Chart(tasksCtx, {
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

// --- Embedded Reports Viewer Functionality ---

const embeddedReportList = document.getElementById("embedded-report-list");
const embeddedReportViewer = document.getElementById("embedded-report-viewer");

function groupReports(reportsArray) {
  const groups = {};
  
  reportsArray.forEach(r => {
    const end = new Date(r.period_end);
    const year = end.getFullYear().toString();
    const month = end.toLocaleDateString(undefined, { month: 'long' });
    
    if (!groups[year]) {
      groups[year] = {};
    }
    if (!groups[year][month]) {
      groups[year][month] = [];
    }
    groups[year][month].push(r);
  });
  
  return groups;
}

function renderEmbeddedReportList() {
  if (!embeddedReportList) return;
  embeddedReportList.innerHTML = '';
  
  if (reports.length === 0) {
    embeddedReportList.innerHTML = '<div style="color:var(--muted); font-size:13px; text-align:center; padding: 20px;">No reports generated yet.</div>';
    return;
  }
  
  const grouped = groupReports(reports);
  const sortedYears = Object.keys(grouped).sort((a, b) => b - a);
  
  sortedYears.forEach(year => {
    const yearDetails = document.createElement('details');
    yearDetails.style.margin = '0 0 10px 0';
    yearDetails.open = true;
    
    const yearSummary = document.createElement('summary');
    yearSummary.style = 'cursor: pointer; font-weight: 700; font-size: 14px; color: var(--text); padding: 8px 12px; border-radius: 6px; background: rgba(255,255,255,0.02); border: 1px solid var(--border); display: flex; align-items: center; gap: 6px; list-style: none; user-select: none; transition: background 0.2s; margin-bottom: 6px;';
    yearSummary.innerHTML = `📁 Year: ${year}`;
    yearSummary.addEventListener('mouseenter', () => yearSummary.style.background = 'rgba(255,255,255,0.06)');
    yearSummary.addEventListener('mouseleave', () => yearSummary.style.background = 'rgba(255,255,255,0.02)');
    yearDetails.appendChild(yearSummary);
    
    const yearContent = document.createElement('div');
    yearContent.style = 'padding-left: 12px; display: flex; flex-direction: column; gap: 8px;';
    
    const months = grouped[year];
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const sortedMonths = Object.keys(months).sort((a, b) => monthNames.indexOf(b) - monthNames.indexOf(a));
    
    sortedMonths.forEach(month => {
      const monthDetails = document.createElement('details');
      monthDetails.style.margin = '0 0 6px 0';
      monthDetails.open = true;
      
      const monthSummary = document.createElement('summary');
      monthSummary.style = 'cursor: pointer; font-weight: 600; font-size: 13px; color: var(--muted); padding: 6px 10px; border-radius: 4px; display: flex; align-items: center; gap: 6px; list-style: none; user-select: none; transition: background 0.2s; margin-bottom: 4px;';
      monthSummary.innerHTML = `📂 Month: ${month}`;
      monthSummary.addEventListener('mouseenter', () => monthSummary.style.background = 'rgba(255,255,255,0.04)');
      monthSummary.addEventListener('mouseleave', () => monthSummary.style.background = 'transparent');
      monthDetails.appendChild(monthSummary);
      
      const monthContent = document.createElement('div');
      monthContent.style = 'padding-left: 12px; display: flex; flex-direction: column; gap: 6px; border-left: 1px solid var(--border); margin-left: 6px;';
      
      months[month].forEach(r => {
        const el = document.createElement('div');
        el.className = 'report-card-embedded';
        el.setAttribute('data-id', r.id);
        el.style = 'background: rgba(255,255,255,0.03); padding: 10px; border-radius: 6px; cursor: pointer; border: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; transition: all 0.2s;';
        
        const label = r.type === 'weekly' ? `📅 Week ending ${formatPeriod(r)}` : `🌙 Month of ${formatPeriod(r)}`;
        
        el.innerHTML = `
          <div style="flex: 1; min-width: 0;">
            <div class="report-title-text" style="font-weight: 600; font-size: 12px; color: var(--text); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${label}</div>
            <div style="font-size: 10px; color: var(--muted); margin-top: 2px;">${r.summary || ''}</div>
          </div>
        `;
        
        el.addEventListener('mouseenter', () => {
          if (el.style.borderColor !== 'var(--green)') {
            el.style.background = 'rgba(255,255,255,0.06)';
            el.style.borderColor = 'var(--border-2)';
          }
        });
        el.addEventListener('mouseleave', () => {
          if (el.style.borderColor !== 'var(--green)') {
            el.style.background = 'rgba(255,255,255,0.03)';
            el.style.borderColor = 'var(--border)';
          }
        });
        
        el.addEventListener('click', () => {
          document.querySelectorAll('.report-card-embedded').forEach(c => {
            c.style.borderColor = 'var(--border)';
            c.style.background = 'rgba(255,255,255,0.03)';
          });
          el.style.borderColor = 'var(--green)';
          el.style.background = 'rgba(84, 209, 79, 0.05)';
          loadEmbeddedPreview(r.id);
        });
        
        monthContent.appendChild(el);
      });
      
      monthDetails.appendChild(monthContent);
      yearContent.appendChild(monthDetails);
    });
    
    yearDetails.appendChild(yearContent);
    embeddedReportList.appendChild(yearDetails);
  });
}

async function loadEmbeddedPreview(id) {
  if (!embeddedReportViewer) return;
  embeddedReportViewer.innerHTML = '<div style="color:var(--muted); font-size:13px; text-align:center; margin-top:200px;">Loading report content...</div>';
  
  try {
    const data = await fetchAPI(`/reports/${id}`);
    
    embeddedReportViewer.innerHTML = `
      <div style="font-weight:700; font-size:16px; color:var(--text); margin-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
        <span style="text-transform: capitalize;">${data.type || 'Report'} Archive Details</span>
        <button class="btn-secondary" style="font-size: 11px; padding: 2px 8px; height: 24px;" id="embedded-print-btn">Print / Save</button>
      </div>
      
      <div style="display: flex; gap: 8px; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px;">
        <button id="toggle-standard-view" style="background: var(--green); color: white; border: 1px solid var(--border); padding: 6px 12px; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s;">📄 Standard Report</button>
        <button id="toggle-ai-view" style="background: rgba(255,255,255,0.05); color: var(--muted); border: 1px solid var(--border); padding: 6px 12px; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s;">🤖 Raw AI Reflection</button>
      </div>
      
      <div id="embedded-report-text-container" style="font-size: 13px; line-height: 1.6; white-space: pre-wrap; color: #d9e0e6; font-family: monospace;">${data.markdown}</div>
    `;
    
    let activeTab = "standard";
    const textContainer = document.getElementById("embedded-report-text-container");
    const toggleStandardBtn = document.getElementById("toggle-standard-view");
    const toggleAiBtn = document.getElementById("toggle-ai-view");
    
    function setTab(tab) {
      activeTab = tab;
      if (tab === "standard") {
        toggleStandardBtn.style.background = "var(--green)";
        toggleStandardBtn.style.color = "white";
        toggleAiBtn.style.background = "rgba(255,255,255,0.05)";
        toggleAiBtn.style.color = "var(--muted)";
        textContainer.textContent = data.markdown;
      } else {
        toggleAiBtn.style.background = "var(--green)";
        toggleAiBtn.style.color = "white";
        toggleStandardBtn.style.background = "rgba(255,255,255,0.05)";
        toggleStandardBtn.style.color = "var(--muted)";
        textContainer.textContent = data.ai_reflection || "No raw AI reflection backup found for this report period.";
      }
    }
    
    toggleStandardBtn.addEventListener("click", () => setTab("standard"));
    toggleAiBtn.addEventListener("click", () => setTab("ai"));
    
    const printBtn = document.getElementById("embedded-print-btn");
    if (printBtn) {
      printBtn.addEventListener("click", () => {
        const printWin = window.open("", "_blank");
        const printContent = activeTab === "standard" ? data.markdown : (data.ai_reflection || "No raw AI reflection backup found for this report period.");
        printWin.document.write(`
          <html>
            <head>
              <title>${activeTab === 'standard' ? 'Productivity Report' : 'Raw AI Reflection'}</title>
              <style>
                body { font-family: sans-serif; line-height: 1.6; padding: 40px; color: #333; }
                pre { white-space: pre-wrap; font-family: inherit; }
              </style>
            </head>
            <body>
              <pre>${printContent}</pre>
              <script>window.onload = function() { window.print(); window.close(); }</script>
            </body>
          </html>
        `);
        printWin.document.close();
      });
    }
  } catch (err) {
    embeddedReportViewer.innerHTML = `<div style="color:var(--danger); font-size:13px; text-align:center; margin-top:200px;">Failed to load report: ${err.message}</div>`;
  }
}

function closeHistoryModal() {
  historyModal.classList.remove("modal--open");
}

// Auto-init dashboard on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboard);
} else {
  initDashboard();
}
