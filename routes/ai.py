from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime

router = APIRouter(prefix="/ai", tags=["AI & Personalization"])

# In-memory storage for AI insights and check-ins
ai_insights_db: Dict[int, dict] = {}
routine_templates_db: Dict[int, dict] = {}
auto_checkins_db: Dict[int, List[str]] = {}
manual_checkins_db: Dict[int, List[dict]] = {}

@router.post("/insights/{user_id}", summary="AI-generated insights & personalized suggestions")
async def ai_insights(user_id: int):
    insights = ai_insights_db.get(user_id, {
        "insights": "You are most productive in the morning. Focus on deep work before noon.",
        "suggestions": ["Schedule creative tasks in the AM", "Review goals weekly"]
    })
    return {"user_id": user_id, **insights}

@router.post("/routine-template/{user_id}", summary="Generate/update optimal week schedule")
async def routine_template(user_id: int):
    template = routine_templates_db.get(user_id, {
        "template": "Optimal week schedule generated.",
        "blocks": [
            {"day": "Monday", "focus": "Deep Work", "start": "09:00", "end": "12:00"},
            {"day": "Friday", "focus": "Review & Plan", "start": "15:00", "end": "16:00"}
        ]
    })
    return {"user_id": user_id, **template}

@router.get("/auto-checkins/{user_id}", summary="Daily or weekly prompts for consistency")
async def auto_checkins(user_id: int):
    checkins = auto_checkins_db.get(user_id, [
        "Did you complete your morning routine?",
        "What was your biggest win this week?"
    ])
    return {"user_id": user_id, "checkins": checkins}

@router.post("/trigger-checkin/{user_id}", summary="Manual trigger for a check-in via UI")
async def trigger_checkin(user_id: int):
    now = datetime.now().isoformat()
    manual_checkins_db.setdefault(user_id, []).append({"timestamp": now, "status": "triggered"})
    return {"user_id": user_id, "status": "Check-in triggered.", "timestamp": now} 