from fastapi import APIRouter, HTTPException, Query
from database.db import get_db
from schemas.response import APIResponse
from services.report_history_service import (
    get_report_history,
    generate_and_save_report,
    get_report_markdown,
    get_report_ai_reflection,
    report_ai_failed,
)
from services.analytics_service import aggregate_analytics
from services.date_service import get_logical_date_ist
from datetime import timedelta

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/status")
def report_status():
    """
    Returns a unified status keeping the '\ud83d\udcca Generate Report' action always active.
    """
    return APIResponse(data={
        "can_generate": True,
        "report_type": "weekly",
        "button_label": "\ud83d\udcca Generate Report"
    })

@router.get("/analytics")
def report_analytics():
    with get_db() as db:
        analytics = aggregate_analytics(db)
        return APIResponse(data=analytics)

@router.get("/history")
def report_history():
    with get_db() as db:
        history = get_report_history(db)
        return APIResponse(data=history)

@router.post("/generate")
def generate_report():
    """
    Alias / fallback to default weekly smart-generate for backwards compatibility.
    """
    with get_db() as db:
        today = get_logical_date_ist()
        target_date = today - timedelta(days=today.weekday() + 1)
        target_date_str = target_date.isoformat()
        
        # Check existence
        existing = db.execute("SELECT id FROM reports WHERE type = 'weekly' AND period_end = ?", (target_date_str,)).fetchone()
        if existing:
            if report_ai_failed(db, existing["id"]):
                # Bug fix: a report whose AI section failed used to block
                # regeneration forever. Regenerate it in place instead.
                report_data = generate_and_save_report(db, "weekly", report_date=target_date, replace_report_id=existing["id"])
                report_data["status"] = "regenerated"
                return APIResponse(data=report_data, message="Previous report had a failed AI section. Report regenerated.")
            markdown = get_report_markdown(db, existing["id"])
            ai_reflection = get_report_ai_reflection(db, existing["id"])
            return APIResponse(data={
                "id": existing["id"],
                "type": "weekly",
                "markdown_content": markdown,
                "ai_reflection": ai_reflection,
                "status": "existing"
            }, message="Report already exists. Opening saved report.")
            
        report_data = generate_and_save_report(db, "weekly", report_date=target_date)
        report_data["status"] = "created"
        return APIResponse(data=report_data, message="Report generated successfully")

@router.post("/smart-generate")
def smart_generate(type: str = Query("weekly")):
    if type not in ("weekly", "monthly"):
        raise HTTPException(400, "Invalid report type")
        
    with get_db() as db:
        today = get_logical_date_ist()
        if type == "monthly":
            first_of_current = today.replace(day=1)
            target_date = first_of_current - timedelta(days=1)
        else:
            target_date = today - timedelta(days=today.weekday() + 1)
            
        target_date_str = target_date.isoformat()
        
        existing = db.execute(
            "SELECT id FROM reports WHERE type = ? AND period_end = ?",
            (type, target_date_str)
        ).fetchone()
        
        if existing:
            if report_ai_failed(db, existing["id"]):
                # Bug fix: regenerate in place instead of blocking forever.
                report_data = generate_and_save_report(db, type, report_date=target_date, replace_report_id=existing["id"])
                report_data["status"] = "regenerated"
                return APIResponse(data=report_data, message="Previous report had a failed AI section. Report regenerated.")
            markdown = get_report_markdown(db, existing["id"])
            ai_reflection = get_report_ai_reflection(db, existing["id"])
            return APIResponse(data={
                "id": existing["id"],
                "type": type,
                "markdown_content": markdown,
                "ai_reflection": ai_reflection,
                "status": "existing"
            }, message="Report already exists. Opening saved report.")
            
        # Trigger generation
        report_data = generate_and_save_report(db, type, report_date=target_date)
        report_data["status"] = "created"
        return APIResponse(data=report_data, message="Report generated successfully")

@router.get("/{report_id}")
def get_report(report_id: int):
    with get_db() as db:
        markdown = get_report_markdown(db, report_id)
        if markdown is None:
            raise HTTPException(404, "Report not found")
            
        ai_reflection = get_report_ai_reflection(db, report_id)
        
        row = db.execute("SELECT type, generated_at, period_start, period_end, summary FROM reports WHERE id = ?", (report_id,)).fetchone()
        
        return APIResponse(data={
            "id": report_id,
            "type": row["type"],
            "generated_at": row["generated_at"],
            "period_start": row["period_start"],
            "period_end": row["period_end"],
            "summary": row["summary"],
            "markdown": markdown,
            "ai_reflection": ai_reflection
        })
