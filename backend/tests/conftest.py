"""Shared fixtures for the critical-path test suite.

Guarantees:
  - Every test runs against a temporary SQLite database created by the
    unified migration runner (never the real tracker.db).
  - All artifact directories (backups, reports, ai_reports, ai_context,
    intelligence_snapshots) are redirected into a temp workspace.
  - No live AI calls: use the mock_ai fixture wherever reports are generated.
"""

import sys
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.migrations import run_migrations  # noqa: E402


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Isolated workspace: temp DB plus all artifact directories redirected."""
    db_path = tmp_path / "database" / "tracker.db"
    run_migrations(db_path)

    import database.db as db_module
    import services.backup_service as backup_service
    import services.report_history_service as rhs
    import intelligence.snapshot_service as snapshot_service
    import intelligence.prediction_accuracy as prediction_accuracy

    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(backup_service, "BASE_DIR", tmp_path)
    monkeypatch.setattr(backup_service, "BACKUPS_DIR", tmp_path / "backups")
    monkeypatch.setattr(rhs, "REPORTS_BASE_DIR", tmp_path / "reports")
    monkeypatch.setattr(rhs, "AI_REPORTS_BASE_DIR", tmp_path / "ai_reports")
    monkeypatch.setattr(rhs, "AI_CONTEXT_BASE_DIR", tmp_path / "ai_context")
    monkeypatch.setattr(snapshot_service, "SNAPSHOT_DIR", tmp_path / "intelligence_snapshots")
    return tmp_path


@pytest.fixture
def db(workspace):
    conn = sqlite3.connect(workspace / "database" / "tracker.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


@pytest.fixture
def seeded_db(db):
    """A database with a small, realistic data set."""
    today = date.today()
    cur = db.execute(
        "INSERT INTO tasks (title, recurring, created_at) VALUES ('Deep work', 1, ?)",
        ((today - timedelta(days=30)).isoformat(),),
    )
    task_id = cur.lastrowid
    for i in range(7):
        d = (today - timedelta(days=i)).isoformat()
        note = "Felt tired and drained today" if i % 3 == 0 else "Good session"
        db.execute(
            "INSERT INTO daily_entries (task_id, date, completed, note) VALUES (?, ?, ?, ?)",
            (task_id, d, 1 if i % 2 == 0 else 0, note),
        )
    db.execute(
        "INSERT INTO goals (title, description, category, progress, target_date, created_at) VALUES ('Learn SQL', '', 'Short-Term Goals', 40, ?, ?)",
        ((today + timedelta(days=30)).isoformat(), (today - timedelta(days=10)).isoformat()),
    )
    cur = db.execute(
        "INSERT INTO projects (title, description, deadline, progress, created_at) VALUES ('Tracker hardening', '', ?, 50, ?)",
        ((today + timedelta(days=14)).isoformat(), (today - timedelta(days=14)).isoformat()),
    )
    project_id = cur.lastrowid
    db.execute(
        "INSERT INTO project_milestones (project_id, title, completed, created_at) VALUES (?, 'Phase 1', 1, ?)",
        (project_id, today.isoformat()),
    )
    db.execute(
        "INSERT INTO project_milestones (project_id, title, completed, created_at) VALUES (?, 'Phase 2', 0, ?)",
        (project_id, today.isoformat()),
    )
    db.execute(
        "INSERT INTO focus_sessions (title, start_time, end_time, duration, notes) VALUES ('Morning block', ?, ?, 3600, '')",
        (f"{today.isoformat()}T09:00:00", f"{today.isoformat()}T10:00:00"),
    )
    db.execute(
        "INSERT INTO reminders (title, datetime, recurring, completed) VALUES ('Stand up', ?, 'none', 0)",
        (f"{today.isoformat()}T17:00:00",),
    )
    db.commit()
    return db


@pytest.fixture
def mock_ai(monkeypatch):
    """Prevent live AI calls; return a deterministic reflection."""
    from ai.ai_service import AIService
    monkeypatch.setattr(AIService, "generate_reflection", lambda self, prompt, **kwargs: ("Mock AI reflection.", "mock", "mock-model"))
    return "Mock AI reflection."
