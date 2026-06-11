from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import sqlite3
import os
import shutil
from pathlib import Path

from database.db import get_db
from services.backup_service import create_backup, get_available_backups, restore_from_backup, BASE_DIR

router = APIRouter()

def get_dir_size(path: Path) -> float:
    total = 0
    if not path.exists():
        return 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = Path(root) / f
            total += fp.stat().st_size
    return total / (1024 * 1024)

@router.get("/health")
def get_health():
    with get_db() as db:
        goals_count = db.execute("SELECT COUNT(*) as c FROM goals").fetchone()["c"]
        projects_count = db.execute("SELECT COUNT(*) as c FROM projects").fetchone()["c"]
        entries_count = db.execute("SELECT COUNT(*) as c FROM daily_entries").fetchone()["c"]
        sessions_count = db.execute("SELECT COUNT(*) as c FROM focus_sessions").fetchone()["c"]
        reports_count = db.execute("SELECT COUNT(*) as c FROM reports").fetchone()["c"]
        
        return {
            "success": True,
            "data": {
                "database_records": {
                    "goals": goals_count,
                    "projects": projects_count,
                    "daily_entries": entries_count,
                    "focus_sessions": sessions_count,
                    "reports_generated": reports_count
                }
            }
        }

@router.get("/storage")
def get_storage():
    db_size = (BASE_DIR / "database" / "productivity.db").stat().st_size / (1024 * 1024) if (BASE_DIR / "database" / "productivity.db").exists() else 0
    
    sizes = {
        "database_mb": round(db_size, 2),
        "reports_mb": round(get_dir_size(BASE_DIR / "reports"), 2),
        "ai_reports_mb": round(get_dir_size(BASE_DIR / "ai_reports"), 2),
        "backups_mb": round(get_dir_size(BASE_DIR / "backups"), 2),
        "intelligence_snapshots_mb": round(get_dir_size(BASE_DIR / "intelligence_snapshots"), 2)
    }
    
    return {
        "success": True,
        "data": sizes
    }

@router.get("/backups")
def list_backups():
    backups = get_available_backups()
    return {
        "success": True,
        "data": backups
    }

@router.post("/backups/create")
def trigger_backup():
    try:
        path = create_backup("manual")
        return {"success": True, "message": f"Backup created successfully."}
    except Exception as e:
        raise HTTPException(500, f"Failed to create backup: {e}")

@router.post("/backups/restore")
def restore_backup(path: str):
    if restore_from_backup(path):
        return {"success": True, "message": "System restored successfully. Please restart the application."}
    else:
        raise HTTPException(500, "Failed to restore backup.")

@router.get("/export")
def export_data():
    path = create_backup("export")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/zip", filename=os.path.basename(path))
    raise HTTPException(500, "Failed to create export archive.")
