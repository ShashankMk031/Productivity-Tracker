import sqlite3
from fastapi import HTTPException
from schemas.goal_schemas import GoalCreate, GoalUpdate
from services.date_service import get_logical_date_ist

def _serialize_goal(row: sqlite3.Row) -> dict:
    return dict(row)

def get_all_goals(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute("SELECT * FROM goals ORDER BY completed ASC, target_date ASC").fetchall()
    return [_serialize_goal(row) for row in rows]

def get_goal(db: sqlite3.Connection, goal_id: int) -> dict:
    row = db.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Goal not found")
    return _serialize_goal(row)

def create_goal(db: sqlite3.Connection, data: GoalCreate) -> dict:
    title = data.title.strip()
    created_at = get_logical_date_ist().isoformat()
    
    cur = db.execute(
        """
        INSERT INTO goals (title, description, category, progress, target_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, data.description, data.category, data.progress or 0, data.target_date, created_at)
    )
    return get_goal(db, cur.lastrowid)

def update_goal(db: sqlite3.Connection, goal_id: int, data: GoalUpdate) -> dict:
    goal = get_goal(db, goal_id)
    
    title = data.title.strip() if data.title is not None else goal["title"]
    description = data.description if data.description is not None else goal["description"]
    category = data.category if data.category is not None else goal["category"]
    progress = data.progress if data.progress is not None else goal["progress"]
    target_date = data.target_date if data.target_date is not None else goal["target_date"]
    completed = data.completed if data.completed is not None else goal["completed"]

    db.execute(
        """
        UPDATE goals
        SET title = ?, description = ?, category = ?, progress = ?, target_date = ?, completed = ?
        WHERE id = ?
        """,
        (title, description, category, progress, target_date, completed, goal_id)
    )
    return get_goal(db, goal_id)

def delete_goal(db: sqlite3.Connection, goal_id: int):
    get_goal(db, goal_id)
    db.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
