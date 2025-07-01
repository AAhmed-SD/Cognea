from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks, Request
from models.text import TextGenerationRequest, TextGenerationResponse
from services.openai_integration import generate_openai_text
from services.ai_cache import ai_cached, ai_cache_service
from services.cost_tracking import cost_tracking_service
import logging
import os
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import aioredis
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.supabase import get_supabase_client
from services.auth import get_current_user

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the rate limiter
limiter = Limiter(key_func=get_remote_address)


# Placeholder for API key authentication
async def api_key_auth(api_key: str = Header(...)):
    # Example logic to validate API key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if api_key != OPENAI_API_KEY:
        logging.warning("Invalid API Key")
        raise HTTPException(status_code=403, detail="Not authenticated")
    return api_key


# Initialize Redis client for caching
async def get_redis_client():
    return await aioredis.create_redis_pool("redis://localhost")


async def _get_user_context(user_id: str) -> Dict[str, Any]:
    """Get user context data for AI operations"""
    try:
        supabase = get_supabase_client()
        
        # Fetch user's recent data in parallel
        tasks_result = supabase.table("tasks").select("*").eq("user_id", user_id).limit(20).execute()
        goals_result = supabase.table("goals").select("*").eq("user_id", user_id).limit(10).execute()
        schedule_result = supabase.table("schedule_blocks").select("*").eq("user_id", user_id).limit(15).execute()
        
        return {
            "tasks": tasks_result.data or [],
            "goals": goals_result.data or [],
            "schedule_blocks": schedule_result.data or [],
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return {"user_id": user_id, "timestamp": datetime.utcnow().isoformat()}


@router.post(
    "/generate-text",
    response_model=TextGenerationResponse,
    tags=["Text Generation"],
    summary="Generate text using OpenAI API",
)
@limiter.limit("5/minute")
@ai_cached("text_generation", ttl=3600)  # Cache for 1 hour
async def generate_text_endpoint(
    request: Request,
    request_data: TextGenerationRequest,
    api_key: str = Depends(api_key_auth),
):
    """Generate text with caching and optimization"""
    try:
        # Check budget limits
        budget_check = await cost_tracking_service.check_budget_limits(request_data.user_id)
        if budget_check["daily_exceeded"] or budget_check["monthly_exceeded"]:
            raise HTTPException(status_code=429, detail="Budget limit exceeded")

        logging.debug(f"Received request: {request_data}")
        
        # Call OpenAI API
        response = await generate_openai_text(
            prompt=request_data.prompt,
            model=request_data.model,
            max_tokens=request_data.max_tokens,
            temperature=request_data.temperature,
            stop=request_data.stop,
        )
        
        if "error" in response:
            logging.warning(f"Error in text generation: {response['error']}")
            raise HTTPException(status_code=500, detail=response["error"])
        
        logging.info(f"Generated text: {response['generated_text']}")
        
        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=request_data.user_id,
            endpoint="/generate-text",
            model=request_data.model,
            input_tokens=response.get("usage", {}).get("prompt_tokens", 100),
            output_tokens=response.get("usage", {}).get("completion_tokens", 200),
            cost_usd=response.get("usage", {}).get("total_cost", 0.01),
        )
        
        response_obj = TextGenerationResponse(
            original_prompt=request_data.prompt,
            model=request_data.model,
            generated_text=response["generated_text"],
            total_tokens=response["total_tokens"],
        )

        return response_obj
        
    except Exception as e:
        logging.error(f"Unhandled exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Define the request model for input validation
class DailyBriefRequest(BaseModel):
    date: str
    user_id: int


# Function to process the daily brief
async def process_daily_brief(date: str, user_id: int):
    """Process daily brief in background"""
    try:
        logging.info(f"Processing daily brief for user {user_id} on {date}")
        
        # Get user context
        user_context = await _get_user_context(str(user_id))
        
        # Generate AI prompt for daily brief
        prompt = f"""Generate a daily brief for {date} based on user data:

User Context:
- Tasks: {len(user_context.get('tasks', []))} tasks
- Goals: {len(user_context.get('goals', []))} goals
- Schedule blocks: {len(user_context.get('schedule_blocks', []))} blocks

Generate a concise daily summary in JSON format:
{{
    "summary": "Brief overview of the day",
    "key_tasks": ["Task 1", "Task 2"],
    "focus_areas": ["Area 1", "Area 2"],
    "energy_level": "high/medium/low",
    "recommendations": ["Recommendation 1", "Recommendation 2"]
}}"""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt,
            model="gpt-4-turbo-preview",
            max_tokens=400,
            temperature=0.3
        )

        if "error" not in response:
            # Store brief in database
            supabase = get_supabase_client()
            brief_data = {
                "user_id": str(user_id),
                "date": date,
                "brief": response.get("generated_text", ""),
                "created_at": datetime.utcnow().isoformat(),
            }
            supabase.table("daily_briefs").insert(brief_data).execute()
            
            # Track API usage
            await cost_tracking_service.track_api_call(
                user_id=str(user_id),
                endpoint="/daily-brief",
                model="gpt-4-turbo-preview",
                input_tokens=response.get("usage", {}).get("prompt_tokens", 100),
                output_tokens=response.get("usage", {}).get("completion_tokens", 200),
                cost_usd=response.get("usage", {}).get("total_cost", 0.01),
            )
            
    except Exception as e:
        logger.error(f"Error processing daily brief: {e}")


@router.post(
    "/daily-brief",
    summary="Generate Daily Brief",
    description="Generates a daily summary of tasks.",
)
@limiter.limit("5/minute")
@ai_cached("daily_brief", ttl=1800)  # Cache for 30 minutes
async def generate_daily_brief(
    request: Request,
    request_data: DailyBriefRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Generate AI-powered daily brief with caching"""
    try:
        logging.info("Generating daily brief")
        
        # Add the task to be processed in the background
        background_tasks.add_task(
            process_daily_brief, request_data.date, current_user["id"]
        )
        
        return {"message": "Daily brief is being generated."}
        
    except Exception as e:
        logging.error(f"Error generating daily brief: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Define the request model for input validation
class QuizMeRequest(BaseModel):
    deck_id: int


# Function to generate quiz questions
async def generate_quiz_questions(deck_id: int, user_id: str):
    """Generate AI-powered quiz questions"""
    try:
        logging.info(f"Generating quiz for deck {deck_id}")
        
        # Get flashcards for the deck
        supabase = get_supabase_client()
        flashcards_result = supabase.table("flashcards").select("*").eq("deck_id", deck_id).eq("user_id", user_id).limit(10).execute()
        
        flashcards = flashcards_result.data or []
        
        if not flashcards:
            return [
                {"question": "What is the capital of France?", "answer": "Paris"},
                {"question": "What is 2 + 2?", "answer": "4"},
                {"question": "What is the boiling point of water?", "answer": "100°C"},
            ]
        
        # Generate AI prompt for quiz questions
        prompt = f"""Generate 3-5 quiz questions based on these flashcards:

Flashcards: {json.dumps([f.get('front', '') for f in flashcards[:5]], indent=2)}

Generate questions in JSON format:
[
    {{
        "question": "Question text",
        "answer": "Correct answer",
        "difficulty": "easy/medium/hard"
    }}
]

Make questions engaging and test understanding of the concepts."""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt,
            model="gpt-4-turbo-preview",
            max_tokens=600,
            temperature=0.4
        )

        if "error" in response:
            # Fallback questions
            return [
                {"question": "What is the capital of France?", "answer": "Paris"},
                {"question": "What is 2 + 2?", "answer": "4"},
                {"question": "What is the boiling point of water?", "answer": "100°C"},
            ]

        # Parse AI response
        try:
            response_text = response.get("generated_text", "")
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            if start_idx != -1 and end_idx != 0:
                questions = json.loads(response_text[start_idx:end_idx])
            else:
                questions = [
                    {"question": "What is the capital of France?", "answer": "Paris"},
                    {"question": "What is 2 + 2?", "answer": "4"},
                    {"question": "What is the boiling point of water?", "answer": "100°C"},
                ]
        except json.JSONDecodeError:
            questions = [
                {"question": "What is the capital of France?", "answer": "Paris"},
                {"question": "What is 2 + 2?", "answer": "4"},
                {"question": "What is the boiling point of water?", "answer": "100°C"},
            ]

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=user_id,
            endpoint="/quiz-me",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 150),
            output_tokens=response.get("usage", {}).get("completion_tokens", 300),
            cost_usd=response.get("usage", {}).get("total_cost", 0.015),
        )

        return questions
        
    except Exception as e:
        logger.error(f"Error generating quiz questions: {e}")
        return [
            {"question": "What is the capital of France?", "answer": "Paris"},
            {"question": "What is 2 + 2?", "answer": "4"},
            {"question": "What is the boiling point of water?", "answer": "100°C"},
        ]


@router.post(
    "/quiz-me",
    summary="Generate Quiz Questions",
    description="Takes a deck ID and returns 3–5 questions from that deck to quiz the user.",
)
@ai_cached("quiz_questions", ttl=1800)  # Cache for 30 minutes
async def quiz_me(
    request: Request,
    request_data: QuizMeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate AI-powered quiz questions with caching"""
    try:
        logging.info("Generating quiz questions")
        questions = await generate_quiz_questions(request_data.deck_id, current_user["id"])
        return {"questions": questions}
    except Exception as e:
        logging.error(f"Error generating quiz questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Define the request model for input validation
class SummarizeNotesRequest(BaseModel):
    notes: str
    summary_type: Optional[str] = "TL;DR"
    user_id: Optional[int] = None


# Function to split text into manageable chunks
async def split_into_chunks(text: str, max_tokens: int = 1000) -> List[str]:
    """Split text into manageable chunks for processing"""
    logging.info("Splitting text into chunks")
    # Simple splitting by sentences or paragraphs
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk + sentence) > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                chunks.append(sentence)
        else:
            current_chunk += sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]


# Function to summarize notes
async def summarize_notes(notes: str, summary_type: str, user_id: str) -> str:
    """Generate AI-powered note summarization"""
    try:
        logging.info(f"Summarizing notes with summary type: {summary_type}")
        
        # Generate AI prompt for summarization
        prompt = f"""Summarize the following notes in {summary_type} format:

Notes: {notes[:2000]}  # Limit to avoid token limits

Generate a concise summary that captures the key points and main ideas.
Focus on clarity and actionable insights."""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt,
            model="gpt-4-turbo-preview",
            max_tokens=500,
            temperature=0.3
        )

        if "error" in response:
            return f"Summary ({summary_type}): {notes[:100]}..."

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=user_id,
            endpoint="/summarize-notes",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 200),
            output_tokens=response.get("usage", {}).get("completion_tokens", 300),
            cost_usd=response.get("usage", {}).get("total_cost", 0.02),
        )

        return response.get("generated_text", f"Summary ({summary_type}): {notes[:100]}...")
        
    except Exception as e:
        logger.error(f"Error summarizing notes: {e}")
        return f"Summary ({summary_type}): {notes[:100]}..."


@router.post(
    "/summarize-notes",
    summary="Summarize Notes",
    description="Compress long notes into key takeaways.",
)
@limiter.limit("5/minute")
@ai_cached("note_summarization", ttl=3600)  # Cache for 1 hour
async def summarize_notes_endpoint(
    request: SummarizeNotesRequest, current_user: dict = Depends(get_current_user)
):
    """Summarize notes with AI and caching"""
    try:
        # Input size validation
        if len(request.notes) > 5000:  # Example limit
            logging.warning(
                f"User {current_user['id']} submitted notes exceeding size limit: {len(request.notes)} characters"
            )
            raise HTTPException(
                status_code=400,
                detail="Notes exceed the maximum allowed size of 5000 characters.",
            )

        logging.info(
            f"User {current_user['id']} is summarizing notes of length {len(request.notes)}"
        )
        
        chunks = await split_into_chunks(request.notes)
        summaries = [
            await summarize_notes(chunk, request.summary_type, current_user["id"]) 
            for chunk in chunks
        ]
        
        return {"summaries": summaries}
        
    except Exception as e:
        logging.error(
            f"Error summarizing notes for user {current_user['id']}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


# Define the request model for input validation
class SuggestRescheduleRequest(BaseModel):
    task_title: str
    reason_missed: Optional[str]
    task_deadline: Optional[str]
    task_duration_minutes: Optional[int]
    energy_level: Optional[str]  # low, medium, high
    user_schedule_context: Optional[str]  # e.g., "Fully booked on Thursday"


# Define the response model
class RescheduleSuggestion(BaseModel):
    suggested_time: str
    reason: str
    alternative_times: Optional[List[str]] = None


# Function to suggest a reschedule time
async def suggest_reschedule_logic(
    request: SuggestRescheduleRequest,
    user_id: str
) -> RescheduleSuggestion:
    """Generate AI-powered reschedule suggestions"""
    try:
        logging.info(f"Suggesting reschedule for task: {request.task_title}")
        
        # Get user context
        user_context = await _get_user_context(user_id)
        
        # Generate AI prompt for rescheduling
        prompt = f"""Suggest an optimal reschedule time for this task:

Task: {request.task_title}
Reason missed: {request.reason_missed or 'Not specified'}
Deadline: {request.task_deadline or 'Not specified'}
Duration: {request.task_duration_minutes or 60} minutes
Energy level: {request.energy_level or 'medium'}
Schedule context: {request.user_schedule_context or 'No specific constraints'}

User's recent schedule: {len(user_context.get('schedule_blocks', []))} blocks

Generate suggestion in JSON format:
{{
    "suggested_time": "Specific time recommendation",
    "reason": "Why this time is optimal",
    "alternative_times": ["Alternative 1", "Alternative 2"]
}}

Consider energy levels, deadlines, and existing commitments."""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt,
            model="gpt-4-turbo-preview",
            max_tokens=400,
            temperature=0.3
        )

        if "error" in response:
            # Fallback suggestion
            return RescheduleSuggestion(
                suggested_time="Friday, 9:00 AM - 10:30 AM",
                reason="Closer to the deadline. User has higher focus in the morning and Friday is still open."
            )

        # Parse AI response
        try:
            response_text = response.get("generated_text", "")
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                suggestion_data = json.loads(response_text[start_idx:end_idx])
                return RescheduleSuggestion(
                    suggested_time=suggestion_data.get("suggested_time", "Friday, 9:00 AM - 10:30 AM"),
                    reason=suggestion_data.get("reason", "Optimal time based on your schedule"),
                    alternative_times=suggestion_data.get("alternative_times", [])
                )
            else:
                return RescheduleSuggestion(
                    suggested_time="Friday, 9:00 AM - 10:30 AM",
                    reason="Closer to the deadline. User has higher focus in the morning and Friday is still open."
                )
        except json.JSONDecodeError:
            return RescheduleSuggestion(
                suggested_time="Friday, 9:00 AM - 10:30 AM",
                reason="Closer to the deadline. User has higher focus in the morning and Friday is still open."
            )

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=user_id,
            endpoint="/suggest-reschedule",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 150),
            output_tokens=response.get("usage", {}).get("completion_tokens", 200),
            cost_usd=response.get("usage", {}).get("total_cost", 0.01),
        )
        
    except Exception as e:
        logger.error(f"Error suggesting reschedule: {e}")
        return RescheduleSuggestion(
            suggested_time="Friday, 9:00 AM - 10:30 AM",
            reason="Closer to the deadline. User has higher focus in the morning and Friday is still open."
        )


@router.post(
    "/suggest-reschedule",
    summary="Suggest Reschedule Time",
    description="Suggest an optimal new time for a missed or rescheduled task based on context.",
)
@limiter.limit("5/minute")
@ai_cached("reschedule_suggestion", ttl=900)  # Cache for 15 minutes
async def suggest_reschedule_endpoint(
    request: SuggestRescheduleRequest, current_user: dict = Depends(get_current_user)
):
    """Suggest reschedule time with AI and caching"""
    try:
        logging.info(f"User {current_user['id']} requesting reschedule suggestion")
        suggestion = await suggest_reschedule_logic(request, current_user["id"])
        return suggestion
    except Exception as e:
        logging.error(
            f"Error suggesting reschedule for user {current_user['id']}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


# Define the request model for input validation
class ExtractTasksRequest(BaseModel):
    text: str
    goal_context: Optional[str] = None  # Optional: Help AI link tasks to goals


# Define the response model
class ExtractedTask(BaseModel):
    task: str
    priority: Optional[str] = "medium"
    time_estimate_minutes: Optional[int] = None
    goal: Optional[str] = None


# Define the response model
class ExtractTasksResponse(BaseModel):
    extracted_tasks: List[ExtractedTask]


@router.post(
    "/extract-tasks-from-text",
    response_model=ExtractTasksResponse,
    summary="Extract structured tasks from messy notes",
    tags=["AI Tasks & Memory"],
)
@ai_cached("task_extraction", ttl=1800)  # Cache for 30 minutes
async def extract_tasks(
    request: ExtractTasksRequest, current_user: dict = Depends(get_current_user)
):
    """Extract tasks from text with AI and caching"""
    try:
        logging.info(f"User {current_user['id']} extracting tasks from text")

        # Generate AI prompt for task extraction
        prompt = f"""Extract structured tasks from the following text and return them as a JSON array:

Text: {request.text}

{f"Goal Context: {request.goal_context}" if request.goal_context else ""}

For each task, provide:
- task: A clear, actionable task description
- priority: "high", "medium", or "low" based on urgency and importance
- time_estimate_minutes: Estimated time to complete in minutes
- goal: The goal this task relates to (if any)

Return the response as a valid JSON array like this:
[
    {{
        "task": "Complete project proposal",
        "priority": "high",
        "time_estimate_minutes": 120,
        "goal": "Finish Q1 deliverables"
    }}
]

Focus on extracting actionable, specific tasks rather than general statements."""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=1000, temperature=0.3
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=current_user["id"],
            endpoint="/extract-tasks-from-text",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 200),
            output_tokens=response.get("usage", {}).get("completion_tokens", 400),
            cost_usd=response.get("usage", {}).get("total_cost", 0.02),
        )

        # Parse the response
        try:
            response_text = response.get("generated_text", "")
            # Extract JSON from the response
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                tasks_data = json.loads(json_str)

                extracted_tasks = [
                    ExtractedTask(
                        task=task.get("task", "Unknown task"),
                        priority=task.get("priority", "medium"),
                        time_estimate_minutes=task.get("time_estimate_minutes", 30),
                        goal=task.get("goal", request.goal_context),
                    )
                    for task in tasks_data
                ]
            else:
                # Fallback if JSON parsing fails
                extracted_tasks = [
                    ExtractedTask(
                        task="Failed to parse tasks from text",
                        priority="medium",
                        time_estimate_minutes=30,
                        goal=request.goal_context,
                    )
                ]
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            extracted_tasks = [
                ExtractedTask(
                    task="Failed to parse tasks from text",
                    priority="medium",
                    time_estimate_minutes=30,
                    goal=request.goal_context,
                )
            ]

        return ExtractTasksResponse(extracted_tasks=extracted_tasks)
    except Exception as e:
        logging.error(f"Error extracting tasks for user {current_user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Define the request model for input validation
class PlanMyDayRequest(BaseModel):
    user_id: str
    date: str  # e.g. "2025-06-06"
    focus_hours: Optional[List[str]] = None  # e.g. ["09:00-12:00", "14:00-17:00"]
    include_reflections: Optional[bool] = False
    preferred_working_hours: Optional[List[str]] = (
        None  # e.g. ["08:00-12:00", "13:00-17:00"]
    )
    break_times: Optional[List[str]] = None  # e.g. ["12:00-13:00"]


# Define the response model
class TimeBlock(BaseModel):
    start_time: str
    end_time: str
    task_name: str
    task_id: Optional[str]
    goal: Optional[str]
    priority: Optional[str]


# Define the response model
class PlanMyDayResponse(BaseModel):
    date: str
    user_id: str
    timeblocks: List[TimeBlock]
    notes: Optional[str]  # Optional summary or planning AI notes


@router.post(
    "/plan-my-day",
    response_model=PlanMyDayResponse,
    tags=["Planning"],
    summary="AI-generated daily plan",
)
@ai_cached("daily_planning", ttl=1800)  # Cache for 30 minutes
async def plan_my_day(
    request: PlanMyDayRequest, current_user: dict = Depends(get_current_user)
):
    """Generate AI-powered daily plan with caching"""
    try:
        logging.info(f"User {current_user['id']} requesting daily plan")
        
        # Get user context
        user_context = await _get_user_context(current_user["id"])
        
        # Generate AI prompt for daily planning
        prompt = f"""Create a personalized daily schedule for {request.date} based on:

User Preferences:
- Focus hours: {request.focus_hours or 'Not specified'}
- Preferred working hours: {request.preferred_working_hours or 'Not specified'}
- Break times: {request.break_times or 'Not specified'}

User Context:
- Recent tasks: {len(user_context.get('tasks', []))} tasks
- Active goals: {len(user_context.get('goals', []))} goals
- Schedule blocks: {len(user_context.get('schedule_blocks', []))} blocks

Generate a structured daily plan in JSON format:
{{
    "timeblocks": [
        {{
            "start_time": "09:00",
            "end_time": "10:30",
            "task_name": "Morning Focus Session",
            "task_id": "task1",
            "goal": "Productivity",
            "priority": "high"
        }}
    ],
    "notes": "AI-generated plan based on your preferences and current tasks"
}}"""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt,
            model="gpt-4-turbo-preview",
            max_tokens=800,
            temperature=0.3
        )

        if "error" in response:
            # Fallback plan
            timeblocks = [
                TimeBlock(
                    start_time="09:00",
                    end_time="10:30",
                    task_name="Morning Focus Session",
                    task_id="task1",
                    goal="Productivity",
                    priority="high",
                ),
                TimeBlock(
                    start_time="14:00",
                    end_time="16:00",
                    task_name="Afternoon Work",
                    task_id="task2",
                    goal="Project Completion",
                    priority="medium",
                ),
            ]
        else:
            # Parse AI response
            try:
                response_text = response.get("generated_text", "")
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                if start_idx != -1 and end_idx != 0:
                    plan_data = json.loads(response_text[start_idx:end_idx])
                    timeblocks = [
                        TimeBlock(**block) for block in plan_data.get("timeblocks", [])
                    ]
                    notes = plan_data.get("notes", "AI-generated plan based on your preferences and current tasks.")
                else:
                    timeblocks = [
                        TimeBlock(
                            start_time="09:00",
                            end_time="10:30",
                            task_name="Morning Focus Session",
                            task_id="task1",
                            goal="Productivity",
                            priority="high",
                        )
                    ]
                    notes = "AI-generated plan based on your preferences and current tasks."
            except json.JSONDecodeError:
                timeblocks = [
                    TimeBlock(
                        start_time="09:00",
                        end_time="10:30",
                        task_name="Morning Focus Session",
                        task_id="task1",
                        goal="Productivity",
                        priority="high",
                    )
                ]
                notes = "AI-generated plan based on your preferences and current tasks."

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=current_user["id"],
            endpoint="/plan-my-day",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 200),
            output_tokens=response.get("usage", {}).get("completion_tokens", 400),
            cost_usd=response.get("usage", {}).get("total_cost", 0.02),
        )

        return PlanMyDayResponse(
            date=request.date,
            user_id=current_user["id"],
            timeblocks=timeblocks,
            notes=notes,
        )
    except Exception as e:
        logging.error(f"Error planning day for user {current_user['id']}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Keep only unique review-related endpoints
@router.get(
    "/review-plan",
    response_model=List[dict],  # Simplified response model
    tags=["Review"],
    summary="Get today's review plan",
)
@ai_cached("review_planning", ttl=900)  # Cache for 15 minutes
async def get_review_plan(
    user_id: str,
    time_available: int = 30,
    current_user: dict = Depends(get_current_user),
):
    """Get AI-powered review plan with caching"""
    try:
        logging.info(
            f"Generating review plan for user {current_user['id']} with {time_available} minutes available"
        )

        # Get user's flashcards from database
        supabase = get_supabase_client()
        flashcards_result = (
            supabase.table("flashcards")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not flashcards_result.data:
            return []

        flashcards = flashcards_result.data

        # Generate AI prompt for review planning
        prompt = f"""Create a personalized review plan for a user with {time_available} minutes available.

Available flashcards: {len(flashcards)} cards
- Cards due for review: {len([f for f in flashcards if f.get('next_review_date') and f.get('next_review_date') <= datetime.now().isoformat()])}
- Cards with high difficulty: {len([f for f in flashcards if f.get('ease_factor', 2.5) < 2.0])}
- Cards with low difficulty: {len([f for f in flashcards if f.get('ease_factor', 2.5) > 3.0])}

Create a review plan that:
1. Prioritizes cards due for review
2. Includes some challenging cards (low ease factor)
3. Balances with easier cards for confidence building
4. Fits within {time_available} minutes (estimate 2-3 minutes per card)

Return the response as a JSON array like this:
[
    {{
        "flashcard_id": "card_id",
        "question": "The actual question from the flashcard",
        "estimated_time": 2,
        "reason": "Due for review" or "High difficulty" or "Confidence building"
    }}
]

Focus on creating an effective learning experience within the time constraint."""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=800, temperature=0.3
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Track API usage
        await cost_tracking_service.track_api_call(
            user_id=current_user["id"],
            endpoint="/review-plan",
            model="gpt-4-turbo-preview",
            input_tokens=response.get("usage", {}).get("prompt_tokens", 200),
            output_tokens=response.get("usage", {}).get("completion_tokens", 400),
            cost_usd=response.get("usage", {}).get("total_cost", 0.02),
        )

        # Parse the response
        try:
            response_text = response.get("generated_text", "")
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                plan_data = json.loads(json_str)

                # Map to actual flashcards and validate
                plan = []
                for item in plan_data:
                    flashcard_id = item.get("flashcard_id")
                    # Find the actual flashcard
                    flashcard = next(
                        (f for f in flashcards if f.get("id") == flashcard_id), None
                    )
                    if flashcard:
                        plan.append(
                            {
                                "flashcard_id": flashcard_id,
                                "question": flashcard.get(
                                    "question", item.get("question", "Unknown question")
                                ),
                                "estimated_time": item.get("estimated_time", 2),
                                "reason": item.get("reason", "Review"),
                            }
                        )

                return plan
            else:
                # Fallback plan
                return [
                    {
                        "flashcard_id": "fallback",
                        "question": "Review plan generation failed",
                        "estimated_time": 2,
                        "reason": "System error",
                    }
                ]
        except json.JSONDecodeError:
            # Fallback plan
            return [
                {
                    "flashcard_id": "fallback",
                    "question": "Review plan generation failed",
                    "estimated_time": 2,
                    "reason": "Parsing error",
                }
            ]
    except Exception as e:
        logging.error(f"Failed to generate review plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate review plan")


# Define the request model for input validation
class ReviewUpdateRequest(BaseModel):
    flashcard_id: str
    was_correct: bool


# Function to check if a flashcard exists
async def flashcard_exists(flashcard_id: str) -> bool:
    supabase = get_supabase_client()
    result = supabase.table("flashcards").select("id").eq("id", flashcard_id).execute()
    return len(result.data) > 0


# Function to update flashcard review
async def update_flashcard_review(flashcard_id: str, was_correct: bool):
    supabase = get_supabase_client()
    # TODO: Implement SM-2 algorithm for spaced repetition
    # For now, just update the last_reviewed_at timestamp
    result = (
        supabase.table("flashcards")
        .update({"last_reviewed_at": datetime.utcnow().isoformat()})
        .eq("id", flashcard_id)
        .execute()
    )


# SM-2 algorithm for spaced repetition
async def calculate_next_interval(
    ease_factor: float, repetitions: int, was_correct: bool
) -> tuple[int, float]:
    # SM-2 algorithm logic
    if was_correct:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = int(interval * ease_factor)
        repetitions += 1
        ease_factor = max(1.3, ease_factor + 0.1 - (5 - 5) * 0.08)
    else:
        repetitions = 0
        interval = 1
        ease_factor = max(1.3, ease_factor - 0.2)

    return interval, ease_factor


@router.post(
    "/review/update",
    tags=["Review"],
    summary="Update flashcard review result",
    response_description="Review updated successfully",
)
async def update_review_result(
    request: ReviewUpdateRequest, current_user: dict = Depends(get_current_user)
):
    """Update flashcard review result and recalculate next review date"""
    try:
        logging.info(
            f"User {current_user['id']} updating review for flashcard {request.flashcard_id}"
        )

        # Check if flashcard exists
        if not await flashcard_exists(request.flashcard_id):
            raise HTTPException(status_code=404, detail="Flashcard not found")

        # Update the review
        await update_flashcard_review(request.flashcard_id, request.was_correct)

        return {"message": "Review updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to update review: {e}")
        raise HTTPException(status_code=500, detail="Failed to update review")


# Cache management endpoints
@router.post("/cache/invalidate", summary="Invalidate AI cache for user")
async def invalidate_cache(
    operations: List[str] = None, current_user: dict = Depends(get_current_user)
):
    """Invalidate AI cache for specific operations"""
    try:
        deleted_count = await ai_cache_service.invalidate_user_ai_cache(
            current_user["id"], operations
        )
        return {
            "success": True,
            "deleted_entries": deleted_count,
            "operations": operations or "all"
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats", summary="Get AI cache statistics")
async def get_cache_stats(current_user: dict = Depends(get_current_user)):
    """Get AI cache statistics"""
    try:
        stats = ai_cache_service.get_cache_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
