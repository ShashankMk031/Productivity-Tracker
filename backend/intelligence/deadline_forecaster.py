import sqlite3
from datetime import datetime

def forecast_deadlines(db: sqlite3.Connection) -> dict:
    now = datetime.now()
    
    projects = db.execute("SELECT * FROM projects WHERE completed = 0").fetchall()
    
    forecasts = []
    
    for p in projects:
        try:
            created_date = datetime.fromisoformat(p["created_at"])
            deadline_date = datetime.fromisoformat(p["deadline"])
        except ValueError:
            continue
            
        days_elapsed = (now - created_date).days
        days_remaining = (deadline_date - now).days
        
        milestones = db.execute("SELECT * FROM project_milestones WHERE project_id = ?", (p["id"],)).fetchall()
        
        total_milestones = len(milestones)
        completed_milestones = sum(1 for m in milestones if m["completed"])
        
        progress_pct = p["progress"]
        
        if total_milestones > 0:
            remaining_milestones = total_milestones - completed_milestones
            if days_elapsed > 0:
                milestones_per_day = completed_milestones / days_elapsed
            else:
                milestones_per_day = completed_milestones
                
            milestones_per_week = milestones_per_day * 7
            
            if milestones_per_day > 0:
                estimated_days_left = remaining_milestones / milestones_per_day
            else:
                estimated_days_left = remaining_milestones * 3 # rough guess if 0 velocity
                
        else:
            # Fallback to pure percentage
            remaining_pct = 100 - progress_pct
            if days_elapsed > 0:
                pct_per_day = progress_pct / days_elapsed
            else:
                pct_per_day = progress_pct
                
            progress_per_week = pct_per_day * 7
                
            if pct_per_day > 0:
                estimated_days_left = remaining_pct / pct_per_day
            else:
                estimated_days_left = remaining_pct * 0.5 # rough guess
                
        # Determine risk
        risk = "LOW"
        warning = "INFO"
        reason = "On track to complete before deadline."
        
        if days_remaining < 0:
            risk = "HIGH"
            warning = "CRITICAL"
            reason = "Deadline has already passed."
            confidence = 99
        elif estimated_days_left > days_remaining:
            if estimated_days_left > days_remaining * 1.5:
                risk = "HIGH"
                warning = "CRITICAL"
                reason = f"Current velocity is too slow. Estimated completion is {int(estimated_days_left - days_remaining)} days late."
            else:
                risk = "MEDIUM"
                warning = "WARNING"
                reason = "Pace is slightly behind schedule. Needs acceleration."
            confidence = min(90, 50 + days_elapsed * 2) # More confident if project has been running longer
        else:
            confidence = min(85, 40 + days_elapsed * 2)
            
        if total_milestones > 0:
            velocity_metric = f"{milestones_per_week:.1f} milestones/week"
        else:
            velocity_metric = f"{progress_per_week:.1f}% per week"

        forecasts.append({
            "project_id": p["id"],
            "project_title": p["title"],
            "risk_level": risk,
            "warning_level": warning,
            "reason": reason,
            "supporting_metrics": {
                "days_remaining": days_remaining,
                "velocity": velocity_metric,
                "progress": f"{progress_pct}%",
                "progress_pct": progress_pct,
                "total_milestones": total_milestones,
                "completed_milestones": completed_milestones,
                "sample_size": max(days_elapsed, 1),
                "data_completeness": 1.0 if p["deadline"] else 0.6,
            },
            "confidence": int(confidence)
        })
        
    return {"deadlines": forecasts}
