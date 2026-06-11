import json
import sqlite3
from datetime import date
from fastapi import HTTPException
from .timezone import DAY_ORDER, FULL_WEEK

def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(400, "Invalid date") from exc

def weekday_key(target_date: date) -> str:
    return DAY_ORDER[target_date.weekday()]

def normalize_active_days(raw_value):
    if raw_value in (None, ""):
        return FULL_WEEK[:]

    parsed = raw_value
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            parsed = [part.strip() for part in raw_value.split(",") if part.strip()]

    if not isinstance(parsed, (list, tuple, set)):
        parsed = FULL_WEEK

    days = []
    for item in parsed:
        if item in DAY_ORDER and item not in days:
            days.append(item)

    return days or FULL_WEEK[:]

def encode_active_days(days):
    return json.dumps(normalize_active_days(days))

def serialize_task(row: sqlite3.Row) -> dict:
    task = dict(row)
    task["active_days"] = normalize_active_days(task.get("active_days"))
    task["recurring"] = int(bool(task["recurring"]))
    task["completed_forever"] = int(bool(task["completed_forever"]))
    return task
