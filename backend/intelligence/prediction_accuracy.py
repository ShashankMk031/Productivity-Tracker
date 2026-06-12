import json
from datetime import datetime, timedelta
import sqlite3

from services.date_service import get_logical_date_ist
from config import SNAPSHOT_DIR

def evaluate_prediction_accuracy(db: sqlite3.Connection) -> dict:
    # 1. Find the snapshot from approximately 1 week ago
    now = get_logical_date_ist()
    one_week_ago = now - timedelta(days=7)
    
    year_str = one_week_ago.strftime("%Y")
    month_str = one_week_ago.strftime("%B")
    target_dir = SNAPSHOT_DIR / year_str / month_str
    
    if not target_dir.exists():
        return {"status": "No historical snapshots to evaluate"}
        
    snapshots = sorted(target_dir.glob("*.json"))
    if not snapshots:
        return {"status": "No historical snapshots to evaluate"}
        
    # Just take the most recent one in that month to evaluate
    latest_snapshot_path = snapshots[-1]
    
    with open(latest_snapshot_path, "r") as f:
        try:
            history = json.load(f)
        except json.JSONDecodeError:
            return {"status": "Failed to parse historical snapshot"}
            
    evaluations = []
    
    # Evaluate Deadlines
    for d in history.get("deadlines", []):
        proj_title = d["project_title"]
        predicted_risk = d["risk_level"]
        # Look up project current state
        proj = db.execute("SELECT * FROM projects WHERE title = ?", (proj_title,)).fetchone()
        if not proj: continue
        
        actual_outcome = "Unknown"
        accuracy = "Unknown"
        
        is_completed = proj["completed"] == 1
        deadline_date = datetime.fromisoformat(proj["deadline"]).date()
        
        if is_completed:
            if deadline_date >= now:
                actual_outcome = "Completed on time"
                if predicted_risk == "LOW": accuracy = "Correct prediction"
                else: accuracy = "False positive (was completed on time despite risk)"
            else:
                actual_outcome = "Completed late"
                if predicted_risk in ["HIGH", "MEDIUM"]: accuracy = "Correct prediction"
                else: accuracy = "False negative (missed risk)"
        else:
            if deadline_date < now:
                actual_outcome = "Deadline missed"
                if predicted_risk in ["HIGH", "MEDIUM"]: accuracy = "Correct prediction"
                else: accuracy = "False negative (missed risk)"
            else:
                actual_outcome = "Still pending"
                accuracy = "Pending evaluation"
                
        evaluations.append({
            "type": "Deadline",
            "target": proj_title,
            "prediction_date": history["generated_at"],
            "predicted": f"{predicted_risk} Risk",
            "actual_outcome": actual_outcome,
            "accuracy": accuracy
        })
        
    return {
        "evaluated_snapshot": latest_snapshot_path.name,
        "evaluations": evaluations
    }
