"""
User model for the Personal Agent application.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    energy_curve: Optional[Dict[str, Any]] = Field(default_factory=dict)
    default_scheduling_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)
    smart_planning_enabled: bool = True
    encryption_enabled: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    preferences: Optional[Dict[str, Any]] = None
    energy_curve: Optional[Dict[str, Any]] = None
    default_scheduling_rules: Optional[Dict[str, Any]] = None
    smart_planning_enabled: Optional[bool] = None
    encryption_enabled: Optional[bool] = None

class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserInDB(User):
    hashed_password: str 