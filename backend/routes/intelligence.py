from fastapi import APIRouter
import sqlite3

from database.db import get_db
from intelligence.snapshot_service import get_latest_snapshot, save_snapshot
from intelligence.prediction_accuracy import evaluate_prediction_accuracy

router = APIRouter()

@router.get("/dashboard")
def get_intelligence_dashboard():
    with get_db() as db:
        snapshot = get_latest_snapshot(db)
        accuracy = evaluate_prediction_accuracy(db)
        
        return {
            "success": True,
            "data": {
                "snapshot": snapshot,
                "accuracy": accuracy
            }
        }

@router.post("/snapshot")
def force_snapshot():
    with get_db() as db:
        path = save_snapshot(db, "manual")
        return {
            "success": True,
            "message": f"Snapshot saved to {path}"
        }
