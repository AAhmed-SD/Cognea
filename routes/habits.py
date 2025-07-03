from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.supabase import get_supabase_client

router = APIRouter(prefix="/habits", tags=["Habits & Routines"])


class Habit(BaseModel):
    id: str  # UUID from Supabase
    user_id: str
    title: str
    description: str | None = None
    frequency: str | None = None
    time: str | None = None
    energy_level: str | None = None
    reminders: list | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class HabitCreate(BaseModel):
    user_id: str
    title: str
    description: str | None = None
    frequency: str | None = None
    time: str | None = None
    energy_level: str | None = None
    reminders: list | None = None


class HabitLog(BaseModel):
    id: str
    habit_id: str
    user_id: str
    completed_at: datetime
    mood_before: str | None = None
    notes: str | None = None


@router.post("/", response_model=Habit, summary="Create a new habit/routine")
async def create_habit(habit: HabitCreate):
    supabase = get_supabase_client()
    result = supabase.table("habits").insert(habit.dict()).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create habit")
    return result.data[0]


@router.get(
    "/{user_id}", response_model=list[Habit], summary="List all habits for a user"
)
async def list_habits(user_id: str):
    supabase = get_supabase_client()
    result = supabase.table("habits").select("*").eq("user_id", user_id).execute()
    return result.data


@router.put("/{habit_id}", response_model=Habit, summary="Update a habit")
async def update_habit(habit_id: str, habit: HabitCreate):
    supabase = get_supabase_client()
    result = supabase.table("habits").update(habit.dict()).eq("id", habit_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Habit not found")
    return result.data[0]


@router.delete("/{habit_id}", summary="Delete a habit")
async def delete_habit(habit_id: str):
    supabase = get_supabase_client()
    supabase.table("habits").delete().eq("id", habit_id).execute()
    return {"message": f"Habit {habit_id} deleted"}


@router.post("/log", response_model=HabitLog, summary="Mark habit as complete")
async def log_habit(
    habit_id: str,
    user_id: str,
    mood_before: str | None = None,
    notes: str | None = None,
):
    supabase = get_supabase_client()
    log_data = {
        "habit_id": habit_id,
        "user_id": user_id,
        "completed_at": datetime.now().isoformat(),
        "mood_before": mood_before,
        "notes": notes,
    }
    result = supabase.table("habit_logs").insert(log_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to log habit")
    return result.data[0]


@router.get("/streaks/{user_id}", summary="View active and historical streaks")
async def habit_streaks(user_id: str):
    supabase = get_supabase_client()
    # Get all habit logs for user
    logs = (
        supabase.table("habit_logs")
        .select("habit_id, completed_at")
        .eq("user_id", user_id)
        .order("completed_at")
        .execute()
        .data
    )
    # Calculate streaks per habit
    from collections import defaultdict

    streaks = defaultdict(int)
    last_dates = {}
    for log in logs:
        habit_id = log["habit_id"]
        date = datetime.fromisoformat(log["completed_at"][:19])
        if habit_id in last_dates:
            if (date.date() - last_dates[habit_id]).days == 1:
                streaks[habit_id] += 1
            else:
                streaks[habit_id] = 1
        else:
            streaks[habit_id] = 1
        last_dates[habit_id] = date.date()
    return {
        "user_id": user_id,
        "streaks": [{"habit_id": k, "streak": v} for k, v in streaks.items()],
    }


@router.get("/calendar/{user_id}", summary="Return heatmap view of completions")
async def habit_calendar(user_id: str):
    supabase = get_supabase_client()
    logs = (
        supabase.table("habit_logs")
        .select("habit_id, completed_at")
        .eq("user_id", user_id)
        .execute()
        .data
    )
    completions = [
        {"habit_id": log["habit_id"], "date": log["completed_at"][:10]} for log in logs
    ]
    return {"user_id": user_id, "calendar": completions}


@router.post("/suggest", summary="AI suggestion for new habits based on user behavior")
async def habit_suggest(user_id: str):
    # Placeholder AI logic
    return {"suggestion": f"User {user_id}, try a 10-minute walk after lunch."}
