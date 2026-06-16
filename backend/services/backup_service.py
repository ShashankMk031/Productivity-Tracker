import os
import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from .logging_service import log_critical, log_error
from config import BASE_DIR, BACKUPS_DIR

DIRECTORIES_TO_BACKUP = [
    "database",
    "reports",
    "ai_reports",
    "ai_context",
    "intelligence_snapshots",
    "logs"
]

DB_FILENAME = "tracker.db"


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

    # Copy data to a temp directory first, then archive it, to avoid
    # zipping files while they change underneath us.
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

        archive_path = shutil.make_archive(
            base_name=str(zip_path_base),
            format="zip",
            root_dir=str(temp_path)
        )

    return archive_path


def get_available_backups() -> list:
    ensure_backups_dir()
    backups = []

    for root, _, files in os.walk(BACKUPS_DIR):
        for file in files:
            if file.endswith(".zip"):
                full_path = Path(root) / file
                size_mb = full_path.stat().st_size / (1024 * 1024)

                rel_path = full_path.relative_to(BACKUPS_DIR)
                parts = rel_path.parts

                backups.append({
                    "filename": file,
                    "path": str(full_path),
                    "relative_path": str(rel_path),
                    "size_mb": round(size_mb, 2),
                    "year": parts[0] if len(parts) > 1 else "Unknown",
                    "month": parts[1] if len(parts) > 2 else "Unknown",
                    "created_at": datetime.fromtimestamp(full_path.stat().st_ctime).isoformat()
                })

    backups.sort(key=lambda x: x["created_at"], reverse=True)
    return backups


def _resolve_managed_backup(filename: str):
    """
    Resolve a backup identifier (a filename or a path relative to the backups
    directory) to a zip file inside BACKUPS_DIR.

    Returns None when the file does not exist, is not a zip, or the path
    escapes the managed backups directory. This intentionally removes the
    previous behavior of restoring from arbitrary filesystem paths.
    """
    ensure_backups_dir()
    try:
        candidate = (BACKUPS_DIR / filename).resolve()
        candidate.relative_to(BACKUPS_DIR.resolve())
    except (ValueError, OSError):
        return None
    if not candidate.is_file() or candidate.suffix != ".zip":
        return None
    return candidate


def validate_backup_archive(zip_path: Path) -> tuple:
    """Validate a backup archive before any restore step touches live data."""
    if not zipfile.is_zipfile(zip_path):
        return False, "File is not a valid zip archive."
    try:
        with zipfile.ZipFile(zip_path) as zf:
            corrupt_member = zf.testzip()
            if corrupt_member is not None:
                return False, f"Archive is corrupt (first bad member: {corrupt_member})."
            names = zf.namelist()
    except (zipfile.BadZipFile, OSError) as e:
        return False, f"Could not read archive: {e}"

    allowed_roots = set(DIRECTORIES_TO_BACKUP)
    has_database = False
    for name in names:
        parts = Path(name).parts
        if not parts:
            continue
        if Path(name).is_absolute() or ".." in parts:
            return False, f"Archive contains an unsafe member path: {name}"
        if parts[0] not in allowed_roots:
            return False, f"Archive contains an unexpected top-level entry: {parts[0]}"
        if parts[0] == "database":
            has_database = True

    if not has_database:
        return False, "Archive does not contain a database directory."
    return True, "ok"


def verify_database_integrity(db_file: Path) -> tuple:
    """Open the restored database read-only and run PRAGMA integrity_check."""
    if not db_file.exists():
        return False, f"Restored archive is missing database/{DB_FILENAME}."
    try:
        conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
        try:
            row = conn.execute("PRAGMA integrity_check").fetchone()
        finally:
            conn.close()
    except sqlite3.Error as e:
        return False, f"Restored database cannot be opened: {e}"
    if not row or row[0] != "ok":
        return False, f"Restored database failed integrity check: {row[0] if row else 'no result'}"
    return True, "ok"


def restore_from_backup(filename: str) -> dict:
    """
    Safely restore the system from a managed backup.

    Sequence (replaces the old delete-then-copy implementation, which could
    destroy live data when a restore failed midway):
      1. Back up the current state (safety copy, kept afterwards).
      2. Validate the archive (zip integrity, member safety, expected layout).
      3. Extract to a temporary staging location.
      4. Verify the restored database (PRAGMA integrity_check).
      5. Atomically swap each data directory into place; on failure, roll
         back to the original directories.
      6. Preserve the displaced directories alongside the safety backup.
    """
    archive = _resolve_managed_backup(filename)
    if archive is None:
        msg = "Restore is only allowed from managed backups inside the backups directory."
        log_error("Restore", f"{msg} Requested: {filename}")
        return {"success": False, "message": msg, "safety_backup": None}

    # 1. Safety copy of the current state
    try:
        safety_backup = create_backup("pre_restore")
    except Exception as e:
        msg = f"Could not create a pre-restore safety backup, aborting restore: {e}"
        log_critical("Restore", msg)
        return {"success": False, "message": msg, "safety_backup": None}

    # 2. Validate the archive
    valid, reason = validate_backup_archive(archive)
    if not valid:
        log_error("Restore", f"Archive validation failed for {archive.name}: {reason}")
        return {"success": False, "message": f"Archive validation failed: {reason}", "safety_backup": safety_backup}

    staging = Path(tempfile.mkdtemp(prefix=".restore_staging_", dir=BACKUPS_DIR))
    try:
        # 3. Extract to staging
        try:
            shutil.unpack_archive(str(archive), str(staging), format="zip")
        except (shutil.ReadError, OSError) as e:
            msg = f"Failed to extract archive: {e}"
            log_error("Restore", msg)
            return {"success": False, "message": msg, "safety_backup": safety_backup}

        # 4. Verify restored database integrity
        ok, reason = verify_database_integrity(staging / "database" / DB_FILENAME)
        if not ok:
            log_error("Restore", f"Integrity verification failed for {archive.name}: {reason}")
            return {"success": False, "message": f"Integrity verification failed: {reason}", "safety_backup": safety_backup}

        # 5. Atomic swap with rollback
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        aside_dir = BACKUPS_DIR / f"pre_restore_{timestamp}"
        aside_dir.mkdir(parents=True, exist_ok=True)

        moved_aside = []
        placed = []
        try:
            for d in DIRECTORIES_TO_BACKUP:
                restored = staging / d
                if not restored.exists():
                    continue
                current = BASE_DIR / d
                if current.exists():
                    shutil.move(str(current), str(aside_dir / d))
                    moved_aside.append(d)
                shutil.move(str(restored), str(current))
                placed.append(d)
        except Exception as e:
            # Roll back: remove partially placed dirs, then put originals back
            for d in placed:
                shutil.rmtree(BASE_DIR / d, ignore_errors=True)
            for d in moved_aside:
                original = aside_dir / d
                if original.exists() and not (BASE_DIR / d).exists():
                    shutil.move(str(original), str(BASE_DIR / d))
            msg = f"Restore failed during swap and was rolled back: {e}"
            log_critical("Restore", msg)
            return {"success": False, "message": msg, "safety_backup": safety_backup}

        # 6. Safety copies are preserved (pre-restore zip + displaced dirs)
        msg = (
            f"System restored from {archive.name}. "
            f"Pre-restore safety backup: {Path(safety_backup).name}; "
            f"previous data preserved in backups/{aside_dir.name}."
        )
        return {"success": True, "message": msg, "safety_backup": safety_backup}
    finally:
        shutil.rmtree(staging, ignore_errors=True)
