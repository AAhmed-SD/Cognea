from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# Define Pydantic models for the new endpoints
class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    preferences: Optional[dict] = None

class ActivityLog(BaseModel):
    user_id: str
    activity: str
    timestamp: datetime

class Feedback(BaseModel):
    user_id: str
    feedback: str
    timestamp: datetime

class HelpResource(BaseModel):
    title: str
    content: str

# In-memory storage for demonstration purposes
user_profiles = []
activity_logs = []
feedbacks = []
help_resources = [
    {"title": "Getting Started", "content": "Here's how to get started..."},
    {"title": "FAQ", "content": "Frequently Asked Questions..."}
]

# User Profile Endpoints
@router.get("/user-profile/{user_id}", response_model=UserProfile, tags=["User Profile"], summary="Get user profile")
async def get_user_profile(user_id: str):
    user_profile = next((profile for profile in user_profiles if profile["user_id"] == user_id), None)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return user_profile

# Activity Log Endpoints
@router.get("/activity-log/{user_id}", response_model=List[ActivityLog], tags=["Activity Log"], summary="Get activity log")
async def get_activity_log(user_id: str):
    return [log for log in activity_logs if log["user_id"] == user_id]

# Feedback Endpoints
@router.post("/feedback", tags=["Feedback"], summary="Submit feedback")
async def submit_feedback(feedback: Feedback):
    feedbacks.append(feedback)
    return {"message": "Feedback submitted successfully"}

# Help Endpoints
@router.get("/help", response_model=List[HelpResource], tags=["Help"], summary="Get help resources")
async def get_help_resources():
    return help_resources 