import sqlite3
from datetime import date, timedelta
from utils.helpers import parse_date, serialize_task
from services.date_service import get_logical_date_ist, task_active_on_date

def get_chart_data(db: sqlite3.Connection):
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
    
    # 1. Weekly Completion Chart (Last 7 Days)
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    weekly_completion = {
        "labels": [],
        "data": []
    }
    for d in last_7_days:
        date_str = d.isoformat()
        weekly_completion["labels"].append(d.strftime("%a")) # Mon, Tue...
        t_slots = 0
        c_slots = 0
        for task in tasks:
            if task_active_on_date(task, d):
                t_slots += 1
                if completed_lookup.get((task["id"], date_str)):
                    c_slots += 1
        pct = round((c_slots / t_slots * 100)) if t_slots else 0
        weekly_completion["data"].append(pct)
        
    # 2. Task Performance Chart (Bar chart comparing tasks)
    task_performance = {
        "labels": [],
        "data": []
    }
    
    for task in tasks:
        tid = task["id"]
        task_created = parse_date(task["created_at"])
        
        # Performance over last 30 days or since creation
        start_date = max(today - timedelta(days=30), task_created)
        
        t_slots = 0
        c_slots = 0
        check = start_date
        while check <= today:
            if task_active_on_date(task, check):
                t_slots += 1
                if completed_lookup.get((tid, check.isoformat())):
                    c_slots += 1
            check += timedelta(days=1)
            
        pct = round((c_slots / t_slots * 100)) if t_slots else 0
        task_performance["labels"].append(task["title"])
        task_performance["data"].append(pct)
        
    return {
        "weekly_completion": weekly_completion,
        "task_performance": task_performance
    }
