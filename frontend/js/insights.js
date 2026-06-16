import { fetchAPI } from './api.js';

export async function initInsights() {
  const container = document.getElementById("insights-container");
  const wrapper = document.getElementById("insights-container-wrapper");
  const headerToggle = document.getElementById("insights-header-toggle");
  const toggleIcon = document.getElementById("insights-toggle-icon");
  
  if (!container) return;

  // Collapse/Expand toggle for the entire wrapper
  let isExpanded = true;
  headerToggle.addEventListener("click", () => {
    isExpanded = !isExpanded;
    if (wrapper) wrapper.style.display = isExpanded ? "block" : "none";
    toggleIcon.textContent = isExpanded ? "▼" : "▶";
  });

  try {
    const res = await fetchAPI("/api/intelligence/dashboard");
    if (!res || !res.data) return;

    const snap = res.data.snapshot;
    const accuracy = res.data.accuracy;
    
    renderInsights(container, snap);
    renderAccuracy(accuracy);
  } catch (err) {
    console.error("Failed to load insights", err);
    container.innerHTML = `<div style="color: var(--danger); font-size: 13px;">Failed to load insights.</div>`;
  }
}

function renderInsights(container, snap) {
  container.innerHTML = "";

  // 1. Burnout Insight
  if (snap.burnout) {
    container.appendChild(createCard("Burnout Risk", snap.burnout));
  }

  // 2. Focus Insight
  if (snap.focus) {
    // Focus doesn't have a risk_level naturally, let's map it
    const focusData = { ...snap.focus, risk_level: "LOW", warning_level: "INFO" };
    container.appendChild(createCard("Focus Analysis", focusData, `Optimal focus: ${snap.focus.best_focus_range}`));
  }

  // 3. Habit Consistencies
  if (snap.habits && snap.habits.length > 0) {
    // Show only the worst offending habit or highest risk
    const atRisk = snap.habits.filter(h => h.risk_level === "HIGH" || h.risk_level === "MEDIUM");
    if (atRisk.length > 0) {
      atRisk.forEach(h => {
        container.appendChild(createCard(`Habit Risk: ${h.task_title}`, h));
      });
    }
  }

  // 4. Deadline Forecasts
  if (snap.deadlines && snap.deadlines.length > 0) {
    const atRisk = snap.deadlines.filter(d => d.risk_level === "HIGH" || d.risk_level === "MEDIUM");
    atRisk.forEach(d => {
      container.appendChild(createCard(`Project Risk: ${d.project_title}`, d));
    });
  }
}

function createCard(title, data, subtitleOverride = null) {
  const card = document.createElement("div");
  card.className = "dashboard-panel";
  
  let borderColor = "var(--border)";
  if (data.warning_level === "CRITICAL") borderColor = "var(--danger)";
  else if (data.warning_level === "WARNING") borderColor = "#ffaa00";
  else if (data.warning_level === "WATCH") borderColor = "#e8d21d";
  else if (data.warning_level === "INFO") borderColor = "var(--green)";
  
  card.style.borderLeft = `4px solid ${borderColor}`;
  card.style.background = "rgba(255,255,255,0.02)";
  card.style.display = "flex";
  card.style.flexDirection = "column";
  card.style.gap = "8px";

  const headerRow = document.createElement("div");
  headerRow.style.display = "flex";
  headerRow.style.justifyContent = "space-between";
  headerRow.style.alignItems = "center";
  
  const h3 = document.createElement("h3");
  h3.textContent = title;
  h3.style.fontSize = "14px";
  h3.style.margin = "0";
  h3.style.color = "var(--text)";
  
  const badge = document.createElement("span");
  badge.textContent = data.warning_level;
  badge.style.fontSize = "10px";
  badge.style.padding = "2px 6px";
  badge.style.borderRadius = "4px";
  badge.style.fontWeight = "bold";
  badge.style.background = borderColor;
  badge.style.color = data.warning_level === "INFO" ? "#fff" : "#000";
  if(data.warning_level === "CRITICAL") badge.style.color = "#fff";
  
  headerRow.appendChild(h3);
  headerRow.appendChild(badge);
  card.appendChild(headerRow);

  const reason = document.createElement("div");
  reason.style.fontSize = "12px";
  reason.style.color = "var(--muted)";
  reason.textContent = subtitleOverride || data.reason;
  card.appendChild(reason);
  
  // Expandable metrics
  const expandBtn = document.createElement("button");
  expandBtn.textContent = "View Metrics";
  expandBtn.style.background = "transparent";
  expandBtn.style.border = "none";
  expandBtn.style.color = "#4a90e2";
  expandBtn.style.fontSize = "11px";
  expandBtn.style.cursor = "pointer";
  expandBtn.style.textAlign = "left";
  expandBtn.style.padding = "0";
  expandBtn.style.marginTop = "4px";
  
  const metricsBox = document.createElement("div");
  metricsBox.style.display = "none";
  metricsBox.style.fontSize = "11px";
  metricsBox.style.color = "var(--muted)";
  metricsBox.style.background = "rgba(0,0,0,0.2)";
  metricsBox.style.padding = "8px";
  metricsBox.style.borderRadius = "4px";
  metricsBox.style.marginTop = "4px";
  
  if (data.supporting_metrics) {
    let metricsHtml = "";
    for (const [k, v] of Object.entries(data.supporting_metrics)) {
      metricsHtml += `<div><strong>${k}:</strong> ${v}</div>`;
    }
    if (data.confidence) {
       metricsHtml += `<div style="margin-top:4px; color:var(--text)">Confidence: ${data.confidence}%</div>`;
    }
    metricsBox.innerHTML = metricsHtml;
  }
  
  expandBtn.addEventListener("click", () => {
    if (metricsBox.style.display === "none") {
      metricsBox.style.display = "block";
      expandBtn.textContent = "Hide Metrics";
    } else {
      metricsBox.style.display = "none";
      expandBtn.textContent = "View Metrics";
    }
  });

  card.appendChild(expandBtn);
  card.appendChild(metricsBox);

  return card;
}

function renderAccuracy(accuracy) {
  const summaryContainer = document.getElementById("accuracy-metrics-summary");
  const tbody = document.getElementById("recent-evaluations-tbody");
  
  if (!summaryContainer || !tbody) return;
  
  summaryContainer.innerHTML = "";
  tbody.innerHTML = "";
  
  if (!accuracy || accuracy.status === "No evaluated predictions yet" || !accuracy.predictors || Object.keys(accuracy.predictors).length === 0) {
    summaryContainer.innerHTML = `<div style="color:var(--muted); font-size:12px; grid-column: 1 / -1; text-align: center; padding: 12px; background: rgba(255,255,255,0.01); border: 1px dashed var(--border); border-radius: 6px;">No accuracy evaluations recorded yet. (Needs predictions that have passed their 7 or 14-day horizon).</div>`;
    tbody.innerHTML = `<tr><td colspan="6" style="padding:16px; text-align:center; color:var(--muted);">No recent evaluations.</td></tr>`;
    return;
  }
  
  // 1. Render Summary Cards
  for (const [predictor, meta] of Object.entries(accuracy.predictors)) {
    const card = document.createElement("div");
    card.style = `
      background: rgba(255,255,255,0.02);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      border-top: 3px solid #4a90e2;
    `;
    
    // Pick border top color based on accuracy percentage
    const pct = meta.accuracy_pct;
    let color = "var(--danger)";
    if (pct >= 80) color = "var(--green)";
    else if (pct >= 50) color = "#ffaa00";
    
    card.style.borderTop = `3px solid ${color}`;
    
    const label = predictor.replace('_', ' ').toUpperCase();
    
    card.innerHTML = `
      <span style="font-size:10px; color:var(--muted); font-weight:700; letter-spacing:0.5px;">${label}</span>
      <span style="font-size:20px; font-weight:700; color:${color}">${pct}%</span>
      <span style="font-size:9px; color:var(--muted)">${meta.total_evaluated} evaluated</span>
    `;
    summaryContainer.appendChild(card);
  }
  
  // 2. Render Recent Evaluations Table
  const evals = accuracy.recent_evaluations || [];
  if (evals.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="padding:16px; text-align:center; color:var(--muted);">No recent evaluations.</td></tr>`;
    return;
  }
  
  evals.forEach(ev => {
    const tr = document.createElement("tr");
    tr.style.borderBottom = "1px solid rgba(255,255,255,0.02)";
    
    let scoreColor = "var(--muted)";
    if (ev.accuracy_label === "Correct") scoreColor = "var(--green)";
    else if (ev.accuracy_label === "Near miss") scoreColor = "#ffaa00";
    else if (ev.accuracy_label === "Missed risk") scoreColor = "var(--danger)";
    
    const dateStr = new Date(ev.predicted_on).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    
    tr.innerHTML = `
      <td style="padding:10px; font-weight:600; color:var(--text);">${ev.predictor_type.toUpperCase()}</td>
      <td style="padding:10px;">${ev.target}</td>
      <td style="padding:10px;"><span style="font-size:10px; padding:2px 6px; border-radius:4px; font-weight:700; background:rgba(255,255,255,0.05); color:#fff;">${ev.predicted_risk}</span></td>
      <td style="padding:10px; font-size:11px; color:var(--muted);">${ev.actual_outcome}</td>
      <td style="padding:10px;"><span style="color:${scoreColor}; font-weight:bold;">${ev.accuracy_label}</span></td>
      <td style="padding:10px; color:var(--muted); font-family:monospace;">${dateStr}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Auto-init
initInsights();
