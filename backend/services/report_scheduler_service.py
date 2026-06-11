from datetime import datetime, timedelta
from services.date_service import get_logical_date_ist

def check_report_status(db):
    """
    Determines if today is a valid day for a report generation.
    Returns the report status, the button label, and the report type.
    """
    logical_today = get_logical_date_ist()
    day_of_week = logical_today.weekday() # 0 = Monday, 6 = Sunday
    day_of_month = logical_today.day

    # Check if a report was already generated today
    today_str = logical_today.isoformat()
    already_generated = False
    row = db.execute("SELECT id FROM reports WHERE date(generated_at) = ?", (today_str,)).fetchone()
    if row:
        already_generated = True

    can_generate = False
    report_type = None
    
    # Priority: Monthly report on the 1st
    if day_of_month == 1 and not already_generated:
        can_generate = True
        report_type = "monthly"
    # Secondary: Weekly report on Monday
    elif day_of_week == 0 and not already_generated:
        can_generate = True
        report_type = "weekly"
        
    button_label = "📊 Generate Report" if can_generate else "📖 Check Reports"
    
    return {
        "can_generate": can_generate,
        "report_type": report_type,
        "button_label": button_label
    }
