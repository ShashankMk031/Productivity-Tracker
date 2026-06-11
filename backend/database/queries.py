import sqlite3
from typing import List

def get_task_by_id(db: sqlite3.Connection, task_id: int) -> sqlite3.Row | None:
    return db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

def get_active_tasks(db: sqlite3.Connection) -> List[sqlite3.Row]:
    return db.execute("SELECT * FROM tasks WHERE completed_forever = 0 ORDER BY sort_order, id").fetchall()

def get_archived_tasks(db: sqlite3.Connection) -> List[sqlite3.Row]:
    return db.execute("SELECT * FROM tasks WHERE completed_forever = 1 ORDER BY id DESC").fetchall()

def create_task(db: sqlite3.Connection, title: str, recurring: int, created_at: str, active_days: str) -> int:
    cur = db.execute(
        "INSERT INTO tasks (title, recurring, created_at, active_days) VALUES (?, ?, ?, ?)",
        (title, recurring, created_at, active_days)
    )
    return cur.lastrowid

def update_task(db: sqlite3.Connection, task_id: int, title: str, recurring: int, active_days: str):
    db.execute(
        "UPDATE tasks SET title = ?, recurring = ?, active_days = ? WHERE id = ?",
        (title, recurring, active_days, task_id)
    )

def delete_task(db: sqlite3.Connection, task_id: int):
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

def set_task_archived(db: sqlite3.Connection, task_id: int, archived: int):
    db.execute("UPDATE tasks SET completed_forever = ? WHERE id = ?", (archived, task_id))

def get_entries_in_range(db: sqlite3.Connection, start_date: str, end_date: str) -> List[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM daily_entries WHERE date >= ? AND date <= ? ORDER BY task_id, date",
        (start_date, end_date)
    ).fetchall()

def get_entry(db: sqlite3.Connection, task_id: int, date_str: str) -> sqlite3.Row | None:
    return db.execute(
        "SELECT * FROM daily_entries WHERE task_id = ? AND date = ?",
        (task_id, date_str)
    ).fetchone()

def update_entry_completed(db: sqlite3.Connection, entry_id: int, completed: int):
    db.execute("UPDATE daily_entries SET completed = ? WHERE id = ?", (completed, entry_id))

def update_entry_note(db: sqlite3.Connection, entry_id: int, note: str):
    db.execute("UPDATE daily_entries SET note = ? WHERE id = ?", (note, entry_id))

def create_entry(db: sqlite3.Connection, task_id: int, date_str: str, completed: int, note: str) -> int:
    cur = db.execute(
        "INSERT INTO daily_entries (task_id, date, completed, note) VALUES (?, ?, ?, ?)",
        (task_id, date_str, completed, note)
    )
    return cur.lastrowid
