from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["Analytics & Trends"])

# In-memory storage for analytics data
user_analytics_db: Dict[int, dict] = {}
user_trends_db: Dict[int, list] = {}
user_weekly_reviews_db: Dict[int, dict] = {}
user_productivity_patterns_db: Dict[int, dict] = {}

@router.get("/{user_id}", summary="Personalized dashboard (habits, mood, focus time, goals)")
async def analytics_dashboard(user_id: int):
    # Simulate dashboard aggregation
    dashboard = user_analytics_db.get(user_id, {
        "habits": ["Read", "Exercise"],
        "mood": ["happy", "neutral"],
        "focus_time": [
            {"date": (datetime.now() - timedelta(days=i)).date().isoformat(), "minutes": 120 - i*10}
            for i in range(7)
        ],
        "goals": ["Finish project", "Run 5k"]
    })
    return {"user_id": user_id, "dashboard": dashboard}

@router.get("/trends/{user_id}", summary="Visual insights over time (calendar heatmap, bar charts)")
async def trends(user_id: int):
    # Simulate trend data
    trends = user_trends_db.get(user_id, [
        {"date": (datetime.now() - timedelta(days=i)).date().isoformat(), "score": 80 + i}
        for i in range(7)
    ])
    return {"user_id": user_id, "trends": trends}

@router.get("/weekly-review/{user_id}", summary="AI-generated summary of the week")
async def weekly_review(user_id: int):
    # Simulate weekly review
    review = user_weekly_reviews_db.get(user_id, {
        "summary": "You had a productive week!",
        "completed_tasks": 15,
        "missed_tasks": 2,
        "streak": 5
    })
    return {"user_id": user_id, **review}

@router.get("/productivity-patterns/{user_id}", summary="Best day/time insights")
async def productivity_patterns(user_id: int):
    # Simulate productivity pattern
    pattern = user_productivity_patterns_db.get(user_id, {
        "best_time": "morning",
        "best_day": "Wednesday",
        "focus_blocks": [
            {"day": "Monday", "minutes": 120},
            {"day": "Tuesday", "minutes": 90},
            {"day": "Wednesday", "minutes": 150}
        ]
    })
    return {"user_id": user_id, **pattern} 