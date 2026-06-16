import sqlite3
from services.analytics_service import aggregate_analytics
from .schemas import BehavioralSummary

def generate_behavioral_summary(
    db: sqlite3.Connection,
    period_start: str | None = None,
    period_end: str | None = None,
) -> BehavioralSummary:
    analytics = aggregate_analytics(db, period_start=period_start, period_end=period_end)
    metrics = analytics.get("metrics", {})
    insights = analytics.get("insights", {})
    
    # Map productive and weak weekdays into lists
    productive = insights.get("most_productive_weekday", "N/A")
    weak = insights.get("least_productive_weekday", "N/A")
    
    productive_weekdays = [productive] if productive and productive != "N/A" else []
    weak_weekdays = [weak] if weak and weak != "N/A" else []
    
    return BehavioralSummary(
        completion_rate=metrics.get("completion_pct", 0.0),
        current_streak=metrics.get("current_streak", 0),
        longest_streak=metrics.get("longest_streak", 0),
        productive_weekdays=productive_weekdays,
        weak_weekdays=weak_weekdays,
        missed_days_count=metrics.get("missed_slots", metrics.get("missed_days", 0)),
        active_tasks_count=metrics.get("active_tasks", 0)
    )
