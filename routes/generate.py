from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks
from models.text import TextGenerationRequest, TextGenerationResponse
from services.openai_integration import generate_openai_text
import logging
import os
from starlette.status import HTTP_401_UNAUTHORIZED
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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