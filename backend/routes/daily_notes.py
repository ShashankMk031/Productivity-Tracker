from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.db import get_db
from schemas.response import APIResponse

router = APIRouter(prefix="/daily-notes", tags=["Daily Notes"])

class DailyNoteSave(BaseModel):
    content: str

@router.get("/{date}")
def get_daily_note(date: str):
    with get_db() as db:
        row = db.execute("SELECT content FROM daily_notes WHERE date = ?", (date,)).fetchone()
        if not row:
            return APIResponse(data={"date": date, "content": ""})
        return APIResponse(data={"date": date, "content": row[0]})

@router.put("/{date}")
def save_daily_note(date: str, body: DailyNoteSave):
    content = body.content.strip()
    with get_db() as db:
        if not content:
            # Delete if empty to save space
            db.execute("DELETE FROM daily_notes WHERE date = ?", (date,))
        else:
            db.execute(
                """
                INSERT INTO daily_notes (date, content)
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET content = excluded.content
                """,
                (date, content)
            )
        db.commit()
        return APIResponse(data={"date": date, "content": content}, message="Daily note saved")
