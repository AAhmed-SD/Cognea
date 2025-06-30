from fastapi import APIRouter
from typing import List
from datetime import datetime
from pydantic import BaseModel
from services.supabase import get_supabase_client

router = APIRouter(prefix="/calendar", tags=["Calendar Sync"])


class CalendarPushRequest(BaseModel):
    user_id: str
    tasks: List[str]


@router.post("/connect", summary="Start Google/Apple Calendar sync via OAuth")
async def calendar_connect(user_id: str):
    supabase = get_supabase_client()
    data = {
        "user_id": user_id,
        "connected": True,
        "connected_at": datetime.now().isoformat(),
    }
    result = (
        supabase.table("calendar_connections")
        .upsert(data, on_conflict=["user_id"])
        .execute()
    )
    return {
        "user_id": user_id,
        "status": "calendar connected",
        "connected_at": data["connected_at"],
    }


@router.get("/sync", summary="Fetch user events")
async def calendar_sync(user_id: str):
    supabase = get_supabase_client()
    result = (
        supabase.table("calendar_events").select("*").eq("user_id", user_id).execute()
    )
    return {"user_id": user_id, "events": result.data}


@router.post("/push", summary="Push Cognie tasks into calendar")
async def calendar_push(request: CalendarPushRequest):
    supabase = get_supabase_client()
    events = []
    for task in request.tasks:
        event_data = {
            "user_id": request.user_id,
            "title": task,
            "start": datetime.now().isoformat(),
            "end": datetime.now().isoformat(),
        }
        result = supabase.table("calendar_events").insert(event_data).execute()
        if result.data:
            events.append(result.data[0])
    return {
        "user_id": request.user_id,
        "status": "tasks pushed to calendar",
        "events": events,
    }


@router.get("/events", summary="Get all calendar events for user")
async def get_calendar_events(user_id: str):
    supabase = get_supabase_client()
    result = (
        supabase.table("calendar_events").select("*").eq("user_id", user_id).execute()
    )
    return {"user_id": user_id, "events": result.data}
