import { fetchAPI } from './api.js';

export async function initInsights() {
  const container = document.getElementById("insights-container");
  const headerToggle = document.getElementById("insights-header-toggle");
  const toggleIcon = document.getElementById("insights-toggle-icon");
  
  if (!container) return;

  // Collapse/Expand toggle
  let isExpanded = true;
  headerToggle.addEventListener("click", () => {
    isExpanded = !isExpanded;
    container.style.display = isExpanded ? "grid" : "none";
    toggleIcon.textContent = isExpanded ? "▼" : "▶";
  });

  try {
    const res = await fetchAPI("/api/intelligence/dashboard");
    if (!res || !res.data) return;

    const snap = res.data.snapshot;
    renderInsights(container, snap);
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

// Auto-init
initInsights();
