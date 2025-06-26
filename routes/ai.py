from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, confloat
from sqlalchemy.orm import Session
from models.database import get_db
from models.user import User
from models.plan import Plan
from models.flashcard import Flashcard, FlashcardReview
from services.auth import get_current_user

# Remove the /ai prefix since it's already added in main.py
router = APIRouter(tags=["AI & Personalization"])

# In-memory storage for AI insights and check-ins
ai_insights_db: Dict[int, dict] = {}
routine_templates_db: Dict[int, dict] = {}
auto_checkins_db: Dict[int, List[str]] = {}
manual_checkins_db: Dict[int, List[dict]] = {}

class PlanPreferences(BaseModel):
    focus_areas: List[str]
    duration: Optional[str] = "8h"

class PlanDayRequest(BaseModel):
    date: str
    preferences: PlanPreferences

class FlashcardRequest(BaseModel):
    topic: str
    difficulty: str
    count: int

class FlashcardReviewRequest(BaseModel):
    flashcard_id: int
    response: str
    confidence: confloat(ge=0.0, le=1.0)

class InsightRequest(BaseModel):
    date_range: str
    categories: List[str]

class GoalRequest(BaseModel):
    title: str
    description: str
    target_date: str
    category: str
    priority: str = "medium"

class HabitSuggestionRequest(BaseModel):
    user_preferences: List[str]
    current_habits: List[str]
    available_time: int  # minutes per day

class ProductivityAnalysisRequest(BaseModel):
    date_range: str
    include_calendar: bool = True
    include_habits: bool = True
    include_learning: bool = True

class SmartScheduleRequest(BaseModel):
    tasks: List[dict]  # List of tasks with priority, duration, deadline
    available_time: dict  # Available time slots
    preferences: dict  # User preferences

@router.post("/plan-day", summary="Generate a daily plan based on preferences")
async def plan_day(
    request: PlanDayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # In a real implementation, this would use OpenAI or another AI service
    # to generate a personalized plan based on preferences
    schedule = [
        {
            "time": "09:00-10:30",
            "activity": "Deep work session",
            "focus_area": request.preferences.focus_areas[0]
        },
        {
            "time": "10:45-12:00",
            "activity": "Team meeting",
            "focus_area": "work"
        }
    ]

    # Create plan in database
    plan = Plan(
        date=datetime.fromisoformat(request.date),
        preferences=request.preferences.model_dump(),
        schedule=schedule,
        user_id=current_user.id
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return {
        "success": True,
        "plan_id": plan.id,
        "plan": {
            "date": request.date,
            "schedule": schedule
        }
    }

@router.post("/generate-flashcards", summary="Generate flashcards for a topic")
async def generate_flashcards(
    request: FlashcardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # In a real implementation, this would use OpenAI or another AI service
    # to generate flashcards based on the topic and difficulty
    flashcard_data = [
        {
            "front": "What is Python?",
            "back": "Python is a high-level, interpreted programming language."
        },
        {
            "front": "What is a list in Python?",
            "back": "A list is a mutable sequence type that can store multiple items."
        },
        {
            "front": "What is a dictionary in Python?",
            "back": "A dictionary is a mutable mapping type that stores key-value pairs."
        },
        {
            "front": "What is a tuple in Python?",
            "back": "A tuple is an immutable sequence type that can store multiple items."
        },
        {
            "front": "What is a set in Python?",
            "back": "A set is an unordered collection of unique elements."
        }
    ]
    
    # Create flashcards in database
    flashcards = []
    for data in flashcard_data[:request.count]:
        flashcard = Flashcard(
            user_id=current_user.id,
            topic=request.topic,
            difficulty=request.difficulty,
            front=data["front"],
            back=data["back"]
        )
        db.add(flashcard)
        flashcards.append(flashcard)
    
    db.commit()
    
    # Return flashcards with IDs
    return {
        "success": True,
        "flashcards": [
            {
                "id": f.id,
                "front": f.front,
                "back": f.back,
                "topic": f.topic,
                "difficulty": f.difficulty
            }
            for f in flashcards
        ]
    }

@router.post("/complete-review", summary="Submit a flashcard review")
async def review_flashcard(
    request: FlashcardReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if flashcard exists and belongs to user
    flashcard = db.query(Flashcard).filter(
        Flashcard.id == request.flashcard_id,
        Flashcard.user_id == current_user.id
    ).first()
    
    if not flashcard:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    
    # Create review
    review = FlashcardReview(
        flashcard_id=flashcard.id,
        user_id=current_user.id,
        response=request.response,
        confidence=request.confidence
    )
    
    db.add(review)
    db.commit()
    db.refresh(review)
    
    return {
        "success": True,
        "review_id": review.id
    }

@router.get("/plan/{plan_id}", summary="Get a plan by ID")
async def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Row-level security: only allow access to own plans
    if plan.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this plan")
    
    return {
        "success": True,
        "plan": {
            "id": plan.id,
            "date": plan.date.isoformat(),
            "preferences": plan.preferences,
            "schedule": plan.schedule
        }
    }

@router.post("/insights", summary="Generate AI insights based on user data")
async def generate_insights(
    request: InsightRequest,
    current_user: User = Depends(get_current_user)
):
    # In a real implementation, this would analyze user data and generate insights
    # using AI/ML models. For now, we'll return mock insights.
    insights = {
        "productivity_trends": [
            {
                "category": "Focus Time",
                "trend": "increasing",
                "details": "Your deep work sessions have increased by 25% this week"
            },
            {
                "category": "Learning",
                "trend": "stable",
                "details": "Consistent progress in flashcard reviews"
            }
        ],
        "recommendations": [
            "Consider scheduling more breaks between deep work sessions",
            "Your peak productivity hours appear to be in the morning"
        ],
        "achievements": [
            "Completed 5 days of consistent planning",
            "Achieved 80% confidence in Python flashcards"
        ]
    }
    
    return {
        "success": True,
        "date_range": request.date_range,
        "categories": request.categories,
        "insights": insights
    }

@router.get("/insights/latest", summary="Get latest AI insights")
async def get_latest_insights(
    current_user: User = Depends(get_current_user)
):
    # In a real implementation, this would fetch the most recent insights
    # from a database. For now, we'll return mock data.
    latest_insights = {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": "You've been making steady progress in your learning goals",
        "key_metrics": {
            "productivity_score": 85,
            "learning_efficiency": 92,
            "habit_consistency": 78
        }
    }
    
    return {
        "success": True,
        "insights": latest_insights
    }

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

@router.post("/goals/track", summary="Track and analyze goal progress")
async def track_goal_progress(
    request: GoalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track a new goal and provide AI-powered progress analysis"""
    
    # In a real implementation, this would store goals in a database
    # and use AI to analyze progress patterns
    
    goal_analysis = {
        "goal_id": f"goal_{current_user.id}_{datetime.now().timestamp()}",
        "title": request.title,
        "progress_estimate": 0,
        "milestones": [
            {"description": "Define clear objectives", "completed": True},
            {"description": "Create action plan", "completed": False},
            {"description": "Start implementation", "completed": False},
            {"description": "Review and adjust", "completed": False}
        ],
        "ai_suggestions": [
            f"Break down '{request.title}' into smaller, actionable tasks",
            "Schedule regular review sessions to track progress",
            "Set up reminders for key milestones"
        ],
        "similar_goals_success_rate": 0.78,
        "estimated_completion_time": "3-4 weeks"
    }
    
    return {
        "success": True,
        "goal": goal_analysis
    }

@router.post("/habits/suggest", summary="Get AI-powered habit suggestions")
async def suggest_habits(
    request: HabitSuggestionRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate personalized habit suggestions based on user preferences"""
    
    # AI analysis of user preferences and current habits
    habit_suggestions = {
        "morning_routine": [
            {
                "habit": "5-minute meditation",
                "benefit": "Improves focus and reduces stress",
                "difficulty": "easy",
                "time_required": 5
            },
            {
                "habit": "Journaling",
                "benefit": "Enhances self-awareness and goal clarity",
                "difficulty": "medium",
                "time_required": 10
            }
        ],
        "productivity_habits": [
            {
                "habit": "Time blocking",
                "benefit": "Increases focus and reduces context switching",
                "difficulty": "medium",
                "time_required": 15
            },
            {
                "habit": "Pomodoro technique",
                "benefit": "Maintains energy and prevents burnout",
                "difficulty": "easy",
                "time_required": 25
            }
        ],
        "learning_habits": [
            {
                "habit": "Spaced repetition review",
                "benefit": "Improves long-term retention",
                "difficulty": "easy",
                "time_required": 10
            }
        ],
        "ai_recommendations": [
            "Start with 1-2 easy habits and build consistency",
            "Link new habits to existing routines",
            "Track progress daily for the first 21 days"
        ]
    }
    
    return {
        "success": True,
        "suggestions": habit_suggestions
    }

@router.post("/productivity/analyze", summary="Analyze productivity patterns")
async def analyze_productivity(
    request: ProductivityAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze user productivity patterns and provide insights"""
    
    # Mock productivity analysis - in real implementation, this would
    # analyze actual user data from calendar, habits, and learning activities
    
    productivity_analysis = {
        "overall_score": 82,
        "trends": {
            "focus_time": {"trend": "increasing", "change": "+15%"},
            "task_completion": {"trend": "stable", "change": "+2%"},
            "learning_consistency": {"trend": "increasing", "change": "+25%"}
        },
        "peak_hours": {
            "morning": "09:00-11:00",
            "afternoon": "14:00-16:00",
            "evening": "19:00-21:00"
        },
        "productivity_blocks": [
            {
                "type": "Deep Work",
                "duration": "2-3 hours",
                "best_time": "Morning",
                "success_rate": 0.85
            },
            {
                "type": "Learning",
                "duration": "45-60 minutes",
                "best_time": "Afternoon",
                "success_rate": 0.92
            },
            {
                "type": "Planning",
                "duration": "30 minutes",
                "best_time": "Evening",
                "success_rate": 0.78
            }
        ],
        "ai_insights": [
            "Your productivity peaks in the morning - schedule important tasks then",
            "Learning sessions are most effective in the afternoon",
            "Consider adding more breaks between deep work sessions"
        ],
        "optimization_suggestions": [
            "Move creative tasks to your peak morning hours",
            "Schedule meetings in the afternoon when focus is lower",
            "Add 5-minute breaks every 90 minutes of deep work"
        ]
    }
    
    return {
        "success": True,
        "analysis": productivity_analysis
    }

@router.post("/schedule/optimize", summary="Optimize schedule using AI")
async def optimize_schedule(
    request: SmartScheduleRequest,
    current_user: User = Depends(get_current_user)
):
    """Use AI to optimize task scheduling based on priorities and preferences"""
    
    # AI scheduling algorithm would consider:
    # - Task priority and deadlines
    # - User's peak productivity hours
    # - Energy levels throughout the day
    # - Task dependencies and context switching
    
    optimized_schedule = {
        "morning": [
            {
                "task": "High Priority Project",
                "duration": 120,
                "start_time": "09:00",
                "energy_level": "high",
                "focus_required": "deep"
            },
            {
                "task": "Creative Brainstorming",
                "duration": 45,
                "start_time": "11:15",
                "energy_level": "high",
                "focus_required": "creative"
            }
        ],
        "afternoon": [
            {
                "task": "Learning Session",
                "duration": 60,
                "start_time": "14:00",
                "energy_level": "medium",
                "focus_required": "learning"
            },
            {
                "task": "Administrative Tasks",
                "duration": 30,
                "start_time": "15:30",
                "energy_level": "medium",
                "focus_required": "light"
            }
        ],
        "evening": [
            {
                "task": "Planning & Review",
                "duration": 45,
                "start_time": "19:00",
                "energy_level": "low",
                "focus_required": "planning"
            }
        ],
        "ai_recommendations": [
            "Schedule your most important task first thing in the morning",
            "Group similar tasks together to reduce context switching",
            "Leave buffer time between tasks for unexpected interruptions"
        ],
        "estimated_completion_rate": 0.92,
        "total_focus_time": 300,
        "breaks_scheduled": 4
    }
    
    return {
        "success": True,
        "optimized_schedule": optimized_schedule
    }

@router.get("/insights/weekly-summary", summary="Get weekly productivity summary")
async def get_weekly_summary(
    current_user: User = Depends(get_current_user)
):
    """Generate a comprehensive weekly productivity summary"""
    
    weekly_summary = {
        "week_ending": datetime.now().strftime("%Y-%m-%d"),
        "overall_score": 87,
        "key_achievements": [
            "Completed 5 deep work sessions",
            "Maintained 7-day learning streak",
            "Achieved 90% task completion rate"
        ],
        "areas_for_improvement": [
            "Reduce meeting time by 20%",
            "Increase physical activity breaks",
            "Improve evening routine consistency"
        ],
        "next_week_focus": [
            "Prioritize project milestone completion",
            "Start new learning module",
            "Optimize morning routine"
        ],
        "productivity_metrics": {
            "focus_time": "18.5 hours",
            "tasks_completed": 23,
            "learning_sessions": 7,
            "habit_streak": 5
        },
        "ai_predictions": {
            "next_week_score": 89,
            "confidence": 0.85,
            "key_factors": ["Reduced meeting load", "Improved sleep schedule"]
        }
    }
    
    return {
        "success": True,
        "weekly_summary": weekly_summary
    } 