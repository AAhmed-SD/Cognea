from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks, Request
from models.text import TextGenerationRequest, TextGenerationResponse
from services.openai_integration import generate_openai_text
import logging
import os
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import aioredis
from services.review_engine import ReviewEngine
from uuid import uuid4
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.supabase import get_supabase_client

router = APIRouter()

# Set up basic logging
logging.basicConfig(level=logging.INFO)

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


@router.post(
    "/generate-text",
    response_model=TextGenerationResponse,
    tags=["Text Generation"],
    summary="Generate text using OpenAI API",
)
@limiter.limit("5/minute")
async def generate_text_endpoint(
    request: Request,
    request_data: TextGenerationRequest,
    api_key: str = Depends(api_key_auth),
):
    try:
        redis = await get_redis_client()
        cache_key = f"generate_text:{hash(request_data.prompt)}"
        cached_response = await redis.get(cache_key)
        if cached_response:
            logging.info("Cache hit for text generation")
            return json.loads(cached_response)

        logging.debug(f"Received request: {request_data}")
        generated_text, total_tokens = generate_openai_text(
            prompt=request_data.prompt,
            model=request_data.model,
            max_tokens=request_data.max_tokens,
            temperature=request_data.temperature,
            stop=request_data.stop,
        )
        if "error" in generated_text:
            logging.warning(f"Error in text generation: {generated_text['error']}")
            raise HTTPException(status_code=500, detail=generated_text["error"])
        logging.info(f"Generated text: {generated_text['generated_text']}")
        response = TextGenerationResponse(
            original_prompt=request_data.prompt,
            model=request_data.model,
            generated_text=generated_text["generated_text"],
            total_tokens=generated_text["total_tokens"],
        )

        # Cache the response
        await redis.set(
            cache_key, json.dumps(response), expire=3600
        )  # Cache for 1 hour
        return response
    except Exception as e:
        logging.error(f"Unhandled exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Define the request model for input validation
class DailyBriefRequest(BaseModel):
    date: str
    user_id: int


# Function to process the daily brief
async def process_daily_brief(date: str, user_id: int):
    # Placeholder for the actual processing logic
    logging.info(f"Processing daily brief for user {user_id} on {date}")
    # Simulate processing
    return {"summary": f"Daily brief for user {user_id} on {date}"}


@router.post(
    "/daily-brief",
    summary="Generate Daily Brief",
    description="Generates a daily summary of tasks.",
)
@limiter.limit("5/minute")
async def generate_daily_brief(
    request: Request, request_data: DailyBriefRequest, background_tasks: BackgroundTasks
):
    try:
        logging.info("Generating daily brief")
        # Add the task to be processed in the background
        background_tasks.add_task(
            process_daily_brief, request_data.date, request_data.user_id
        )
        return {"message": "Daily brief is being generated."}
    except Exception as e:
        logging.error(f"Error generating daily brief: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Define the request model for input validation
class QuizMeRequest(BaseModel):
    deck_id: int


# Function to generate quiz questions
async def generate_quiz_questions(deck_id: int):
    # Placeholder for the actual quiz generation logic
    logging.info(f"Generating quiz for deck {deck_id}")
    # Simulate quiz generation
    questions = [
        {"question": "What is the capital of France?", "answer": "Paris"},
        {"question": "What is 2 + 2?", "answer": "4"},
        {"question": "What is the boiling point of water?", "answer": "100°C"},
    ]
    return questions


@router.post(
    "/quiz-me",
    summary="Generate Quiz Questions",
    description="Takes a deck ID and returns 3–5 questions from that deck to quiz the user.",
)
async def quiz_me(request: Request, request_data: QuizMeRequest):
    try:
        logging.info("Generating quiz questions")
        questions = await generate_quiz_questions(request_data.deck_id)
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
    # Basic splitting logic here...
    logging.info("Splitting text into chunks")
    return [text[i : i + max_tokens] for i in range(0, len(text), max_tokens)]


# Function to summarize notes
async def summarize_notes(notes: str, summary_type: str) -> str:
    # Placeholder for the actual summarization logic
    logging.info(f"Summarizing notes with summary type: {summary_type}")
    # Simulate summarization
    return f"Summary ({summary_type}): {notes[:100]}..."


@router.post(
    "/summarize-notes",
    summary="Summarize Notes",
    description="Compress long notes into key takeaways.",
)
@limiter.limit("5/minute")
async def summarize_notes_endpoint(request: SummarizeNotesRequest):
    try:
        # Input size validation
        if len(request.notes) > 5000:  # Example limit
            logging.warning(
                f"User {request.user_id} submitted notes exceeding size limit: {len(request.notes)} characters"
            )
            raise HTTPException(
                status_code=400,
                detail="Notes exceed the maximum allowed size of 5000 characters.",
            )

        logging.info(
            f"User {request.user_id} is summarizing notes of length {len(request.notes)}"
        )
        chunks = await split_into_chunks(request.notes)
        summaries = [
            await summarize_notes(chunk, request.summary_type) for chunk in chunks
        ]
        return {"summaries": summaries}
    except Exception as e:
        logging.error(f"Error summarizing notes for user {request.user_id}: {str(e)}")
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
) -> RescheduleSuggestion:
    # Placeholder for the actual AI logic
    logging.info(f"Suggesting reschedule for task: {request.task_title}")
    # Simulate AI response
    suggested_time = "Friday, 9:00 AM - 10:30 AM"
    reason = "Closer to the deadline. User has higher focus in the morning and Friday is still open."
    return RescheduleSuggestion(suggested_time=suggested_time, reason=reason)


@router.post(
    "/suggest-reschedule",
    summary="Suggest Reschedule Time",
    description="Suggest an optimal new time for a missed or rescheduled task based on context.",
)
@limiter.limit("5/minute")
async def suggest_reschedule_endpoint(request: SuggestRescheduleRequest):
    try:
        logging.info(f"Received reschedule request for task: {request.task_title}")
        suggestion = await suggest_reschedule_logic(request)
        logging.info(
            f"Suggested time: {suggestion.suggested_time}, Reason: {suggestion.reason}"
        )
        return suggestion
    except ValueError as e:
        logging.error(f"Invalid task object: {str(e)}")
        raise HTTPException(status_code=422, detail="Invalid task object.")
    except Exception as e:
        logging.error(f"Error suggesting reschedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to suggest reschedule.")


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


# Function to generate AI prompt for task extraction
async def generate_ai_prompt(text: str, goal_context: Optional[str] = None) -> str:
    # Placeholder for AI prompt generation
    prompt = f"Extract tasks from the following text: {text}"
    if goal_context:
        prompt += f"\nContext: {goal_context}"
    return prompt


@router.post(
    "/extract-tasks-from-text",
    response_model=ExtractTasksResponse,
    summary="Extract structured tasks from messy notes",
    tags=["AI Tasks & Memory"],
)
async def extract_tasks(request: ExtractTasksRequest):
    try:
        logging.info(f"Extracting tasks from text of length {len(request.text)}")

        # Real OpenAI integration for task extraction
        prompt = f"""Extract structured tasks from the following text. For each task, provide:
1. A clear, actionable task description
2. Priority level (high, medium, low)
3. Time estimate in minutes
4. Any relevant goal context

Text: {request.text}
Goal Context: {request.goal_context or 'General'}

Return the tasks in JSON format with this structure:
{{
    "tasks": [
        {{
            "task": "task description",
            "priority": "high/medium/low",
            "time_estimate_minutes": 30,
            "goal": "goal context"
        }}
    ]
}}"""

        # Call OpenAI API
        from services.openai_integration import generate_openai_text

        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=1000, temperature=0.3
        )

        # Parse the response
        import json

        try:
            # Try to extract JSON from the response
            response_text = response.get("generated_text", "")
            # Find JSON in the response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                tasks_data = parsed.get("tasks", [])
            else:
                # Fallback: create tasks from the response text
                tasks_data = [
                    {
                        "task": response_text,
                        "priority": "medium",
                        "time_estimate_minutes": 30,
                        "goal": request.goal_context,
                    }
                ]
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            tasks_data = [
                {
                    "task": response_text,
                    "priority": "medium",
                    "time_estimate_minutes": 30,
                    "goal": request.goal_context,
                }
            ]

        extracted_tasks = [
            ExtractedTask(
                task=task.get("task", "Unknown task"),
                priority=task.get("priority", "medium"),
                time_estimate_minutes=task.get("time_estimate_minutes", 30),
                goal=task.get("goal", request.goal_context),
            )
            for task in tasks_data
        ]

        return ExtractTasksResponse(extracted_tasks=extracted_tasks)
    except Exception as e:
        logging.error(f"Error extracting tasks: {str(e)}")
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


# Function to generate planning prompt
async def generate_planning_prompt(
    tasks: List[dict], focus_hours: Optional[List[str]]
) -> str:
    # Placeholder for planning prompt generation
    return f"Plan day with {len(tasks)} tasks and focus hours: {focus_hours}"


@router.post(
    "/plan-my-day",
    response_model=PlanMyDayResponse,
    tags=["Planning"],
    summary="AI-generated daily plan",
)
async def plan_my_day(request: PlanMyDayRequest):
    try:
        logging.info(
            f"Generating daily plan for user {request.user_id} on {request.date}"
        )

        # Get user's tasks from database
        from services.supabase import get_supabase_client

        supabase = get_supabase_client()

        # Fetch user's tasks for the given date
        result = (
            supabase.table("tasks").select("*").eq("user_id", request.user_id).execute()
        )
        user_tasks = result.data if result.data else []

        # Real OpenAI integration for daily planning
        tasks_info = "\n".join(
            [
                f"- {task.get('title', 'Unknown')} (Priority: {task.get('priority', 'medium')})"
                for task in user_tasks
            ]
        )

        prompt = f"""Create an optimal daily schedule for {request.date} based on the following information:

User Tasks:
{tasks_info}

Focus Hours: {request.focus_hours or '9:00-12:00, 14:00-17:00'}
Preferred Working Hours: {request.preferred_working_hours or '8:00-18:00'}
Break Times: {request.break_times or '12:00-13:00'}

Generate a realistic schedule with:
1. Time blocks for each task
2. Appropriate breaks
3. Consider task priorities and energy levels
4. Include buffer time between tasks

Return the schedule in JSON format:
{{
    "timeblocks": [
        {{
            "start_time": "09:00",
            "end_time": "10:30",
            "task_name": "Task description",
            "task_id": "task_id_if_available",
            "goal": "related goal",
            "priority": "high/medium/low"
        }}
    ],
    "notes": "Brief explanation of the schedule"
}}"""

        # Call OpenAI API
        from services.openai_integration import generate_openai_text

        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=1500, temperature=0.4
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
                timeblocks_data = parsed.get("timeblocks", [])
                notes = parsed.get(
                    "notes",
                    "AI-generated plan based on your preferences and available tasks.",
                )
            else:
                # Fallback schedule
                timeblocks_data = [
                    {
                        "start_time": "09:00",
                        "end_time": "10:30",
                        "task_name": "Deep Work Session",
                        "task_id": None,
                        "goal": "Productivity",
                        "priority": "high",
                    },
                    {
                        "start_time": "10:45",
                        "end_time": "12:00",
                        "task_name": "Task Completion",
                        "task_id": None,
                        "goal": "Goal Achievement",
                        "priority": "medium",
                    },
                ]
                notes = (
                    "AI-generated plan based on your preferences and available tasks."
                )
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            timeblocks_data = [
                {
                    "start_time": "09:00",
                    "end_time": "10:30",
                    "task_name": "Deep Work Session",
                    "task_id": None,
                    "goal": "Productivity",
                    "priority": "high",
                }
            ]
            notes = "AI-generated plan based on your preferences and available tasks."

        timeblocks = [
            TimeBlock(
                start_time=block.get("start_time", "09:00"),
                end_time=block.get("end_time", "10:30"),
                task_name=block.get("task_name", "Scheduled Task"),
                task_id=block.get("task_id"),
                goal=block.get("goal"),
                priority=block.get("priority", "medium"),
            )
            for block in timeblocks_data
        ]

        return PlanMyDayResponse(
            date=request.date,
            user_id=request.user_id,
            timeblocks=timeblocks,
            notes=notes,
        )
    except Exception as e:
        logging.error(f"Error generating daily plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Define the request model for input validation
class GoalRequest(BaseModel):
    user_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None  # e.g. "2025-06-06"
    priority: Optional[str] = "medium"
    is_starred: bool = False


# Define the response model
class GoalResponse(BaseModel):
    goal_id: str
    user_id: int
    title: str
    description: Optional[str]
    due_date: Optional[str]
    priority: str
    status: str
    progress: Optional[int] = 0
    created_at: datetime
    updated_at: datetime
    analytics: Optional[dict] = None


@router.post(
    "/goals",
    response_model=GoalResponse,
    tags=["Goals"],
    summary="Create and track high-level goals",
)
async def create_goal(request: GoalRequest):
    """
    Create a new goal.
    """
    try:
        logging.info(f"Creating goal for user {request.user_id}")

        supabase = get_supabase_client()
        goal_data = {
            "user_id": request.user_id,
            "title": request.title,
            "description": request.description,
            "due_date": request.due_date,
            "priority": request.priority,
            "is_starred": request.is_starred,
            "status": "active",
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table("goals").insert(goal_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create goal")

        goal = result.data[0]
        return GoalResponse(**goal)
    except Exception as e:
        logging.error(f"Failed to create goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to create goal")


# Define the request model for input validation
class ScheduleBlock(BaseModel):
    user_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    context: Optional[str] = "Work"
    goal_id: Optional[str]
    is_fixed: bool = False
    is_rescheduled: bool = False
    rescheduled_count: int = 0
    color_code: Optional[str]


@router.post(
    "/schedule",
    response_model=ScheduleBlock,
    tags=["Schedule"],
    summary="Create a scheduled block",
)
async def create_schedule_block(request: ScheduleBlock):
    """
    Create a new schedule block.
    """
    try:
        logging.info(f"Creating schedule block for user {request.user_id}")

        supabase = get_supabase_client()
        schedule_data = {
            "user_id": request.user_id,
            "title": request.title,
            "description": request.description,
            "start_time": request.start_time.isoformat(),
            "end_time": request.end_time.isoformat(),
            "context": request.context,
            "goal_id": request.goal_id,
            "is_fixed": request.is_fixed,
            "is_rescheduled": request.is_rescheduled,
            "rescheduled_count": request.rescheduled_count,
            "color_code": request.color_code,
            "created_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table("schedule_blocks").insert(schedule_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=500, detail="Failed to create schedule block"
            )

        schedule = result.data[0]
        return ScheduleBlock(**schedule)
    except Exception as e:
        logging.error(f"Failed to create schedule block: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule block")


@router.get(
    "/schedule",
    response_model=List[ScheduleBlock],
    tags=["Schedule"],
    summary="Read scheduled blocks",
)
async def read_scheduled_blocks(user_id: str, view: Optional[str] = "week"):
    """
    Retrieve scheduled blocks for a user.
    """
    try:
        logging.info(f"Retrieving schedule blocks for user {user_id} with view {view}")

        supabase = get_supabase_client()
        result = (
            supabase.table("schedule_blocks")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        if not result.data:
            return []

        return [ScheduleBlock(**schedule) for schedule in result.data]
    except Exception as e:
        logging.error(f"Failed to retrieve schedule blocks: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve schedule blocks"
        )


@router.put(
    "/schedule/{schedule_id}",
    response_model=ScheduleBlock,
    tags=["Schedule"],
    summary="Update a scheduled block",
)
async def update_schedule_block(schedule_id: str, request: ScheduleBlock):
    """
    Update an existing schedule block.
    """
    try:
        logging.info(f"Updating schedule block {schedule_id}")

        supabase = get_supabase_client()
        schedule_data = {
            "user_id": request.user_id,
            "title": request.title,
            "description": request.description,
            "start_time": request.start_time.isoformat(),
            "end_time": request.end_time.isoformat(),
            "context": request.context,
            "goal_id": request.goal_id,
            "is_fixed": request.is_fixed,
            "is_rescheduled": request.is_rescheduled,
            "rescheduled_count": request.rescheduled_count,
            "color_code": request.color_code,
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = (
            supabase.table("schedule_blocks")
            .update(schedule_data)
            .eq("id", schedule_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Schedule block not found")

        schedule = result.data[0]
        return ScheduleBlock(**schedule)
    except Exception as e:
        logging.error(f"Failed to update schedule block: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule block")


@router.delete(
    "/schedule/{schedule_id}", tags=["Schedule"], summary="Delete a scheduled block"
)
async def delete_schedule_block(schedule_id: str):
    """
    Delete a schedule block.
    """
    try:
        logging.info(f"Deleting schedule block {schedule_id}")

        supabase = get_supabase_client()
        result = (
            supabase.table("schedule_blocks").delete().eq("id", schedule_id).execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Schedule block not found")

        return {"message": "Schedule block deleted"}
    except Exception as e:
        logging.error(f"Failed to delete schedule block: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete schedule block")


# Define the request model for input validation
class FlashcardRequest(BaseModel):
    user_id: str
    question: str
    answer: str
    tags: Optional[List[str]] = None
    deck_id: Optional[str] = None
    deck_name: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    ease_factor: Optional[float] = 2.5
    interval: Optional[int] = 1


# Define the response model
class FlashcardResponse(BaseModel):
    flashcard_id: str
    user_id: str
    question: str
    answer: str
    tags: Optional[List[str]]
    deck_id: Optional[str]
    deck_name: Optional[str]
    last_reviewed_at: Optional[datetime]
    next_review_date: Optional[datetime]
    ease_factor: Optional[float]
    interval: Optional[int]


@router.post(
    "/flashcards",
    response_model=FlashcardResponse,
    tags=["Flashcards"],
    summary="Create a flashcard",
)
async def create_flashcard(request: FlashcardRequest):
    """
    Create a new flashcard.
    """
    try:
        logging.info(f"Creating flashcard for user {request.user_id}")

        supabase = get_supabase_client()
        flashcard_data = {
            "user_id": request.user_id,
            "question": request.question,
            "answer": request.answer,
            "tags": request.tags,
            "deck_id": request.deck_id,
            "deck_name": request.deck_name,
            "last_reviewed_at": (
                request.last_reviewed_at.isoformat()
                if request.last_reviewed_at
                else None
            ),
            "next_review_date": (
                request.next_review_date.isoformat()
                if request.next_review_date
                else None
            ),
            "ease_factor": request.ease_factor,
            "interval": request.interval,
            "created_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table("flashcards").insert(flashcard_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create flashcard")

        flashcard = result.data[0]
        return FlashcardResponse(**flashcard)
    except Exception as e:
        logging.error(f"Failed to create flashcard: {e}")
        raise HTTPException(status_code=500, detail="Failed to create flashcard")


@router.get(
    "/flashcards",
    response_model=List[FlashcardResponse],
    tags=["Flashcards"],
    summary="Read flashcards",
)
async def read_flashcards(user_id: str):
    """
    Retrieve flashcards for a user.
    """
    try:
        logging.info(f"Retrieving flashcards for user {user_id}")

        supabase = get_supabase_client()
        result = (
            supabase.table("flashcards").select("*").eq("user_id", user_id).execute()
        )

        if not result.data:
            return []

        return [FlashcardResponse(**flashcard) for flashcard in result.data]
    except Exception as e:
        logging.error(f"Failed to retrieve flashcards: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve flashcards")


@router.get(
    "/flashcards/{flashcard_id}",
    response_model=FlashcardResponse,
    tags=["Flashcards"],
    summary="Read a flashcard",
)
async def read_flashcard(flashcard_id: str):
    """
    Retrieve a single flashcard by ID.
    """
    try:
        logging.info(f"Retrieving flashcard {flashcard_id}")

        supabase = get_supabase_client()
        result = (
            supabase.table("flashcards").select("*").eq("id", flashcard_id).execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Flashcard not found")

        flashcard = result.data[0]
        return FlashcardResponse(**flashcard)
    except Exception as e:
        logging.error(f"Failed to retrieve flashcard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve flashcard")


@router.put(
    "/flashcards/{flashcard_id}",
    response_model=FlashcardResponse,
    tags=["Flashcards"],
    summary="Update a flashcard",
)
async def update_flashcard(flashcard_id: str, request: FlashcardRequest):
    """
    Update an existing flashcard.
    """
    try:
        logging.info(f"Updating flashcard {flashcard_id}")

        supabase = get_supabase_client()
        flashcard_data = {
            "user_id": request.user_id,
            "question": request.question,
            "answer": request.answer,
            "tags": request.tags,
            "deck_id": request.deck_id,
            "deck_name": request.deck_name,
            "last_reviewed_at": (
                request.last_reviewed_at.isoformat()
                if request.last_reviewed_at
                else None
            ),
            "next_review_date": (
                request.next_review_date.isoformat()
                if request.next_review_date
                else None
            ),
            "ease_factor": request.ease_factor,
            "interval": request.interval,
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = (
            supabase.table("flashcards")
            .update(flashcard_data)
            .eq("id", flashcard_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Flashcard not found")

        flashcard = result.data[0]
        return FlashcardResponse(**flashcard)
    except Exception as e:
        logging.error(f"Failed to update flashcard: {e}")
        raise HTTPException(status_code=500, detail="Failed to update flashcard")


@router.delete(
    "/flashcards/{flashcard_id}", tags=["Flashcards"], summary="Delete a flashcard"
)
async def delete_flashcard(flashcard_id: str):
    """
    Delete a flashcard.
    """
    try:
        logging.info(f"Deleting flashcard {flashcard_id}")

        supabase = get_supabase_client()
        result = supabase.table("flashcards").delete().eq("id", flashcard_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Flashcard not found")

        return {"message": "Flashcard deleted"}
    except Exception as e:
        logging.error(f"Failed to delete flashcard: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete flashcard")


@router.get(
    "/review-plan",
    response_model=List[FlashcardResponse],
    tags=["Review"],
    summary="Get today's review plan",
)
async def get_review_plan(user_id: str, time_available: int = 30):
    """
    Retrieve a personalized review plan for the user based on available time.
    """
    try:
        logging.info(
            f"Generating review plan for user {user_id} with {time_available} minutes available"
        )
        engine = ReviewEngine(user_id=user_id)
        plan = engine.get_today_review_plan(time_available_mins=time_available)
        return plan
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
) -> (int, float):
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
async def update_review_result(request: ReviewUpdateRequest):
    """
    Update the result of a flashcard review.
    """
    try:
        logging.info(f"Updating review result for flashcard {request.flashcard_id}")

        # Check if flashcard exists
        if not await flashcard_exists(request.flashcard_id):
            raise HTTPException(status_code=404, detail="Flashcard not found")

        # Update flashcard review
        await update_flashcard_review(request.flashcard_id, request.was_correct)

        return {"message": "Review updated successfully"}
    except Exception as e:
        logging.error(f"Failed to update review result: {e}")
        raise HTTPException(status_code=500, detail="Failed to update review result")


# Notification model
class Notification(BaseModel):
    id: Optional[str] = None
    user_id: str
    title: str
    message: str
    send_time: datetime
    type: str = "reminder"
    is_sent: bool = False
    is_read: bool = False
    repeat_interval: Optional[str] = None  # daily, weekly, custom
    category: Optional[str] = "task"  # task, goal, system, alert


# POST /notifications: create a new notification
@router.post(
    "/notifications", tags=["Notifications"], summary="Create a new notification"
)
async def create_notification(notification: Notification):
    try:
        supabase = get_supabase_client()
        notification_id = str(uuid4())
        notification_data = notification.dict()
        notification_data["id"] = notification_id
        result = supabase.table("notifications").insert(notification_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create notification")
        return {
            "message": "Notification created successfully",
            "notification": result.data[0],
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create notification")


# GET /notifications?user_id=...: get all notifications for a user
@router.get(
    "/notifications", tags=["Notifications"], summary="Get all notifications for a user"
)
async def get_notifications(user_id: str):
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("notifications").select("*").eq("user_id", user_id).execute()
        )
        return {"notifications": result.data or []}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")


# PUT /notifications/{notification_id}: update an existing notification
@router.put(
    "/notifications/{notification_id}",
    tags=["Notifications"],
    summary="Update an existing notification",
)
async def update_notification(notification_id: str, updated_notification: Notification):
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("notifications")
            .update(updated_notification.dict())
            .eq("id", notification_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {
            "message": "Notification updated successfully",
            "notification": result.data[0],
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update notification")


# DELETE /notifications/{notification_id}: delete a notification
@router.delete(
    "/notifications/{notification_id}",
    tags=["Notifications"],
    summary="Delete a notification",
)
async def delete_notification(notification_id: str):
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("notifications").delete().eq("id", notification_id).execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification deleted successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete notification")


# PUT /notifications/{notification_id}/read: mark as read
@router.put(
    "/notifications/{notification_id}/read",
    tags=["Notifications"],
    summary="Mark a notification as read",
)
async def mark_notification_as_read(notification_id: str):
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("notifications")
            .update({"is_read": True})
            .eq("id", notification_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification marked as read"}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Failed to mark notification as read"
        )


# GET /notifications/unread-count: get unread notification count
@router.get(
    "/notifications/unread-count",
    tags=["Notifications"],
    summary="Get unread notification count",
)
async def get_unread_notification_count(user_id: str):
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("notifications")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_read", False)
            .execute()
        )
        unread_count = len(result.data) if result.data else 0
        return {"unread_count": unread_count}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve unread notification count"
        )


# Feedback and insights models
class FeedbackHistoryResponse(BaseModel):
    feedback_history: List[dict]


class AIFeedbackRequest(BaseModel):
    user_id: str
    week_start: Optional[datetime] = None
    week_end: Optional[datetime] = None


class AIFeedbackResponse(BaseModel):
    feedback: str
    suggestions: List[str]


# POST /ai-feedback: log and return feedback
@router.post(
    "/ai-feedback",
    response_model=AIFeedbackResponse,
    tags=["Insights"],
    summary="Get AI-generated feedback for the week",
)
async def ai_feedback(request: AIFeedbackRequest):
    try:
        supabase = get_supabase_client()
        feedback = (
            "You have been consistent with your tasks this week. Keep up the good work!"
        )
        suggestions = [
            "Set specific goals for each day",
            "Limit distractions during work hours",
        ]
        feedback_entry = {
            "user_id": request.user_id,
            "feedback": feedback,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat(),
            "acknowledgment_status": False,
        }
        supabase.table("feedback_history").insert(feedback_entry).execute()
        return AIFeedbackResponse(feedback=feedback, suggestions=suggestions)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate AI feedback")


# GET /ai-feedback/history: get feedback history
@router.get(
    "/ai-feedback/history",
    response_model=FeedbackHistoryResponse,
    tags=["Insights"],
    summary="Get feedback history",
)
async def get_feedback_history(user_id: str):
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("feedback_history")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return FeedbackHistoryResponse(feedback_history=result.data or [])
    except Exception:
        raise HTTPException(
            status_code=500, detail="Failed to retrieve feedback history"
        )


# User insights models
class UserInsightsRequest(BaseModel):
    user_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class UserInsightsResponse(BaseModel):
    user_id: str
    date_range: dict
    task_summary: dict
    flashcard_summary: dict
    goal_progress: List[dict]
    suggestions: List[str]


# GET /user-insights: get user productivity insights
@router.get(
    "/user-insights",
    response_model=UserInsightsResponse,
    tags=["Insights"],
    summary="Get user productivity insights",
)
async def get_user_insights(request: UserInsightsRequest):
    try:
        # TODO: Implement real insights logic using Supabase data
        # For now, return mock data
        insights = {
            "user_id": request.user_id,
            "date_range": {
                "start": request.start_date or "2025-06-01",
                "end": request.end_date or "2025-06-07",
            },
            "task_summary": {
                "completed": 12,
                "missed": 3,
                "rescheduled": 2,
                "overbooked_days": ["2025-06-03", "2025-06-04"],
            },
            "flashcard_summary": {
                "reviewed": 45,
                "forgotten": 9,
                "avg_accuracy": 80,
                "most_forgotten_deck": "Neuroscience",
            },
            "goal_progress": [
                {
                    "goal_id": "goal123",
                    "title": "Finish ML Course",
                    "progress": "60%",
                    "status": "on_track",
                }
            ],
            "suggestions": [
                "Review 'Neuroscience' deck earlier in the day",
                "Avoid scheduling >5 tasks on weekdays",
                "You're most consistent at 9–11 AM. Leverage that.",
            ],
        }
        return UserInsightsResponse(**insights)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate user insights")


# TODO: Continue with remaining endpoints (notifications, insights, etc.)
# The remaining endpoints can be refactored similarly to use Supabase
