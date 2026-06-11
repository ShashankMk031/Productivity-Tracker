import sqlite3
from datetime import date, timedelta
from utils.helpers import parse_date, serialize_task
from services.date_service import get_logical_date_ist, task_active_on_date

def compute_all_streaks(db: sqlite3.Connection) -> dict[int, dict]:
    """
    Computes current and longest streaks for all tasks.
    Returns: { task_id: {"current_streak": X, "longest_streak": Y} }
    """
    today = get_logical_date_ist()
    task_rows = db.execute("SELECT * FROM tasks").fetchall()
    tasks = [serialize_task(row) for row in task_rows]
    
    if not tasks:
        return {}

    earliest_created = min(parse_date(task["created_at"]) for task in tasks)
    earliest_start = date(earliest_created.year, earliest_created.month, 1)

    completed_rows = db.execute(
        """
        SELECT task_id, date, completed
        FROM daily_entries
        WHERE completed = 1 AND date >= ?
        """,
        (earliest_start.isoformat(),),
    ).fetchall()
    
    completed_lookup = {
        (row["task_id"], row["date"]): bool(row["completed"])
        for row in completed_rows
    }
    
    streaks = {}
    for task in tasks:
        longest_streak = 0
        current_iter_streak = 0
        
        task_created = parse_date(task["created_at"])
        task_start = date(task_created.year, task_created.month, 1)
        
        check = task_start
        
        while check <= today:
            if not task_active_on_date(task, check):
                check += timedelta(days=1)
                continue
                
            date_str = check.isoformat()
            is_done = completed_lookup.get((task["id"], date_str), False)
            
            if is_done:
                current_iter_streak += 1
                if current_iter_streak > longest_streak:
                    longest_streak = current_iter_streak
            else:
                if check != today:
                    current_iter_streak = 0
                    
            check += timedelta(days=1)
            
        streaks[task["id"]] = {
            "current_streak": current_iter_streak,
            "longest_streak": longest_streak
        }
        
    return streaks


def compute_task_streaks(db: sqlite3.Connection) -> dict[int, int]:
    """Backwards compatibility for Phase 1 endpoints"""
    all_streaks = compute_all_streaks(db)
    return {tid: data["current_streak"] for tid, data in all_streaks.items()}
