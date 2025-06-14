from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks, Request, Response
from models.text import TextGenerationRequest, TextGenerationResponse
from services.openai_integration import generate_openai_text
import logging
import os
from starlette.status import HTTP_401_UNAUTHORIZED
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import json
import aioredis
from services.review_engine import ReviewEngine
from uuid import uuid4
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

router = APIRouter()

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# Initialize the rate limiter
limiter = Limiter(key_func=get_remote_address)

# Placeholder for API key authentication
async def api_key_auth(api_key: str = Header(...)):
    # Example logic to validate API key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Replace with your actual keys or fetch from a secure source
    if api_key != OPENAI_API_KEY:
        logging.warning("Invalid API Key")
        raise HTTPException(status_code=403, detail="Not authenticated")
    return api_key

# Initialize Redis client for caching
async def get_redis_client():
    return await aioredis.create_redis_pool("redis://localhost")

@router.post("/generate-text", response_model=TextGenerationResponse, tags=["Text Generation"], summary="Generate text using OpenAI API")
@limiter.limit("5/minute")
async def generate_text_endpoint(request: Request, request_data: TextGenerationRequest, api_key: str = Depends(api_key_auth)):
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
            stop=request_data.stop
        )
        if "error" in generated_text:
            logging.warning(f"Error in text generation: {generated_text['error']}")
            raise HTTPException(status_code=500, detail=generated_text['error'])
        logging.info(f"Generated text: {generated_text['generated_text']}")
        response = TextGenerationResponse(
            original_prompt=request_data.prompt,
            model=request_data.model,
            generated_text=generated_text['generated_text'],
            total_tokens=generated_text['total_tokens']
        )

        # Cache the response
        await redis.set(cache_key, json.dumps(response), expire=3600)  # Cache for 1 hour
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

@router.post("/daily-brief", summary="Generate Daily Brief", description="Generates a daily summary of tasks.")
@limiter.limit("5/minute")
async def generate_daily_brief(request: Request, request_data: DailyBriefRequest, background_tasks: BackgroundTasks):
    try:
        logging.info("Generating daily brief")
        # Add the task to be processed in the background
        background_tasks.add_task(process_daily_brief, request_data.date, request_data.user_id)
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
        {"question": "What is the boiling point of water?", "answer": "100°C"}
    ]
    return questions

@router.post("/quiz-me", summary="Generate Quiz Questions", description="Takes a deck ID and returns 3–5 questions from that deck to quiz the user.")
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
    return [text[i:i+max_tokens] for i in range(0, len(text), max_tokens)]

# Function to summarize notes
async def summarize_notes(notes: str, summary_type: str) -> str:
    # Placeholder for the actual summarization logic
    logging.info(f"Summarizing notes with summary type: {summary_type}")
    # Simulate summarization
    return f"Summary ({summary_type}): {notes[:100]}..."

@router.post("/summarize-notes", summary="Summarize Notes", description="Compress long notes into key takeaways.")
@limiter.limit("5/minute")
async def summarize_notes_endpoint(request: SummarizeNotesRequest):
    try:
        # Input size validation
        if len(request.notes) > 5000:  # Example limit
            logging.warning(f"User {request.user_id} submitted notes exceeding size limit: {len(request.notes)} characters")
            raise HTTPException(status_code=400, detail="Notes exceed the maximum allowed size of 5000 characters.")

        logging.info(f"User {request.user_id} is summarizing notes of length {len(request.notes)}")
        chunks = await split_into_chunks(request.notes)
        summaries = [await summarize_notes(chunk, request.summary_type) for chunk in chunks]
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
async def suggest_reschedule_logic(request: SuggestRescheduleRequest) -> RescheduleSuggestion:
    # Placeholder for the actual AI logic
    logging.info(f"Suggesting reschedule for task: {request.task_title}")
    # Simulate AI response
    suggested_time = "Friday, 9:00 AM - 10:30 AM"
    reason = "Closer to the deadline. User has higher focus in the morning and Friday is still open."
    return RescheduleSuggestion(suggested_time=suggested_time, reason=reason)

@router.post("/suggest-reschedule", summary="Suggest Reschedule Time", description="Suggest an optimal new time for a missed or rescheduled task based on context.")
@limiter.limit("5/minute")
async def suggest_reschedule_endpoint(request: SuggestRescheduleRequest):
    try:
        logging.info(f"Received reschedule request for task: {request.task_title}")
        suggestion = await suggest_reschedule_logic(request)
        logging.info(f"Suggested time: {suggestion.suggested_time}, Reason: {suggestion.reason}")
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

# Define the response models
class ExtractedTask(BaseModel):
    task: str
    priority: Optional[str] = "medium"
    time_estimate_minutes: Optional[int] = None
    goal: Optional[str] = None

class ExtractTasksResponse(BaseModel):
    extracted_tasks: List[ExtractedTask]

# Function to generate AI prompt
async def generate_ai_prompt(text: str, goal_context: Optional[str] = None) -> str:
    prompt = f"""
    Extract clear, actionable tasks from the following notes. 
    Return a JSON list with fields: task, priority (low/medium/high), time_estimate_minutes, and goal (if mentioned).

    Text: {text}

    {f"Goal Context: {goal_context}" if goal_context else ""}
    """
    return prompt

@router.post("/extract-tasks-from-text", response_model=ExtractTasksResponse, summary="Extract structured tasks from messy notes", tags=["AI Tasks & Memory"])
async def extract_tasks(request: ExtractTasksRequest):
    try:
        logging.info(f"Extracting tasks for user with text length {len(request.text)}")
        redis = await get_redis_client()
        cache_key = f"extract_tasks:{hash(request.text)}"
        cached_tasks = await redis.get(cache_key)
        if cached_tasks:
            logging.info("Cache hit for task extraction")
            return {"extracted_tasks": json.loads(cached_tasks)}

        prompt = await generate_ai_prompt(request.text, request.goal_context)
        # Simulate AI call
        ai_response = '[{"task": "Write project proposal", "priority": "high", "time_estimate_minutes": 90, "goal": "Launch SaaS"}]'
        try:
            tasks = json.loads(ai_response)
        except json.JSONDecodeError as e:
            logging.error(f"JSON decoding failed: {e}")
            raise HTTPException(status_code=500, detail="Invalid response format from AI")

        await redis.set(cache_key, json.dumps(tasks))
        return {"extracted_tasks": tasks}
    except Exception as e:
        logging.error(f"Task extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Task extraction failed")

# Define the request model for input validation
class PlanMyDayRequest(BaseModel):
    user_id: str
    date: str  # e.g. "2025-06-06"
    focus_hours: Optional[List[str]] = None  # e.g. ["09:00-12:00", "14:00-17:00"]
    include_reflections: Optional[bool] = False
    preferred_working_hours: Optional[List[str]] = None  # e.g. ["08:00-12:00", "13:00-17:00"]
    break_times: Optional[List[str]] = None  # e.g. ["12:00-13:00"]

# Define the response models
class TimeBlock(BaseModel):
    start_time: str
    end_time: str
    task_name: str
    task_id: Optional[str]
    goal: Optional[str]
    priority: Optional[str]

class PlanMyDayResponse(BaseModel):
    date: str
    user_id: str
    timeblocks: List[TimeBlock]
    notes: Optional[str]  # Optional summary or planning AI notes

# Function to generate AI prompt for planning
async def generate_planning_prompt(tasks: List[dict], focus_hours: Optional[List[str]]) -> str:
    prompt = f"""
    Given these tasks and time windows, create a focused, realistic plan.
    Tasks: {tasks}
    Focus Hours: {focus_hours}
    """
    return prompt

@router.post("/plan-my-day", response_model=PlanMyDayResponse, tags=["Planning"], summary="AI-generated daily plan")
async def plan_my_day(request: PlanMyDayRequest):
    """
    Generate an AI-powered daily time-blocked plan based on your pending tasks, priorities, and focus windows.
    """
    try:
        logging.info(f"Planning day for user {request.user_id} on {request.date}")
        # Simulate fetching tasks
        tasks = [
            {"task_name": "Write report", "duration": 120, "priority": "high"},
            {"task_name": "Email follow-up", "duration": 30, "priority": "medium"}
        ]
        prompt = await generate_planning_prompt(tasks, request.focus_hours)
        # Simulate AI call
        ai_response = '[{"start_time": "09:00", "end_time": "11:00", "task_name": "Write report", "priority": "high"}, {"start_time": "11:30", "end_time": "12:00", "task_name": "Email follow-up", "priority": "medium"}]'
        try:
            timeblocks = json.loads(ai_response)
        except json.JSONDecodeError as e:
            logging.error(f"JSON decoding failed: {e}")
            raise HTTPException(status_code=500, detail="Invalid response format from AI")

        # Incorporate user preferences into the plan
        # This is a placeholder for actual logic
        if request.preferred_working_hours:
            logging.info(f"User preferred working hours: {request.preferred_working_hours}")
        if request.break_times:
            logging.info(f"User break times: {request.break_times}")

        return PlanMyDayResponse(date=request.date, user_id=request.user_id, timeblocks=timeblocks, notes="AI-generated plan")
    except Exception as e:
        logging.error(f"Failed to plan day: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate plan")

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

# In-memory storage for goals (for demonstration purposes)
goals_db = []

@router.post("/goals", response_model=GoalResponse, tags=["Goals"], summary="Create and track high-level goals")
async def create_goal(request: GoalRequest):
    """
    Create a new goal and track its progress.
    """
    try:
        logging.info(f"Creating goal for user {request.user_id} with title: {request.title}")
        # Simulate goal creation
        goal_id = f"goal_{len(goals_db) + 1}"
        now = datetime.now()
        new_goal = {
            "goal_id": goal_id,
            "user_id": request.user_id,
            "title": request.title,
            "description": request.description,
            "due_date": request.due_date,
            "priority": request.priority,
            "status": "Not Started",
            "progress": 0,
            "created_at": now,
            "updated_at": now,
            "analytics": {"tags": ["Academic", "Health", "Career"]},
            "is_starred": request.is_starred
        }
        goals_db.append(new_goal)
        return GoalResponse(**new_goal)
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

# In-memory storage for schedules (for demonstration purposes)
schedules_db = []

@router.post("/schedule", response_model=ScheduleBlock, tags=["Schedule"], summary="Create a scheduled block")
async def create_schedule_block(request: ScheduleBlock):
    """
    Create a new schedule block for a task.
    """
    try:
        logging.info(f"Creating schedule block for user {request.user_id} from {request.start_time} to {request.end_time}")
        # Simulate schedule creation
        schedule_id = f"schedule_{len(schedules_db) + 1}"
        new_schedule = request.dict()
        new_schedule["schedule_id"] = schedule_id
        schedules_db.append(new_schedule)
        return new_schedule
    except Exception as e:
        logging.error(f"Failed to create schedule block: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule block")

@router.get("/schedule", response_model=List[ScheduleBlock], tags=["Schedule"], summary="Read scheduled blocks")
async def read_scheduled_blocks(user_id: str, view: Optional[str] = "week"):
    """
    Retrieve scheduled blocks for a user.
    """
    try:
        logging.info(f"Retrieving schedule blocks for user {user_id} with view {view}")
        # Filter schedules by user_id
        user_schedules = [s for s in schedules_db if s["user_id"] == user_id]
        return user_schedules
    except Exception as e:
        logging.error(f"Failed to retrieve schedule blocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve schedule blocks")

@router.put("/schedule/{schedule_id}", response_model=ScheduleBlock, tags=["Schedule"], summary="Update a scheduled block")
async def update_schedule_block(schedule_id: str, request: ScheduleBlock):
    """
    Update an existing schedule block.
    """
    try:
        logging.info(f"Updating schedule block {schedule_id}")
        # Find and update the schedule
        for schedule in schedules_db:
            if schedule["schedule_id"] == schedule_id:
                schedule.update(request.dict())
                return schedule
        raise HTTPException(status_code=404, detail="Schedule block not found")
    except Exception as e:
        logging.error(f"Failed to update schedule block: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule block")

@router.delete("/schedule/{schedule_id}", tags=["Schedule"], summary="Delete a scheduled block")
async def delete_schedule_block(schedule_id: str):
    """
    Delete a schedule block.
    """
    try:
        logging.info(f"Deleting schedule block {schedule_id}")
        # Find and delete the schedule
        global schedules_db
        schedules_db = [s for s in schedules_db if s["schedule_id"] != schedule_id]
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

# In-memory storage for flashcards (for demonstration purposes)
flashcards_db = []

@router.post("/flashcards", response_model=FlashcardResponse, tags=["Flashcards"], summary="Create a flashcard")
async def create_flashcard(request: FlashcardRequest):
    """
    Create a new flashcard.
    """
    try:
        logging.info(f"Creating flashcard for user {request.user_id}")
        # Simulate flashcard creation
        flashcard_id = f"flashcard_{len(flashcards_db) + 1}"
        new_flashcard = request.dict()
        new_flashcard["flashcard_id"] = flashcard_id
        flashcards_db.append(new_flashcard)
        return new_flashcard
    except Exception as e:
        logging.error(f"Failed to create flashcard: {e}")
        raise HTTPException(status_code=500, detail="Failed to create flashcard")

@router.get("/flashcards", response_model=List[FlashcardResponse], tags=["Flashcards"], summary="Read flashcards")
async def read_flashcards(user_id: str):
    """
    Retrieve flashcards for a user.
    """
    try:
        logging.info(f"Retrieving flashcards for user {user_id}")
        # Filter flashcards by user_id
        user_flashcards = [f for f in flashcards_db if f["user_id"] == user_id]
        return user_flashcards
    except Exception as e:
        logging.error(f"Failed to retrieve flashcards: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve flashcards")

@router.get("/flashcards/{flashcard_id}", response_model=FlashcardResponse, tags=["Flashcards"], summary="Read a flashcard")
async def read_flashcard(flashcard_id: str):
    """
    Retrieve a single flashcard by ID.
    """
    try:
        logging.info(f"Retrieving flashcard {flashcard_id}")
        flashcard = next((f for f in flashcards_db if f["flashcard_id"] == flashcard_id), None)
        if not flashcard:
            raise HTTPException(status_code=404, detail="Flashcard not found")
        return flashcard
    except Exception as e:
        logging.error(f"Failed to retrieve flashcard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve flashcard")

@router.put("/flashcards/{flashcard_id}", response_model=FlashcardResponse, tags=["Flashcards"], summary="Update a flashcard")
async def update_flashcard(flashcard_id: str, request: FlashcardRequest):
    """
    Update an existing flashcard.
    """
    try:
        logging.info(f"Updating flashcard {flashcard_id}")
        # Find and update the flashcard
        for flashcard in flashcards_db:
            if flashcard["flashcard_id"] == flashcard_id:
                flashcard.update(request.dict())
                return flashcard
        raise HTTPException(status_code=404, detail="Flashcard not found")
    except Exception as e:
        logging.error(f"Failed to update flashcard: {e}")
        raise HTTPException(status_code=500, detail="Failed to update flashcard")

@router.delete("/flashcards/{flashcard_id}", tags=["Flashcards"], summary="Delete a flashcard")
async def delete_flashcard(flashcard_id: str):
    """
    Delete a flashcard.
    """
    try:
        logging.info(f"Deleting flashcard {flashcard_id}")
        # Find and delete the flashcard
        global flashcards_db
        flashcards_db = [f for f in flashcards_db if f["flashcard_id"] != flashcard_id]
        return {"message": "Flashcard deleted"}
    except Exception as e:
        logging.error(f"Failed to delete flashcard: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete flashcard")

@router.get("/review-plan", response_model=List[FlashcardResponse], tags=["Review"], summary="Get today's review plan")
async def get_review_plan(user_id: str, time_available: int = 30):
    """
    Retrieve a personalized review plan for the user based on available time.
    """
    try:
        logging.info(f"Generating review plan for user {user_id} with {time_available} minutes available")
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

# Simulate a function to check if a flashcard exists
async def flashcard_exists(flashcard_id: str) -> bool:
    # Placeholder logic to check if a flashcard exists
    return any(flashcard["flashcard_id"] == flashcard_id for flashcard in flashcards_db)

# Simulate a function to update flashcard review
async def update_flashcard_review(flashcard_id: str, was_correct: bool):
    # Placeholder logic to update flashcard review
    for flashcard in flashcards_db:
        if flashcard["flashcard_id"] == flashcard_id:
            # Update logic here
            pass

# Simulate SM-2 algorithm
async def calculate_next_interval(ease_factor: float, repetitions: int, was_correct: bool) -> (int, float):
    # SM-2 algorithm logic
    if was_correct:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        repetitions += 1
    else:
        repetitions = 0
        interval = 1
    ease_factor = max(1.3, ease_factor + (0.1 - (5 - 3) * (0.08 + (5 - 3) * 0.02)))
    return repetitions, ease_factor

@router.post("/review/update", tags=["Review"], summary="Update flashcard review result", response_description="Review updated successfully")
async def update_review_result(request: ReviewUpdateRequest):
    """
    Log the outcome of a flashcard review and update review performance metrics.
    """
    try:
        logging.info(f"Updating review result for flashcard {request.flashcard_id}")
        if not await flashcard_exists(request.flashcard_id):
            raise HTTPException(status_code=404, detail="Flashcard not found")

        # Simulate atomic transaction
        # with database.transaction():
        await update_flashcard_review(request.flashcard_id, request.was_correct)

        # Calculate next review interval
        repetitions, ease_factor = await calculate_next_interval(2.5, 0, request.was_correct)

        # Simulate next review date calculation
        next_review_date = datetime.now() + timedelta(days=repetitions)

        return {"message": "Review updated successfully", "next_review_date": next_review_date}
    except Exception as e:
        logging.error(f"Failed to update review result: {e}")
        raise HTTPException(status_code=500, detail="Failed to update review result")

# Define the request model for input validation
class UserInsightsRequest(BaseModel):
    user_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# Define the response model
class UserInsightsResponse(BaseModel):
    user_id: str
    date_range: dict
    task_summary: dict
    flashcard_summary: dict
    goal_progress: List[dict]
    suggestions: List[str]

@router.get("/user-insights", response_model=UserInsightsResponse, tags=["Insights"], summary="Get user productivity insights")
async def get_user_insights(request: UserInsightsRequest):
    """
    Provide insights into user productivity and scheduling habits, including trends, missed patterns, and overbooking.
    """
    try:
        logging.info(f"Generating insights for user {request.user_id}")
        # Simulate fetching insights
        insights = {
            "user_id": request.user_id,
            "date_range": {"start": request.start_date or "2025-06-01", "end": request.end_date or "2025-06-07"},
            "task_summary": {
                "completed": 12,
                "missed": 3,
                "rescheduled": 2,
                "overbooked_days": ["2025-06-03", "2025-06-04"]
            },
            "flashcard_summary": {
                "reviewed": 45,
                "forgotten": 9,
                "avg_accuracy": 80,
                "most_forgotten_deck": "Neuroscience"
            },
            "goal_progress": [
                {
                    "goal_id": "goal123",
                    "title": "Finish ML Course",
                    "progress": "60%",
                    "status": "on_track"
                }
            ],
            "suggestions": [
                "Review 'Neuroscience' deck earlier in the day",
                "Avoid scheduling >5 tasks on weekdays",
                "You're most consistent at 9–11 AM. Leverage that."
            ]
        }
        return UserInsightsResponse(**insights)
    except Exception as e:
        logging.error(f"Failed to generate user insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate user insights")

# Define the request model for input validation
class AIFeedbackRequest(BaseModel):
    user_id: str
    week_start: Optional[datetime] = None
    week_end: Optional[datetime] = None

# Define the response model
class AIFeedbackResponse(BaseModel):
    feedback: str
    suggestions: List[str]

# Simulate a function to fetch user preferences
async def get_user_preferences(user_id: str) -> dict:
    # Placeholder logic to fetch user preferences
    return {
        "feedback_topics": ["productivity", "learning progress"],
        "feedback_frequency": "weekly"
    }

# Simulate an analysis module
async def analyze_user_data(user_id: str) -> dict:
    # Placeholder logic to analyze user data
    return {
        "areas_for_improvement": ["Improve time management", "Focus on deep work"],
        "actionable_steps": [
            "Set specific goals for each day",
            "Limit distractions during work hours"
        ]
    }

# Simulate a database for feedback history
feedback_history_db = []

# Function to log feedback
async def log_feedback(user_id: str, feedback: str, suggestions: List[str]):
    feedback_entry = {
        "user_id": user_id,
        "feedback": feedback,
        "suggestions": suggestions,
        "timestamp": datetime.now(),
        "acknowledgment_status": False
    }
    feedback_history_db.append(feedback_entry)

# Define the response model for feedback history
class FeedbackHistoryResponse(BaseModel):
    feedback_history: List[dict]

@router.get("/ai-feedback/history", response_model=FeedbackHistoryResponse, tags=["Insights"], summary="Get feedback history")
async def get_feedback_history(user_id: str):
    """
    Retrieve feedback history for a user.
    """
    try:
        logging.info(f"Retrieving feedback history for user {user_id}")
        user_feedback_history = [entry for entry in feedback_history_db if entry["user_id"] == user_id]
        return FeedbackHistoryResponse(feedback_history=user_feedback_history)
    except Exception as e:
        logging.error(f"Failed to retrieve feedback history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback history")

@router.post("/ai-feedback", response_model=AIFeedbackResponse, tags=["Insights"], summary="Get AI-generated feedback for the week")
async def ai_feedback(request: AIFeedbackRequest, api_key: str = Depends(api_key_auth)):
    """
    Provide AI-generated feedback and suggestions based on the user's weekly activities.
    """
    try:
        logging.info(f"Generating AI feedback for user {request.user_id}")
        # Fetch user preferences
        preferences = await get_user_preferences(request.user_id)
        logging.info(f"User preferences: {preferences}")

        # Analyze user data
        analysis = await analyze_user_data(request.user_id)
        logging.info(f"Analysis results: {analysis}")

        # Simulate AI feedback generation
        feedback = "You have been consistent with your tasks this week. Keep up the good work!"
        suggestions = analysis["actionable_steps"]

        # Log feedback
        await log_feedback(request.user_id, feedback, suggestions)

        return AIFeedbackResponse(feedback=feedback, suggestions=suggestions)
    except Exception as e:
        logging.error(f"Failed to generate AI feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI feedback")

# Define the request model for input validation
class UserSettingsRequest(BaseModel):
    user_id: str
    feedback_topics: Optional[List[str]] = None  # e.g., ['productivity', 'learning progress']
    feedback_frequency: Optional[str] = 'weekly'  # e.g., 'daily', 'weekly'

# Define the response model
class UserSettingsResponse(BaseModel):
    message: str

@router.post("/settings", response_model=UserSettingsResponse, tags=["Settings"], summary="Set user preferences for feedback")
async def set_user_settings(request: UserSettingsRequest):
    """
    Allow users to set their preferences for feedback, including topics and frequency.
    """
    try:
        logging.info(f"Setting preferences for user {request.user_id}")
        # Simulate saving user settings
        # This is where you would save the settings to a database
        return UserSettingsResponse(message="User settings updated successfully")
    except Exception as e:
        logging.error(f"Failed to set user settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to set user settings")

# Update the Pydantic model for notifications
class Notification(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    send_time: datetime
    type: str = "reminder"
    is_sent: bool = False
    is_read: bool = False
    repeat_interval: Optional[str] = None  # daily, weekly, custom
    category: Optional[str] = "task"  # task, goal, system, alert

# In-memory storage for notifications
notifications = []

# POST /notifications: create a new notification
@router.post("/notifications", tags=["Notifications"], summary="Create a new notification")
async def create_notification(notification: Notification):
    try:
        notification.id = str(uuid4())  # Generate a unique ID
        notifications.append(notification)
        logging.info(f"Notification created: {notification}")
        return {"message": "Notification created successfully", "notification": notification}
    except Exception as e:
        logging.error(f"Error creating notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create notification")

# GET /notifications?user_id=...: get all notifications for a user
@router.get("/notifications", tags=["Notifications"], summary="Get all notifications for a user")
async def get_notifications(user_id: str):
    try:
        user_notifications = [n for n in notifications if n.user_id == user_id]
        logging.info(f"Retrieved notifications for user {user_id}")
        return {"notifications": user_notifications}
    except Exception as e:
        logging.error(f"Error retrieving notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")

# PUT /notifications/{notification_id}: update an existing notification
@router.put("/notifications/{notification_id}", tags=["Notifications"], summary="Update an existing notification")
async def update_notification(notification_id: str, updated_notification: Notification):
    try:
        for i, n in enumerate(notifications):
            if n.id == notification_id:
                notifications[i] = updated_notification
                logging.info(f"Notification updated: {updated_notification}")
                return {"message": "Notification updated successfully", "notification": updated_notification}
        raise HTTPException(status_code=404, detail="Notification not found")
    except Exception as e:
        logging.error(f"Error updating notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification")

# DELETE /notifications/{notification_id}: delete a notification
@router.delete("/notifications/{notification_id}", tags=["Notifications"], summary="Delete a notification")
async def delete_notification(notification_id: str):
    try:
        global notifications
        notifications = [n for n in notifications if n.id != notification_id]
        logging.info(f"Notification deleted: {notification_id}")
        return {"message": "Notification deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")

# Add support for marking a notification as read
@router.put("/notifications/{notification_id}/read", tags=["Notifications"], summary="Mark a notification as read")
async def mark_notification_as_read(notification_id: str):
    try:
        for notification in notifications:
            if notification.id == notification_id:
                notification.is_read = True
                logging.info(f"Notification marked as read: {notification_id}")
                return {"message": "Notification marked as read"}
        raise HTTPException(status_code=404, detail="Notification not found")
    except Exception as e:
        logging.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

# Add endpoint to get unread notification count
@router.get("/notifications/unread-count", tags=["Notifications"], summary="Get unread notification count")
async def get_unread_notification_count(user_id: str):
    try:
        unread_count = sum(1 for n in notifications if n.user_id == user_id and not n.is_read)
        logging.info(f"Unread notification count for user {user_id}: {unread_count}")
        return {"unread_count": unread_count}
    except Exception as e:
        logging.error(f"Error retrieving unread notification count: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve unread notification count")

@router.post("/notion-sync", summary="Sync notes and tasks from/to Notion")
async def notion_sync(user_id: str):
    # Placeholder for the actual Notion sync logic
    logging.info(f"Syncing notes and tasks for user {user_id}")
    # Simulate sync process
    return {"message": "Notes and tasks synced successfully"}

@router.post("/notion-sync", summary="Sync notes and tasks from/to Notion")
async def notion_sync(user_id: str):
    # Placeholder for the actual Notion sync logic
    logging.info(f"Syncing notes and tasks for user {user_id}")
    # Simulate sync process
    return {"message": "Notes and tasks synced successfully"}

# Define the request model for AI command
class AICommandRequest(BaseModel):
    command: str
    context: Optional[dict] = None

# Define the response model for AI command
class AICommandResponse(BaseModel):
    result: dict

@router.post("/ai-command", response_model=AICommandResponse, tags=["AI Command"], summary="Handle command-palette input")
async def ai_command(request: AICommandRequest):
    """
    Process a command-palette input and route to the appropriate function.
    """
    try:
        logging.info(f"Processing AI command: {request.command}")
        # Simulate OpenAI call to parse intent
        # This is a placeholder for actual OpenAI integration
        if "summarize" in request.command:
            result = {"action": "summarize_notes", "details": "Summarizing notes..."}
        elif "create flashcards" in request.command:
            result = {"action": "create_flashcards", "details": "Creating flashcards..."}
        else:
            result = {"action": "unknown", "details": "Command not recognized."}

        return AICommandResponse(result=result)
    except Exception as e:
        logging.error(f"Failed to process AI command: {e}")
        raise HTTPException(status_code=500, detail="Failed to process AI command")

# Define a standardized error response model
class ErrorResponse(BaseModel):
    code: int
    message: str

# Example of using the standardized error response
@router.post("/example-endpoint")
@limiter.limit("5/minute")
async def example_endpoint(request: Request):
    try:
        # Process request and generate response
        response = {"data": "example"}
        return response
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        error_response = ErrorResponse(code=500, message="Internal Server Error")
        return JSONResponse(status_code=500, content=error_response.dict())

@router.post("/generate-flashcards", tags=["AI"], summary="Generate flashcards from notes", description="Turn raw notes or textbook content into flashcards.")
async def generate_flashcards(notes: str, topic_tags: Optional[List[str]] = None):
    try:
        flashcards = []
        for note in notes.split("\n"):
            question = f"What is the key point of: {note}?"
            answer = note
            flashcards.append({"question": question, "answer": answer})
        return {"flashcards": flashcards}
    except Exception as e:
        logging.error(f"Error generating flashcards: {str(e)}")
        error_response = ErrorResponse(error="Flashcard Generation Error", detail=str(e))
        return JSONResponse(status_code=500, content=error_response.dict())

@router.post("/simulate-openai-failure", summary="Simulate OpenAI downtime")
async def simulate_openai_failure():
    return Response(content='{"error": "OpenAI Down"}', status_code=503, media_type="application/json")

@router.get("/force-error", summary="Force a generic error for testing")
async def force_error():
    return Response(content='{"message": "Simulated error for testing error handling"}', status_code=500, media_type="application/json")

@router.get("/stream", summary="Stream endpoint placeholder")
async def stream():
    return {"message": "Stream started"}

@router.get("/daily-brief", summary="Daily brief placeholder")
async def daily_brief():
    return {"brief": "This is your daily brief."} 