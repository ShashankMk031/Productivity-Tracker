-- Productivity Tracker - SQLite Schema
-- Phase 1

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    recurring INTEGER NOT NULL DEFAULT 1,  -- 1 = recurring monthly, 0 = one-time
    created_at TEXT NOT NULL DEFAULT (date('now')),
    active_days TEXT NOT NULL DEFAULT '["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]',
    completed_forever INTEGER NOT NULL DEFAULT 0,  -- 1 = archived to completed goals
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS daily_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    date TEXT NOT NULL,           -- ISO format: YYYY-MM-DD
    completed INTEGER NOT NULL DEFAULT 0,
    note TEXT DEFAULT '',
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE(task_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_entries_task_date ON daily_entries(task_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_entries_date ON daily_entries(date);

-- Phase 3: Goals and Deadlines

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    progress INTEGER NOT NULL DEFAULT 0,
    priority INTEGER NOT NULL DEFAULT 0,
    target_date TEXT,
    created_at TEXT NOT NULL DEFAULT (date('now')),
    completed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    deadline TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (date('now')),
    completed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS project_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (date('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL, -- 'weekly' or 'monthly'
    generated_at TEXT NOT NULL DEFAULT (datetime('now')),
    markdown_path TEXT NOT NULL,
    summary TEXT,
    period_start TEXT,
    period_end TEXT
);
