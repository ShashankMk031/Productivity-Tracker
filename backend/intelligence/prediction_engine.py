import sqlite3
from datetime import datetime
from typing import Dict, Any

from .burnout_detector import detect_burnout
from .consistency_predictor import predict_consistency
from .deadline_forecaster import forecast_deadlines
from .focus_analyzer import analyze_focus




def _historical_accuracy(db: sqlite3.Connection, predictor_type: str) -> tuple[float | None, int]:
    try:
        rows = db.execute(
            """
            SELECT accuracy_score
            FROM prediction_records
            WHERE predictor_type = ? AND accuracy_score IS NOT NULL
            ORDER BY evaluated_at DESC
            LIMIT 24
            """,
            (predictor_type,),
        ).fetchall()
    except sqlite3.OperationalError:
        return None, 0
    if not rows:
        return None, 0
    values = [float(row["accuracy_score"]) for row in rows]
    return (sum(values) / len(values)) * 100, len(values)


def _calibrate_confidence(
    db: sqlite3.Connection,
    predictor_type: str,
    base_confidence: int,
    sample_size: int,
    data_completeness: float,
) -> int:
    history_accuracy, history_samples = _historical_accuracy(db, predictor_type)
    parts = [
        (base_confidence, 0.45),
        (min(sample_size, 21) / 21 * 100, 0.25),
        (max(0.0, min(data_completeness, 1.0)) * 100, 0.15),
    ]
    if history_accuracy is not None and history_samples > 0:
        parts.append((history_accuracy, min(0.30, 0.05 * history_samples)))
    total_weight = sum(weight for _, weight in parts)
    score = sum(value * weight for value, weight in parts) / total_weight
    return max(20, min(96, int(round(score))))


def _apply_calibration(db: sqlite3.Connection, predictor_type: str, item: dict) -> dict:
    metrics = item.setdefault("supporting_metrics", {})
    sample_size = int(metrics.get("sample_size", 0) or 0)
    data_completeness = float(metrics.get("data_completeness", 0) or 0)
    item["confidence"] = _calibrate_confidence(
        db,
        predictor_type,
        int(item.get("confidence", 50) or 50),
        sample_size,
        data_completeness,
    )
    metrics["confidence_basis"] = {
        "historical_accuracy_used": _historical_accuracy(db, predictor_type)[0] is not None,
        "sample_size": sample_size,
        "data_completeness": data_completeness,
    }
    return item


def generate_intelligence_snapshot(db: sqlite3.Connection) -> Dict[str, Any]:
    burnout = _apply_calibration(db, "burnout", detect_burnout(db))
    consistency = predict_consistency(db)
    deadlines = forecast_deadlines(db)
    focus = _apply_calibration(db, "focus", analyze_focus(db))
    
    # Also forecast Goals
    goals = forecast_goals(db)
    habits = [_apply_calibration(db, "consistency", item) for item in consistency["habits"]]
    deadline_rows = [_apply_calibration(db, "deadline", item) for item in deadlines["deadlines"]]
    goal_rows = [_apply_calibration(db, "goal", item) for item in goals["goals"]]
    
    return {
        "generated_at": datetime.now().isoformat(),
        "prediction_version": "v2",
        "burnout": burnout,
        "habits": habits,
        "deadlines": deadline_rows,
        "goals": goal_rows,
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
            "goal_id": g["id"],
            "goal_title": g["title"],
            "risk_level": risk,
            "warning_level": warning,
            "reason": reason,
            "supporting_metrics": {
                "progress_per_week": f"{progress_per_week:.1f}% per week",
                "estimated_days_left": int(estimated_days_left),
                "progress_pct": progress_pct,
                "days_elapsed": days_elapsed,
                "days_remaining": days_remaining,
                "sample_size": max(days_elapsed, 1),
                "data_completeness": 1.0 if g["target_date"] else 0.7,
            },
            "confidence": min(85, 40 + days_elapsed * 2)
        })
        
    return {"goals": forecasts}
