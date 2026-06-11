import sqlite3
from datetime import date, timedelta
from utils.helpers import parse_date, serialize_task, weekday_key
from services.date_service import get_logical_date_ist, task_active_on_date
from .streaks import compute_all_streaks

def get_global_metrics(db: sqlite3.Connection):
    today = get_logical_date_ist()
    task_rows = db.execute("SELECT * FROM tasks WHERE completed_forever = 0").fetchall()
    tasks = [serialize_task(row) for row in task_rows]
    
    empty_result = {
        "completion_pct": 0, "completed_days": 0, "missed_days": 0, 
        "active_tasks": 0, "current_streak": 0, "longest_streak": 0,
        "weekly_consistency": 0, "monthly_consistency": 0
    }
    
    if not tasks:
        return empty_result

    earliest_created = min(parse_date(task["created_at"]) for task in tasks)
    
    completed_rows = db.execute(
        "SELECT task_id, date, completed FROM daily_entries WHERE completed = 1 AND date >= ?",
        (earliest_created.isoformat(),)
    ).fetchall()
    
    completed_lookup = { (row["task_id"], row["date"]): True for row in completed_rows }
    
    total_slots = 0
    completed_slots = 0
    
    # For global streaks (perfect days)
    perfect_days_lookup = {}
    check = earliest_created
    while check <= today:
        date_str = check.isoformat()
        day_total = 0
        day_completed = 0
        for task in tasks:
            if task_active_on_date(task, check):
                day_total += 1
                if completed_lookup.get((task["id"], date_str)):
                    day_completed += 1
        
        if day_total > 0:
            total_slots += day_total
            completed_slots += day_completed
            if day_completed == day_total:
                perfect_days_lookup[date_str] = True
        
        check += timedelta(days=1)
        
    missed_slots = total_slots - completed_slots
    completion_pct = round((completed_slots / total_slots * 100), 1) if total_slots else 0
    
    # Global streaks
    current_global_streak = 0
    longest_global_streak = 0
    curr_streak = 0
    
    check = earliest_created
    while check <= today:
        date_str = check.isoformat()
        day_total = sum(1 for task in tasks if task_active_on_date(task, check))
        if day_total > 0:
            if perfect_days_lookup.get(date_str):
                curr_streak += 1
                if curr_streak > longest_global_streak:
                    longest_global_streak = curr_streak
            else:
                if check != today:
                    curr_streak = 0
        check += timedelta(days=1)
    
    current_global_streak = curr_streak
    
    # Consistency
    last_7_days = [today - timedelta(days=i) for i in range(7)]
    prev_7_days = [today - timedelta(days=i) for i in range(7, 14)]
    
    def get_period_completion(period_dates):
        t_slots = 0
        c_slots = 0
        for d in period_dates:
            date_str = d.isoformat()
            for task in tasks:
                if task_active_on_date(task, d):
                    t_slots += 1
                    if completed_lookup.get((task["id"], date_str)):
                        c_slots += 1
        return round((c_slots / t_slots * 100), 1) if t_slots else 0

    weekly_consistency = get_period_completion(last_7_days)
    prev_weekly_consistency = get_period_completion(prev_7_days)
    
    last_30_days = [today - timedelta(days=i) for i in range(30)]
    monthly_consistency = get_period_completion(last_30_days)
    
    return {
        "completion_pct": completion_pct,
        "completed_days": completed_slots,
        "missed_days": missed_slots,
        "active_tasks": len(tasks),
        "current_streak": current_global_streak,
        "longest_streak": longest_global_streak,
        "weekly_consistency": weekly_consistency,
        "prev_weekly_consistency": prev_weekly_consistency,
        "monthly_consistency": monthly_consistency
    }


def get_task_metrics(db: sqlite3.Connection):
    today = get_logical_date_ist()
    task_rows = db.execute("SELECT * FROM tasks WHERE completed_forever = 0").fetchall()
    tasks = [serialize_task(row) for row in task_rows]
    
    if not tasks:
        return []
        
    earliest_created = min(parse_date(task["created_at"]) for task in tasks)
    completed_rows = db.execute(
        "SELECT task_id, date, completed FROM daily_entries WHERE completed = 1 AND date >= ?",
        (earliest_created.isoformat(),)
    ).fetchall()
    
    completed_lookup = { (row["task_id"], row["date"]): True for row in completed_rows }
    streaks = compute_all_streaks(db)
    
    task_metrics = []
    
    last_7_days = [today - timedelta(days=i) for i in range(7)]
    
    for task in tasks:
        tid = task["id"]
        task_created = parse_date(task["created_at"])
        
        total = 0
        completed = 0
        check = task_created
        while check <= today:
            if task_active_on_date(task, check):
                total += 1
                if completed_lookup.get((tid, check.isoformat())):
                    completed += 1
            check += timedelta(days=1)
            
        pct = round((completed / total * 100), 1) if total else 0
        
        w_total = 0
        w_completed = 0
        for d in last_7_days:
            if d >= task_created and task_active_on_date(task, d):
                w_total += 1
                if completed_lookup.get((tid, d.isoformat())):
                    w_completed += 1
        w_pct = round((w_completed / w_total * 100), 1) if w_total else 0
        
        task_metrics.append({
            "id": tid,
            "title": task["title"],
            "completion_pct": pct,
            "completed_count": completed,
            "missed_count": total - completed,
            "current_streak": streaks.get(tid, {}).get("current_streak", 0),
            "longest_streak": streaks.get(tid, {}).get("longest_streak", 0),
            "weekly_trend": w_pct
        })
        
    return task_metrics

def get_behavioral_insights(db: sqlite3.Connection):
    today = get_logical_date_ist()
    task_rows = db.execute("SELECT * FROM tasks WHERE completed_forever = 0").fetchall()
    tasks = [serialize_task(row) for row in task_rows]
    
    if not tasks:
        return {}

    earliest_created = min(parse_date(task["created_at"]) for task in tasks)
    completed_rows = db.execute(
        "SELECT task_id, date, completed FROM daily_entries WHERE completed = 1 AND date >= ?",
        (earliest_created.isoformat(),)
    ).fetchall()
    
    completed_lookup = { (row["task_id"], row["date"]): True for row in completed_rows }
    
    weekday_counts = {day: {"total": 0, "completed": 0} for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
    
    for task in tasks:
        tid = task["id"]
        check = parse_date(task["created_at"])
        while check <= today:
            if task_active_on_date(task, check):
                wk = weekday_key(check)
                weekday_counts[wk]["total"] += 1
                if completed_lookup.get((tid, check.isoformat())):
                    weekday_counts[wk]["completed"] += 1
            check += timedelta(days=1)
            
    weekday_pcts = {}
    for wk, data in weekday_counts.items():
        if data["total"] > 0:
            weekday_pcts[wk] = data["completed"] / data["total"]
            
    most_productive_weekday = max(weekday_pcts, key=weekday_pcts.get) if weekday_pcts else "N/A"
    least_productive_weekday = min(weekday_pcts, key=weekday_pcts.get) if weekday_pcts else "N/A"
    
    task_metrics = get_task_metrics(db)
    if not task_metrics:
        return {}
        
    best_task = max(task_metrics, key=lambda x: x["completion_pct"])
    most_skipped = max(task_metrics, key=lambda x: x["missed_count"])
    
    return {
        "most_productive_weekday": most_productive_weekday,
        "least_productive_weekday": least_productive_weekday,
        "best_task": best_task["title"],
        "most_skipped_task": most_skipped["title"]
    }
