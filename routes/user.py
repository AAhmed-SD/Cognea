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
    {"title": "FAQ", "content": "Frequently Asked Questions..."},
]


# User Profile Endpoints
@router.get(
    "/user-profile/{user_id}",
    response_model=UserProfile,
    tags=["User Profile"],
    summary="Get user profile",
)
async def get_user_profile(user_id: str):
    user_profile = next(
        (profile for profile in user_profiles if profile["user_id"] == user_id), None
    )
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return user_profile


# Activity Log Endpoints
@router.get(
    "/activity-log/{user_id}",
    response_model=List[ActivityLog],
    tags=["Activity Log"],
    summary="Get activity log",
)
async def get_activity_log(user_id: str):
    return [log for log in activity_logs if log["user_id"] == user_id]


# Feedback Endpoints
@router.post("/feedback", tags=["Feedback"], summary="Submit feedback")
async def submit_feedback(feedback: Feedback):
    feedbacks.append(feedback)
    return {"message": "Feedback submitted successfully"}


# Help Endpoints
@router.get(
    "/help",
    response_model=List[HelpResource],
    tags=["Help"],
    summary="Get help resources",
)
async def get_help_resources():
    return help_resources


@router.get("/api/tasks")
async def get_tasks():
    return {"tasks": []}


@router.post("/api/tasks")
async def create_task():
    return {"message": "Task created"}


@router.put("/api/tasks/1")
async def update_task():
    return {"message": "Task updated"}


@router.delete("/api/tasks/1")
async def delete_task():
    return {"message": "Task deleted"}


@router.get("/api/settings")
async def get_settings():
    return {"settings": {}}


@router.put("/api/settings")
async def update_settings():
    return {"message": "Settings updated"}


@router.get("/api/notifications")
async def get_notifications():
    return {"notifications": []}


@router.post("/api/notifications")
async def create_notification():
    return {"message": "Notification created"}


@router.delete("/api/notifications/1")
async def delete_notification():
    return {"message": "Notification deleted"}


@router.get("/api/calendar/events")
async def get_calendar_events():
    return {"events": []}


@router.post("/api/calendar/events")
async def create_calendar_event():
    return {"message": "Event created"}


@router.put("/api/calendar/events/1")
async def update_calendar_event():
    return {"message": "Event updated"}


@router.delete("/api/calendar/events/1")
async def delete_calendar_event():
    return {"message": "Event deleted"}
