from datetime import date, timedelta
import pytest
from schemas.project_schemas import ProjectCreate, ProjectUpdate, MilestoneUpdate, MilestoneCreate
from schemas.goal_schemas import GoalCreate
from services import project_service, goal_service

def test_goal_project_linking_and_progress(db):
    # 1. Create a goal
    goal = goal_service.create_goal(db, GoalCreate(title="Learn Programming", category="Short-Term Goals", progress=0))
    assert goal["progress"] == 0

    # 2. Create a project linked to that goal
    deadline = (date.today() + timedelta(days=30)).isoformat()
    proj1 = project_service.create_project(
        db, ProjectCreate(title="Code Project 1", deadline=deadline, goal_id=goal["id"], initial_milestones=["Milestone A", "Milestone B"])
    )
    assert proj1["goal_id"] == goal["id"]
    assert proj1["goal_title"] == "Learn Programming"
    
    # Assert goal progress is updated to 0% (since project has 0 progress)
    goal_after = goal_service.get_goal(db, goal["id"])
    assert goal_after["progress"] == 0

    # 3. Complete a milestone, project progress should become 50%
    proj_updated = project_service.update_milestone(db, proj1["milestones"][0]["id"], MilestoneUpdate(completed=1))
    assert proj_updated["progress"] == 50

    # Assert goal progress is auto-updated to 50%
    goal_after = goal_service.get_goal(db, goal["id"])
    assert goal_after["progress"] == 50

    # 4. Create another project linked to the same goal with 1 milestone
    proj2 = project_service.create_project(
        db, ProjectCreate(title="Code Project 2", deadline=deadline, goal_id=goal["id"], initial_milestones=["Single Milestone"])
    )
    # Average progress of project 1 (50%) and project 2 (0%) is (50+0)/2 = 25%
    goal_after = goal_service.get_goal(db, goal["id"])
    assert goal_after["progress"] == 25

    # 5. Complete project 2's milestone
    project_service.update_milestone(db, proj2["milestones"][0]["id"], MilestoneUpdate(completed=1))
    # Average progress of project 1 (50%) and project 2 (100%) is (50+100)/2 = 75%
    goal_after = goal_service.get_goal(db, goal["id"])
    assert goal_after["progress"] == 75

    # 6. Delete project 2
    project_service.delete_project(db, proj2["id"])
    # Only project 1 remains (50%)
    goal_after = goal_service.get_goal(db, goal["id"])
    assert goal_after["progress"] == 50
