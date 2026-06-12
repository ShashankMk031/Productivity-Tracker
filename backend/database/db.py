import sqlite3
from contextlib import contextmanager

from config import DB_PATH
from database.migrations import run_migrations
from services.logging_service import get_logger

logger = get_logger(__name__)


def init_db():
    """Bring the database up to date via the unified migration runner.

    Replaces the legacy trio of init.sql executescript, ensure_schema()
    and db_migrations.run_migrations(). See backend/database/migrations.py.
    """
    run_migrations(DB_PATH)
    logger.info("Database ready at %s", DB_PATH)


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
