from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database.db import get_db
from schemas.response import APIResponse
import services.sticky_service as sticky_service

router = APIRouter(prefix="/sticky-notes", tags=["Sticky Notes"])

class UpdateStickyPayload(BaseModel):
    content: Optional[str] = None
    color: Optional[str] = None
    text_color: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    z_index: Optional[int] = None
    is_completed: Optional[bool] = None
    is_draft: Optional[bool] = None
    tag: Optional[str] = None
    is_archived: Optional[bool] = None
    rotation: Optional[float] = None

@router.get("")
def list_sticky_notes(query: Optional[str] = None):
    with get_db() as db:
        notes = sticky_service.get_active_stickies(db, query=query)
        return APIResponse(data=notes)

@router.put("/{sticky_id}")
def update_sticky_note(sticky_id: int, payload: UpdateStickyPayload):
    with get_db() as db:
        # Check if the sticky note exists
        existing = sticky_service.get_sticky(db, sticky_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Sticky note not found")
            
        # Parse inputs
        is_completed_val = int(payload.is_completed) if payload.is_completed is not None else None
        is_draft_val = int(payload.is_draft) if payload.is_draft is not None else None
        is_archived_val = int(payload.is_archived) if payload.is_archived is not None else None
        
        updated = sticky_service.update_sticky(
            db,
            sticky_id,
            content=payload.content,
            color=payload.color,
            text_color=payload.text_color,
            position_x=payload.position_x,
            position_y=payload.position_y,
            width=payload.width,
            height=payload.height,
            z_index=payload.z_index,
            is_completed=is_completed_val,
            is_draft=is_draft_val,
            tag=payload.tag,
            is_archived=is_archived_val,
            rotation=payload.rotation
        )
        return APIResponse(data=updated, message="Sticky note updated successfully")

@router.delete("/{sticky_id}")
def delete_sticky_note(sticky_id: int):
    with get_db() as db:
        existing = sticky_service.get_sticky(db, sticky_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Sticky note not found")
            
        deleted = sticky_service.delete_sticky(db, sticky_id)
        return APIResponse(data={"deleted": deleted}, message="Sticky note deleted successfully")

@router.post("/archive-completed")
def archive_completed_stickies():
    with get_db() as db:
        count = sticky_service.archive_completed_stickies(db)
        return APIResponse(data={"archived_count": count}, message=f"Archived {count} completed sticky notes")

@router.post("/delete-completed")
def delete_completed_stickies():
    with get_db() as db:
        count = sticky_service.delete_completed_stickies(db)
        return APIResponse(data={"deleted_count": count}, message=f"Deleted {count} completed sticky notes")
