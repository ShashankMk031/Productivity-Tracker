import sqlite3
import statistics

def analyze_focus(db: sqlite3.Connection) -> dict:
    # We want to find the optimal focus duration based on 'completed tasks' correlation
    # For a simple heuristic: we group focus sessions into buckets (0-30, 30-50, 50-70, 70-90, 90+)
    # and we look at the daily_entries completed on the same day.
    
    sessions = db.execute("SELECT start_time, duration FROM focus_sessions WHERE duration > 0").fetchall()
    
    if not sessions:
        return {
            "best_focus_range": "Unknown",
            "task_completion_rate": "N/A",
            "reason": "Not enough focus session data to determine optimum.",
            "supporting_metrics": {},
            "confidence": 0
        }
        
    buckets = {
        "Short (< 30m)": {"sessions": 0, "tasks_completed": 0, "tasks_total": 0},
        "Medium (30-50m)": {"sessions": 0, "tasks_completed": 0, "tasks_total": 0},
        "Optimal (50-70m)": {"sessions": 0, "tasks_completed": 0, "tasks_total": 0},
        "Long (70-90m)": {"sessions": 0, "tasks_completed": 0, "tasks_total": 0},
        "Marathon (> 90m)": {"sessions": 0, "tasks_completed": 0, "tasks_total": 0}
    }
    
    # Pre-fetch all daily entries grouped by date
    daily_stats = {}
    rows = db.execute("SELECT date, completed FROM daily_entries").fetchall()
    for r in rows:
        d = r["date"]
        if d not in daily_stats:
            daily_stats[d] = {"comp": 0, "total": 0}
        daily_stats[d]["total"] += 1
        if r["completed"]:
            daily_stats[d]["comp"] += 1
            
    for s in sessions:
        dur = s["duration"] / 60.0 # minutes
        date_str = s["start_time"][:10]
        
        if dur < 30: b = "Short (< 30m)"
        elif dur <= 50: b = "Medium (30-50m)"
        elif dur <= 70: b = "Optimal (50-70m)"
        elif dur <= 90: b = "Long (70-90m)"
        else: b = "Marathon (> 90m)"
        
        buckets[b]["sessions"] += 1
        if date_str in daily_stats:
            buckets[b]["tasks_completed"] += daily_stats[date_str]["comp"]
            buckets[b]["tasks_total"] += daily_stats[date_str]["total"]

    best_bucket = None
    best_rate = -1
    
    for b_name, data in buckets.items():
        if data["tasks_total"] > 0:
            rate = data["tasks_completed"] / data["tasks_total"]
            # Weight by number of sessions to avoid tiny sample bias
            weighted_rate = rate * min(1.0, data["sessions"] / 5.0)
            if weighted_rate > best_rate and data["sessions"] >= 2:
                best_rate = weighted_rate
                best_bucket = b_name
                best_actual_rate = rate

    if best_bucket:
        return {
            "best_focus_range": best_bucket,
            "task_completion_rate": f"{int(best_actual_rate * 100)}%",
            "reason": f"Days with {best_bucket} sessions show the highest task completion correlation.",
            "supporting_metrics": {
                "sessions_in_best_range": buckets[best_bucket]["sessions"]
            },
            "confidence": min(85, sum(b["sessions"] for b in buckets.values()) * 5)
        }
    else:
        # Default fallback
        return {
            "best_focus_range": "Medium (30-50m)",
            "task_completion_rate": "N/A",
            "reason": "Insufficient correlation data. Suggesting standard Pomodoro.",
            "supporting_metrics": {},
            "confidence": 30
        }
