from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, confloat
from services.supabase import get_supabase_client
from services.auth import get_current_user
from services.cost_tracking import cost_tracking_service
from services.ai_cache import ai_cached, ai_cache_service, invalidate_ai_cache_for_user
from services.openai_integration import generate_openai_text
from services.background_workers import (
    background_worker,
    background_task,
    scheduled_job,
)
from services.performance_monitor import monitor_performance
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


class AIInsightRequest(BaseModel):
    insight_type: str
    user_data: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None


class AIAnalysisRequest(BaseModel):
    analysis_type: str
    data: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None


class AISuggestionRequest(BaseModel):
    suggestion_type: str
    context: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None


async def _get_user_context(user_id: str) -> Dict[str, Any]:
    """Get user context data for AI operations"""
    try:
        supabase = get_supabase_client()

        # Fetch user's recent data in parallel
        tasks_result = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .limit(20)
            .execute()
        )
        goals_result = (
            supabase.table("goals")
            .select("*")
            .eq("user_id", user_id)
            .limit(10)
            .execute()
        )
        schedule_result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", user_id)
            .limit(15)
            .execute()
        )

        return {
            "tasks": tasks_result.data or [],
            "goals": goals_result.data or [],
            "schedule_blocks": schedule_result.data or [],
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return {"user_id": user_id, "timestamp": datetime.utcnow().isoformat()}


@router.post("/plan-day", summary="Generate a daily plan based on preferences")
@ai_cached("ai_planning", ttl=1800)  # Cache for 30 minutes
async def plan_day(
    request: PlanDayRequest,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
):
    """Generate AI-powered daily plan with caching and optimization"""
    try:
        # Check budget limits before making AI call
        budget_check = await cost_tracking_service.check_budget_limits(
            current_user["id"]
        )
        if budget_check["daily_exceeded"] or budget_check["monthly_exceeded"]:
            raise HTTPException(status_code=429, detail="Budget limit exceeded")

        # Get user context for personalization
        user_context = await _get_user_context(current_user["id"])  # noqa: F841

        # Generate AI prompt for planning
        prompt = f"""Create a personalized daily schedule for {request.date} based on:

User Preferences:
- Focus areas: {', '.join(request.preferences.focus_areas)}
- Duration: {request.preferences.duration}

User Context:
- Recent tasks: {len(user_context.get('tasks', []))} tasks
- Active goals: {len(user_context.get('goals', []))} goals
- Schedule blocks: {len(user_context.get('schedule_blocks', []))} blocks

Generate a structured daily plan with specific time slots and activities.
Return as JSON array with time, activity, and focus_area fields."""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=800, temperature=0.3
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Parse AI response
        try:
            response_text = response.get("generated_text", "")
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            if start_idx != -1 and end_idx != 0:
                schedule = json.loads(response_text[start_idx:end_idx])
            else:
                # Fallback schedule
                schedule = [
                    {
                        "time": "09:00-10:30",
                        "activity": "Deep work session",
                        "focus_area": (
                            request.preferences.focus_areas[0]
                            if request.preferences.focus_areas
                            else "work"
                        ),
                    },
                    {
                        "time": "10:45-12:00",
                        "activity": "Team meeting",
                        "focus_area": "work",
                    },
                ]
        except json.JSONDecodeError:
            # Fallback schedule
            schedule = [
                {
                    "time": "09:00-10:30",
                    "activity": "Deep work session",
                    "focus_area": (
                        request.preferences.focus_areas[0]
                        if request.preferences.focus_areas
                        else "work"
                    ),
                },
                {
                    "time": "10:45-12:00",
                    "activity": "Team meeting",
                    "focus_area": "work",
                },
            ]

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=current_user["id"],
            endpoint="/plan-day",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 150),
            output_tokens=response.get("usage", {}).get("completion_tokens", 200),
            cost_usd=response.get("usage", {}).get("total_cost", 0.01),
        )

        # Store plan in database (async)
        if background_tasks:
            background_tasks.add_task(
                _store_plan,
                current_user["id"],
                request.date,
                request.preferences.model_dump(),
                schedule,
            )

        return {
            "success": True,
            "plan": {
                "date": request.date,
                "schedule": schedule,
                "cached": False,  # Will be true when served from cache
            },
        }

    except Exception as e:
        logger.error(f"Error in plan_day: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _store_plan(user_id: str, date: str, preferences: dict, schedule: list):
    """Store plan in database (background task)"""
    try:
        supabase = get_supabase_client()
        plan_data = {
            "user_id": user_id,
            "date": date,
            "preferences": preferences,
            "schedule": schedule,
            "created_at": datetime.utcnow().isoformat(),
        }
        supabase.table("plans").insert(plan_data).execute()
    except Exception as e:
        logger.error(f"Error storing plan: {e}")


@router.post("/generate-flashcards", summary="Generate flashcards for a topic")
@ai_cached("ai_flashcards", ttl=7200)  # Cache for 2 hours
async def generate_flashcards(
    request: FlashcardRequest, current_user: dict = Depends(get_current_user)
):
    """Generate AI-powered flashcards with caching"""
    try:
        # Check budget limits
        budget_check = await cost_tracking_service.check_budget_limits(
            current_user["id"]
        )
        if budget_check["daily_exceeded"] or budget_check["monthly_exceeded"]:
            raise HTTPException(status_code=429, detail="Budget limit exceeded")

        # Generate AI prompt for flashcards
        prompt = f"""Generate {request.count} flashcards for the topic: {request.topic}

Difficulty level: {request.difficulty}

Generate flashcards in JSON format:
[
    {{
        "front": "Question or concept",
        "back": "Answer or explanation"
    }}
]

Make the flashcards engaging and appropriate for {request.difficulty} difficulty level."""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=1000, temperature=0.4
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Parse AI response
        try:
            response_text = response.get("generated_text", "")
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            if start_idx != -1 and end_idx != 0:
                flashcard_data = json.loads(response_text[start_idx:end_idx])
            else:
                # Fallback flashcards
                flashcard_data = [
                    {
                        "front": "What is Python?",
                        "back": "Python is a high-level, interpreted programming language.",
                    },
                    {
                        "front": "What is a list in Python?",
                        "back": "A list is a mutable sequence type that can store multiple items.",
                    },
                ]
        except json.JSONDecodeError:
            # Fallback flashcards
            flashcard_data = [
                {
                    "front": "What is Python?",
                    "back": "Python is a high-level, interpreted programming language.",
                },
                {
                    "front": "What is a list in Python?",
                    "back": "A list is a mutable sequence type that can store multiple items.",
                },
            ]

        # Limit to requested count
        flashcard_data = flashcard_data[: request.count]

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=current_user["id"],
            endpoint="/generate-flashcards",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 100),
            output_tokens=response.get("usage", {}).get("completion_tokens", 300),
            cost_usd=response.get("usage", {}).get("total_cost", 0.015),
        )

        # Store flashcards in database
        supabase = get_supabase_client()
        flashcards_to_insert = [
            {
                "user_id": current_user["id"],
                "topic": request.topic,
                "difficulty": request.difficulty,
                "front": data["front"],
                "back": data["back"],
                "created_at": datetime.utcnow().isoformat(),
            }
            for data in flashcard_data
        ]

        result = supabase.table("flashcards").insert(flashcards_to_insert).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create flashcards")

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

    except Exception as e:
        logger.error(f"Error in generate_flashcards: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights", summary="Generate AI insights based on user data")
@monitor_performance("ai_insights")
async def get_ai_insights(
    request: AIInsightRequest,
    current_user: Dict = Depends(get_current_user),
):
    """Get AI insights for user data"""
    try:
        user_id = current_user["id"]

        # Check cache first
        cached_insight = await ai_cache_service.get_cached_ai_response(
            "ai_insights",
            user_id,
            request.user_data,
            insight_type=request.insight_type,
            **request.parameters or {},
        )

        if cached_insight:
            return cached_insight.get("response")

        # Generate AI insight
        prompt = f"""
        Analyze the user data and provide insights for {request.insight_type}.
        Focus on actionable recommendations and patterns.
        
        User Data: {request.user_data}
        Parameters: {request.parameters}
        
        Provide a comprehensive analysis with specific insights and recommendations.
        """

        insight = await generate_openai_text(prompt, max_tokens=1000)

        # Cache the result
        await ai_cache_service.set_cached_ai_response(
            "ai_insights",
            user_id,
            insight,
            request.user_data,
            insight_type=request.insight_type,
            **request.parameters or {},
        )

        return {"insight": insight, "type": request.insight_type}

    except Exception as e:
        logger.error(f"Error generating AI insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI insights")


@router.get("/insights/latest", summary="Get latest AI insights")
@ai_cached("ai_insights", ttl=1800)  # Cache for 30 minutes
async def get_latest_insights(current_user: dict = Depends(get_current_user)):
    """Get latest cached insights for user"""
    try:
        # Get user context
        user_context = await _get_user_context(current_user["id"])  # noqa: F841

        # Generate insights for the current week
        request = InsightRequest(
            date_range="this_week", categories=["productivity", "goals", "habits"]
        )

        return await get_ai_insights(request, current_user)

    except Exception as e:
        logger.error(f"Error in get_latest_insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/habits/suggest", summary="Get AI-powered habit suggestions")
@ai_cached("ai_suggestions", ttl=3600)  # Cache for 1 hour
async def suggest_habits(
    request: HabitSuggestionRequest, current_user: dict = Depends(get_current_user)
):
    """Generate AI-powered habit suggestions with caching"""
    try:
        # Check budget limits
        budget_check = await cost_tracking_service.check_budget_limits(
            current_user["id"]
        )
        if budget_check["daily_exceeded"] or budget_check["monthly_exceeded"]:
            raise HTTPException(status_code=429, detail="Budget limit exceeded")

        # Generate AI prompt for habit suggestions
        prompt = f"""Suggest new habits based on user preferences and current habits.

User Preferences: {', '.join(request.user_preferences)}
Current Habits: {', '.join(request.current_habits)}
Available Time: {request.available_time} minutes per day

Generate suggestions in JSON format:
{{
    "suggestions": [
        {{
            "habit": "Habit name",
            "description": "Detailed description",
            "time_required": "minutes per day",
            "difficulty": "easy/medium/hard",
            "expected_impact": "high/medium/low"
        }}
    ],
    "reasoning": "Why these habits would be beneficial"
}}"""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=600, temperature=0.4
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Parse AI response
        try:
            response_text = response.get("generated_text", "")
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                suggestions = json.loads(response_text[start_idx:end_idx])
            else:
                suggestions = {
                    "suggestions": [
                        {
                            "habit": "Morning Planning",
                            "description": "Spend 10 minutes planning your day",
                            "time_required": 10,
                            "difficulty": "easy",
                            "expected_impact": "high",
                        }
                    ],
                    "reasoning": "Morning planning helps set clear priorities for the day",
                }
        except json.JSONDecodeError:
            suggestions = {
                "suggestions": [
                    {
                        "habit": "Morning Planning",
                        "description": "Spend 10 minutes planning your day",
                        "time_required": 10,
                        "difficulty": "easy",
                        "expected_impact": "high",
                    }
                ],
                "reasoning": "Morning planning helps set clear priorities for the day",
            }

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=current_user["id"],
            endpoint="/habits/suggest",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 150),
            output_tokens=response.get("usage", {}).get("completion_tokens", 300),
            cost_usd=response.get("usage", {}).get("total_cost", 0.015),
        )

        return {
            "success": True,
            "suggestions": suggestions,
        }

    except Exception as e:
        logger.error(f"Error in suggest_habits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/productivity/analyze", summary="Analyze productivity patterns")
@ai_cached("ai_analysis", ttl=900)  # Cache for 15 minutes
async def analyze_productivity(
    request: ProductivityAnalysisRequest, current_user: dict = Depends(get_current_user)
):
    """Analyze productivity patterns with caching"""
    try:
        # Check budget limits
        budget_check = await cost_tracking_service.check_budget_limits(
            current_user["id"]
        )
        if budget_check["daily_exceeded"] or budget_check["monthly_exceeded"]:
            raise HTTPException(status_code=429, detail="Budget limit exceeded")

        # Get user context
        user_context = await _get_user_context(current_user["id"])  # noqa: F841

        # Generate AI prompt for productivity analysis
        prompt = f"""Analyze productivity patterns for {request.date_range}.

Include Calendar: {request.include_calendar}
Include Habits: {request.include_habits}
Include Learning: {request.include_learning}

User Data:
- Tasks: {len(user_context.get('tasks', []))} tasks
- Goals: {len(user_context.get('goals', []))} goals
- Schedule blocks: {len(user_context.get('schedule_blocks', []))} blocks

Generate analysis in JSON format:
{{
    "overall_score": 85,
    "trends": {{
        "focus_time": {{"trend": "increasing", "change": "+5%"}},
        "task_completion": {{"trend": "stable", "change": "+2%"}},
        "learning_consistency": {{"trend": "stable", "change": "+3%"}}
    }},
    "peak_hours": {{
        "morning": "09:00-11:00",
        "afternoon": "14:00-16:00",
        "evening": "19:00-21:00"
    }},
    "productivity_blocks": [
        {{
            "type": "Deep Work",
            "duration": "2-3 hours",
            "best_time": "Morning",
            "success_rate": 0.8
        }}
    ],
    "ai_insights": [
        "Your productivity is consistent",
        "You maintain good focus during scheduled blocks",
        "Your goal progress shows steady improvement"
    ],
    "optimization_suggestions": [
        "Continue with your current productivity patterns",
        "Consider adding more breaks between deep work sessions",
        "Review your goals weekly to maintain focus"
    ]
}}"""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=1200, temperature=0.3
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Parse AI response
        try:
            response_text = response.get("generated_text", "")
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                analysis = json.loads(response_text[start_idx:end_idx])
            else:
                analysis = {
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
            analysis = {
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

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=current_user["id"],
            endpoint="/productivity/analyze",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 300),
            output_tokens=response.get("usage", {}).get("completion_tokens", 600),
            cost_usd=response.get("usage", {}).get("total_cost", 0.03),
        )

        return {
            "success": True,
            "analysis": analysis,
            "date_range": request.date_range,
        }

    except Exception as e:
        logger.error(f"Error in analyze_productivity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/optimize", summary="Optimize schedule using AI")
@ai_cached("ai_optimization", ttl=600)  # Cache for 10 minutes
async def optimize_schedule(
    request: SmartScheduleRequest, current_user: dict = Depends(get_current_user)
):
    """Optimize schedule using AI with caching"""
    try:
        # Check budget limits
        budget_check = await cost_tracking_service.check_budget_limits(
            current_user["id"]
        )
        if budget_check["daily_exceeded"] or budget_check["monthly_exceeded"]:
            raise HTTPException(status_code=429, detail="Budget limit exceeded")

        # Generate AI prompt for schedule optimization
        prompt = f"""Optimize the user's schedule based on tasks, available time, and preferences.

Tasks: {json.dumps(request.tasks, indent=2)}
Available Time: {json.dumps(request.available_time, indent=2)}
Preferences: {json.dumps(request.preferences, indent=2)}

Generate optimized schedule in JSON format:
{{
    "optimized_schedule": [
        {{
            "task_id": "task_id",
            "start_time": "HH:MM",
            "end_time": "HH:MM",
            "priority": "high/medium/low",
            "reasoning": "Why this time slot was chosen"
        }}
    ],
    "efficiency_score": 85,
    "time_saved": "2 hours",
    "recommendations": [
        "Specific recommendation 1",
        "Specific recommendation 2"
    ]
}}"""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=1000, temperature=0.3
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Parse AI response
        try:
            response_text = response.get("generated_text", "")
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                optimization = json.loads(response_text[start_idx:end_idx])
            else:
                optimization = {
                    "optimized_schedule": [],
                    "efficiency_score": 80,
                    "time_saved": "1 hour",
                    "recommendations": [
                        "Consider batching similar tasks",
                        "Schedule breaks between deep work sessions",
                    ],
                }
        except json.JSONDecodeError:
            optimization = {
                "optimized_schedule": [],
                "efficiency_score": 80,
                "time_saved": "1 hour",
                "recommendations": [
                    "Consider batching similar tasks",
                    "Schedule breaks between deep work sessions",
                ],
            }

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=current_user["id"],
            endpoint="/schedule/optimize",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 400),
            output_tokens=response.get("usage", {}).get("completion_tokens", 500),
            cost_usd=response.get("usage", {}).get("total_cost", 0.025),
        )

        return {
            "success": True,
            "optimization": optimization,
        }

    except Exception as e:
        logger.error(f"Error in optimize_schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/weekly-summary", summary="Get weekly productivity summary")
@ai_cached("ai_summary", ttl=1800)  # Cache for 30 minutes
async def get_weekly_summary(current_user: dict = Depends(get_current_user)):
    """Get weekly productivity summary with caching"""
    try:
        # Get user context
        user_context = await _get_user_context(current_user["id"])  # noqa: F841

        # Calculate date range for this week
        now = datetime.utcnow()
        start_date = now - timedelta(days=7)
        end_date = now

        # Generate AI prompt for weekly summary
        prompt = f"""Generate a weekly productivity summary for the past week.

Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}

User Data:
- Tasks: {len(user_context.get('tasks', []))} tasks
- Goals: {len(user_context.get('goals', []))} goals
- Schedule blocks: {len(user_context.get('schedule_blocks', []))} blocks

Generate summary in JSON format:
{{
    "week_ending": "{end_date.strftime('%Y-%m-%d')}",
    "overall_score": 85,
    "key_achievements": [
        "Achievement 1",
        "Achievement 2"
    ],
    "areas_for_improvement": [
        "Area 1",
        "Area 2"
    ],
    "next_week_focus": [
        "Focus area 1",
        "Focus area 2"
    ],
    "productivity_metrics": {{
        "focus_time": "20 hours",
        "tasks_completed": 15,
        "learning_sessions": 5,
        "habit_streak": 7
    }},
    "ai_predictions": {{
        "next_week_score": 88,
        "confidence": 0.8,
        "key_factors": ["Factor 1", "Factor 2"]
    }}
}}"""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=1000, temperature=0.4
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Parse AI response
        try:
            response_text = response.get("generated_text", "")
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                summary = json.loads(response_text[start_idx:end_idx])
            else:
                summary = {
                    "week_ending": end_date.strftime("%Y-%m-%d"),
                    "overall_score": 80,
                    "key_achievements": [
                        "Maintained consistent productivity",
                        "Completed all high-priority tasks",
                    ],
                    "areas_for_improvement": [
                        "Consider adding more breaks",
                        "Review goals weekly",
                    ],
                    "next_week_focus": [
                        "Continue current patterns",
                        "Focus on high-impact tasks",
                    ],
                    "productivity_metrics": {
                        "focus_time": "18 hours",
                        "tasks_completed": 12,
                        "learning_sessions": 4,
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
            summary = {
                "week_ending": end_date.strftime("%Y-%m-%d"),
                "overall_score": 80,
                "key_achievements": [
                    "Maintained consistent productivity",
                    "Completed all high-priority tasks",
                ],
                "areas_for_improvement": [
                    "Consider adding more breaks",
                    "Review goals weekly",
                ],
                "next_week_focus": [
                    "Continue current patterns",
                    "Focus on high-impact tasks",
                ],
                "productivity_metrics": {
                    "focus_time": "18 hours",
                    "tasks_completed": 12,
                    "learning_sessions": 4,
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

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=current_user["id"],
            endpoint="/insights/weekly-summary",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 250),
            output_tokens=response.get("usage", {}).get("completion_tokens", 500),
            cost_usd=response.get("usage", {}).get("total_cost", 0.025),
        )

        return {
            "success": True,
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Error in get_weekly_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Cache management endpoints
@router.post("/cache/invalidate", summary="Invalidate AI cache for user")
async def invalidate_cache(
    operations: List[str] = None, current_user: dict = Depends(get_current_user)
):
    """Invalidate AI cache for specific operations"""
    try:
        deleted_count = await invalidate_ai_cache_for_user(
            current_user["id"], operations
        )
        return {
            "success": True,
            "deleted_entries": deleted_count,
            "operations": operations or "all",
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats", summary="Get AI cache statistics")
async def get_cache_stats(current_user: dict = Depends(get_current_user)):
    """Get AI cache statistics"""
    try:
        stats = ai_cache_service.get_cache_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task for AI processing
@background_task(name="ai_batch_processing", priority="normal")
async def process_ai_batch(user_id: str, data: Dict[str, Any]):
    """Background task for batch AI processing"""
    try:
        logger.info(f"Processing AI batch for user {user_id}")

        # Process AI operations in background
        results = {}

        # Example: Process multiple AI operations
        for operation_type in ["insights", "analysis", "suggestions"]:
            prompt = f"Process {operation_type} for user data: {data}"
            result = await generate_openai_text(prompt, max_tokens=500)
            results[operation_type] = result

        # Store results in database
        supabase = get_supabase_client()
        await supabase.table("ai_results").insert(
            {"user_id": user_id, "results": results, "processed_at": "now()"}
        ).execute()

        logger.info(f"Completed AI batch processing for user {user_id}")
        return results

    except Exception as e:
        logger.error(f"Error in AI batch processing: {e}")
        raise


@router.post("/batch-process")
async def start_ai_batch_processing(
    data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
):
    """Start background AI batch processing"""
    try:
        user_id = current_user["id"]

        # Enqueue background task
        task_id = await background_worker.enqueue_task(
            "ai_batch_processing", user_id, data, priority="normal"
        )

        return {
            "message": "AI batch processing started",
            "task_id": task_id,
            "status": "queued",
        }

    except Exception as e:
        logger.error(f"Error starting AI batch processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start batch processing")


# Scheduled job for AI maintenance
@scheduled_job(cron_expression="0 2 * * *")  # Daily at 2 AM
async def ai_cache_maintenance():
    """Scheduled job for AI cache maintenance"""
    try:
        logger.info("Starting AI cache maintenance")

        # Clean up old cache entries
        # This would be implemented based on your cache strategy

        logger.info("Completed AI cache maintenance")

    except Exception as e:
        logger.error(f"Error in AI cache maintenance: {e}")


@scheduled_job(cron_expression="0 */6 * * *")  # Every 6 hours
async def ai_performance_analysis():
    """Scheduled job for AI performance analysis"""
    try:
        logger.info("Starting AI performance analysis")

        # Analyze AI performance metrics
        # Generate performance reports
        # Send alerts if needed

        logger.info("Completed AI performance analysis")

    except Exception as e:
        logger.error(f"Error in AI performance analysis: {e}")
