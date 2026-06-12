import os
import json
from datetime import datetime
from pathlib import Path
import sqlite3

from .prediction_engine import generate_intelligence_snapshot
from services.date_service import get_logical_date_ist

BASE_DIR = Path(__file__).parent.parent.parent
SNAPSHOT_DIR = BASE_DIR / "intelligence_snapshots"

def save_snapshot(db: sqlite3.Connection, report_period: str = "manual"):
    snapshot = generate_intelligence_snapshot(db)
    snapshot["report_period"] = report_period
    
    logical_date = get_logical_date_ist()
    year = logical_date.strftime("%Y")
    month = logical_date.strftime("%B") # e.g. June
    
    # Calculate week of month roughly
    day_of_month = logical_date.day
    week_num = (day_of_month - 1) // 7 + 1
    
    target_dir = SNAPSHOT_DIR / year / month
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Bug fix: the timestamp must come from a real datetime. Previously this
    # called strftime("%H%M%S") on the logical *date*, which always rendered
    # 000000 and made same-day snapshots of the same type overwrite each
    # other, silently truncating prediction history.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if "weekly" in report_period:
        filename = f"week_{week_num}_forecast_{timestamp}.json"
    elif "monthly" in report_period:
        filename = f"month_forecast_{timestamp}.json"
    else:
        filename = f"manual_forecast_{timestamp}.json"
        
    file_path = target_dir / filename
    
    with open(file_path, "w") as f:
        json.dump(snapshot, f, indent=2)
        
    return file_path
    
def get_latest_snapshot(db: sqlite3.Connection):
    # This generates it live for the dashboard, but doesn't necessarily save it to disk
    return generate_intelligence_snapshot(db)
