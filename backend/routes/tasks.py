from fastapi import APIRouter, HTTPException
from database.db import get_db
from schemas.task_schemas import TaskCreate, TaskUpdate, EntryToggle, NoteUpdate
from schemas.response import APIResponse
from services.task_service import (
    get_all_active_tasks, get_all_archived_tasks, add_new_task, modify_task,
    remove_task, archive_task_service, restore_task_service, toggle_task_entry,
    update_task_note
)
from services.date_service import get_logical_date_ist, month_bounds, task_visible_in_month, task_active_on_date
from database.queries import get_entries_in_range
from utils.timezone import DAY_RESET_LABEL
from utils.helpers import parse_date
from datetime import date

router = APIRouter()

@router.get("/tasks")
def get_tasks():
    with get_db() as db:
        tasks = get_all_active_tasks(db)
        return APIResponse(data=tasks)

@router.get("/tasks/archived")
def get_archived_tasks():
    with get_db() as db:
        tasks = get_all_archived_tasks(db)
        return APIResponse(data=tasks)

@router.post("/tasks")
def add_task(body: TaskCreate):
    with get_db() as db:
        task = add_new_task(db, body)
        return APIResponse(data=task, message="Task created")

@router.put("/tasks/{task_id}")
def update_task(task_id: int, body: TaskUpdate):
    with get_db() as db:
        task = modify_task(db, task_id, body)
        return APIResponse(data=task, message="Task updated")

@router.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    with get_db() as db:
        remove_task(db, task_id)
        return APIResponse(data={"deleted": task_id}, message="Task deleted")

@router.post("/tasks/{task_id}/archive")
def archive_task(task_id: int):
    with get_db() as db:
        task = archive_task_service(db, task_id)
        return APIResponse(data=task, message="Task archived")

@router.post("/tasks/{task_id}/restore")
def restore_task(task_id: int):
    with get_db() as db:
        task = restore_task_service(db, task_id)
        return APIResponse(data=task, message="Task restored")

@router.get("/entries/{year}/{month}")
def get_monthly_entries(year: int, month: int):
    if not (1 <= month <= 12):
        raise HTTPException(400, "Invalid month")
    
    month_start, month_end, days_in_month = month_bounds(year, month)
    logical_today = get_logical_date_ist()

    with get_db() as db:
        tasks = get_all_active_tasks(db)
        visible_tasks = [
            t for t in tasks if task_visible_in_month(t, month_start, month_end)
        ]

        entries = get_entries_in_range(db, month_start.isoformat(), month_end.isoformat())
        
        from analytics.streaks import compute_task_streaks
        streaks = compute_task_streaks(db)

    entry_lookup = {(row["task_id"], row["date"]): dict(row) for row in entries}
    count_until = min(logical_today, month_end)
    task_list = []

    for task in visible_tasks:
        days_data = {}
        task_total_slots = 0
        task_completed_slots = 0
        
        for day_num in range(1, days_in_month + 1):
            day_date = date(year, month, day_num)
            date_str = day_date.isoformat()
            active = task_active_on_date(task, day_date)
            entry = entry_lookup.get((task["id"], date_str))

            days_data[date_str] = {
                "id": entry["id"] if entry else None,
                "completed": int(bool(entry["completed"])) if entry else 0,
                "note": entry["note"] if entry else "",
                "active": active,
            }

            if active and day_date <= count_until:
                task_total_slots += 1
                if entry and entry["completed"]:
                    task_completed_slots += 1

        task_completion_pct = round((task_completed_slots / task_total_slots * 100) if task_total_slots else 0, 1)

        task_with_days = dict(task)
        task_with_days["days"] = days_data
        task_with_days["streak"] = streaks.get(task["id"], 0)
        task_with_days["completion_pct"] = task_completion_pct
        task_list.append(task_with_days)

    return APIResponse(data={
        "year": year,
        "month": month,
        "days_in_month": days_in_month,
        "tasks": task_list,
        "stats": {
            "total_slots": 0,
            "completed_slots": 0,
            "completion_pct": 0,
        },
        "meta": {
            "logical_today": logical_today.isoformat(),
            "day_reset_label": DAY_RESET_LABEL,
        },
    })

@router.post("/entries/toggle")
def toggle_entry(body: EntryToggle):
    with get_db() as db:
        res = toggle_task_entry(db, body)
        return APIResponse(data=res)

@router.put("/entries/note")
def update_note(body: NoteUpdate):
    with get_db() as db:
        res = update_task_note(db, body)
        return APIResponse(data=res)
