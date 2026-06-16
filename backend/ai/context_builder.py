import sqlite3
from datetime import datetime
from typing import Optional

from services.analytics_service import aggregate_analytics
from services.goal_service import get_all_goals
from services.project_service import get_all_projects

from .note_analysis import analyze_notes
from .behavioral_summary import generate_behavioral_summary
from .prediction_summary_builder import build_prediction_summary
from intelligence.prediction_engine import generate_intelligence_snapshot
from intelligence.prediction_accuracy import evaluate_prediction_accuracy
from .schemas import (
    AIContextPackage,
    GoalProgressInfo,
    ProjectProgressInfo,
    ProjectMilestoneInfo
)

def build_ai_context(
    db: sqlite3.Connection,
    period_type: str = "weekly",
    period_start: Optional[str] = None,
    period_end: Optional[str] = None
) -> AIContextPackage:
    # 1. Gather Analytics
    analytics = aggregate_analytics(db, period_start=period_start, period_end=period_end)
    
    # 2. Gather Note Analysis
    notes_analysis = analyze_notes(db, period_start, period_end)
    
    # 3. Gather Behavioral Summary
    behavioral_patterns = generate_behavioral_summary(db, period_start=period_start, period_end=period_end)
    
    # 4. Gather & Map Goals
    goals_raw = get_all_goals(db)
    goals = []
    for g in goals_raw:
        goals.append(GoalProgressInfo(
            id=g["id"],
            title=g["title"],
            category=g["category"] or "General",
            progress=g["progress"],
            target_date=g["target_date"],
            completed=g["completed"]
        ))
        
    # 5. Gather & Map Projects with Milestones
    projects_raw = get_all_projects(db)
    projects = []
    for p in projects_raw:
        milestones = []
        for m in p.get("milestones", []):
            milestones.append(ProjectMilestoneInfo(
                id=m["id"],
                title=m["title"],
                completed=m["completed"]
            ))
            
        countdown = p.get("countdown", {})
        urgency = countdown.get("urgency", "GREEN")
        
        projects.append(ProjectProgressInfo(
            id=p["id"],
            title=p["title"],
            deadline=p["deadline"],
            progress=p["progress"],
            urgency=urgency,
            milestones=milestones
        ))
        
    # 6. Gather OS Dimension Stats
    focus_stats = {"total_duration_sec": 0, "total_sessions": 0, "completed_sessions": 0}
    if period_start and period_end:
        # Pad dates to search full days YYYY-MM-DD
        p_start_pad = f"{period_start}T00:00:00"
        p_end_pad = f"{period_end}T23:59:59"
        focus_row = db.execute(
            "SELECT SUM(duration) as total_duration, COUNT(*) as total, SUM(CASE WHEN end_time IS NOT NULL THEN 1 ELSE 0 END) as completed FROM focus_sessions WHERE start_time >= ? AND start_time <= ?",
            (p_start_pad, p_end_pad)
        ).fetchone()
        if focus_row:
            focus_stats["total_duration_sec"] = focus_row["total_duration"] or 0
            focus_stats["total_sessions"] = focus_row["total"] or 0
            focus_stats["completed_sessions"] = focus_row["completed"] or 0
            
    reminder_stats = {"total_reminders": 0, "completed_reminders": 0}
    if period_start and period_end:
        p_start_pad = f"{period_start}T00:00:00"
        p_end_pad = f"{period_end}T23:59:59"
        reminder_row = db.execute(
            "SELECT COUNT(*) as total, SUM(completed) as completed FROM reminders WHERE datetime >= ? AND datetime <= ?",
            (p_start_pad, p_end_pad)
        ).fetchone()
        if reminder_row:
            reminder_stats["total_reminders"] = reminder_row["total"] or 0
            reminder_stats["completed_reminders"] = reminder_row["completed"] or 0
            
    from services.scoring_service import calculate_productivity_scores
    scores = calculate_productivity_scores(db)
    
    intelligence_snapshot = generate_intelligence_snapshot(db)
    prediction_acc = evaluate_prediction_accuracy(db)
    prediction_summary = build_prediction_summary(intelligence_snapshot, prediction_acc)
    
    generated_at = datetime.now().isoformat()
    
    return AIContextPackage(
        analytics=analytics,
        notes=notes_analysis,
        goals=goals,
        projects=projects,
        behavioral_patterns=behavioral_patterns,
        generated_at=generated_at,
        period_type=period_type,
        period_start=period_start,
        period_end=period_end,
        focus_stats=focus_stats,
        reminder_stats=reminder_stats,
        scores=scores,
        intelligence_snapshot=intelligence_snapshot,
        prediction_accuracy=prediction_acc,
        prediction_summary_markdown=prediction_summary,
    )
