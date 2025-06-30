from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, confloat
from services.supabase import get_supabase_client
from services.auth import get_current_user
from services.cost_tracking import cost_tracking_service
import logging

# Remove the /ai prefix since it's already added in main.py
router = APIRouter(tags=["AI & Personalization"])


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
    request: PlanDayRequest, current_user: dict = Depends(get_current_user)
):
    # Check budget limits before making AI call
    budget_check = await cost_tracking_service.check_budget_limits(current_user["id"])
    if budget_check["daily_exceeded"] or budget_check["monthly_exceeded"]:
        raise HTTPException(status_code=429, detail="Budget limit exceeded")

    # In a real implementation, this would use OpenAI or another AI service
    # to generate a personalized plan based on preferences
    schedule = [
        {
            "time": "09:00-10:30",
            "activity": "Deep work session",
            "focus_area": request.preferences.focus_areas[0],
        },
        {"time": "10:45-12:00", "activity": "Team meeting", "focus_area": "work"},
    ]

    # Track API usage (mock values for now)
    await cost_tracking_service.track_api_call(
        user_id=current_user["id"],
        endpoint="/plan-day",
        model="gpt-4",
        input_tokens=150,
        output_tokens=200,
        cost_usd=0.01,
    )

    # Create plan in Supabase
    supabase = get_supabase_client()
    plan_data = {
        "user_id": current_user["id"],
        "date": request.date,
        "preferences": request.preferences.model_dump(),
        "schedule": schedule,
        "created_at": datetime.utcnow().isoformat(),
    }

    result = supabase.table("plans").insert(plan_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create plan")

    plan = result.data[0]

    return {
        "success": True,
        "plan_id": plan["id"],
        "plan": {"date": request.date, "schedule": schedule},
    }


@router.post("/generate-flashcards", summary="Generate flashcards for a topic")
async def generate_flashcards(
    request: FlashcardRequest, current_user: dict = Depends(get_current_user)
):
    # Check budget limits before making AI call
    budget_check = await cost_tracking_service.check_budget_limits(current_user["id"])
    if budget_check["daily_exceeded"] or budget_check["monthly_exceeded"]:
        raise HTTPException(status_code=429, detail="Budget limit exceeded")

    # In a real implementation, this would use OpenAI or another AI service
    # to generate flashcards based on the topic and difficulty
    flashcard_data = [
        {
            "front": "What is Python?",
            "back": "Python is a high-level, interpreted programming language.",
        },
        {
            "front": "What is a list in Python?",
            "back": "A list is a mutable sequence type that can store multiple items.",
        },
        {
            "front": "What is a dictionary in Python?",
            "back": "A dictionary is a mutable mapping type that stores key-value pairs.",
        },
        {
            "front": "What is a tuple in Python?",
            "back": "A tuple is an immutable sequence type that can store multiple items.",
        },
        {
            "front": "What is a set in Python?",
            "back": "A set is an unordered collection of unique elements.",
        },
    ]

    # Track API usage (mock values for now)
    await cost_tracking_service.track_api_call(
        user_id=current_user["id"],
        endpoint="/generate-flashcards",
        model="gpt-4",
        input_tokens=100,
        output_tokens=300,
        cost_usd=0.015,
    )

    # Create flashcards in Supabase
    supabase = get_supabase_client()
    flashcards_to_insert = []

    for data in flashcard_data[: request.count]:
        flashcard_data = {
            "user_id": current_user["id"],
            "topic": request.topic,
            "difficulty": request.difficulty,
            "front": data["front"],
            "back": data["back"],
            "created_at": datetime.utcnow().isoformat(),
        }
        flashcards_to_insert.append(flashcard_data)

    result = supabase.table("flashcards").insert(flashcards_to_insert).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create flashcards")

    # Return flashcards with IDs
    return {
        "success": True,
        "flashcards": [
            {
                "id": f["id"],
                "front": f["front"],
                "back": f["back"],
                "topic": f["topic"],
                "difficulty": f["difficulty"],
            }
            for f in result.data
        ],
    }


@router.post("/complete-review", summary="Submit a flashcard review")
async def review_flashcard(
    request: FlashcardReviewRequest, current_user: dict = Depends(get_current_user)
):
    # Check if flashcard exists and belongs to user
    supabase = get_supabase_client()

    flashcard_result = (
        supabase.table("flashcards")
        .select("*")
        .eq("id", request.flashcard_id)
        .eq("user_id", current_user["id"])
        .execute()
    )

    if not flashcard_result.data:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    flashcard = flashcard_result.data[0]

    # Create review in Supabase
    review_data = {
        "flashcard_id": flashcard["id"],
        "user_id": current_user["id"],
        "response": request.response,
        "confidence": request.confidence,
        "created_at": datetime.utcnow().isoformat(),
    }

    result = supabase.table("flashcard_reviews").insert(review_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create review")

    review = result.data[0]

    return {"success": True, "review_id": review["id"]}


@router.get("/plan/{plan_id}", summary="Get a plan by ID")
async def get_plan(plan_id: int, current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()

    result = supabase.table("plans").select("*").eq("id", plan_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan = result.data[0]

    # Row-level security: only allow access to own plans
    if plan["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this plan"
        )

    return {
        "success": True,
        "plan": {
            "id": plan["id"],
            "date": plan["date"],
            "preferences": plan["preferences"],
            "schedule": plan["schedule"],
        },
    }


@router.post("/insights", summary="Generate AI insights based on user data")
async def generate_insights(
    request: InsightRequest, current_user: dict = Depends(get_current_user)
):
    # TODO: In a real implementation, this would analyze user data and generate insights
    # using AI/ML models. For now, we'll return mock insights.
    insights = {
        "productivity_trends": [
            {
                "category": "Focus Time",
                "trend": "increasing",
                "details": "Your deep work sessions have increased by 25% this week",
            },
            {
                "category": "Learning",
                "trend": "stable",
                "details": "Consistent progress in flashcard reviews",
            },
        ],
        "recommendations": [
            "Consider scheduling more breaks between deep work sessions",
            "Your peak productivity hours appear to be in the morning",
        ],
        "achievements": [
            "Completed 5 days of consistent planning",
            "Achieved 80% confidence in Python flashcards",
        ],
    }

    return {
        "success": True,
        "date_range": request.date_range,
        "categories": request.categories,
        "insights": insights,
    }


@router.get("/insights/latest", summary="Get latest AI insights")
async def get_latest_insights(current_user: dict = Depends(get_current_user)):
    try:
        # Get user's recent data from database
        supabase = get_supabase_client()

        # Fetch recent tasks, goals, and schedule blocks
        tasks_result = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", current_user["id"])
            .limit(20)
            .execute()
        )
        goals_result = (
            supabase.table("goals")
            .select("*")
            .eq("user_id", current_user["id"])
            .limit(10)
            .execute()
        )
        schedule_result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", current_user["id"])
            .limit(20)
            .execute()
        )

        tasks = tasks_result.data if tasks_result.data else []
        goals = goals_result.data if goals_result.data else []
        schedule_blocks = schedule_result.data if schedule_result.data else []

        # Real OpenAI integration for insights generation
        data_summary = f"""
Recent Tasks: {len(tasks)} tasks
- Completed: {len([t for t in tasks if t.get('status') == 'completed'])}
- Pending: {len([t for t in tasks if t.get('status') == 'pending'])}
- High Priority: {len([t for t in tasks if t.get('priority') == 'high'])}

Recent Goals: {len(goals)} goals
- Active: {len([g for g in goals if g.get('status') == 'active'])}
- Progress Range: {min([g.get('progress', 0) for g in goals])}% - {max([g.get('progress', 0) for g in goals])}%

Schedule Blocks: {len(schedule_blocks)} blocks
- Fixed: {len([s for s in schedule_blocks if s.get('is_fixed')])}
- Rescheduled: {len([s for s in schedule_blocks if s.get('is_rescheduled')])}
"""

        prompt = f"""Based on the following user data, generate personalized productivity insights:

{data_summary}

Provide insights in JSON format:
{{
    "summary": "Brief summary of user's productivity patterns",
    "key_metrics": {{
        "productivity_score": 0-100,
        "learning_efficiency": 0-100,
        "habit_consistency": 0-100
    }},
    "recommendations": [
        "Specific actionable recommendation 1",
        "Specific actionable recommendation 2",
        "Specific actionable recommendation 3"
    ]
}}

Focus on actionable insights that can help improve productivity and goal achievement."""

        # Call OpenAI API
        from services.openai_integration import generate_openai_text

        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=800, temperature=0.3
        )

        # Parse the response
        import json

        try:
            response_text = response.get("generated_text", "")
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                insights = {
                    "generated_at": datetime.utcnow().isoformat(),
                    "summary": parsed.get(
                        "summary",
                        "You've been making steady progress in your learning goals",
                    ),
                    "key_metrics": parsed.get(
                        "key_metrics",
                        {
                            "productivity_score": 85,
                            "learning_efficiency": 92,
                            "habit_consistency": 78,
                        },
                    ),
                    "recommendations": parsed.get(
                        "recommendations",
                        [
                            "Continue with your current productivity patterns",
                            "Consider adding more breaks between deep work sessions",
                            "Review your goals weekly to maintain focus",
                        ],
                    ),
                }
            else:
                # Fallback insights
                insights = {
                    "generated_at": datetime.utcnow().isoformat(),
                    "summary": "You've been making steady progress in your learning goals",
                    "key_metrics": {
                        "productivity_score": 85,
                        "learning_efficiency": 92,
                        "habit_consistency": 78,
                    },
                    "recommendations": [
                        "Continue with your current productivity patterns",
                        "Consider adding more breaks between deep work sessions",
                        "Review your goals weekly to maintain focus",
                    ],
                }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            insights = {
                "generated_at": datetime.utcnow().isoformat(),
                "summary": "You've been making steady progress in your learning goals",
                "key_metrics": {
                    "productivity_score": 85,
                    "learning_efficiency": 92,
                    "habit_consistency": 78,
                },
                "recommendations": [
                    "Continue with your current productivity patterns",
                    "Consider adding more breaks between deep work sessions",
                    "Review your goals weekly to maintain focus",
                ],
            }

        return {"success": True, "insights": insights}
    except Exception as e:
        logging.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/routine-template/{user_id}", summary="Generate/update optimal week schedule"
)
async def routine_template(user_id: int):
    # TODO: In a real implementation, this would generate/retrieve routine templates
    # from Supabase. For now, we'll return mock data.
    template = {
        "template": "Optimal week schedule generated.",
        "blocks": [
            {"day": "Monday", "focus": "Deep Work", "start": "09:00", "end": "12:00"},
            {
                "day": "Friday",
                "focus": "Review & Plan",
                "start": "15:00",
                "end": "16:00",
            },
        ],
    }
    return {"user_id": user_id, **template}


@router.get(
    "/auto-checkins/{user_id}", summary="Daily or weekly prompts for consistency"
)
async def auto_checkins(user_id: int):
    # TODO: In a real implementation, this would fetch check-ins from Supabase
    # For now, we'll return mock data.
    checkins = [
        "Did you complete your morning routine?",
        "What was your biggest win this week?",
    ]
    return {"user_id": user_id, "checkins": checkins}


@router.post(
    "/trigger-checkin/{user_id}", summary="Manual trigger for a check-in via UI"
)
async def trigger_checkin(user_id: int):
    # TODO: In a real implementation, this would store check-ins in Supabase
    # For now, we'll return mock data.
    now = datetime.now().isoformat()
    return {"user_id": user_id, "status": "Check-in triggered.", "timestamp": now}


@router.post("/goals/track", summary="Track and analyze goal progress")
async def track_goal_progress(
    request: GoalRequest, current_user: dict = Depends(get_current_user)
):
    """Track a new goal and provide AI-powered progress analysis"""

    # TODO: In a real implementation, this would store goals in Supabase
    # and use AI to analyze progress patterns

    goal_analysis = {
        "goal_id": f"goal_{current_user['id']}_{datetime.now().timestamp()}",
        "title": request.title,
        "progress_estimate": 0,
        "milestones": [
            {"description": "Define clear objectives", "completed": True},
            {"description": "Create action plan", "completed": False},
            {"description": "Start implementation", "completed": False},
            {"description": "Review and adjust", "completed": False},
        ],
        "ai_suggestions": [
            f"Break down '{request.title}' into smaller, actionable tasks",
            "Schedule regular review sessions to track progress",
            "Set up reminders for key milestones",
        ],
        "similar_goals_success_rate": 0.78,
        "estimated_completion_time": "3-4 weeks",
    }

    return {"success": True, "goal": goal_analysis}


@router.post("/habits/suggest", summary="Get AI-powered habit suggestions")
async def suggest_habits(
    request: HabitSuggestionRequest, current_user: dict = Depends(get_current_user)
):
    """Generate personalized habit suggestions based on user preferences"""

    # TODO: AI analysis of user preferences and current habits
    habit_suggestions = {
        "morning_routine": [
            {
                "habit": "5-minute meditation",
                "benefit": "Improves focus and reduces stress",
                "difficulty": "easy",
                "time_required": 5,
            },
            {
                "habit": "Journaling",
                "benefit": "Enhances self-awareness and goal clarity",
                "difficulty": "medium",
                "time_required": 10,
            },
        ],
        "productivity_habits": [
            {
                "habit": "Time blocking",
                "benefit": "Increases focus and reduces context switching",
                "difficulty": "medium",
                "time_required": 15,
            },
            {
                "habit": "Pomodoro technique",
                "benefit": "Maintains energy and prevents burnout",
                "difficulty": "easy",
                "time_required": 25,
            },
        ],
        "learning_habits": [
            {
                "habit": "Spaced repetition review",
                "benefit": "Improves long-term retention",
                "difficulty": "easy",
                "time_required": 10,
            }
        ],
        "ai_recommendations": [
            "Start with 1-2 easy habits and build consistency",
            "Link new habits to existing routines",
            "Track progress daily for the first 21 days",
        ],
    }

    return {"success": True, "suggestions": habit_suggestions}


@router.post("/productivity/analyze", summary="Analyze productivity patterns")
async def analyze_productivity(
    request: ProductivityAnalysisRequest, current_user: dict = Depends(get_current_user)
):
    """Analyze user productivity patterns and provide insights"""

    # TODO: Mock productivity analysis - in real implementation, this would
    # analyze actual user data from calendar, habits, and learning activities

    productivity_analysis = {
        "overall_score": 82,
        "trends": {
            "focus_time": {"trend": "increasing", "change": "+15%"},
            "task_completion": {"trend": "stable", "change": "+2%"},
            "learning_consistency": {"trend": "increasing", "change": "+25%"},
        },
        "peak_hours": {
            "morning": "09:00-11:00",
            "afternoon": "14:00-16:00",
            "evening": "19:00-21:00",
        },
        "productivity_blocks": [
            {
                "type": "Deep Work",
                "duration": "2-3 hours",
                "best_time": "Morning",
                "success_rate": 0.85,
            },
            {
                "type": "Learning",
                "duration": "45-60 minutes",
                "best_time": "Afternoon",
                "success_rate": 0.92,
            },
            {
                "type": "Planning",
                "duration": "30 minutes",
                "best_time": "Evening",
                "success_rate": 0.78,
            },
        ],
        "ai_insights": [
            "Your productivity peaks in the morning - schedule important tasks then",
            "Learning sessions are most effective in the afternoon",
            "Consider adding more breaks between deep work sessions",
        ],
        "optimization_suggestions": [
            "Move creative tasks to your peak morning hours",
            "Schedule meetings in the afternoon when focus is lower",
            "Add 5-minute breaks every 90 minutes of deep work",
        ],
    }

    return {"success": True, "analysis": productivity_analysis}


@router.post("/schedule/optimize", summary="Optimize schedule using AI")
async def optimize_schedule(
    request: SmartScheduleRequest, current_user: dict = Depends(get_current_user)
):
    """Use AI to optimize task scheduling based on priorities and preferences"""

    # TODO: AI scheduling algorithm would consider:
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
                "focus_required": "deep",
            },
            {
                "task": "Creative Brainstorming",
                "duration": 45,
                "start_time": "11:15",
                "energy_level": "high",
                "focus_required": "creative",
            },
        ],
        "afternoon": [
            {
                "task": "Learning Session",
                "duration": 60,
                "start_time": "14:00",
                "energy_level": "medium",
                "focus_required": "learning",
            },
            {
                "task": "Administrative Tasks",
                "duration": 30,
                "start_time": "15:30",
                "energy_level": "medium",
                "focus_required": "light",
            },
        ],
        "evening": [
            {
                "task": "Planning & Review",
                "duration": 45,
                "start_time": "19:00",
                "energy_level": "low",
                "focus_required": "planning",
            }
        ],
        "ai_recommendations": [
            "Schedule your most important task first thing in the morning",
            "Group similar tasks together to reduce context switching",
            "Leave buffer time between tasks for unexpected interruptions",
        ],
        "estimated_completion_rate": 0.92,
        "total_focus_time": 300,
        "breaks_scheduled": 4,
    }

    return {"success": True, "optimized_schedule": optimized_schedule}


@router.get("/insights/weekly-summary", summary="Get weekly productivity summary")
async def get_weekly_summary(current_user: dict = Depends(get_current_user)):
    """Generate a comprehensive weekly productivity summary"""

    # TODO: In a real implementation, this would analyze actual user data
    # from Supabase tables and generate insights

    weekly_summary = {
        "week_ending": datetime.now().strftime("%Y-%m-%d"),
        "overall_score": 87,
        "key_achievements": [
            "Completed 5 deep work sessions",
            "Maintained 7-day learning streak",
            "Achieved 90% task completion rate",
        ],
        "areas_for_improvement": [
            "Reduce meeting time by 20%",
            "Increase physical activity breaks",
            "Improve evening routine consistency",
        ],
        "next_week_focus": [
            "Prioritize project milestone completion",
            "Start new learning module",
            "Optimize morning routine",
        ],
        "productivity_metrics": {
            "focus_time": "18.5 hours",
            "tasks_completed": 23,
            "learning_sessions": 7,
            "habit_streak": 5,
        },
        "ai_predictions": {
            "next_week_score": 89,
            "confidence": 0.85,
            "key_factors": ["Reduced meeting load", "Improved sleep schedule"],
        },
    }

    return {"success": True, "weekly_summary": weekly_summary}
