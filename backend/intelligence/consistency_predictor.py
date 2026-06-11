import sqlite3
from datetime import datetime, timedelta

def predict_consistency(db: sqlite3.Connection) -> dict:
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    # Get all active tasks
    tasks = db.execute("SELECT id, title FROM tasks WHERE completed_forever = 0").fetchall()
    
    habit_trends = []
    
    for task in tasks:
        # Fetch last 30 days of entries
        entries = db.execute(
            "SELECT date, completed FROM daily_entries WHERE task_id = ? AND date <= ? ORDER BY date DESC LIMIT 30",
            (task["id"], today_str)
        ).fetchall()
        
        if not entries:
            continue
            
        # Split into last 14 and prev 14 for trend
        last_14 = [e for e in entries if e["date"] >= (now - timedelta(days=14)).strftime("%Y-%m-%d")]
        prev_14 = [e for e in entries if e["date"] >= (now - timedelta(days=28)).strftime("%Y-%m-%d") and e["date"] < (now - timedelta(days=14)).strftime("%Y-%m-%d")]
        
        comp_last_14 = sum(1 for e in last_14 if e["completed"])
        comp_prev_14 = sum(1 for e in prev_14 if e["completed"])
        
        # Calculate current streak
        streak = 0
        for e in entries:
            if e["completed"]:
                streak += 1
            else:
                break
                
        # Determine trend
        trend = "Stable"
        reason = "Consistent completion rate."
        risk = "LOW"
        warning = "INFO"
        
        if comp_last_14 > comp_prev_14 + 2:
            trend = "Improving"
            reason = f"Completed {comp_last_14} times recently, up from {comp_prev_14}."
            risk = "LOW"
        elif comp_last_14 < comp_prev_14 - 2:
            trend = "Declining"
            reason = f"Completed only {comp_last_14} times recently, down from {comp_prev_14}."
            risk = "MEDIUM"
            warning = "WATCH"
            if comp_last_14 == 0 and comp_prev_14 > 0:
                risk = "HIGH"
                warning = "WARNING"
                
        # Likely streak break?
        if streak > 0 and streak % 7 == 0 and trend != "Improving":
            # Just a heuristic: long streaks without improving momentum might be at risk
            risk = "MEDIUM" if risk == "LOW" else risk
            warning = "WATCH"
            reason += f" Streak is at {streak}, statistically vulnerable to breakage without high momentum."

        habit_trends.append({
            "task_title": task["title"],
            "trend": trend,
            "risk_level": risk,
            "warning_level": warning,
            "reason": reason,
            "supporting_metrics": {
                "current_streak": streak,
                "completions_last_14d": comp_last_14,
                "completions_prev_14d": comp_prev_14
            },
            "confidence": 80 if len(entries) >= 14 else 50
        })
        
    return {"habits": habit_trends}
