from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.db import get_db
from schemas.response import APIResponse
from services.reminder_service import (
    add_reminder,
    delete_reminder,
    toggle_reminder_completed,
    get_active_reminders,
    get_all_reminders
)

router = APIRouter(prefix="/reminders", tags=["Reminders"])

class AddReminderPayload(BaseModel):
    title: str
    datetime: str
    recurring: str = 'none'

@router.get("")
def list_reminders():
    with get_db() as db:
        res = get_all_reminders(db)
        return APIResponse(data=res)

@router.get("/active")
def list_active_reminders():
    with get_db() as db:
        res = get_active_reminders(db)
        return APIResponse(data=res)

@router.post("")
def create_reminder(payload: AddReminderPayload):
    with get_db() as db:
        res = add_reminder(db, payload.title, payload.datetime, payload.recurring)
        return APIResponse(data=res)

@router.post("/{reminder_id}/toggle")
def toggle_reminder(reminder_id: int):
    with get_db() as db:
        res = toggle_reminder_completed(db, reminder_id)
        if not res:
            raise HTTPException(404, "Reminder not found")
        return APIResponse(data=res)

@router.delete("/{reminder_id}")
def remove_reminder(reminder_id: int):
    with get_db() as db:
        success = delete_reminder(db, reminder_id)
        if not success:
            raise HTTPException(404, "Reminder not found")
        return APIResponse(message="Reminder deleted successfully")
