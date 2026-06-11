from pydantic import BaseModel, Field
from typing import Optional, List

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = ""
    deadline: str
    priority: Optional[int] = 0
    initial_milestones: Optional[List[str]] = []

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[int] = None
    progress: Optional[int] = None
    completed: Optional[int] = None
    completed_at: Optional[str] = None

class MilestoneCreate(BaseModel):
    title: str = Field(..., min_length=1)

class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[int] = None

class MilestoneResponse(BaseModel):
    id: int
    project_id: int
    title: str
    completed: int
    created_at: str

class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    deadline: str
    progress: int
    priority: int
    created_at: str
    completed: int
    completed_at: Optional[str] = None
    milestones: List[MilestoneResponse] = []
