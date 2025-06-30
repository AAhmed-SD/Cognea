from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/mood", tags=["Mood & Emotion Tracking"])


class MoodLog(BaseModel):
    id: int
    user_id: int
    value: str
    timestamp: datetime
    tags: Optional[List[str]] = None
    journal: Optional[str] = None


class MoodLogCreate(BaseModel):
    user_id: int
    value: str
    timestamp: datetime
    tags: Optional[List[str]] = None
    journal: Optional[str] = None


# In-memory storage
mood_logs_db = []


@router.post("/", response_model=MoodLog, summary="Log mood")
async def log_mood(mood: MoodLogCreate):
    new_id = len(mood_logs_db) + 1
    log = MoodLog(id=new_id, **mood.dict())
    mood_logs_db.append(log)
    return log


@router.get("/logs/{user_id}", response_model=List[MoodLog], summary="List mood logs")
async def list_moods(user_id: int):
    return [log for log in mood_logs_db if log.user_id == user_id]


@router.get(
    "/stats/{user_id}", summary="Mood trends: most common moods, mood over time"
)
async def mood_stats(user_id: int):
    user_logs = [log for log in mood_logs_db if log.user_id == user_id]
    if not user_logs:
        return {"user_id": user_id, "most_common": None, "trend": []}
    mood_counts = {}
    trend = []
    for log in user_logs:
        mood_counts[log.value] = mood_counts.get(log.value, 0) + 1
        trend.append(log.value)
    most_common = max(mood_counts, key=mood_counts.get)
    return {"user_id": user_id, "most_common": most_common, "trend": trend}


@router.post("/prompt", summary="Trigger journaling or quote based on mood")
async def mood_prompt(user_id: int):
    user_logs = [log for log in mood_logs_db if log.user_id == user_id]
    if user_logs and user_logs[-1].value == "happy":
        return {"prompt": "Write about what made you happy today."}
    return {"prompt": "How are you feeling right now?"}


@router.get(
    "/correlations/{user_id}",
    summary="Return correlations with tasks, sleep, focus time, etc.",
)
async def mood_correlations(user_id: int):
    # Simulate correlations
    return {
        "user_id": user_id,
        "correlations": {"sleep": "positive", "tasks": "neutral"},
    }
