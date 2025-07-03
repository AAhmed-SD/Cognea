"""
User model for the Personal Agent application.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    preferences: dict[str, Any] | None = Field(default_factory=dict)
    energy_curve: dict[str, Any] | None = Field(default_factory=dict)
    default_scheduling_rules: dict[str, Any] | None = Field(default_factory=dict)
    smart_planning_enabled: bool = True
    encryption_enabled: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    preferences: dict[str, Any] | None = None
    energy_curve: dict[str, Any] | None = None
    default_scheduling_rules: dict[str, Any] | None = None
    smart_planning_enabled: bool | None = None
    encryption_enabled: bool | None = None


class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserInDB(User):
    hashed_password: str
