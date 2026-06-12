from fastapi import APIRouter, HTTPException, Query
from datetime import timedelta

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

router = APIRouter(prefix="/reports", tags=["Reports"])


def _target_period_end(report_type: str):
    """Period end for the latest completed cycle of the given report type."""
    today = get_logical_date_ist()
    if report_type == "monthly":
        return today.replace(day=1) - timedelta(days=1)
    return today - timedelta(days=today.weekday() + 1)


def _get_or_generate(report_type: str) -> APIResponse:
    """Single report generation flow shared by /generate and /smart-generate.

    Order: return the saved report if one exists for the period, unless its
    AI section failed (then regenerate it in place); otherwise generate.
    """
    with get_db() as db:
        target_date = _target_period_end(report_type)
        existing = db.execute(
            "SELECT id FROM reports WHERE type = ? AND period_end = ?",
            (report_type, target_date.isoformat())
        ).fetchone()

        if existing:
            if report_ai_failed(db, existing["id"]):
                report_data = generate_and_save_report(
                    db, report_type, report_date=target_date, replace_report_id=existing["id"]
                )
                report_data["status"] = "regenerated"
                return APIResponse(data=report_data, message="Previous report had a failed AI section. Report regenerated.")
            return APIResponse(data={
                "id": existing["id"],
                "type": report_type,
                "markdown_content": get_report_markdown(db, existing["id"]),
                "ai_reflection": get_report_ai_reflection(db, existing["id"]),
                "status": "existing"
            }, message="Report already exists. Opening saved report.")

        report_data = generate_and_save_report(db, report_type, report_date=target_date)
        report_data["status"] = "created"
        return APIResponse(data=report_data, message="Report generated successfully")


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
    """Backwards-compatible alias for the weekly report flow."""
    return _get_or_generate("weekly")


@router.post("/smart-generate")
def smart_generate(type: str = Query("weekly")):
    if type not in ("weekly", "monthly"):
        raise HTTPException(400, "Invalid report type")
    return _get_or_generate(type)


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
