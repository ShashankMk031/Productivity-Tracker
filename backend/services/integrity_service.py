import sqlite3
import os
from pathlib import Path
from .logging_service import log_critical, log_error

BASE_DIR = Path(__file__).parent.parent.parent

CRITICAL_DIRS = [
    "reports",
    "ai_reports",
    "ai_context",
    "intelligence_snapshots",
    "backups",
    "logs",
    "database"
]

def run_integrity_check(db: sqlite3.Connection):
    issues_found = 0
    details = []
    
    # 1. Self-heal directories
    for d in CRITICAL_DIRS:
        dir_path = BASE_DIR / d
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"[Self-Healing] Created missing directory: {d}")
                details.append(f"Fixed: Recreated missing directory '{d}'")
            except Exception as e:
                log_critical("Integrity", f"Failed to create critical directory '{d}': {e}")
                issues_found += 1
                details.append(f"Error: Failed to create critical directory '{d}'")
                
    # 2. Check Database Orphans
    # Orphan milestones (project_id doesn't exist)
    orphans = db.execute("""
        SELECT m.id, m.title 
        FROM project_milestones m 
        LEFT JOIN projects p ON m.project_id = p.id 
        WHERE p.id IS NULL
    """).fetchall()
    
    if orphans:
        issues_found += len(orphans)
        for o in orphans:
            log_critical("Integrity (DB)", f"Orphan milestone found: ID {o['id']} ('{o['title']}')")
            details.append(f"Orphan Milestone: ID {o['id']} ('{o['title']}') - Project missing")
            # Auto-cleanup optionally: db.execute("DELETE FROM project_milestones WHERE id = ?", (o["id"],))

    # 3. Check Report Files Mismatches
    reports = db.execute("SELECT id, markdown_path FROM reports WHERE markdown_path IS NOT NULL").fetchall()
    for r in reports:
        if not os.path.exists(r["markdown_path"]):
            issues_found += 1
            log_critical("Integrity (FS)", f"Report record {r['id']} points to missing file: {r['markdown_path']}")
            details.append(f"Missing File: Report {r['id']} markdown file does not exist on disk")
            
    return {
        "status": "Healthy" if issues_found == 0 else "Degraded",
        "issues_found": issues_found,
        "details": details
    }
