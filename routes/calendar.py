from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/calendar", tags=["Calendar Sync"])

# In-memory storage for calendar connections and events
calendar_connections_db: Dict[int, dict] = {}
calendar_events_db: Dict[int, List[dict]] = {}

class CalendarPushRequest(BaseModel):
    user_id: int
    tasks: List[str]

@router.post("/connect", summary="Start Google/Apple Calendar sync via OAuth")
async def calendar_connect(user_id: int):
    calendar_connections_db[user_id] = {"connected": True, "connected_at": datetime.now().isoformat()}
    return {"user_id": user_id, "status": "calendar connected", "connected_at": calendar_connections_db[user_id]["connected_at"]}

@router.get("/sync", summary="Fetch user events")
async def calendar_sync(user_id: int):
    events = calendar_events_db.get(user_id, [
        {"id": 1, "title": "Meeting", "start": datetime.now().isoformat(), "end": datetime.now().isoformat(), "location": "Zoom"}
    ])
    return {"user_id": user_id, "events": events}

@router.post("/push", summary="Push Cognie tasks into calendar")
async def calendar_push(request: CalendarPushRequest):
    # Simulate pushing tasks as events
    events = calendar_events_db.setdefault(request.user_id, [])
    for i, task in enumerate(request.tasks, start=1):
        events.append({"id": len(events)+1, "title": task, "start": datetime.now().isoformat(), "end": datetime.now().isoformat()})
    return {"user_id": request.user_id, "status": "tasks pushed to calendar", "events": events}

@router.get("/events", summary="Get all calendar events for user")
async def get_calendar_events(user_id: int):
    events = calendar_events_db.get(user_id, [])
    return {"user_id": user_id, "events": events} 