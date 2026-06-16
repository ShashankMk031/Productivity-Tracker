import { fetchAPI } from './api.js';

document.addEventListener("DOMContentLoaded", () => {
  loadHealth();
  loadStorage();
  loadBackups();
  loadAIHealth();
  
  const btnBackup = document.getElementById("btn-create-backup");
  if (btnBackup) {
    btnBackup.addEventListener("click", async () => {
      btnBackup.textContent = "Creating...";
      btnBackup.disabled = true;
      try {
        const res = await fetchAPI("/api/settings/backups/create", { method: "POST" });
        if (res && res.success) {
          alert("Backup created successfully!");
          loadBackups();
          loadStorage();
        }
      } catch (err) {
        alert("Failed to create backup.");
      } finally {
        btnBackup.textContent = "💾 Create Backup Now";
        btnBackup.disabled = false;
      }
    });
  }
});

async function loadHealth() {
  const container = document.getElementById("health-stats");
  const integrityContainer = document.getElementById("integrity-stats");
  const backupSummaryContainer = document.getElementById("backup-status-summary");
  if (!container) return;
  try {
    const res = await fetchAPI("/api/settings/health");
    if (res && res.data) {
      // 1. Database records counts
      let html = "";
      for (const [k, v] of Object.entries(res.data.database_records)) {
        html += `<div class="stat-row"><span>${k.replace('_', ' ').toUpperCase()}</span><span style="font-weight:bold">${v} records</span></div>`;
      }
      container.innerHTML = html;

      // 2. Integrity info
      if (integrityContainer && res.data.integrity) {
        const integrity = res.data.integrity;
        let integrityHtml = "";
        
        let badgeColor = "var(--green)";
        if (integrity.status === "Degraded") badgeColor = "var(--danger)";
        
        integrityHtml += `<div class="stat-row">
          <span>Integrity Status</span>
          <span style="font-weight:bold; color:${badgeColor}; background:rgba(255,255,255,0.03); padding:2px 8px; border-radius:4px;">${integrity.status}</span>
        </div>`;
        
        integrityHtml += `<div class="stat-row">
          <span>Issues Found</span>
          <span style="font-weight:bold">${integrity.issues_found}</span>
        </div>`;
        
        if (integrity.details && integrity.details.length > 0) {
          integrityHtml += `<div style="margin-top: 10px; font-size:12px; color:var(--muted); background:rgba(0,0,0,0.2); padding:10px; border-radius:6px; border:1px solid var(--border);">`;
          integrity.details.forEach(detail => {
            integrityHtml += `<div style="margin-bottom: 4px;">⚠️ ${detail}</div>`;
          });
          integrityHtml += `</div>`;
        } else {
          integrityHtml += `<div style="margin-top: 10px; font-size:12px; color:var(--green); text-align:center;">✓ All database constraints and filesystem structures are valid.</div>`;
        }
        
        integrityContainer.innerHTML = integrityHtml;
      }

      // 3. Backup Status Summary
      if (backupSummaryContainer && res.data.backup_status) {
        const bs = res.data.backup_status;
        let lastBackupDate = "N/A";
        if (bs.last_backup && bs.last_backup !== "None") {
           lastBackupDate = new Date(bs.last_backup).toLocaleString();
        }
        backupSummaryContainer.innerHTML = `
          Total Backups: <strong>${bs.total_backups}</strong> | Last Backup: <strong>${lastBackupDate}</strong>
        `;
      }
    }
  } catch (err) {
    container.innerHTML = "Failed to load.";
    if (integrityContainer) integrityContainer.innerHTML = "Failed to load.";
  }
}

async function loadStorage() {
  const container = document.getElementById("storage-stats");
  if (!container) return;
  try {
    const res = await fetchAPI("/api/settings/storage");
    if (res && res.data) {
      let html = "";
      let total = 0;
      for (const [k, v] of Object.entries(res.data)) {
        html += `<div class="stat-row"><span>${k.replace('_', ' ').toUpperCase()}</span><span style="font-weight:bold">${v} MB</span></div>`;
        total += v;
      }
      html += `<div class="stat-row" style="border-top:2px solid rgba(255,255,255,0.1); margin-top:8px;"><span>TOTAL</span><span style="font-weight:bold; color:var(--green)">${total.toFixed(2)} MB</span></div>`;
      container.innerHTML = html;
    }
  } catch (err) {
    container.innerHTML = "Failed to load.";
  }
}

async function loadBackups() {
  const container = document.getElementById("backups-list");
  if (!container) return;
  try {
    const res = await fetchAPI("/api/settings/backups");
    if (res && res.data) {
      if (res.data.length === 0) {
        container.innerHTML = "<div style='color:var(--muted); font-size:13px;'>No backups found.</div>";
        return;
      }
      let html = "";
      res.data.forEach(b => {
        html += `
          <div class="backup-item">
            <div class="backup-info">
              <strong style="font-size:14px;">${b.filename}</strong>
              <span style="font-size:12px; color:var(--muted)">${new Date(b.created_at).toLocaleString()} | ${b.size_mb} MB</span>
            </div>
            <div class="backup-actions">
              <button class="btn-secondary" style="font-size:12px; padding:4px 8px;" onclick="window.restoreBackup('${b.relative_path}')">Restore</button>
            </div>
          </div>
        `;
      });
      container.innerHTML = html;
    }
  } catch (err) {
    container.innerHTML = "Failed to load.";
  }
}

window.restoreBackup = async function(filename) {
  if (!confirm("WARNING: Restoring a backup will replace current data. A safety backup of the current state is created first. Continue?")) return;
  
  try {
    const res = await fetchAPI(`/api/settings/backups/restore?filename=${encodeURIComponent(filename)}`, { method: "POST" });
    if (res && res.success) {
      alert("Restore complete. Please restart the backend server manually to ensure clean state.");
      window.location.href = "/";
    }
  } catch (err) {
    alert("Restore failed.");
  }
}

async function loadAIHealth() {
  const primaryEl = document.getElementById("ai-primary-provider");
  const fallbackEl = document.getElementById("ai-fallback-order");
  const healthEl = document.getElementById("ai-providers-health");
  if (!healthEl) return;

  try {
    const res = await fetchAPI("/api/settings/ai-health");
    if (res && res.success && res.data) {
      const { statuses, active_provider, fallback_order } = res.data;
      if (primaryEl) {
        primaryEl.textContent = active_provider;
      }
      if (fallbackEl) {
        fallbackEl.textContent = fallback_order.map(p => p.toUpperCase()).join(" → ");
      }

      let html = "";
      const order = ["gemini", "groq", "openrouter", "lmstudio"];
      order.forEach(p => {
        if (statuses[p] !== undefined) {
          const status = statuses[p];
          let statusText = "Offline";
          let statusColor = "var(--danger)";
          if (status === "healthy") {
            statusText = "Connected";
            statusColor = "var(--green)";
          } else if (status === "missing_key") {
            statusText = "Missing API Key";
            statusColor = "var(--warning)";
          }
          
          html += `
            <div class="backup-item" style="margin-bottom: 8px;">
              <div class="backup-info">
                <strong style="font-size:14px; text-transform: uppercase; color: var(--text);">${p}</strong>
                <span style="font-size:12px; color:var(--muted)">Status: <span style="color:${statusColor}; font-weight:bold;">${statusText}</span></span>
              </div>
              <div class="backup-actions">
                <button class="ui-btn ui-btn-secondary" style="font-size:12px; padding:6px 12px;" onclick="window.testAIProvider('${p}', this)">⚡ Test Connection</button>
              </div>
            </div>
          `;
        }
      });
      healthEl.innerHTML = html;
    }
  } catch (err) {
    console.error("Failed to load AI health", err);
    healthEl.innerHTML = "<div style='color:var(--danger); font-size:13px;'>Failed to load AI health configurations.</div>";
  }
}

window.testAIProvider = async function(provider, btn) {
  const originalText = btn.innerHTML;
  btn.innerHTML = "Testing...";
  btn.disabled = true;
  try {
    const res = await fetchAPI(`/api/settings/ai-test?provider=${encodeURIComponent(provider)}`, { method: "POST" });
    if (res && res.success) {
      alert(`Success: ${res.message}`);
    } else {
      alert(`Error: ${res.message || "Failed to test provider connection."}`);
    }
  } catch (err) {
    alert(`Error: ${err.message || "Network error testing provider."}`);
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
    loadAIHealth();
  }
};
