"""
Task Pydantic schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskStatus, TaskType, TaskValidity


class TaskBase(BaseModel):
    """Base task schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    departure_city: str = Field(..., min_length=1, max_length=100)
    arrival_city: str = Field(..., min_length=1, max_length=100)
    travel_date: datetime
    return_date: Optional[datetime] = None
    num_travelers: int = Field(default=1, ge=1, le=10)
    cabin_class: str = Field(default="economy", pattern="^(economy|premium_economy|business|first)$")
    task_type: TaskType = TaskType.ONE_TIME
    task_validity: TaskValidity = TaskValidity.INSTANT
    scheduled_time: Optional[datetime] = None
    frequency: Optional[str] = None


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    scheduled_time: Optional[datetime] = None
    frequency: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v and v not in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            raise ValueError('Invalid task status')
        return v


class TaskResponse(TaskBase):
    """Schema for task response"""
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    max_retries: int
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for task list response"""
    tasks: List[TaskResponse]
    total: int
    skip: int
    limit: int


class TaskStats(BaseModel):
    """Schema for task statistics"""
    total: int
    running: int
    completed: int
    failed: int
    recent_24h: int
