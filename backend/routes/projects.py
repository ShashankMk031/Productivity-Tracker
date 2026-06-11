from fastapi import APIRouter
from database.db import get_db
from schemas.response import APIResponse
from schemas.project_schemas import ProjectCreate, ProjectUpdate, MilestoneCreate, MilestoneUpdate
from services.project_service import (
    get_all_projects, get_project, create_project, update_project, delete_project,
    create_milestone, update_milestone, delete_milestone
)

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("")
def read_projects():
    with get_db() as db:
        projects = get_all_projects(db)
        return APIResponse(data=projects)

@router.post("")
def add_project(body: ProjectCreate):
    with get_db() as db:
        project = create_project(db, body)
        return APIResponse(data=project, message="Project created")

@router.put("/{project_id}")
def edit_project(project_id: int, body: ProjectUpdate):
    with get_db() as db:
        project = update_project(db, project_id, body)
        return APIResponse(data=project, message="Project updated")

@router.delete("/{project_id}")
def remove_project(project_id: int):
    with get_db() as db:
        delete_project(db, project_id)
        return APIResponse(data={"deleted": project_id}, message="Project deleted")

# --- Milestones ---

@router.post("/{project_id}/milestones")
def add_milestone(project_id: int, body: MilestoneCreate):
    with get_db() as db:
        project = create_milestone(db, project_id, body)
        return APIResponse(data=project, message="Milestone created")

@router.put("/milestones/{milestone_id}")
def edit_milestone(milestone_id: int, body: MilestoneUpdate):
    with get_db() as db:
        project = update_milestone(db, milestone_id, body)
        return APIResponse(data=project, message="Milestone updated")

@router.delete("/milestones/{milestone_id}")
def remove_milestone(milestone_id: int):
    with get_db() as db:
        project = delete_milestone(db, milestone_id)
        return APIResponse(data=project, message="Milestone deleted")
