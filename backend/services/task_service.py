import sqlite3
from fastapi import HTTPException
from database.queries import (
    get_task_by_id, get_active_tasks, get_archived_tasks,
    create_task, update_task, delete_task, set_task_archived,
    get_entry, update_entry_completed, update_entry_note, create_entry
)
from utils.helpers import serialize_task, encode_active_days, parse_date
from services.date_service import get_logical_date_ist, task_active_on_date
from schemas.task_schemas import TaskCreate, TaskUpdate, EntryToggle, NoteUpdate
from analytics.streaks import compute_task_streaks

def fetch_task_or_404(db: sqlite3.Connection, task_id: int) -> dict:
    row = get_task_by_id(db, task_id)
    if not row:
        raise HTTPException(404, "Task not found")
    return serialize_task(row)

def get_all_active_tasks(db: sqlite3.Connection) -> list[dict]:
    rows = get_active_tasks(db)
    return [serialize_task(row) for row in rows]

def get_all_archived_tasks(db: sqlite3.Connection) -> list[dict]:
    rows = get_archived_tasks(db)
    return [serialize_task(row) for row in rows]

def add_new_task(db: sqlite3.Connection, data: TaskCreate) -> dict:
    title = data.title.strip()
    active_days_json = encode_active_days(data.active_days)
    created_at = get_logical_date_ist().isoformat()
    
    # We maintain recurring=1 as requested, since we removed the recurring toggle earlier but keeping it true by default.
    task_id = create_task(db, title, 1, created_at, active_days_json)
    return fetch_task_or_404(db, task_id)

def modify_task(db: sqlite3.Connection, task_id: int, data: TaskUpdate) -> dict:
    task = fetch_task_or_404(db, task_id)
    title = data.title.strip()
    active_days_json = encode_active_days(data.active_days)
    
    update_task(db, task_id, title, task["recurring"], active_days_json)
    return fetch_task_or_404(db, task_id)

def remove_task(db: sqlite3.Connection, task_id: int):
    fetch_task_or_404(db, task_id)
    delete_task(db, task_id)

def archive_task_service(db: sqlite3.Connection, task_id: int) -> dict:
    fetch_task_or_404(db, task_id)
    set_task_archived(db, task_id, 1)
    return fetch_task_or_404(db, task_id)

def restore_task_service(db: sqlite3.Connection, task_id: int) -> dict:
    fetch_task_or_404(db, task_id)
    set_task_archived(db, task_id, 0)
    return fetch_task_or_404(db, task_id)

def toggle_task_entry(db: sqlite3.Connection, data: EntryToggle) -> dict:
    target_date = parse_date(data.date)
    task = fetch_task_or_404(db, data.task_id)
    
    if task["completed_forever"]:
        raise HTTPException(400, "Archived tasks cannot be updated")
    if not task_active_on_date(task, target_date):
        raise HTTPException(400, "Inactive days cannot be completed")

    existing = get_entry(db, data.task_id, data.date)
    
    if existing:
        new_value = 0 if existing["completed"] else 1
        update_entry_completed(db, existing["id"], new_value)
        note = existing["note"]
    else:
        new_value = 1
        note = ""
        create_entry(db, data.task_id, data.date, 1, note)

    new_streak = compute_task_streaks(db).get(data.task_id, 0)

    return {
        "task_id": data.task_id,
        "date": data.date,
        "completed": new_value,
        "note": note,
        "active": True,
        "streak": new_streak,
    }

def update_task_note(db: sqlite3.Connection, data: NoteUpdate) -> dict:
    note = data.note.strip()
    target_date = parse_date(data.date)
    task = fetch_task_or_404(db, data.task_id)
    
    existing = get_entry(db, data.task_id, data.date)
    
    if not existing and not task_active_on_date(task, target_date):
        raise HTTPException(400, "Inactive days cannot be annotated")

    if existing:
        update_entry_note(db, existing["id"], note)
    else:
        create_entry(db, data.task_id, data.date, 0, note)
        
    updated_entry = get_entry(db, data.task_id, data.date)

    return {
        "id": updated_entry["id"],
        "task_id": updated_entry["task_id"],
        "date": updated_entry["date"],
        "completed": int(bool(updated_entry["completed"])),
        "note": updated_entry["note"],
        "active": task_active_on_date(task, target_date),
    }
