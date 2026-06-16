import sqlite3
import zipfile
from pathlib import Path

import services.backup_service as backup_service


def test_create_backup_contains_database(workspace, db):
    db.execute("INSERT INTO goals (title, category) VALUES ('Keep me', 'General')")
    db.commit()
    path = backup_service.create_backup("manual")
    archive = Path(path)
    assert archive.exists()
    with zipfile.ZipFile(archive) as zf:
        assert "database/tracker.db" in zf.namelist()


def test_restore_roundtrip_and_safety_copy(workspace, db):
    db.execute("INSERT INTO goals (title, category) VALUES ('Keep me', 'General')")
    db.commit()
    archive = Path(backup_service.create_backup("manual"))

    db.execute("INSERT INTO goals (title, category) VALUES ('Added after backup', 'General')")
    db.commit()
    db.close()

    relative = str(archive.relative_to(workspace / "backups"))
    result = backup_service.restore_from_backup(relative)
    assert result["success"], result["message"]

    conn = sqlite3.connect(workspace / "database" / "tracker.db")
    try:
        titles = {row[0] for row in conn.execute("SELECT title FROM goals")}
    finally:
        conn.close()
    assert "Keep me" in titles
    assert "Added after backup" not in titles

    # The pre-restore safety copy must be preserved
    assert result["safety_backup"] is not None
    assert Path(result["safety_backup"]).exists()


def test_restore_rejects_path_traversal(workspace):
    result = backup_service.restore_from_backup("../outside.zip")
    assert result["success"] is False


def test_restore_rejects_missing_file(workspace):
    result = backup_service.restore_from_backup("does_not_exist.zip")
    assert result["success"] is False


def test_restore_rejects_corrupt_zip(workspace):
    backups_dir = workspace / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    (backups_dir / "bad.zip").write_bytes(b"this is not a zip archive")
    result = backup_service.restore_from_backup("bad.zip")
    assert result["success"] is False


def test_restore_rejects_archive_without_database(workspace):
    backups_dir = workspace / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    target = backups_dir / "nodb.zip"
    with zipfile.ZipFile(target, "w") as zf:
        zf.writestr("reports/something.md", "hello")
    result = backup_service.restore_from_backup("nodb.zip")
    assert result["success"] is False


def test_get_available_backups_sorted_newest_first(workspace, db):
    import time
    backup_service.create_backup("manual")
    time.sleep(1.1)
    backup_service.create_backup("manual")
    backups = backup_service.get_available_backups()
    assert len(backups) >= 2
    created = [b["created_at"] for b in backups]
    assert created == sorted(created, reverse=True)
