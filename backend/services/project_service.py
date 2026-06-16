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

    # Fetch linked goal title
    if proj.get("goal_id"):
        goal_row = db.execute("SELECT title FROM goals WHERE id = ?", (proj["goal_id"],)).fetchone()
        proj["goal_title"] = goal_row[0] if goal_row else None
    else:
        proj["goal_title"] = None

    return proj

def get_all_projects(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute("SELECT * FROM projects ORDER BY completed ASC, deadline ASC").fetchall()
    return [_serialize_project(db, row) for row in rows]

def get_project(db: sqlite3.Connection, project_id: int) -> dict:
    row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Project not found")
    return _serialize_project(db, row)

def update_goal_progress_from_projects(db: sqlite3.Connection, goal_id: int):
    if not goal_id:
        return
    rows = db.execute("SELECT id, progress FROM projects WHERE goal_id = ?", (goal_id,)).fetchall()
    if not rows:
        return
    
    total_progress = 0
    count = 0
    for r in rows:
        proj_id = r["id"]
        # Recalculate project progress using milestones in DB directly
        milestones = db.execute("SELECT completed FROM project_milestones WHERE project_id = ?", (proj_id,)).fetchall()
        if milestones:
            completed_ms = sum(1 for m in milestones if m[0])
            prog = int((completed_ms / len(milestones)) * 100)
        else:
            prog = r["progress"]
        total_progress += prog
        count += 1
        
    if count > 0:
        avg_progress = int(total_progress / count)
        completed = 1 if avg_progress >= 100 else 0
        db.execute(
            "UPDATE goals SET progress = ?, completed = ? WHERE id = ?",
            (avg_progress, completed, goal_id)
        )

def create_project(db: sqlite3.Connection, data: ProjectCreate) -> dict:
    title = data.title.strip()
    created_at = get_logical_date_ist().isoformat()
    
    cur = db.execute(
        """
        INSERT INTO projects (title, description, deadline, priority, created_at, goal_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, data.description, data.deadline, data.priority or 0, created_at, data.goal_id)
    )
    project_id = cur.lastrowid

    if getattr(data, 'initial_milestones', None):
        for ms_title in data.initial_milestones:
            if ms_title.strip():
                db.execute(
                    "INSERT INTO project_milestones (project_id, title, created_at) VALUES (?, ?, ?)",
                    (project_id, ms_title.strip(), created_at)
                )

    if data.goal_id:
        update_goal_progress_from_projects(db, data.goal_id)

    return get_project(db, project_id)

def update_project(db: sqlite3.Connection, project_id: int, data: ProjectUpdate) -> dict:
    project = get_project(db, project_id)
    old_goal_id = project.get("goal_id")
    
    title = data.title.strip() if data.title is not None else project["title"]
    description = data.description if data.description is not None else project["description"]
    deadline = data.deadline if data.deadline is not None else project["deadline"]
    priority = data.priority if data.priority is not None else project["priority"]
    progress = data.progress if data.progress is not None else project["progress"]
    completed = data.completed if data.completed is not None else project["completed"]
    completed_at = data.completed_at if hasattr(data, 'completed_at') and data.completed_at is not None else project.get("completed_at")
    goal_id = data.goal_id if data.goal_id is not None else old_goal_id

    db.execute(
        """
        UPDATE projects
        SET title = ?, description = ?, deadline = ?, priority = ?, progress = ?, completed = ?, completed_at = ?, goal_id = ?
        WHERE id = ?
        """,
        (title, description, deadline, priority, progress, completed, completed_at, goal_id, project_id)
    )
    
    if old_goal_id:
        update_goal_progress_from_projects(db, old_goal_id)
    if goal_id and goal_id != old_goal_id:
        update_goal_progress_from_projects(db, goal_id)

    return get_project(db, project_id)

def delete_project(db: sqlite3.Connection, project_id: int):
    project = get_project(db, project_id)
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    if project.get("goal_id"):
        update_goal_progress_from_projects(db, project["goal_id"])

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
    
    project = get_project(db, project_id)
    if project.get("goal_id"):
        update_goal_progress_from_projects(db, project["goal_id"])
    return project

def update_milestone(db: sqlite3.Connection, milestone_id: int, data: MilestoneUpdate) -> dict:
    milestone = get_milestone(db, milestone_id)
    title = data.title.strip() if data.title is not None else milestone["title"]
    completed = data.completed if data.completed is not None else milestone["completed"]
    
    db.execute(
        "UPDATE project_milestones SET title = ?, completed = ? WHERE id = ?",
        (title, completed, milestone_id)
    )
    
    project = get_project(db, milestone["project_id"])
    if project.get("goal_id"):
        update_goal_progress_from_projects(db, project["goal_id"])
    return project

def delete_milestone(db: sqlite3.Connection, milestone_id: int) -> dict:
    milestone = get_milestone(db, milestone_id)
    db.execute("DELETE FROM project_milestones WHERE id = ?", (milestone_id,))
    
    project = get_project(db, milestone["project_id"])
    if project.get("goal_id"):
        update_goal_progress_from_projects(db, project["goal_id"])
    return project
