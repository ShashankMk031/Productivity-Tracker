import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "database" / "tracker.db"

def run_migrations():
    print("[Migration] Checking database schemas...")
    conn = sqlite3.connect(DB_PATH)
    try:
        # Create focus_sessions table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration INTEGER DEFAULT 0,
            notes TEXT DEFAULT ''
        )
        """)
        
        # Create reminders table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            datetime TEXT NOT NULL,
            recurring TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0
        )
        """)
        
        conn.commit()
        print("✓ [Migration] Schema migrations completed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"❌ [Migration] Schema migration failed: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    run_migrations()
