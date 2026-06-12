import pytest
from fastapi import HTTPException

from schemas.goal_schemas import GoalCreate, GoalUpdate
from services import goal_service


def test_goal_crud_cycle(db):
    created = goal_service.create_goal(db, GoalCreate(title="  Read daily  ", category="Short-Term Goals"))
    assert created["title"] == "Read daily"
    assert created["progress"] == 0
    assert created["completed"] == 0

    fetched = goal_service.get_goal(db, created["id"])
    assert fetched["id"] == created["id"]

    updated = goal_service.update_goal(db, created["id"], GoalUpdate(progress=60, completed=1))
    assert updated["progress"] == 60
    assert updated["completed"] == 1

    assert len(goal_service.get_all_goals(db)) == 1

    goal_service.delete_goal(db, created["id"])
    assert goal_service.get_all_goals(db) == []


def test_get_missing_goal_raises_404(db):
    with pytest.raises(HTTPException) as exc:
        goal_service.get_goal(db, 999)
    assert exc.value.status_code == 404
