"""
Single schema authority for the Productivity Tracker database.

This module replaces the three previous, uncoordinated schema mechanisms:

  - database/init.sql              (executescript on every startup)  -> migration 0001
  - db.py ensure_schema() and
    ensure_project_schema()        (ad-hoc ALTERs)                   -> migrations 0002 / 0003
  - database/db_migrations.py      (Phase 5A tables)                 -> migration 0004

Rules:
  - Applied versions are tracked in the schema_migrations table.
  - Each migration runs inside its own transaction. A failure rolls the
    migration back, leaves its version unrecorded, and aborts the runner.
  - Migrations are written idempotently (IF NOT EXISTS / column checks) so
    that databases created by the legacy mechanisms adopt version tracking
    without being rebuilt.
  - Every migration documents its reverse operation in its docstring so a
    downgrade can be performed manually if ever required.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from config import DB_PATH
from services.logging_service import get_logger

logger = get_logger(__name__)

FULL_WEEK_JSON = '["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]'


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return column in {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _migration_0001_baseline_schema(conn: sqlite3.Connection):
    """Baseline schema (former database/init.sql).

    Reverse: DROP TABLE reports, project_milestones, projects, goals,
    daily_entries, tasks (children before parents).
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            recurring INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (date('now')),
            active_days TEXT NOT NULL DEFAULT '["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]',
            completed_forever INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            note TEXT DEFAULT '',
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            UNIQUE(task_id, date)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_entries_task_date ON daily_entries(task_id, date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_entries_date ON daily_entries(date)")
    conn.execute(
        """
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
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            deadline TEXT NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            priority INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (date('now')),
            completed INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS project_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (date('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            generated_at TEXT NOT NULL DEFAULT (datetime('now')),
            markdown_path TEXT NOT NULL,
            summary TEXT,
            period_start TEXT,
            period_end TEXT
        )
        """
    )


def _migration_0002_task_active_days(conn: sqlite3.Connection):
    """Add tasks.active_days for databases created before the column existed
    (former db.py:ensure_schema()).

    Reverse: ALTER TABLE tasks DROP COLUMN active_days (SQLite >= 3.35).
    """
    if not _column_exists(conn, "tasks", "active_days"):
        conn.execute(
            f"ALTER TABLE tasks ADD COLUMN active_days TEXT NOT NULL DEFAULT '{FULL_WEEK_JSON}'"
        )
    conn.execute(
        "UPDATE tasks SET active_days = ? WHERE active_days IS NULL OR active_days = ''",
        (FULL_WEEK_JSON,),
    )


def _migration_0003_project_completed_at(conn: sqlite3.Connection):
    """Add projects.completed_at (former db.py:ensure_project_schema()).

    Reverse: ALTER TABLE projects DROP COLUMN completed_at (SQLite >= 3.35).
    """
    if not _column_exists(conn, "projects", "completed_at"):
        conn.execute("ALTER TABLE projects ADD COLUMN completed_at TEXT")


def _migration_0004_focus_sessions_and_reminders(conn: sqlite3.Connection):
    """Phase 5A tables (former database/db_migrations.py).

    Reverse: DROP TABLE focus_sessions; DROP TABLE reminders.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration INTEGER DEFAULT 0,
            notes TEXT DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            datetime TEXT NOT NULL,
            recurring TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0
        )
        """
    )


MIGRATIONS = [
    (1, "baseline_schema", _migration_0001_baseline_schema),
    (2, "task_active_days", _migration_0002_task_active_days),
    (3, "project_completed_at", _migration_0003_project_completed_at),
    (4, "focus_sessions_and_reminders", _migration_0004_focus_sessions_and_reminders),
]


def run_migrations(db_path=None) -> list:
    """Apply all pending migrations in order.

    Returns the list of versions applied during this run.
    """
    path = Path(db_path) if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    applied_now = []
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

        applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}

        for version, name, migrate in MIGRATIONS:
            if version in applied:
                continue
            try:
                migrate(conn)
                conn.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                    (version, name, datetime.now().isoformat()),
                )
                conn.commit()
                applied_now.append(version)
                print(f"[Migrations] Applied {version:04d}_{name}")
            except Exception:
                conn.rollback()
                print(f"[Migrations] FAILED at {version:04d}_{name}; rolled back")
                raise
        return applied_now
    finally:
        conn.close()
