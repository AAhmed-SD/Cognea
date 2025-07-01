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
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.supabase import get_supabase_client
from services.auth import get_current_user

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
    request: Request,
    request_data: DailyBriefRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
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
async def quiz_me(
    request: Request,
    request_data: QuizMeRequest,
    current_user: dict = Depends(get_current_user),
):
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
async def summarize_notes_endpoint(
    request: SummarizeNotesRequest, current_user: dict = Depends(get_current_user)
):
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
            await summarize_notes(chunk, request.summary_type) for chunk in chunks
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
async def suggest_reschedule_endpoint(
    request: SuggestRescheduleRequest, current_user: dict = Depends(get_current_user)
):
    try:
        logging.info(f"User {current_user['id']} requesting reschedule suggestion")
        suggestion = await suggest_reschedule_logic(request)
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
async def extract_tasks(
    request: ExtractTasksRequest, current_user: dict = Depends(get_current_user)
):
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

        # Parse the response
        import json

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
async def plan_my_day(
    request: PlanMyDayRequest, current_user: dict = Depends(get_current_user)
):
    try:
        logging.info(f"User {current_user['id']} requesting daily plan")
        # TODO: Replace placeholder AI logic with real AI/database-backed logic
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

        return PlanMyDayResponse(
            date=request.date,
            user_id=current_user["id"],
            timeblocks=timeblocks,
            notes="AI-generated plan based on your preferences and current tasks.",
        )
    except Exception as e:
        logging.error(f"Error planning day for user {current_user['id']}: {str(e)}")
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


# Keep only unique review-related endpoints
@router.get(
    "/review-plan",
    response_model=List[dict],  # Simplified response model
    tags=["Review"],
    summary="Get today's review plan",
)
async def get_review_plan(
    user_id: str,
    time_available: int = 30,
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve a personalized review plan for the user based on available time.
    """
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

        # Parse the response
        import json

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
    """
    Update a flashcard review result and recalculate the next review date.
    """
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
async def ai_feedback(
    request: AIFeedbackRequest, current_user: dict = Depends(get_current_user)
):
    try:
        logging.info(f"User {current_user['id']} requesting AI feedback")

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

        fixed_schedules = len([s for s in schedule_blocks if s.get("is_fixed")])
        rescheduled_count = len([s for s in schedule_blocks if s.get("is_rescheduled")])

        # Generate AI prompt for feedback
        prompt = f"""Analyze this user's productivity data and provide personalized feedback and suggestions:

TASK PERFORMANCE:
- Total tasks: {total_tasks}
- Completed tasks: {completed_tasks}
- Completion rate: {completion_rate:.1f}%

GOAL PROGRESS:
- Active goals: {active_goals}
- Average goal progress: {avg_goal_progress:.1f}%

SCHEDULING:
- Fixed schedule blocks: {fixed_schedules}
- Rescheduled blocks: {rescheduled_count}

Provide constructive feedback and actionable suggestions in JSON format:
{{
    "feedback": "A personalized feedback message based on their patterns",
    "suggestions": [
        "Specific actionable suggestion 1",
        "Specific actionable suggestion 2",
        "Specific actionable suggestion 3"
    ]
}}

Focus on:
1. Positive reinforcement for good habits
2. Constructive suggestions for improvement
3. Specific, actionable advice
4. Encouraging tone while being honest about areas for growth"""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=600, temperature=0.4
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
                feedback_data = json.loads(json_str)

                feedback = feedback_data.get(
                    "feedback", "You're making good progress on your goals."
                )
                suggestions = feedback_data.get(
                    "suggestions",
                    [
                        "Continue with your current productivity patterns",
                        "Consider reviewing your goals weekly to maintain focus",
                    ],
                )
            else:
                # Fallback feedback
                feedback = "You're making steady progress on your goals."
                suggestions = [
                    "Continue with your current productivity patterns",
                    "Consider reviewing your goals weekly to maintain focus",
                ]
        except json.JSONDecodeError:
            # Fallback feedback
            feedback = "You're making steady progress on your goals."
            suggestions = [
                "Continue with your current productivity patterns",
                "Consider reviewing your goals weekly to maintain focus",
            ]

        return AIFeedbackResponse(feedback=feedback, suggestions=suggestions)
    except Exception as e:
        logging.error(
            f"Error generating AI feedback for user {current_user['id']}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


# GET /ai-feedback/history: get feedback history
@router.get(
    "/ai-feedback/history",
    response_model=FeedbackHistoryResponse,
    tags=["Insights"],
    summary="Get feedback history",
)
async def get_feedback_history(
    user_id: str, current_user: dict = Depends(get_current_user)
):
    try:
        logging.info(f"User {current_user['id']} requesting feedback history")

        # Get feedback history from database
        supabase = get_supabase_client()
        feedback_result = (
            supabase.table("ai_feedback_history")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        if feedback_result.data:
            feedback_history = [
                {
                    "date": item.get("created_at", ""),
                    "feedback": item.get("feedback", ""),
                    "suggestions": item.get("suggestions", []),
                }
                for item in feedback_result.data
            ]
        else:
            # Generate initial feedback if no history exists
            prompt = """Generate a welcome feedback message for a new user. Provide encouraging feedback and suggestions in JSON format:
{
    "feedback": "Welcome! You're starting your productivity journey.",
    "suggestions": [
        "Start by creating your first goal",
        "Try scheduling your most important task for tomorrow",
        "Set up a daily review routine"
    ]
}"""

            response = await generate_openai_text(
                prompt=prompt,
                model="gpt-4-turbo-preview",
                max_tokens=300,
                temperature=0.4,
            )

            if "error" not in response:
                import json

                try:
                    response_text = response.get("generated_text", "")
                    start_idx = response_text.find("{")
                    end_idx = response_text.rfind("}") + 1
                    if start_idx != -1 and end_idx != 0:
                        json_str = response_text[start_idx:end_idx]
                        feedback_data = json.loads(json_str)
                        feedback_history = [
                            {
                                "date": datetime.now().isoformat(),
                                "feedback": feedback_data.get(
                                    "feedback", "Welcome to your productivity journey!"
                                ),
                                "suggestions": feedback_data.get(
                                    "suggestions", ["Start by creating your first goal"]
                                ),
                            }
                        ]
                    else:
                        feedback_history = [
                            {
                                "date": datetime.now().isoformat(),
                                "feedback": "Welcome to your productivity journey!",
                                "suggestions": ["Start by creating your first goal"],
                            }
                        ]
                except json.JSONDecodeError:
                    feedback_history = [
                        {
                            "date": datetime.now().isoformat(),
                            "feedback": "Welcome to your productivity journey!",
                            "suggestions": ["Start by creating your first goal"],
                        }
                    ]
            else:
                feedback_history = [
                    {
                        "date": datetime.now().isoformat(),
                        "feedback": "Welcome to your productivity journey!",
                        "suggestions": ["Start by creating your first goal"],
                    }
                ]

        return FeedbackHistoryResponse(feedback_history=feedback_history)
    except Exception as e:
        logging.error(
            f"Error getting feedback history for user {current_user['id']}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


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
async def get_user_insights(
    request: UserInsightsRequest, current_user: dict = Depends(get_current_user)
):
    try:
        logging.info(f"User {current_user['id']} requesting insights")

        # Get user's data from database
        supabase = get_supabase_client()

        # Fetch tasks, goals, flashcards, and schedule blocks
        tasks_result = (
            supabase.table("tasks")
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
        flashcards_result = (
            supabase.table("flashcards")
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

        tasks = tasks_result.data if tasks_result.data else []
        goals = goals_result.data if goals_result.data else []
        flashcards = flashcards_result.data if flashcards_result.data else []
        schedule_blocks = schedule_result.data if schedule_result.data else []

        # Calculate real metrics
        completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
        missed_tasks = len([t for t in tasks if t.get("status") == "missed"])
        rescheduled_tasks = len([t for t in tasks if t.get("rescheduled_count", 0) > 0])

        reviewed_flashcards = len([f for f in flashcards if f.get("last_reviewed_at")])
        forgotten_flashcards = len(
            [f for f in flashcards if f.get("ease_factor", 2.5) < 2.0]
        )
        avg_accuracy = (
            sum([f.get("accuracy", 80) for f in flashcards]) / len(flashcards)
            if flashcards
            else 80
        )

        # Generate AI prompt for insights
        prompt = f"""Analyze this user's productivity data and generate personalized insights:

TASK DATA:
- Total tasks: {len(tasks)}
- Completed: {completed_tasks}
- Missed: {missed_tasks}
- Rescheduled: {rescheduled_tasks}

GOAL DATA:
- Total goals: {len(goals)}
- Active goals: {len([g for g in goals if g.get('status') == 'active'])}
- Average progress: {sum([g.get('progress', 0) for g in goals]) / len(goals) if goals else 0:.1f}%

FLASHCARD DATA:
- Total cards: {len(flashcards)}
- Reviewed: {reviewed_flashcards}
- Difficult cards: {forgotten_flashcards}
- Average accuracy: {avg_accuracy:.1f}%

SCHEDULE DATA:
- Total blocks: {len(schedule_blocks)}
- Fixed blocks: {len([s for s in schedule_blocks if s.get('is_fixed')])}
- Rescheduled blocks: {len([s for s in schedule_blocks if s.get('is_rescheduled')])}

Generate insights in JSON format:
{{
    "task_summary": {{
        "completed": {completed_tasks},
        "missed": {missed_tasks},
        "rescheduled": {rescheduled_tasks},
        "overbooked_days": ["list of dates with too many tasks"]
    }},
    "flashcard_summary": {{
        "reviewed": {reviewed_flashcards},
        "forgotten": {forgotten_flashcards},
        "avg_accuracy": {avg_accuracy:.1f},
        "most_forgotten_deck": "deck name"
    }},
    "goal_progress": [
        {{
            "goal_id": "goal_id",
            "title": "goal title",
            "progress": "progress percentage",
            "status": "on_track/behind/ahead"
        }}
    ],
    "suggestions": [
        "Specific actionable suggestion 1",
        "Specific actionable suggestion 2",
        "Specific actionable suggestion 3"
    ]
}}

Focus on actionable insights that can help improve productivity and learning."""

        # Call OpenAI API
        response = await generate_openai_text(
            prompt=prompt, model="gpt-4-turbo-preview", max_tokens=1000, temperature=0.3
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
                    "user_id": current_user["id"],
                    "date_range": {
                        "start": request.start_date
                        or datetime.now().strftime("%Y-%m-%d"),
                        "end": request.end_date or datetime.now().strftime("%Y-%m-%d"),
                    },
                    "task_summary": insights_data.get(
                        "task_summary",
                        {
                            "completed": completed_tasks,
                            "missed": missed_tasks,
                            "rescheduled": rescheduled_tasks,
                            "overbooked_days": [],
                        },
                    ),
                    "flashcard_summary": insights_data.get(
                        "flashcard_summary",
                        {
                            "reviewed": reviewed_flashcards,
                            "forgotten": forgotten_flashcards,
                            "avg_accuracy": avg_accuracy,
                            "most_forgotten_deck": "General",
                        },
                    ),
                    "goal_progress": insights_data.get("goal_progress", []),
                    "suggestions": insights_data.get(
                        "suggestions",
                        [
                            "Continue with your current productivity patterns",
                            "Review difficult flashcards more frequently",
                            "Set realistic daily task limits",
                        ],
                    ),
                }
            else:
                # Fallback insights
                insights = {
                    "user_id": current_user["id"],
                    "date_range": {
                        "start": request.start_date
                        or datetime.now().strftime("%Y-%m-%d"),
                        "end": request.end_date or datetime.now().strftime("%Y-%m-%d"),
                    },
                    "task_summary": {
                        "completed": completed_tasks,
                        "missed": missed_tasks,
                        "rescheduled": rescheduled_tasks,
                        "overbooked_days": [],
                    },
                    "flashcard_summary": {
                        "reviewed": reviewed_flashcards,
                        "forgotten": forgotten_flashcards,
                        "avg_accuracy": avg_accuracy,
                        "most_forgotten_deck": "General",
                    },
                    "goal_progress": [],
                    "suggestions": [
                        "Continue with your current productivity patterns",
                        "Review difficult flashcards more frequently",
                        "Set realistic daily task limits",
                    ],
                }
        except json.JSONDecodeError:
            # Fallback insights
            insights = {
                "user_id": current_user["id"],
                "date_range": {
                    "start": request.start_date or datetime.now().strftime("%Y-%m-%d"),
                    "end": request.end_date or datetime.now().strftime("%Y-%m-%d"),
                },
                "task_summary": {
                    "completed": completed_tasks,
                    "missed": missed_tasks,
                    "rescheduled": rescheduled_tasks,
                    "overbooked_days": [],
                },
                "flashcard_summary": {
                    "reviewed": reviewed_flashcards,
                    "forgotten": forgotten_flashcards,
                    "avg_accuracy": avg_accuracy,
                    "most_forgotten_deck": "General",
                },
                "goal_progress": [],
                "suggestions": [
                    "Continue with your current productivity patterns",
                    "Review difficult flashcards more frequently",
                    "Set realistic daily task limits",
                ],
            }

        return UserInsightsResponse(**insights)
    except Exception as e:
        logging.error(
            f"Error generating insights for user {current_user['id']}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


# TODO: Continue with remaining endpoints (notifications, insights, etc.)
# The remaining endpoints can be refactored similarly to use Supabase
