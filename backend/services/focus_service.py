import sqlite3
from datetime import datetime

def start_focus_session(db: sqlite3.Connection, title: str) -> dict:
    # 1. Stop any currently active session first
    active = get_active_session(db)
    if active:
        stop_focus_session(db, "Auto-stopped due to new session starting")
        
    start_time = datetime.now().isoformat()
    cur = db.execute(
        "INSERT INTO focus_sessions (title, start_time, duration, notes) VALUES (?, ?, ?, ?)",
        (title, start_time, 0, "")
    )
    session_id = cur.lastrowid
    return {
        "id": session_id,
        "title": title,
        "start_time": start_time,
        "status": "started"
    }

def stop_focus_session(db: sqlite3.Connection, notes: str = "") -> dict:
    active = get_active_session(db)
    if not active:
        return {"status": "no_active_session"}
        
    end_time = datetime.now().isoformat()
    start_dt = datetime.fromisoformat(active["start_time"])
    end_dt = datetime.fromisoformat(end_time)
    
    duration = int((end_dt - start_dt).total_seconds())
    
    db.execute(
        "UPDATE focus_sessions SET end_time = ?, duration = ?, notes = ? WHERE id = ?",
        (end_time, duration, notes, active["id"])
    )
    
    return {
        "id": active["id"],
        "title": active["title"],
        "start_time": active["start_time"],
        "end_time": end_time,
        "duration": duration,
        "notes": notes,
        "status": "stopped"
    }

def get_active_session(db: sqlite3.Connection) -> dict:
    row = db.execute("SELECT * FROM focus_sessions WHERE end_time IS NULL LIMIT 1").fetchone()
    return dict(row) if row else None

def get_focus_history(db: sqlite3.Connection, limit: int = 50) -> list:
    rows = db.execute("SELECT * FROM focus_sessions ORDER BY start_time DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]
