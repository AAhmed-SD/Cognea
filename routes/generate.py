from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks
from models.text import TextGenerationRequest, TextGenerationResponse
from services.openai_integration import generate_openai_text
import logging
import os
from starlette.status import HTTP_401_UNAUTHORIZED
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import aioredis

router = APIRouter()

# Set up basic logging
logging.basicConfig(level=logging.INFO)

# Placeholder for API key authentication
async def api_key_auth(api_key: str = Header(...)):
    # Example logic to validate API key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Replace with your actual keys or fetch from a secure source
    if api_key not in OPENAI_API_KEY:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return api_key

@router.post("/generate-text", response_model=TextGenerationResponse, tags=["Text Generation"], summary="Generate text using OpenAI API")
async def generate_text_endpoint(request: TextGenerationRequest, api_key: str = Depends(api_key_auth)):
    try:
        logging.debug(f"Received request: {request}")
        generated_text, total_tokens = generate_openai_text(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop
        )
        if "error" in generated_text:
            logging.warning(f"Error in text generation: {generated_text['error']}")
            raise HTTPException(status_code=500, detail=generated_text['error'])
        logging.info(f"Generated text: {generated_text['generated_text']}")
        return TextGenerationResponse(
            original_prompt=request.prompt,
            model=request.model,
            generated_text=generated_text['generated_text'],
            total_tokens=generated_text['total_tokens']
        )
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
async def generate_daily_brief(request: DailyBriefRequest, background_tasks: BackgroundTasks):
    try:
        logging.info("Generating daily brief")
        # Add the task to be processed in the background
        background_tasks.add_task(process_daily_brief, request.date, request.user_id)
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
async def quiz_me(request: QuizMeRequest):
    try:
        logging.info("Generating quiz questions")
        questions = await generate_quiz_questions(request.deck_id)
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

# Initialize Redis client within an async function
async def get_redis_client():
    return await aioredis.create_redis_pool("redis://localhost")

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