import sqlite3

from database.migrations import run_migrations, MIGRATIONS

EXPECTED_TABLES = {
    "tasks",
    "daily_entries",
    "goals",
    "projects",
    "project_milestones",
    "reports",
    "focus_sessions",
    "reminders",
    "schema_migrations",
}


def _tables(conn):
    return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def test_runner_creates_all_tables(tmp_path):
    db_path = tmp_path / "tracker.db"
    run_migrations(db_path)
    conn = sqlite3.connect(db_path)
    try:
        assert EXPECTED_TABLES <= _tables(conn)
    finally:
        conn.close()


def test_all_versions_recorded(tmp_path):
    db_path = tmp_path / "tracker.db"
    run_migrations(db_path)
    conn = sqlite3.connect(db_path)
    try:
        versions = [row[0] for row in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
        assert versions == [m[0] for m in MIGRATIONS]
    finally:
        conn.close()


def test_runner_is_idempotent(tmp_path):
    db_path = tmp_path / "tracker.db"
    first = run_migrations(db_path)
    second = run_migrations(db_path)
    assert first == [m[0] for m in MIGRATIONS]
    assert second == []


def test_legacy_columns_present(tmp_path):
    db_path = tmp_path / "tracker.db"
    run_migrations(db_path)
    conn = sqlite3.connect(db_path)
    try:
        assert "active_days" in _columns(conn, "tasks")
        assert "completed_at" in _columns(conn, "projects")
    finally:
        conn.close()
