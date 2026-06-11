from fastapi import APIRouter
from pydantic import BaseModel
from database.db import get_db
from schemas.response import APIResponse
from services.focus_service import start_focus_session, stop_focus_session, get_active_session, get_focus_history

router = APIRouter(prefix="/focus", tags=["Focus Sessions"])

class StartFocusPayload(BaseModel):
    title: str

class StopFocusPayload(BaseModel):
    notes: str = ""

@router.post("/start")
def start_session(payload: StartFocusPayload):
    with get_db() as db:
        res = start_focus_session(db, payload.title)
        return APIResponse(data=res)

@router.post("/stop")
def stop_session(payload: StopFocusPayload):
    with get_db() as db:
        res = stop_focus_session(db, payload.notes)
        return APIResponse(data=res)

@router.get("/active")
def active_session():
    with get_db() as db:
        res = get_active_session(db)
        return APIResponse(data=res)

@router.get("/history")
def history_sessions():
    with get_db() as db:
        res = get_focus_history(db)
        return APIResponse(data=res)
