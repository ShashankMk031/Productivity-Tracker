from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from schemas.project_schemas import ProjectCreate, ProjectUpdate, MilestoneCreate, MilestoneUpdate
from services import project_service


def test_project_crud_cycle(db):
    deadline = (date.today() + timedelta(days=30)).isoformat()
    created = project_service.create_project(
        db, ProjectCreate(title="Ship v1", deadline=deadline, initial_milestones=["Design", "Build"])
    )
    assert len(created["milestones"]) == 2
    assert created["progress"] == 0
    assert "countdown" in created

    project = project_service.update_milestone(db, created["milestones"][0]["id"], MilestoneUpdate(completed=1))
    assert project["progress"] == 50

    project = project_service.create_milestone(db, created["id"], MilestoneCreate(title="Launch"))
    assert len(project["milestones"]) == 3

    updated = project_service.update_project(db, created["id"], ProjectUpdate(priority=2))
    assert updated["priority"] == 2

    project_service.delete_project(db, created["id"])
    with pytest.raises(HTTPException):
        project_service.get_project(db, created["id"])

    # ON DELETE CASCADE removes milestones with the project
    count = db.execute("SELECT COUNT(*) FROM project_milestones").fetchone()[0]
    assert count == 0


def test_get_missing_project_raises_404(db):
    with pytest.raises(HTTPException) as exc:
        project_service.get_project(db, 999)
    assert exc.value.status_code == 404
