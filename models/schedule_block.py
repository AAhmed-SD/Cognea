"""
Schedule Block model for the Personal Agent application.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class ScheduleBlockBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    context: str = "Work"
    goal_id: Optional[UUID] = None
    is_fixed: bool = False
    is_rescheduled: bool = False
    rescheduled_count: int = 0
    color_code: Optional[str] = None

class ScheduleBlockCreate(ScheduleBlockBase):
    user_id: UUID

class ScheduleBlockUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    context: Optional[str] = None
    goal_id: Optional[UUID] = None
    is_fixed: Optional[bool] = None
    is_rescheduled: Optional[bool] = None
    rescheduled_count: Optional[int] = None
    color_code: Optional[str] = None

class ScheduleBlock(ScheduleBlockBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 