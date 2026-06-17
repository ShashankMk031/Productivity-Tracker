import sqlite3
from typing import List, Dict, Optional
from datetime import datetime

def _serialize_sticky(row: sqlite3.Row) -> dict:
    d = dict(row)
    # Ensure booleans are returned as python booleans or 0/1 consistently
    d["is_completed"] = bool(d["is_completed"])
    d["is_draft"] = bool(d["is_draft"])
    d["is_archived"] = bool(d["is_archived"])
    # Return defaults for new fields in case database is in transition
    if "width" not in d:
        d["width"] = 240.0
    if "height" not in d:
        d["height"] = 200.0
    if "text_color" not in d:
        d["text_color"] = "#1e293b"
    if "rotation" not in d:
        d["rotation"] = 0.0
    return d

def ensure_draft_exists(db: sqlite3.Connection) -> None:
    """Ensures that exactly one active draft note exists in the database.
    Staggers the new draft horizontally to the right of the latest pinned note
    to prevent card overlap.
    """
    draft = db.execute(
        "SELECT id FROM sticky_notes WHERE is_draft = 1 AND is_archived = 0"
    ).fetchone()
    
    if not draft:
        # Find the latest pinned active note's position and width to offset the new draft
        latest = db.execute(
            """
            SELECT position_x, position_y, width 
            FROM sticky_notes 
            WHERE is_draft = 0 AND is_archived = 0 
            ORDER BY updated_at DESC LIMIT 1
            """
        ).fetchone()
        
        if latest:
            latest_w = latest["width"] if "width" in latest.keys() else 240.0
            new_x = latest["position_x"] + latest_w + 30.0
            new_y = latest["position_y"]
            
            # Wrap to the left of a new line if it exceeds canvas limits
            if new_x > 3000.0:
                new_x = 100.0
                new_y = latest["position_y"] + 240.0
        else:
            new_x = 100.0
            new_y = 100.0

        max_z = db.execute("SELECT MAX(z_index) FROM sticky_notes").fetchone()[0] or 0
        
        db.execute(
            """
            INSERT INTO sticky_notes (
                content, color, text_color, position_x, position_y, 
                width, height, z_index, is_completed, is_draft, 
                tag, is_archived, created_at, updated_at
            )
            VALUES ('', '#fef3c7', '#1e293b', ?, ?, 240.0, 135.0, ?, 0, 1, NULL, 0, datetime('now'), datetime('now'))
            """,
            (new_x, new_y, max_z + 1)
        )

def get_active_stickies(db: sqlite3.Connection, query: Optional[str] = None) -> List[dict]:
    """Retrieves all active (non-archived) sticky notes, ensuring a draft exists first."""
    ensure_draft_exists(db)
    
    if query:
        like_pattern = f"%{query}%"
        rows = db.execute(
            """
            SELECT * FROM sticky_notes 
            WHERE is_archived = 0 AND (content LIKE ? OR tag LIKE ?)
            ORDER BY z_index ASC
            """,
            (like_pattern, like_pattern)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM sticky_notes WHERE is_archived = 0 ORDER BY z_index ASC"
        ).fetchall()
        
    return [_serialize_sticky(row) for row in rows]

def get_sticky(db: sqlite3.Connection, sticky_id: int) -> Optional[dict]:
    row = db.execute("SELECT * FROM sticky_notes WHERE id = ?", (sticky_id,)).fetchone()
    return _serialize_sticky(row) if row else None

def create_sticky(
    db: sqlite3.Connection,
    content: str,
    color: str,
    text_color: str = "#1e293b",
    position_x: float = 100.0,
    position_y: float = 100.0,
    width: float = 240.0,
    height: float = 135.0,
    z_index: int = 1,
    is_draft: int = 0,
    tag: Optional[str] = None,
    rotation: float = 0.0
) -> dict:
    cur = db.execute(
        """
        INSERT INTO sticky_notes (
            content, color, text_color, position_x, position_y, 
            width, height, rotation, z_index, is_completed, is_draft, 
            tag, is_archived, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 0, datetime('now'), datetime('now'))
        """,
        (content, color, text_color, position_x, position_y, width, height, rotation, z_index, is_draft, tag)
    )
    sticky_id = cur.lastrowid
    return get_sticky(db, sticky_id)

def update_sticky(
    db: sqlite3.Connection,
    sticky_id: int,
    content: Optional[str] = None,
    color: Optional[str] = None,
    text_color: Optional[str] = None,
    position_x: Optional[float] = None,
    position_y: Optional[float] = None,
    width: Optional[float] = None,
    height: Optional[float] = None,
    z_index: Optional[int] = None,
    is_completed: Optional[int] = None,
    is_draft: Optional[int] = None,
    tag: Optional[str] = None,
    is_archived: Optional[int] = None,
    rotation: Optional[float] = None
) -> Optional[dict]:
    updates = []
    params = []
    
    if content is not None:
        updates.append("content = ?")
        params.append(content)
    if color is not None:
        updates.append("color = ?")
        params.append(color)
    if text_color is not None:
        updates.append("text_color = ?")
        params.append(text_color)
    if position_x is not None:
        updates.append("position_x = ?")
        params.append(position_x)
    if position_y is not None:
        updates.append("position_y = ?")
        params.append(position_y)
    if width is not None:
        updates.append("width = ?")
        params.append(width)
    if height is not None:
        updates.append("height = ?")
        params.append(height)
    if z_index is not None:
        updates.append("z_index = ?")
        params.append(z_index)
    if is_completed is not None:
        updates.append("is_completed = ?")
        params.append(is_completed)
    if is_draft is not None:
        updates.append("is_draft = ?")
        params.append(is_draft)
    if tag is not None:
        updates.append("tag = ?")
        params.append(tag if tag.strip() != "" else None)
    elif tag == "":
        updates.append("tag = NULL")
    if is_archived is not None:
        updates.append("is_archived = ?")
        params.append(is_archived)
    if rotation is not None:
        updates.append("rotation = ?")
        params.append(rotation)
        
    if not updates:
        return get_sticky(db, sticky_id)
        
    updates.append("updated_at = datetime('now')")
    query = f"UPDATE sticky_notes SET {', '.join(updates)} WHERE id = ?"
    params.append(sticky_id)
    
    db.execute(query, tuple(params))
    
    # If a draft note was updated to be a non-draft, ensure a new draft is spawned
    if is_draft == 0:
        ensure_draft_exists(db)
        
    return get_sticky(db, sticky_id)

def delete_sticky(db: sqlite3.Connection, sticky_id: int) -> bool:
    cur = db.execute("DELETE FROM sticky_notes WHERE id = ?", (sticky_id,))
    # If we deleted the active draft note, ensure a new one is spawned
    ensure_draft_exists(db)
    return cur.rowcount > 0

def archive_completed_stickies(db: sqlite3.Connection) -> int:
    cur = db.execute(
        "UPDATE sticky_notes SET is_archived = 1, updated_at = datetime('now') WHERE is_completed = 1 AND is_archived = 0"
    )
    return cur.rowcount

def delete_completed_stickies(db: sqlite3.Connection) -> int:
    cur = db.execute("DELETE FROM sticky_notes WHERE is_completed = 1")
    return cur.rowcount
