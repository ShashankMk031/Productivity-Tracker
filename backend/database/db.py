import sqlite3
from contextlib import contextmanager
from pathlib import Path

from database.migrations import run_migrations

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "database" / "tracker.db"


def init_db():
    """Bring the database up to date via the unified migration runner.

    Replaces the legacy trio of init.sql executescript, ensure_schema()
    and db_migrations.run_migrations(). See backend/database/migrations.py.
    """
    run_migrations(DB_PATH)
    print(f"\u2713 Database ready at {DB_PATH}")


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
