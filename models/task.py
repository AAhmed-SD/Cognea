"""
Task model for the Personal Agent application.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum
from pydantic import ConfigDict


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: PriorityLevel = PriorityLevel.MEDIUM


class TaskCreate(TaskBase):
    user_id: UUID


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    priority: Optional[PriorityLevel] = None


class Task(TaskBase):
    id: UUID
    user_id: UUID
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
