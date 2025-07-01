from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta
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
    try:
        # Get user's recent data from database
        supabase = get_supabase_client()

        # Fetch recent tasks, goals, and schedule blocks
        tasks_result = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", current_user["id"])
            .limit(50)
            .execute()
        )
        goals_result = (
            supabase.table("goals")
            .select("*")
            .eq("user_id", current_user["id"])
            .limit(20)
            .execute()
        )
        schedule_result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", current_user["id"])
            .limit(30)
            .execute()
        )

        tasks = tasks_result.data if tasks_result.data else []
        goals = goals_result.data if goals_result.data else []
        schedule_blocks = schedule_result.data if schedule_result.data else []

        # Calculate key metrics
        completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
        total_tasks = len(tasks)
        completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        active_goals = len([g for g in goals if g.get("status") == "active"])
        avg_goal_progress = (
            sum([g.get("progress", 0) for g in goals]) / len(goals) if goals else 0
        )

        # Generate AI prompt for insights
        prompt = f"""Analyze this user's productivity data and generate insights:

TASK PERFORMANCE:
- Total tasks: {total_tasks}
- Completed tasks: {completed_tasks}
- Completion rate: {completion_rate:.1f}%

GOAL PROGRESS:
- Active goals: {active_goals}
- Average goal progress: {avg_goal_progress:.1f}%

SCHEDULE DATA:
- Schedule blocks: {len(schedule_blocks)}
- Fixed blocks: {len([s for s in schedule_blocks if s.get('is_fixed')])}
- Rescheduled blocks: {len([s for s in schedule_blocks if s.get('is_rescheduled')])}

Generate insights in JSON format:
{{
    "productivity_trends": [
        {{
            "category": "Focus Time",
            "trend": "increasing/stable/decreasing",
            "details": "Specific observation about focus time"
        }},
        {{
            "category": "Learning",
            "trend": "increasing/stable/decreasing", 
            "details": "Specific observation about learning"
        }}
    ],
    "recommendations": [
        "Specific actionable recommendation 1",
        "Specific actionable recommendation 2"
    ],
    "achievements": [
        "Specific achievement 1",
        "Specific achievement 2"
    ]
}}

Focus on actionable insights that can help improve productivity."""

        # Call OpenAI API
        from services.openai_integration import generate_openai_text

        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=800, temperature=0.3
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
                insights_data = json.loads(json_str)

                insights = {
                    "productivity_trends": insights_data.get(
                        "productivity_trends",
                        [
                            {
                                "category": "Focus Time",
                                "trend": "stable",
                                "details": "Your focus time has been consistent",
                            }
                        ],
                    ),
                    "recommendations": insights_data.get(
                        "recommendations",
                        [
                            "Continue with your current productivity patterns",
                            "Consider reviewing your goals weekly",
                        ],
                    ),
                    "achievements": insights_data.get(
                        "achievements",
                        [
                            "Maintained consistent task completion",
                            "Kept up with your learning goals",
                        ],
                    ),
                }
            else:
                # Fallback insights
                insights = {
                    "productivity_trends": [
                        {
                            "category": "Focus Time",
                            "trend": "stable",
                            "details": "Your focus time has been consistent",
                        }
                    ],
                    "recommendations": [
                        "Continue with your current productivity patterns",
                        "Consider reviewing your goals weekly",
                    ],
                    "achievements": [
                        "Maintained consistent task completion",
                        "Kept up with your learning goals",
                    ],
                }
        except json.JSONDecodeError:
            # Fallback insights
            insights = {
                "productivity_trends": [
                    {
                        "category": "Focus Time",
                        "trend": "stable",
                        "details": "Your focus time has been consistent",
                    }
                ],
                "recommendations": [
                    "Continue with your current productivity patterns",
                    "Consider reviewing your goals weekly",
                ],
                "achievements": [
                    "Maintained consistent task completion",
                    "Kept up with your learning goals",
                ],
            }

        return {
            "success": True,
            "date_range": request.date_range,
            "categories": request.categories,
            "insights": insights,
        }
    except Exception as e:
        logging.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
    try:
        # Get user's recent data to personalize check-ins
        supabase = get_supabase_client()

        # Fetch user's recent tasks, goals, and habits
        tasks_result = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", str(user_id))
            .limit(20)
            .execute()
        )
        goals_result = (
            supabase.table("goals")
            .select("*")
            .eq("user_id", str(user_id))
            .limit(10)
            .execute()
        )

        tasks = tasks_result.data if tasks_result.data else []
        goals = goals_result.data if goals_result.data else []

        # Calculate metrics for personalization
        completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
        total_tasks = len(tasks)
        active_goals = len([g for g in goals if g.get("status") == "active"])

        # Generate AI prompt for personalized check-ins
        prompt = f"""Generate personalized daily check-in questions for a user with this profile:

TASK PROFILE:
- Total recent tasks: {total_tasks}
- Completed tasks: {completed_tasks}
- Completion rate: {(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0:.1f}%

GOAL PROFILE:
- Active goals: {active_goals}

Generate 3-5 personalized check-in questions in JSON format:
{{
    "checkins": [
        "Specific question about their task completion",
        "Question about their goal progress",
        "Question about their productivity habits",
        "Question about their learning or growth"
    ]
}}

Make questions specific, actionable, and encouraging. Focus on their actual data patterns."""

        # Call OpenAI API
        from services.openai_integration import generate_openai_text

        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=400, temperature=0.4
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
                checkins_data = json.loads(json_str)

                checkins = checkins_data.get(
                    "checkins",
                    [
                        "Did you complete your most important task today?",
                        "What was your biggest win this week?",
                        "How are you progressing toward your goals?",
                    ],
                )
            else:
                # Fallback check-ins
                checkins = [
                    "Did you complete your most important task today?",
                    "What was your biggest win this week?",
                    "How are you progressing toward your goals?",
                ]
        except json.JSONDecodeError:
            # Fallback check-ins
            checkins = [
                "Did you complete your most important task today?",
                "What was your biggest win this week?",
                "How are you progressing toward your goals?",
            ]

        return {"user_id": user_id, "checkins": checkins}
    except Exception as e:
        logging.error(f"Error generating check-ins: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
    try:
        # Get user's data from database
        supabase = get_supabase_client()

        # Fetch user's tasks, schedule blocks, and goals
        tasks_result = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        schedule_result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        goals_result = (
            supabase.table("goals")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )

        tasks = tasks_result.data if tasks_result.data else []
        schedule_blocks = schedule_result.data if schedule_result.data else []
        goals = goals_result.data if goals_result.data else []

        # Calculate real metrics
        completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
        total_tasks = len(tasks)
        completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        fixed_schedules = len([s for s in schedule_blocks if s.get("is_fixed")])
        rescheduled_count = len([s for s in schedule_blocks if s.get("is_rescheduled")])

        active_goals = len([g for g in goals if g.get("status") == "active"])
        avg_goal_progress = (
            sum([g.get("progress", 0) for g in goals]) / len(goals) if goals else 0
        )

        # Generate AI prompt for productivity analysis
        prompt = f"""Analyze this user's productivity patterns and provide detailed insights:

TASK PERFORMANCE:
- Total tasks: {total_tasks}
- Completed: {completed_tasks}
- Completion rate: {completion_rate:.1f}%

SCHEDULE PATTERNS:
- Total schedule blocks: {len(schedule_blocks)}
- Fixed blocks: {fixed_schedules}
- Rescheduled blocks: {rescheduled_count}

GOAL PROGRESS:
- Active goals: {active_goals}
- Average progress: {avg_goal_progress:.1f}%

Generate a comprehensive productivity analysis in JSON format:
{{
    "overall_score": 0-100,
    "trends": {{
        "focus_time": {{"trend": "increasing/stable/decreasing", "change": "percentage"}},
        "task_completion": {{"trend": "increasing/stable/decreasing", "change": "percentage"}},
        "learning_consistency": {{"trend": "increasing/stable/decreasing", "change": "percentage"}}
    }},
    "peak_hours": {{
        "morning": "time range",
        "afternoon": "time range", 
        "evening": "time range"
    }},
    "productivity_blocks": [
        {{
            "type": "block type",
            "duration": "typical duration",
            "best_time": "optimal time",
            "success_rate": 0.0-1.0
        }}
    ],
    "ai_insights": [
        "Specific insight about productivity patterns",
        "Insight about scheduling effectiveness",
        "Insight about goal achievement"
    ],
    "optimization_suggestions": [
        "Specific actionable suggestion 1",
        "Specific actionable suggestion 2",
        "Specific actionable suggestion 3"
    ]
}}

Base the analysis on their actual data patterns and provide actionable recommendations."""

        # Call OpenAI API
        from services.openai_integration import generate_openai_text

        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=1200, temperature=0.3
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
                analysis_data = json.loads(json_str)

                productivity_analysis = {
                    "overall_score": analysis_data.get("overall_score", 75),
                    "trends": analysis_data.get(
                        "trends",
                        {
                            "focus_time": {"trend": "stable", "change": "+5%"},
                            "task_completion": {"trend": "stable", "change": "+2%"},
                            "learning_consistency": {
                                "trend": "stable",
                                "change": "+3%",
                            },
                        },
                    ),
                    "peak_hours": analysis_data.get(
                        "peak_hours",
                        {
                            "morning": "09:00-11:00",
                            "afternoon": "14:00-16:00",
                            "evening": "19:00-21:00",
                        },
                    ),
                    "productivity_blocks": analysis_data.get(
                        "productivity_blocks",
                        [
                            {
                                "type": "Deep Work",
                                "duration": "2-3 hours",
                                "best_time": "Morning",
                                "success_rate": 0.8,
                            }
                        ],
                    ),
                    "ai_insights": analysis_data.get(
                        "ai_insights",
                        [
                            "Your productivity is consistent",
                            "You maintain good focus during scheduled blocks",
                            "Your goal progress shows steady improvement",
                        ],
                    ),
                    "optimization_suggestions": analysis_data.get(
                        "optimization_suggestions",
                        [
                            "Continue with your current productivity patterns",
                            "Consider adding more breaks between deep work sessions",
                            "Review your goals weekly to maintain focus",
                        ],
                    ),
                }
            else:
                # Fallback analysis
                productivity_analysis = {
                    "overall_score": 75,
                    "trends": {
                        "focus_time": {"trend": "stable", "change": "+5%"},
                        "task_completion": {"trend": "stable", "change": "+2%"},
                        "learning_consistency": {"trend": "stable", "change": "+3%"},
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
                            "success_rate": 0.8,
                        }
                    ],
                    "ai_insights": [
                        "Your productivity is consistent",
                        "You maintain good focus during scheduled blocks",
                        "Your goal progress shows steady improvement",
                    ],
                    "optimization_suggestions": [
                        "Continue with your current productivity patterns",
                        "Consider adding more breaks between deep work sessions",
                        "Review your goals weekly to maintain focus",
                    ],
                }
        except json.JSONDecodeError:
            # Fallback analysis
            productivity_analysis = {
                "overall_score": 75,
                "trends": {
                    "focus_time": {"trend": "stable", "change": "+5%"},
                    "task_completion": {"trend": "stable", "change": "+2%"},
                    "learning_consistency": {"trend": "stable", "change": "+3%"},
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
                        "success_rate": 0.8,
                    }
                ],
                "ai_insights": [
                    "Your productivity is consistent",
                    "You maintain good focus during scheduled blocks",
                    "Your goal progress shows steady improvement",
                ],
                "optimization_suggestions": [
                    "Continue with your current productivity patterns",
                    "Consider adding more breaks between deep work sessions",
                    "Review your goals weekly to maintain focus",
                ],
            }

        return {"success": True, "analysis": productivity_analysis}
    except Exception as e:
        logging.error(f"Error analyzing productivity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
    try:
        # Get user's data from database for the past week
        supabase = get_supabase_client()

        # Calculate date range for the past week
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Fetch user's tasks, goals, and schedule blocks for the past week
        tasks_result = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", current_user["id"])
            .gte("created_at", start_date.isoformat())
            .lte("created_at", end_date.isoformat())
            .execute()
        )
        goals_result = (
            supabase.table("goals")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )
        schedule_result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", current_user["id"])
            .gte("start_time", start_date.isoformat())
            .lte("start_time", end_date.isoformat())
            .execute()
        )

        tasks = tasks_result.data if tasks_result.data else []
        goals = goals_result.data if goals_result.data else []
        schedule_blocks = schedule_result.data if schedule_result.data else []

        # Calculate real metrics
        completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
        total_tasks = len(tasks)
        completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        active_goals = len([g for g in goals if g.get("status") == "active"])
        avg_goal_progress = (
            sum([g.get("progress", 0) for g in goals]) / len(goals) if goals else 0
        )

        fixed_schedules = len([s for s in schedule_blocks if s.get("is_fixed")])
        rescheduled_count = len([s for s in schedule_blocks if s.get("is_rescheduled")])

        # Generate AI prompt for weekly summary
        prompt = f"""Generate a comprehensive weekly productivity summary for a user with this data:

WEEKLY TASK PERFORMANCE:
- Total tasks: {total_tasks}
- Completed tasks: {completed_tasks}
- Completion rate: {completion_rate:.1f}%

GOAL PROGRESS:
- Active goals: {active_goals}
- Average progress: {avg_goal_progress:.1f}%

SCHEDULE PATTERNS:
- Total schedule blocks: {len(schedule_blocks)}
- Fixed blocks: {fixed_schedules}
- Rescheduled blocks: {rescheduled_count}

Generate a weekly summary in JSON format:
{{
    "week_ending": "YYYY-MM-DD",
    "overall_score": 0-100,
    "key_achievements": [
        "Specific achievement 1",
        "Specific achievement 2",
        "Specific achievement 3"
    ],
    "areas_for_improvement": [
        "Specific area for improvement 1",
        "Specific area for improvement 2",
        "Specific area for improvement 3"
    ],
    "next_week_focus": [
        "Specific focus area 1",
        "Specific focus area 2",
        "Specific focus area 3"
    ],
    "productivity_metrics": {{
        "focus_time": "total hours",
        "tasks_completed": "number",
        "learning_sessions": "number",
        "habit_streak": "days"
    }},
    "ai_predictions": {{
        "next_week_score": 0-100,
        "confidence": 0.0-1.0,
        "key_factors": ["factor 1", "factor 2"]
    }}
}}

Base the summary on their actual performance and provide encouraging, actionable insights."""

        # Call OpenAI API
        from services.openai_integration import generate_openai_text

        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=1000, temperature=0.4
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
                summary_data = json.loads(json_str)

                weekly_summary = {
                    "week_ending": summary_data.get(
                        "week_ending", end_date.strftime("%Y-%m-%d")
                    ),
                    "overall_score": summary_data.get("overall_score", 80),
                    "key_achievements": summary_data.get(
                        "key_achievements",
                        [
                            f"Completed {completed_tasks} tasks this week",
                            "Maintained consistent productivity patterns",
                            "Kept up with your learning goals",
                        ],
                    ),
                    "areas_for_improvement": summary_data.get(
                        "areas_for_improvement",
                        [
                            "Consider adding more breaks between deep work sessions",
                            "Review your goals weekly to maintain focus",
                            "Optimize your morning routine",
                        ],
                    ),
                    "next_week_focus": summary_data.get(
                        "next_week_focus",
                        [
                            "Continue with your current productivity patterns",
                            "Focus on completing high-priority tasks first",
                            "Maintain your learning momentum",
                        ],
                    ),
                    "productivity_metrics": summary_data.get(
                        "productivity_metrics",
                        {
                            "focus_time": f"{len(schedule_blocks) * 2} hours",
                            "tasks_completed": completed_tasks,
                            "learning_sessions": len(
                                [
                                    s
                                    for s in schedule_blocks
                                    if s.get("context") == "Learning"
                                ]
                            ),
                            "habit_streak": 5,
                        },
                    ),
                    "ai_predictions": summary_data.get(
                        "ai_predictions",
                        {
                            "next_week_score": 85,
                            "confidence": 0.8,
                            "key_factors": [
                                "Consistent task completion",
                                "Good schedule adherence",
                            ],
                        },
                    ),
                }
            else:
                # Fallback summary
                weekly_summary = {
                    "week_ending": end_date.strftime("%Y-%m-%d"),
                    "overall_score": 80,
                    "key_achievements": [
                        f"Completed {completed_tasks} tasks this week",
                        "Maintained consistent productivity patterns",
                        "Kept up with your learning goals",
                    ],
                    "areas_for_improvement": [
                        "Consider adding more breaks between deep work sessions",
                        "Review your goals weekly to maintain focus",
                        "Optimize your morning routine",
                    ],
                    "next_week_focus": [
                        "Continue with your current productivity patterns",
                        "Focus on completing high-priority tasks first",
                        "Maintain your learning momentum",
                    ],
                    "productivity_metrics": {
                        "focus_time": f"{len(schedule_blocks) * 2} hours",
                        "tasks_completed": completed_tasks,
                        "learning_sessions": len(
                            [
                                s
                                for s in schedule_blocks
                                if s.get("context") == "Learning"
                            ]
                        ),
                        "habit_streak": 5,
                    },
                    "ai_predictions": {
                        "next_week_score": 85,
                        "confidence": 0.8,
                        "key_factors": [
                            "Consistent task completion",
                            "Good schedule adherence",
                        ],
                    },
                }
        except json.JSONDecodeError:
            # Fallback summary
            weekly_summary = {
                "week_ending": end_date.strftime("%Y-%m-%d"),
                "overall_score": 80,
                "key_achievements": [
                    f"Completed {completed_tasks} tasks this week",
                    "Maintained consistent productivity patterns",
                    "Kept up with your learning goals",
                ],
                "areas_for_improvement": [
                    "Consider adding more breaks between deep work sessions",
                    "Review your goals weekly to maintain focus",
                    "Optimize your morning routine",
                ],
                "next_week_focus": [
                    "Continue with your current productivity patterns",
                    "Focus on completing high-priority tasks first",
                    "Maintain your learning momentum",
                ],
                "productivity_metrics": {
                    "focus_time": f"{len(schedule_blocks) * 2} hours",
                    "tasks_completed": completed_tasks,
                    "learning_sessions": len(
                        [s for s in schedule_blocks if s.get("context") == "Learning"]
                    ),
                    "habit_streak": 5,
                },
                "ai_predictions": {
                    "next_week_score": 85,
                    "confidence": 0.8,
                    "key_factors": [
                        "Consistent task completion",
                        "Good schedule adherence",
                    ],
                },
            }

        return {"success": True, "weekly_summary": weekly_summary}
    except Exception as e:
        logging.error(f"Error generating weekly summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
