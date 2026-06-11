import sqlite3
from datetime import date
from analytics.metrics import get_global_metrics
from services.date_service import get_logical_date_ist, task_active_on_date
from utils.helpers import serialize_task

def calculate_productivity_scores(db: sqlite3.Connection) -> dict:
    today = get_logical_date_ist()
    today_str = today.isoformat()
    
    # 1. CONSISTENCY SCORE
    # Formula: (Weekly Task Completion Rate * 0.6) + (Min(Current Streak * 10, 100) * 0.4)
    try:
        metrics = get_global_metrics(db)
        weekly_completion = metrics.get("weekly_consistency", 0)
        current_streak = metrics.get("current_streak", 0)
    except Exception:
        weekly_completion = 0
        current_streak = 0
        
    consistency_score = round((weekly_completion * 0.6) + (min(current_streak * 10, 100) * 0.4))
    
    # 2. EXECUTION SCORE
    # Formula: (Today's task completion % * 0.4) + (Milestone completion % * 0.4) + (Project completed % * 0.2)
    # A. Today's task completion %
    task_rows = db.execute("SELECT * FROM tasks WHERE completed_forever = 0").fetchall()
    tasks = [serialize_task(row) for row in task_rows]
    
    today_total = 0
    today_completed = 0
    for task in tasks:
        if task_active_on_date(task, today):
            today_total += 1
            # Check if completed in daily_entries
            completed = db.execute(
                "SELECT completed FROM daily_entries WHERE task_id = ? AND date = ?",
                (task["id"], today_str)
            ).fetchone()
            if completed and completed["completed"] == 1:
                today_completed += 1
                
    today_pct = (today_completed / today_total * 100.0) if today_total > 0 else 100.0
    
    # B. Milestone completion %
    milestone_row = db.execute("SELECT COUNT(*) as total, SUM(completed) as completed FROM project_milestones").fetchone()
    if milestone_row and milestone_row["total"] > 0:
        completed_val = milestone_row["completed"] if milestone_row["completed"] is not None else 0
        milestone_pct = (completed_val / milestone_row["total"]) * 100.0
    else:
        milestone_pct = 100.0
        
    # C. Project completed %
    project_row = db.execute("SELECT COUNT(*) as total, SUM(completed) as completed FROM projects").fetchone()
    if project_row and project_row["total"] > 0:
        completed_val = project_row["completed"] if project_row["completed"] is not None else 0
        project_pct = (completed_val / project_row["total"]) * 100.0
    else:
        project_pct = 100.0
        
    execution_score = round((today_pct * 0.4) + (milestone_pct * 0.4) + (project_pct * 0.2))
    
    # 3. GOAL PROGRESS SCORE
    # Formula: (Average Goal Progress * 0.6) + (Average Active Project Progress * 0.4)
    # A. Goals Progress Avg
    goal_row = db.execute("SELECT COUNT(*) as total, AVG(progress) as avg_progress FROM goals").fetchone()
    if goal_row and goal_row["total"] > 0:
        goal_avg = goal_row["avg_progress"] if goal_row["avg_progress"] is not None else 0.0
    else:
        goal_avg = 100.0
        
    # B. Active Projects Progress Avg
    proj_progress_row = db.execute("SELECT COUNT(*) as total, AVG(progress) as avg_progress FROM projects WHERE completed = 0").fetchone()
    if proj_progress_row and proj_progress_row["total"] > 0:
        proj_avg = proj_progress_row["avg_progress"] if proj_progress_row["avg_progress"] is not None else 0.0
    else:
        proj_avg = 100.0
        
    goal_progress_score = round((goal_avg * 0.6) + (proj_avg * 0.4))
    
    # Enforce bounds
    return {
        "consistency": max(0, min(100, consistency_score)),
        "execution": max(0, min(100, execution_score)),
        "goal_progress": max(0, min(100, goal_progress_score))
    }
