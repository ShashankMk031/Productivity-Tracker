import sqlite3
from datetime import datetime
from typing import Dict, Any

from .burnout_detector import detect_burnout
from .consistency_predictor import predict_consistency
from .deadline_forecaster import forecast_deadlines
from .focus_analyzer import analyze_focus

def generate_intelligence_snapshot(db: sqlite3.Connection) -> Dict[str, Any]:
    burnout = detect_burnout(db)
    consistency = predict_consistency(db)
    deadlines = forecast_deadlines(db)
    focus = analyze_focus(db)
    
    # Also forecast Goals
    goals = forecast_goals(db)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "prediction_version": "v1",
        "burnout": burnout,
        "habits": consistency["habits"],
        "deadlines": deadlines["deadlines"],
        "goals": goals["goals"],
        "focus": focus
    }

def forecast_goals(db: sqlite3.Connection) -> dict:
    now = datetime.now()
    goals = db.execute("SELECT * FROM goals WHERE completed = 0").fetchall()
    
    forecasts = []
    
    for g in goals:
        created_date = datetime.fromisoformat(g["created_at"])
        days_elapsed = (now - created_date).days
        progress_pct = g["progress"]
        
        target_date = None
        days_remaining = None
        if g["target_date"]:
            try:
                target_date = datetime.fromisoformat(g["target_date"])
                days_remaining = (target_date - now).days
            except ValueError:
                pass
                
        remaining_pct = 100 - progress_pct
        if days_elapsed > 0:
            pct_per_day = progress_pct / days_elapsed
        else:
            pct_per_day = progress_pct
            
        progress_per_week = pct_per_day * 7
        
        estimated_days_left = remaining_pct / pct_per_day if pct_per_day > 0 else remaining_pct * 0.5
        
        risk = "LOW"
        warning = "INFO"
        reason = "Making steady progress."
        
        if days_remaining is not None:
            if days_remaining < 0:
                risk = "HIGH"
                warning = "CRITICAL"
                reason = "Target date has passed."
            elif estimated_days_left > days_remaining * 1.5:
                risk = "HIGH"
                warning = "CRITICAL"
                reason = f"Velocity is too slow. Estimated completion is {int(estimated_days_left - days_remaining)} days late."
            elif estimated_days_left > days_remaining:
                risk = "MEDIUM"
                warning = "WARNING"
                reason = "Pace is slightly behind schedule."
        else:
            if pct_per_day == 0 and days_elapsed > 14:
                risk = "HIGH"
                warning = "WARNING"
                reason = "No progress made in over 2 weeks."
            elif pct_per_day < 0.5:
                risk = "MEDIUM"
                warning = "WATCH"
                reason = "Progress is very slow (< 3.5% per week)."
                
        forecasts.append({
            "goal_title": g["title"],
            "risk_level": risk,
            "warning_level": warning,
            "reason": reason,
            "supporting_metrics": {
                "progress_per_week": f"{progress_per_week:.1f}% per week",
                "estimated_days_left": int(estimated_days_left)
            },
            "confidence": min(85, 40 + days_elapsed * 2)
        })
        
    return {"goals": forecasts}
