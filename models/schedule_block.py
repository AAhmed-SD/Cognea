"""
Schedule Block model for the Personal Agent application.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ScheduleBlockBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    start_time: datetime
    end_time: datetime
    context: str = "Work"
    goal_id: UUID | None = None
    is_fixed: bool = False
    is_rescheduled: bool = False
    rescheduled_count: int = 0
    color_code: str | None = None


class ScheduleBlockCreate(ScheduleBlockBase):
    user_id: UUID


class ScheduleBlockUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    context: str | None = None
    goal_id: UUID | None = None
    is_fixed: bool | None = None
    is_rescheduled: bool | None = None
    rescheduled_count: int | None = None
    color_code: str | None = None


class ScheduleBlock(ScheduleBlockBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
