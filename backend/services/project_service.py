import sqlite3
from fastapi import HTTPException
from schemas.project_schemas import ProjectCreate, ProjectUpdate, MilestoneCreate, MilestoneUpdate
from services.date_service import get_logical_date_ist
from services.countdown_service import get_countdown_info

def _serialize_milestone(row: sqlite3.Row) -> dict:
    return dict(row)

def _serialize_project(db: sqlite3.Connection, row: sqlite3.Row) -> dict:
    proj = dict(row)
    milestone_rows = db.execute("SELECT * FROM project_milestones WHERE project_id = ? ORDER BY id ASC", (proj["id"],)).fetchall()
    proj["milestones"] = [_serialize_milestone(m) for m in milestone_rows]
    
    # Calculate progress automatically based on milestones
    if proj["milestones"]:
        completed = sum(1 for m in proj["milestones"] if m["completed"])
        proj["progress"] = int((completed / len(proj["milestones"])) * 100)
    
    # Append countdown info
    countdown = get_countdown_info(proj["deadline"])
    proj["countdown"] = countdown
    return proj

def get_all_projects(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute("SELECT * FROM projects ORDER BY completed ASC, deadline ASC").fetchall()
    return [_serialize_project(db, row) for row in rows]

def get_project(db: sqlite3.Connection, project_id: int) -> dict:
    row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Project not found")
    return _serialize_project(db, row)

def create_project(db: sqlite3.Connection, data: ProjectCreate) -> dict:
    title = data.title.strip()
    created_at = get_logical_date_ist().isoformat()
    
    cur = db.execute(
        """
        INSERT INTO projects (title, description, deadline, priority, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (title, data.description, data.deadline, data.priority or 0, created_at)
    )
    project_id = cur.lastrowid

    if getattr(data, 'initial_milestones', None):
        for ms_title in data.initial_milestones:
            if ms_title.strip():
                db.execute(
                    "INSERT INTO project_milestones (project_id, title, created_at) VALUES (?, ?, ?)",
                    (project_id, ms_title.strip(), created_at)
                )

    return get_project(db, project_id)

def update_project(db: sqlite3.Connection, project_id: int, data: ProjectUpdate) -> dict:
    project = get_project(db, project_id)
    
    title = data.title.strip() if data.title is not None else project["title"]
    description = data.description if data.description is not None else project["description"]
    deadline = data.deadline if data.deadline is not None else project["deadline"]
    priority = data.priority if data.priority is not None else project["priority"]
    progress = data.progress if data.progress is not None else project["progress"]
    completed = data.completed if data.completed is not None else project["completed"]
    completed_at = data.completed_at if hasattr(data, 'completed_at') and data.completed_at is not None else project.get("completed_at")

    db.execute(
        """
        UPDATE projects
        SET title = ?, description = ?, deadline = ?, priority = ?, progress = ?, completed = ?, completed_at = ?
        WHERE id = ?
        """,
        (title, description, deadline, priority, progress, completed, completed_at, project_id)
    )
    return get_project(db, project_id)

def delete_project(db: sqlite3.Connection, project_id: int):
    get_project(db, project_id)
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))

# --- Milestones ---

def get_milestone(db: sqlite3.Connection, milestone_id: int) -> dict:
    row = db.execute("SELECT * FROM project_milestones WHERE id = ?", (milestone_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Milestone not found")
    return _serialize_milestone(row)

def create_milestone(db: sqlite3.Connection, project_id: int, data: MilestoneCreate) -> dict:
    get_project(db, project_id) # ensure project exists
    title = data.title.strip()
    created_at = get_logical_date_ist().isoformat()
    
    cur = db.execute(
        "INSERT INTO project_milestones (project_id, title, created_at) VALUES (?, ?, ?)",
        (project_id, title, created_at)
    )
    # Return the updated project so the UI has the new progress
    return get_project(db, project_id)

def update_milestone(db: sqlite3.Connection, milestone_id: int, data: MilestoneUpdate) -> dict:
    milestone = get_milestone(db, milestone_id)
    title = data.title.strip() if data.title is not None else milestone["title"]
    completed = data.completed if data.completed is not None else milestone["completed"]
    
    db.execute(
        "UPDATE project_milestones SET title = ?, completed = ? WHERE id = ?",
        (title, completed, milestone_id)
    )
    return get_project(db, milestone["project_id"])

def delete_milestone(db: sqlite3.Connection, milestone_id: int) -> dict:
    milestone = get_milestone(db, milestone_id)
    db.execute("DELETE FROM project_milestones WHERE id = ?", (milestone_id,))
    return get_project(db, milestone["project_id"])
