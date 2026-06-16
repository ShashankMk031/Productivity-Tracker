from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path

from config import BASE_DIR, DB_PATH
from database.db import get_db
from services.backup_service import create_backup, get_available_backups, restore_from_backup
from services.integrity_service import run_integrity_check

router = APIRouter()

def get_dir_size(path: Path) -> float:
    total = 0
    if not path.exists():
        return 0
    for root, _, files in os.walk(path):
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
        
        integrity = run_integrity_check(db)
        backups = get_available_backups()
        
        return {
            "success": True,
            "data": {
                "database_records": {
                    "goals": goals_count,
                    "projects": projects_count,
                    "daily_entries": entries_count,
                    "focus_sessions": sessions_count,
                    "reports_generated": reports_count
                },
                "integrity": integrity,
                "backup_status": {
                    "total_backups": len(backups),
                    "last_backup": backups[0]["created_at"] if backups else "None"
                }
            }
        }

@router.get("/storage")
def get_storage():
    # Bug fix: this previously checked database/productivity.db (wrong
    # filename), so the reported DB size was always 0. Use the canonical
    # DB path instead.
    db_size = DB_PATH.stat().st_size / (1024 * 1024) if DB_PATH.exists() else 0
    
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
def restore_backup(filename: str):
    """
    Restore from a managed backup inside the backups directory.

    Behavior change (documented): the previous `path` parameter accepted any
    filesystem path and destroyed live data before copying. Restores are now
    restricted to managed backups, validated, verified, and atomically
    swapped with a pre-restore safety copy.
    """
    result = restore_from_backup(filename)
    if result["success"]:
        return {"success": True, "message": result["message"]}
    raise HTTPException(400, result["message"])

@router.get("/export")
def export_data():
    path = create_backup("export")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/zip", filename=os.path.basename(path))
    raise HTTPException(500, "Failed to create export archive.")


@router.get("/ai-health")
def get_ai_health():
    from ai.ai_service import AIService
    ai_service = AIService()
    health_status = {}
    for name, provider in ai_service.providers.items():
        if name == "static":
            continue
        try:
            health_status[name] = provider.check_health()
        except Exception:
            health_status[name] = "offline"
    
    # Include active provider and fallback order metadata for Settings UI
    return {
        "success": True,
        "data": {
            "statuses": health_status,
            "active_provider": ai_service.primary_provider,
            "fallback_order": ai_service.provider_order
        }
    }


@router.post("/ai-test")
def test_ai_provider(provider: str):
    from ai.ai_service import AIService
    ai_service = AIService()
    prov = ai_service.providers.get(provider.lower())
    if not prov:
        return {"success": False, "message": f"Unknown provider: {provider}"}
    
    if provider.lower() in ("gemini", "groq", "openrouter") and not prov.api_key:
        return {"success": False, "message": "Missing API Key"}
        
    try:
        res = prov.generate("Say 'connected'")
        if res:
            return {"success": True, "message": f"Successfully connected to {provider.upper()}! Response: {res.strip()}"}
        return {"success": False, "message": "Received empty response"}
    except Exception as e:
        return {"success": False, "message": str(e)}

