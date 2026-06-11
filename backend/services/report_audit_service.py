import sqlite3
from datetime import date, timedelta
from services.date_service import get_logical_date_ist
from services.report_history_service import generate_and_save_report

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
    print("[Report Audit Service] Initiating productivity report audit...")
    today = get_logical_date_ist()
    
    # 1. Weekly Check
    w_start, w_end = get_latest_completed_week_bounds(today)
    w_end_str = w_end.isoformat()
    
    existing_weekly = db.execute(
        "SELECT id FROM reports WHERE type = 'weekly' AND period_end = ?",
        (w_end_str,)
    ).fetchone()
    
    if not existing_weekly:
        print(f"[Report Audit Service] Missing weekly report for period ending {w_end_str}. Auto-generating...")
        try:
            res = generate_and_save_report(db, "weekly", report_date=w_end)
            print(f"✓ [Report Audit Service] Auto-generated weekly report ID: {res['id']}")
        except Exception as e:
            print(f"❌ [Report Audit Service] Failed to auto-generate weekly report: {e}")
    else:
        print(f"[Report Audit Service] Weekly report for period ending {w_end_str} already exists (ID: {existing_weekly['id']}).")

    # 2. Monthly Check
    m_start, m_end = get_previous_month_bounds(today)
    m_end_str = m_end.isoformat()
    
    existing_monthly = db.execute(
        "SELECT id FROM reports WHERE type = 'monthly' AND period_end = ?",
        (m_end_str,)
    ).fetchone()
    
    if not existing_monthly:
        print(f"[Report Audit Service] Missing monthly report for period ending {m_end_str}. Auto-generating...")
        try:
            res = generate_and_save_report(db, "monthly", report_date=m_end)
            print(f"✓ [Report Audit Service] Auto-generated monthly report ID: {res['id']}")
        except Exception as e:
            print(f"❌ [Report Audit Service] Failed to auto-generate monthly report: {e}")
    else:
        print(f"[Report Audit Service] Monthly report for period ending {m_end_str} already exists (ID: {existing_monthly['id']}).")
        
    print("[Report Audit Service] Audit complete.")
