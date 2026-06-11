/**
 * api.js — Thin wrapper around all backend endpoints.
 * All functions return parsed JSON or throw on HTTP error.
 */

const BASE = "";

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== null) opts.body = JSON.stringify(body);

  const res = await fetch(BASE + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  const data = await res.json();
  if (data.success !== undefined && !data.success) {
    throw new Error(data.error || data.message || "Request failed");
  }
  return data.data !== undefined ? data.data : data;
}

export async function fetchAPI(path, options = {}) {
  const method = options.method || "GET";
  const headers = options.headers || { "Content-Type": "application/json" };
  const opts = { method, headers };
  if (options.body) opts.body = options.body;

  const fullPath = path.startsWith('/api') ? path : '/api' + path;

  const res = await fetch(BASE + fullPath, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  const data = await res.json();
  if (data.success !== undefined && !data.success) {
    throw new Error(data.error || data.message || "Request failed");
  }
  return data.data !== undefined ? data.data : data;
}

// ── Tasks ──────────────────────────────────────────────────────────────────
export const getTasks       = ()           => request("GET",  "/api/tasks");
export const getArchivedTasks = ()         => request("GET",  "/api/tasks/archived");
export const addTask        = (title, recurring, active_days) =>
  request("POST", "/api/tasks", { title, recurring, active_days });
export const updateTask     = (id, title, recurring, active_days) => 
  request("PUT",  `/api/tasks/${id}`, { title, recurring, active_days });
export const deleteTask     = (id)         => request("DELETE", `/api/tasks/${id}`);
export const archiveTask    = (id)         => request("POST", `/api/tasks/${id}/archive`);
export const restoreTask    = (id)         => request("POST", `/api/tasks/${id}/restore`);

// ── Monthly data ───────────────────────────────────────────────────────────
export const getMonthData   = (year, month) =>
  request("GET", `/api/entries/${year}/${month}`);

// ── Daily entries ──────────────────────────────────────────────────────────
export const toggleEntry    = (task_id, date) =>
  request("POST", "/api/entries/toggle", { task_id, date });
export const updateNote     = (task_id, date, note) =>
  request("PUT",  "/api/entries/note",   { task_id, date, note });

// ── Stats ──────────────────────────────────────────────────────────────────
// (Per-task stats are now returned natively within the tasks/entries responses)
