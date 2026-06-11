import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "database" / "tracker.db"
SCHEMA_PATH = BASE_DIR / "database" / "init.sql"

def ensure_schema(conn: sqlite3.Connection):
    columns = {row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}

    if "active_days" not in columns:
        import json
        FULL_WEEK_JSON = json.dumps(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        conn.execute(
            f"ALTER TABLE tasks ADD COLUMN active_days TEXT NOT NULL DEFAULT '{FULL_WEEK_JSON}'"
        )
        conn.execute(
            "UPDATE tasks SET active_days = ? WHERE active_days IS NULL OR active_days = ''",
            (FULL_WEEK_JSON,),
        )

def ensure_project_schema(conn: sqlite3.Connection):
    columns = {row[1] for row in conn.execute("PRAGMA table_info(projects)").fetchall()}
    if "completed_at" not in columns:
        conn.execute("ALTER TABLE projects ADD COLUMN completed_at TEXT")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_PATH.read_text())
        ensure_schema(conn)
        ensure_project_schema(conn)
    print(f"✓ Database initialized at {DB_PATH}")

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
