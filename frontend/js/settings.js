import { fetchAPI } from './api.js';

document.addEventListener("DOMContentLoaded", () => {
  loadHealth();
  loadStorage();
  loadBackups();
  
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
  if (!container) return;
  try {
    const res = await fetchAPI("/api/settings/health");
    if (res && res.data) {
      let html = "";
      for (const [k, v] of Object.entries(res.data.database_records)) {
        html += `<div class="stat-row"><span>${k.replace('_', ' ').toUpperCase()}</span><span style="font-weight:bold">${v} records</span></div>`;
      }
      container.innerHTML = html;
    }
  } catch (err) {
    container.innerHTML = "Failed to load.";
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
