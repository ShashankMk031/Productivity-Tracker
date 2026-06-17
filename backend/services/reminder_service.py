import sqlite3
from typing import Optional
from datetime import datetime, date, time
from services.date_service import get_logical_date_ist
from utils.timezone import IST

def is_reminder_overdue(reminder: dict) -> bool:
    if reminder.get("completed"):
        return False
    
    due_date_str = reminder.get("due_date")
    due_time_str = reminder.get("due_time")
    
    if not due_date_str and not due_time_str:
        return False
        
    today_logical = get_logical_date_ist()
    now_ist = datetime.now(IST)
    
    due_date = date.fromisoformat(due_date_str) if due_date_str else None
    
    due_time = None
    if due_time_str:
        parts = due_time_str.split(":")
        due_time = time(int(parts[0]), int(parts[1]))
        
    if due_date and due_time:
        due_datetime = datetime.combine(due_date, due_time, tzinfo=IST)
        return now_ist > due_datetime
        
    if due_date and not due_time:
        return today_logical > due_date
        
    if not due_date and due_time:
        due_datetime = datetime.combine(today_logical, due_time, tzinfo=IST)
        return now_ist > due_datetime
        
    return False

def _serialize_reminder(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["is_overdue"] = is_reminder_overdue(d)
    return d

def add_reminder(
    db: sqlite3.Connection,
    title: str,
    due_date: Optional[str] = None,
    due_time: Optional[str] = None,
    recurring: str = 'none',
    datetime_str: Optional[str] = None
) -> dict:
    # Handle legacy datetime string payloads
    if due_date and 'T' in due_date:
        datetime_str = due_date
        due_date = None
        
    if datetime_str:
        parts = datetime_str.split('T')
        due_date = parts[0]
        if len(parts) > 1:
            due_time = parts[1][:5]
            
    # Calculate computed datetime column for sorting
    computed_datetime = None
    if due_date:
        if due_time:
            computed_datetime = f"{due_date}T{due_time}:00"
        else:
            computed_datetime = f"{due_date}T23:59:59"

    cur = db.execute(
        """
        INSERT INTO reminders (title, due_date, due_time, datetime, recurring, completed)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        (title.strip(), due_date, due_time, computed_datetime, recurring)
    )
    reminder_id = cur.lastrowid
    
    return get_reminder(db, reminder_id)

def get_reminder(db: sqlite3.Connection, reminder_id: int) -> Optional[dict]:
    row = db.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
    return _serialize_reminder(row) if row else None

def delete_reminder(db: sqlite3.Connection, reminder_id: int) -> bool:
    cur = db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    return cur.rowcount > 0

def toggle_reminder_completed(db: sqlite3.Connection, reminder_id: int) -> dict:
    row = db.execute("SELECT completed FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
    if not row:
        return None
    new_completed = 1 if row["completed"] == 0 else 0
    db.execute("UPDATE reminders SET completed = ? WHERE id = ?", (new_completed, reminder_id))
    return get_reminder(db, reminder_id)

def get_active_reminders(db: sqlite3.Connection) -> list:
    rows = db.execute(
        """
        SELECT * FROM reminders 
        WHERE completed = 0 
        ORDER BY 
            (CASE WHEN due_date IS NULL THEN 1 ELSE 0 END), 
            due_date ASC, 
            due_time ASC, 
            id ASC
        """
    ).fetchall()
    return [_serialize_reminder(row) for row in rows]

def get_all_reminders(db: sqlite3.Connection) -> list:
    rows = db.execute(
        """
        SELECT * FROM reminders 
        ORDER BY 
            (CASE WHEN due_date IS NULL THEN 1 ELSE 0 END), 
            due_date ASC, 
            due_time ASC, 
            id ASC
        """
    ).fetchall()
    return [_serialize_reminder(row) for row in rows]
