from pydantic import BaseModel, Field
from typing import Optional, List

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = ""
    deadline: str
    priority: Optional[int] = 0
    initial_milestones: Optional[List[str]] = []
    goal_id: Optional[int] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[int] = None
    progress: Optional[int] = None
    completed: Optional[int] = None
    completed_at: Optional[str] = None
    goal_id: Optional[int] = None

class MilestoneCreate(BaseModel):
    title: str = Field(..., min_length=1)

class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[int] = None

