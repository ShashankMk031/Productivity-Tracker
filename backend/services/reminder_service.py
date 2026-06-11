import sqlite3

def add_reminder(db: sqlite3.Connection, title: str, datetime_str: str, recurring: str = 'none') -> dict:
    cur = db.execute(
        "INSERT INTO reminders (title, datetime, recurring, completed) VALUES (?, ?, ?, 0)",
        (title, datetime_str, recurring)
    )
    reminder_id = cur.lastrowid
    return {
        "id": reminder_id,
        "title": title,
        "datetime": datetime_str,
        "recurring": recurring,
        "completed": 0
    }

def delete_reminder(db: sqlite3.Connection, reminder_id: int) -> bool:
    cur = db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    return cur.rowcount > 0

def toggle_reminder_completed(db: sqlite3.Connection, reminder_id: int) -> dict:
    row = db.execute("SELECT completed FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
    if not row:
        return None
    new_completed = 1 if row["completed"] == 0 else 0
    db.execute("UPDATE reminders SET completed = ? WHERE id = ?", (new_completed, reminder_id))
    return {
        "id": reminder_id,
        "completed": new_completed
    }

def get_active_reminders(db: sqlite3.Connection) -> list:
    rows = db.execute("SELECT * FROM reminders WHERE completed = 0 ORDER BY datetime ASC").fetchall()
    return [dict(row) for row in rows]

def get_all_reminders(db: sqlite3.Connection) -> list:
    rows = db.execute("SELECT * FROM reminders ORDER BY datetime ASC").fetchall()
    return [dict(row) for row in rows]
