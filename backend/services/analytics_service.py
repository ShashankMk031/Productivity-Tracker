import sqlite3
from datetime import date, timedelta

from analytics.metrics import get_global_metrics, get_behavioral_insights
from analytics.charts import get_chart_data
from services.date_service import task_active_on_date
from utils.helpers import parse_date, serialize_task, weekday_key

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _build_period_analytics(db: sqlite3.Connection, period_start: str, period_end: str) -> dict:
    start = parse_date(period_start)
    end = parse_date(period_end)
    task_rows = db.execute("SELECT * FROM tasks WHERE completed_forever = 0").fetchall()
    tasks = [serialize_task(row) for row in task_rows]

    if not tasks:
        return {
            "metrics": {
                "completion_pct": 0,
                "completed_slots": 0,
                "missed_slots": 0,
                "active_tasks": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "days_in_period": (end - start).days + 1,
                "perfect_days": 0,
            },
            "insights": {},
            "charts": {},
        }

    active_tasks = [task for task in tasks if parse_date(task["created_at"]) <= end]
    completed_rows = db.execute(
        """
        SELECT task_id, date, completed
        FROM daily_entries
        WHERE date >= ? AND date <= ? AND completed = 1
        """,
        (period_start, period_end),
    ).fetchall()
    completed_lookup = {(row["task_id"], row["date"]): True for row in completed_rows}

    weekday_counts = {day: {"total": 0, "completed": 0} for day in WEEKDAYS}
    task_totals = {
        task["id"]: {"title": task["title"], "total": 0, "completed": 0}
        for task in active_tasks
    }
    total_slots = 0
    completed_slots = 0
    perfect_days = 0
    longest_streak = 0
    current_streak = 0
    running_streak = 0
    current = start
    while current <= end:
        date_str = current.isoformat()
        day_total = 0
        day_completed = 0
        for task in active_tasks:
            if task_active_on_date(task, current):
                day_total += 1
                total_slots += 1
                task_totals[task["id"]]["total"] += 1
                weekday = weekday_key(current)
                weekday_counts[weekday]["total"] += 1
                if completed_lookup.get((task["id"], date_str)):
                    day_completed += 1
                    completed_slots += 1
                    task_totals[task["id"]]["completed"] += 1
                    weekday_counts[weekday]["completed"] += 1
        if day_total > 0 and day_completed == day_total:
            perfect_days += 1
            running_streak += 1
            longest_streak = max(longest_streak, running_streak)
            current_streak = running_streak
        elif day_total > 0:
            running_streak = 0
            current_streak = 0
        current += timedelta(days=1)

    weekday_rates = {
        day: data["completed"] / data["total"]
        for day, data in weekday_counts.items()
        if data["total"] > 0
    }
    completion_pct = round((completed_slots / total_slots) * 100, 1) if total_slots else 0

    best_task = None
    most_skipped = None
    if task_totals:
        best_task = max(
            task_totals.values(),
            key=lambda item: (item["completed"] / item["total"]) if item["total"] else 0,
        )
        most_skipped = max(
            task_totals.values(),
            key=lambda item: item["total"] - item["completed"],
        )

    return {
        "metrics": {
            "completion_pct": completion_pct,
            "completed_slots": completed_slots,
            "missed_slots": total_slots - completed_slots,
            "active_tasks": len(active_tasks),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "days_in_period": (end - start).days + 1,
            "perfect_days": perfect_days,
        },
        "insights": {
            "most_productive_weekday": max(weekday_rates, key=weekday_rates.get) if weekday_rates else "N/A",
            "least_productive_weekday": min(weekday_rates, key=weekday_rates.get) if weekday_rates else "N/A",
            "best_task": best_task["title"] if best_task else "N/A",
            "most_skipped_task": most_skipped["title"] if most_skipped else "N/A",
        },
        "charts": {},
    }


def aggregate_analytics(db: sqlite3.Connection, period_start: str | None = None, period_end: str | None = None) -> dict:
    if period_start and period_end:
        return _build_period_analytics(db, period_start, period_end)

    global_metrics = get_global_metrics(db)
    insights = get_behavioral_insights(db)
    chart_data = get_chart_data(db)
    
    return {
        "metrics": global_metrics,
        "insights": insights,
        "charts": chart_data
    }
