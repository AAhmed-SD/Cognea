import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from openai_integration import generate_text
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
import functools
import redis
import json
import logging
from logging.handlers import RotatingFileHandler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize FastAPI app with rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Cognie API",
    description="AI-powered productivity and scheduling assistant",
    version="1.0.0",
    contact={
        "name": "Cognie Dev Team",
        "url": "https://github.com/AAhmed-SD/Cognie",
        "email": "support@cognie.app",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)
app.state.limiter = limiter

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key")

# Initialize Redis client
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# Configure logging with a rotating file handler
log_handler = RotatingFileHandler("app.log", maxBytes=1000000, backupCount=3)
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)

async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != "expected_api_key":
        raise HTTPException(status_code=403, detail="Could not validate credentials")

# Define Pydantic models for request and response
class TextGenerationRequest(BaseModel):
    prompt: str
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 500
    temperature: float = 0.7
    stop: Optional[List[str]] = None

class TextGenerationResponse(BaseModel):
    original_prompt: str
    model: str
    generated_text: str
    total_tokens: Optional[int] = None

# Standardized error response
class ErrorResponse(BaseModel):
    error: str
    detail: str

# In-memory data storage
users = []
tasks = [
    {'id': 1, 'title': 'Task 1', 'completed': False},
    {'id': 2, 'title': 'Task 2', 'completed': True}
]
calendar_events = []
notifications = []
settings = {}

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI application!"}

@app.get("/api/users", tags=["User Management"], summary="Get all users", description="Retrieve a list of all users.", responses={
    200: {"description": "Successful retrieval of users"},
    404: {"description": "Users not found"}
})
async def get_users():
    return users

@app.get("/api/users/{user_id}", tags=["User Management"], summary="Get a user by ID", description="Retrieve a user's details by their ID.")
async def get_user(user_id: int):
    user = next((user for user in users if user['id'] == user_id), None)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/api/users/{user_id}")
async def update_user(user_id: int, user_data: dict):
    user = next((user for user in users if user['id'] == user_id), None)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.update(user_data)
    return user

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    global users
    users = [user for user in users if user['id'] != user_id]
    return {"message": "User deleted"}

@app.get("/api/calendar/events")
async def get_calendar_events():
    return calendar_events

@app.post("/api/calendar/events")
async def create_calendar_event(event: dict):
    calendar_events.append(event)
    return event

@app.put("/api/calendar/events/{event_id}")
async def update_calendar_event(event_id: int, event_data: dict):
    event = next((event for event in calendar_events if event['id'] == event_id), None)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    event.update(event_data)
    return event

@app.delete("/api/calendar/events/{event_id}")
async def delete_calendar_event(event_id: int):
    global calendar_events
    calendar_events = [event for event in calendar_events if event['id'] != event_id]
    return {"message": "Event deleted"}

@app.get("/api/notifications")
async def get_notifications():
    return notifications

@app.post("/api/notifications")
async def create_notification(notification: dict):
    notifications.append(notification)
    return notification

@app.delete("/api/notifications/{notification_id}")
async def delete_notification(notification_id: int):
    global notifications
    notifications = [notification for notification in notifications if notification['id'] != notification_id]
    return {"message": "Notification deleted"}

@app.get("/api/settings")
async def get_settings():
    return settings

@app.put("/api/settings")
async def update_settings(settings_data: dict):
    settings.update(settings_data)
    return settings

@app.get("/api/tasks", dependencies=[Depends(get_api_key)], tags=["Tasks"], summary="List all tasks", description="Retrieve a list of all tasks.")
async def get_tasks():
    return tasks

@app.post("/api/tasks")
async def create_task(new_task: dict):
    new_task['id'] = len(tasks) + 1
    tasks.append(new_task)
    return new_task

@app.put("/api/tasks/{task_id}")
async def update_task(task_id: int, task_data: dict):
    task = next((task for task in tasks if task['id'] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task.update(task_data)
    return task

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    global tasks
    tasks = [task for task in tasks if task['id'] != task_id]
    return {"message": "Task deleted"}

# Model Validation
supported_models = ["gpt-3.5-turbo", "gpt-4"]

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")
    if not OPENAI_API_KEY:
        raise RuntimeError("Missing OpenAI API key")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")

@app.post("/generate-text", response_model=TextGenerationResponse, tags=["AI"], summary="Generate text using GPT", description="Generate text using OpenAI's GPT model based on the provided prompt.")
@limiter.limit("5/minute")  # Rate limiting
async def generate_text_endpoint(request: TextGenerationRequest, api_key: str = Depends(get_api_key)):
    try:
        logger.info(f"Received request for model: {request.model} with prompt: {request.prompt}")
        # Validate model
        if request.model not in supported_models:
            raise HTTPException(status_code=400, detail="Unsupported model")

        # Normalize prompt
        normalized_prompt = request.prompt.strip().lower()
        cache_key = f"{request.model}:{normalized_prompt}"
        cached_response = redis_client.get(cache_key)
        if cached_response:
            logger.info("Cache hit")
            return TextGenerationResponse(**json.loads(cached_response))

        # Asynchronous OpenAI call
        loop = asyncio.get_event_loop()
        result, total_tokens = await loop.run_in_executor(None, functools.partial(generate_text,
            prompt=normalized_prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop
        ))

        # Cache the response
        response_data = TextGenerationResponse(
            original_prompt=request.prompt,
            model=request.model,
            generated_text=result,
            total_tokens=total_tokens
        )
        redis_client.setex(cache_key, 3600, response_data.json())  # Cache for 1 hour

        logger.info("Response cached")

        # Return a structured response
        return response_data
    except ValueError as e:
        logger.error(f"Error processing request: {str(e)}")
        error_response = ErrorResponse(error="OpenAI API Error", detail=str(e))
        return JSONResponse(status_code=500, content=error_response.dict())

# Streaming Response Example
async def stream_data():
    # Example streaming logic
    yield b"some data"

@app.get("/stream")
async def get_stream():
    return StreamingResponse(stream_data(), media_type="application/octet-stream")

@app.post("/generate-flashcards", tags=["AI"], summary="Generate flashcards from notes", description="Turn raw notes or textbook content into flashcards.")
async def generate_flashcards(notes: str, topic_tags: Optional[List[str]] = None):
    try:
        # Example logic to generate flashcards
        # This should be replaced with actual logic using OpenAI or another service
        flashcards = []
        for note in notes.split("\n"):
            question = f"What is the key point of: {note}?"
            answer = note  # Simplified example
            flashcards.append({"question": question, "answer": answer})

        return {"flashcards": flashcards}
    except Exception as e:
        logger.error(f"Error generating flashcards: {str(e)}")
        error_response = ErrorResponse(error="Flashcard Generation Error", detail=str(e))
        return JSONResponse(status_code=500, content=error_response.dict())

# Example of adding examples to a Pydantic model
class TaskUpdate(BaseModel):
    title: str = Field(..., example="Update notes for biology")
    completed: bool = Field(..., example=True)

# Custom exception handler for HTTPException
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTPException", "detail": exc.detail},
    )

# Custom exception handler for RequestValidationError
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation Error", "detail": exc.errors()},
    )

# Custom exception handler for generic exceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred."},
    )

@app.get("/daily-brief", tags=["AI"], summary="Generate a daily brief", description="Generate a daily summary of tasks, priorities, missed tasks, and a reflection.")
async def daily_brief():
    today = datetime.now().date()
    # Example logic for generating a daily brief
    completed_tasks = [task for task in tasks if task['completed']]
    pending_tasks = [task for task in tasks if not task['completed']]
    missed_tasks = [task for task in tasks if not task['completed'] and task.get('due_date') and task['due_date'] < today]
    reflection = "Reflect on your day: What went well? What could be improved?"

    return {
        "date": today.isoformat(),
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "missed_tasks": missed_tasks,
        "reflection": reflection
    } 