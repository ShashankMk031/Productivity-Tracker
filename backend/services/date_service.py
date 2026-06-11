import calendar
from datetime import date, datetime, timedelta
from utils.timezone import IST, DAY_RESET_HOUR_IST
from utils.helpers import parse_date, weekday_key, normalize_active_days

def get_logical_date_ist(now: datetime | None = None) -> date:
    if now is None:
        current = datetime.now(IST)
    elif now.tzinfo is None:
        current = now.replace(tzinfo=IST)
    else:
        current = now.astimezone(IST)
    return (current - timedelta(hours=DAY_RESET_HOUR_IST)).date()

def month_bounds(year: int, month: int) -> tuple[date, date, int]:
    _, days_in_month = calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, days_in_month)
    return month_start, month_end, days_in_month

def task_visible_in_month(task: dict, month_start: date, month_end: date) -> bool:
    created_at = parse_date(task["created_at"])
    if created_at > month_end:
        return False
    if task["recurring"]:
        return True
    return created_at.year == month_start.year and created_at.month == month_start.month

def task_active_on_date(task: dict, target_date: date) -> bool:
    created_at = parse_date(task["created_at"])
    month_start = date(created_at.year, created_at.month, 1)
    if target_date < month_start:
        return False
    if not task["recurring"]:
        if target_date.year != created_at.year or target_date.month != created_at.month:
            return False
    return weekday_key(target_date) in normalize_active_days(task["active_days"])
