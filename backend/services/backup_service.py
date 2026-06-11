import os
import shutil
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime
from .logging_service import log_critical, log_error

BASE_DIR = Path(__file__).parent.parent.parent
BACKUPS_DIR = BASE_DIR / "backups"

DIRECTORIES_TO_BACKUP = [
    "database",
    "reports",
    "ai_reports",
    "ai_context",
    "intelligence_snapshots",
    "logs"
]

def ensure_backups_dir():
    if not BACKUPS_DIR.exists():
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

def create_backup(trigger: str = "manual") -> str:
    """
    Creates a zip archive of all critical data directories.
    Saves to /backups/YYYY/Month/backup_YYYYMMDD_HHMMSS_{trigger}.zip
    Returns the path to the zip file.
    """
    ensure_backups_dir()
    
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%B")
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    target_dir = BACKUPS_DIR / year / month
    target_dir.mkdir(parents=True, exist_ok=True)
    
    zip_filename = f"backup_{timestamp}_{trigger}"
    zip_path_base = target_dir / zip_filename
    
    # We need to copy files to a temp directory first to avoid locking issues, 
    # but for simplicity and since sqlite can be copied while running (though might have slight inconsistency),
    # we will just zip the directories directly.
    # To be safer, we create a temp folder, copy dirs there, then zip.
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        for d in DIRECTORIES_TO_BACKUP:
            src = BASE_DIR / d
            if src.exists():
                dst = temp_path / d
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                    
        # Now create the archive
        archive_path = shutil.make_archive(
            base_name=str(zip_path_base),
            format="zip",
            root_dir=str(temp_path)
        )
        
    return archive_path

def get_available_backups() -> list:
    ensure_backups_dir()
    backups = []
    
    for root, dirs, files in os.walk(BACKUPS_DIR):
        for file in files:
            if file.endswith(".zip"):
                full_path = Path(root) / file
                size_mb = full_path.stat().st_size / (1024 * 1024)
                
                # Extract year/month from path if possible
                rel_path = full_path.relative_to(BACKUPS_DIR)
                parts = rel_path.parts
                
                backups.append({
                    "filename": file,
                    "path": str(full_path),
                    "size_mb": round(size_mb, 2),
                    "year": parts[0] if len(parts) > 1 else "Unknown",
                    "month": parts[1] if len(parts) > 2 else "Unknown",
                    "created_at": datetime.fromtimestamp(full_path.stat().st_ctime).isoformat()
                })
                
    # Sort newest first
    backups.sort(key=lambda x: x["created_at"], reverse=True)
    return backups

def restore_from_backup(zip_path: str) -> bool:
    """
    Restores the system from a given zip file.
    Warning: This replaces current data!
    """
    path = Path(zip_path)
    if not path.exists():
        log_error("Restore", f"Backup file not found: {zip_path}")
        return False
        
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            shutil.unpack_archive(str(path), temp_dir, format="zip")
            
            # For each restored directory, replace the current one
            for d in DIRECTORIES_TO_BACKUP:
                restored_dir = Path(temp_dir) / d
                current_dir = BASE_DIR / d
                
                if restored_dir.exists():
                    if current_dir.exists():
                        shutil.rmtree(current_dir)
                    shutil.copytree(restored_dir, current_dir)
                    
        return True
    except Exception as e:
        log_critical("Restore", f"Failed to restore backup from {zip_path}: {e}")
        return False
