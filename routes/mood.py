from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
import logging
from services.supabase import get_supabase_client

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
    try:
        # Get user's mood and productivity data from database
        supabase = get_supabase_client()

        # Fetch user's mood entries, tasks, and schedule blocks
        mood_result = (
            supabase.table("mood_entries")
            .select("*")
            .eq("user_id", str(user_id))
            .limit(50)
            .execute()
        )
        tasks_result = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", str(user_id))
            .limit(50)
            .execute()
        )
        schedule_result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", str(user_id))
            .limit(50)
            .execute()
        )

        mood_entries = mood_result.data if mood_result.data else []
        tasks = tasks_result.data if tasks_result.data else []
        schedule_blocks = schedule_result.data if schedule_result.data else []

        # Calculate basic correlations
        avg_mood = (
            sum([m.get("mood_score", 5) for m in mood_entries]) / len(mood_entries)
            if mood_entries
            else 5
        )
        completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
        total_tasks = len(tasks)
        task_completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        # Generate AI prompt for mood correlations
        prompt = f"""Analyze this user's mood and productivity data to identify correlations:

MOOD DATA:
- Total mood entries: {len(mood_entries)}
- Average mood score: {avg_mood:.1f}/10

PRODUCTIVITY DATA:
- Total tasks: {total_tasks}
- Completed tasks: {completed_tasks}
- Task completion rate: {task_completion_rate:.1f}%
- Schedule blocks: {len(schedule_blocks)}

Generate correlations in JSON format:
{{
    "correlations": {{
        "sleep": "positive/negative/neutral",
        "tasks": "positive/negative/neutral",
        "focus_time": "positive/negative/neutral",
        "social_activity": "positive/negative/neutral"
    }},
    "insights": [
        "Specific insight about mood-productivity relationship 1",
        "Specific insight about mood-productivity relationship 2"
    ],
    "recommendations": [
        "Specific recommendation based on correlations 1",
        "Specific recommendation based on correlations 2"
    ]
}}

Base the analysis on patterns in their actual data."""

        # Call OpenAI API
        from services.openai_integration import generate_openai_text

        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=600, temperature=0.3
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Parse the response
        import json

        try:
            response_text = response.get("generated_text", "")
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                correlations_data = json.loads(json_str)

                correlations = correlations_data.get(
                    "correlations", {"sleep": "positive", "tasks": "neutral"}
                )
                insights = correlations_data.get(
                    "insights",
                    [
                        "Your mood tends to improve when you complete tasks",
                        "Consistent sleep patterns correlate with better productivity",
                    ],
                )
                recommendations = correlations_data.get(
                    "recommendations",
                    [
                        "Maintain consistent sleep schedule",
                        "Focus on completing high-priority tasks first",
                    ],
                )
            else:
                # Fallback correlations
                correlations = {"sleep": "positive", "tasks": "neutral"}
                insights = [
                    "Your mood tends to improve when you complete tasks",
                    "Consistent sleep patterns correlate with better productivity",
                ]
                recommendations = [
                    "Maintain consistent sleep schedule",
                    "Focus on completing high-priority tasks first",
                ]
        except json.JSONDecodeError:
            # Fallback correlations
            correlations = {"sleep": "positive", "tasks": "neutral"}
            insights = [
                "Your mood tends to improve when you complete tasks",
                "Consistent sleep patterns correlate with better productivity",
            ]
            recommendations = [
                "Maintain consistent sleep schedule",
                "Focus on completing high-priority tasks first",
            ]

        return {
            "user_id": user_id,
            "correlations": correlations,
            "insights": insights,
            "recommendations": recommendations,
        }
    except Exception as e:
        logging.error(f"Error generating mood correlations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
