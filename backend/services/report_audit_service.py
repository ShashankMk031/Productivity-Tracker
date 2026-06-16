import sqlite3
from datetime import date, timedelta
from services.date_service import get_logical_date_ist
from services.report_history_service import generate_and_save_report
from services.logging_service import get_logger

logger = get_logger(__name__)

def get_latest_completed_week_bounds(today: date) -> tuple[date, date]:
    """
    Returns (start_date, end_date) for the latest completed calendar week (Mon-Sun).
    """
    current_week_Monday = today - timedelta(days=today.weekday())
    period_end = current_week_Monday - timedelta(days=1)
    period_start = period_end - timedelta(days=6)
    return period_start, period_end

def get_previous_month_bounds(today: date) -> tuple[date, date]:
    """
    Returns (start_date, end_date) for the previous calendar month.
    """
    first_of_current = today.replace(day=1)
    period_end = first_of_current - timedelta(days=1)
    period_start = period_end.replace(day=1)
    return period_start, period_end

def run_report_audit(db: sqlite3.Connection):
    """
    Performs startup report auditing. Detects missing weekly and monthly reports
    for the latest completed calendar cycles and auto-generates them.
    """
    logger.info("Initiating productivity report audit")
    today = get_logical_date_ist()
    
    # 1. Weekly Check
    _, w_end = get_latest_completed_week_bounds(today)
    w_end_str = w_end.isoformat()
    
    existing_weekly = db.execute(
        "SELECT id FROM reports WHERE type = 'weekly' AND period_end = ?",
        (w_end_str,)
    ).fetchone()
    
    if not existing_weekly:
        logger.info("Missing weekly report for period ending %s; auto-generating", w_end_str)
        try:
            res = generate_and_save_report(db, "weekly", report_date=w_end)
            logger.info("Auto-generated weekly report ID %s", res["id"])
        except Exception as e:
            logger.error("Failed to auto-generate weekly report: %s", e)
    else:
        logger.info("Weekly report for period ending %s already exists (ID %s)", w_end_str, existing_weekly["id"])

    # 2. Monthly Check
    _, m_end = get_previous_month_bounds(today)
    m_end_str = m_end.isoformat()
    
    existing_monthly = db.execute(
        "SELECT id FROM reports WHERE type = 'monthly' AND period_end = ?",
        (m_end_str,)
    ).fetchone()
    
    if not existing_monthly:
        logger.info("Missing monthly report for period ending %s; auto-generating", m_end_str)
        try:
            res = generate_and_save_report(db, "monthly", report_date=m_end)
            logger.info("Auto-generated monthly report ID %s", res["id"])
        except Exception as e:
            logger.error("Failed to auto-generate monthly report: %s", e)
    else:
        logger.info("Monthly report for period ending %s already exists (ID %s)", m_end_str, existing_monthly["id"])
        
    logger.info("Audit complete")
