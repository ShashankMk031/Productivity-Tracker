from fastapi import APIRouter
from database.db import get_db
from schemas.response import APIResponse
from schemas.goal_schemas import GoalCreate, GoalUpdate
from services.goal_service import get_all_goals, get_goal, create_goal, update_goal, delete_goal

router = APIRouter(prefix="/goals", tags=["Goals"])

@router.get("")
def read_goals():
    with get_db() as db:
        goals = get_all_goals(db)
        return APIResponse(data=goals)

@router.post("")
def add_goal(body: GoalCreate):
    with get_db() as db:
        goal = create_goal(db, body)
        return APIResponse(data=goal, message="Goal created")

@router.put("/{goal_id}")
def edit_goal(goal_id: int, body: GoalUpdate):
    with get_db() as db:
        goal = update_goal(db, goal_id, body)
        return APIResponse(data=goal, message="Goal updated")

@router.delete("/{goal_id}")
def remove_goal(goal_id: int):
    with get_db() as db:
        delete_goal(db, goal_id)
        return APIResponse(data={"deleted": goal_id}, message="Goal deleted")
