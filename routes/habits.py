from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/habits", tags=["Habits & Routines"])

class Habit(BaseModel):
    id: int
    user_id: int
    name: str
    frequency: str
    time: Optional[str]
    energy_level: Optional[str]
    reminder: Optional[bool]
    category: Optional[str]
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class HabitCreate(BaseModel):
    user_id: int
    name: str
    frequency: str
    time: Optional[str]
    energy_level: Optional[str]
    reminder: Optional[bool]
    category: Optional[str]

class HabitLog(BaseModel):
    id: int
    habit_id: int
    user_id: int
    timestamp: datetime
    mood: Optional[str] = None
    notes: Optional[str] = None

# In-memory storage
habits_db = []
habit_logs_db = []
habit_streaks_db = {}

@router.post("/", response_model=Habit, summary="Create a new habit/routine")
async def create_habit(habit: HabitCreate):
    new_id = len(habits_db) + 1
    new_habit = Habit(id=new_id, **habit.dict())
    habits_db.append(new_habit)
    return new_habit

@router.get("/{user_id}", response_model=List[Habit], summary="List all habits for a user")
async def list_habits(user_id: int):
    return [h for h in habits_db if h.user_id == user_id]

@router.put("/{habit_id}", response_model=Habit, summary="Update a habit")
async def update_habit(habit_id: int, habit: HabitCreate):
    for h in habits_db:
        if h.id == habit_id:
            h.name = habit.name
            h.frequency = habit.frequency
            h.time = habit.time
            h.energy_level = habit.energy_level
            h.reminder = habit.reminder
            h.category = habit.category
            h.updated_at = datetime.now()
            return h
    raise HTTPException(status_code=404, detail="Habit not found")

@router.delete("/{habit_id}", summary="Delete a habit")
async def delete_habit(habit_id: int):
    global habits_db
    habits_db = [h for h in habits_db if h.id != habit_id]
    return {"message": f"Habit {habit_id} deleted"}

@router.post("/log", response_model=HabitLog, summary="Mark habit as complete")
async def log_habit(habit_id: int, user_id: int, mood: Optional[str] = None, notes: Optional[str] = None):
    log_id = len(habit_logs_db) + 1
    log = HabitLog(id=log_id, habit_id=habit_id, user_id=user_id, timestamp=datetime.now(), mood=mood, notes=notes)
    habit_logs_db.append(log)
    # Update streaks
    streak = habit_streaks_db.get((user_id, habit_id), 0) + 1
    habit_streaks_db[(user_id, habit_id)] = streak
    return log

@router.get("/streaks/{user_id}", summary="View active and historical streaks")
async def habit_streaks(user_id: int):
    streaks = [
        {"habit_id": h.id, "streak": habit_streaks_db.get((user_id, h.id), 0)}
        for h in habits_db if h.user_id == user_id
    ]
    return {"user_id": user_id, "streaks": streaks}

@router.get("/calendar/{user_id}", summary="Return heatmap view of completions")
async def habit_calendar(user_id: int):
    completions = [
        {"habit_id": log.habit_id, "date": log.timestamp.date().isoformat()} 
        for log in habit_logs_db if log.user_id == user_id
    ]
    return {"user_id": user_id, "calendar": completions}

@router.post("/suggest", summary="AI suggestion for new habits based on user behavior")
async def habit_suggest(user_id: int):
    # Placeholder AI logic
    return {"suggestion": f"User {user_id}, try a 10-minute walk after lunch."} 