import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from openai_integration import generate_text
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
import functools
import redis
import json
import logging
from logging.handlers import RotatingFileHandler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from slowapi.middleware import SlowAPIMiddleware
from routes import generate
from starlette.requests import Request
from handlers import custom_rate_limit_exceeded_handler
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure rate limiting is disabled during tests
DISABLE_RATE_LIMIT = os.getenv("TEST_ENV", "false").lower() == "true"

# Debug print to confirm the value of DISABLE_RATE_LIMIT
# print("🔧 DISABLE_RATE_LIMIT:", DISABLE_RATE_LIMIT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    logger.info("Application startup")
    if not OPENAI_API_KEY:
        raise RuntimeError("Missing OpenAI API key")
    yield
    # Shutdown event
    logger.info("Application shutdown")


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
        "name": "Proprietary",
        "url": "https://github.com/AAhmed-SD/Cognie/blob/main/LICENSE",
    },
    lifespan=lifespan,
)

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key")

# Initialize Redis client
redis_client = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)

# Configure logging with a rotating file handler
log_handler = RotatingFileHandler("app.log", maxBytes=1000000, backupCount=3)
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
    {"id": 1, "title": "Task 1", "completed": False},
    {"id": 2, "title": "Task 2", "completed": True},
]
calendar_events = []
notifications = []
settings = {}


# Function to initialize middleware
async def initialize_middleware(app):
    if app.state.limiter is not None:
        app.add_middleware(SlowAPIMiddleware)


# Check if rate limiting should be disabled
if os.getenv("DISABLE_RATE_LIMIT", "false").lower() == "true":
    app.state.limiter = None
else:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100 per day", "10 per minute"],
        storage_uri="redis://localhost:6379/0",
        strategy="fixed-window",
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

# Conditionally register middleware and exception handlers
if app.state.limiter:
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)
    initialize_middleware(app)


# Define a decorator factory for conditional rate limiting
def rate_limit_if_enabled(app, rate: str):
    def decorator(func):
        # Check if rate limiting is disabled
        if os.getenv("DISABLE_RATE_LIMIT", "false").lower() == "true":
            return func
        limiter = getattr(app.state, "limiter", None)
        if limiter:
            return limiter.limit(rate)(func)
        return func

    return decorator


@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI application!"}


@app.get(
    "/api/users",
    tags=["User Management"],
    summary="Get all users",
    description="Retrieve a list of all users.",
    responses={
        200: {
            "description": "Successful retrieval of users",
            "content": {
                "application/json": {"example": [{"id": 1, "name": "John Doe"}]}
            },
        },
        404: {"description": "Users not found"},
    },
)
@rate_limit_if_enabled(app, "30/minute")
async def get_users():
    cached_users = redis_client.get("users")
    if cached_users:
        return json.loads(cached_users)
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    redis_client.setex("users", 3600, json.dumps(users))  # Cache for 1 hour
    return users


@app.get(
    "/api/users/{user_id}",
    tags=["User Management"],
    summary="Get a user by ID",
    description="Retrieve a user's details by their ID.",
    responses={
        200: {
            "description": "Successful retrieval of user",
            "content": {"application/json": {"example": {"id": 1, "name": "John Doe"}}},
        },
        404: {"description": "User not found"},
    },
)
async def get_user(user_id: int):
    user = next((user for user in users if user["id"] == user_id), None)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put(
    "/api/users/{user_id}",
    tags=["User Management"],
    summary="Update a user",
    description="Update a user's details by their ID.",
    responses={
        200: {
            "description": "User updated successfully",
            "content": {"application/json": {"example": {"id": 1, "name": "John Doe"}}},
        },
        404: {"description": "User not found"},
        422: {"description": "Validation Error"},
    },
)
async def update_user(user_id: int, user_data: dict):
    user = next((user for user in users if user["id"] == user_id), None)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not isinstance(user_data, dict) or not user_data.get("name"):
        raise HTTPException(status_code=422, detail="Invalid user data")
    user.update(user_data)
    return user


@app.delete(
    "/api/users/{user_id}",
    tags=["User Management"],
    summary="Delete a user",
    description="Delete a user by their ID.",
    responses={
        200: {"description": "User deleted successfully"},
        404: {"description": "User not found"},
    },
)
async def delete_user(user_id: int, api_key: str = Depends(get_api_key)):
    global users
    user = next((user for user in users if user["id"] == user_id), None)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    users = [user for user in users if user["id"] != user_id]
    return {"message": "User deleted"}


@app.get("/api/calendar/events")
async def get_calendar_events():
    return calendar_events


@app.post(
    "/api/calendar/events",
    tags=["Calendar"],
    summary="Create a calendar event",
    description="Create a new calendar event.",
    responses={
        200: {
            "description": "Event created successfully",
            "content": {
                "application/json": {
                    "example": {"id": 1, "title": "Meeting", "date": "2023-10-10"}
                }
            },
        },
        422: {"description": "Validation Error"},
    },
)
async def create_calendar_event(event: dict):
    if not isinstance(event, dict) or not event.get("title") or not event.get("date"):
        raise HTTPException(status_code=422, detail="Invalid event data")
    event["id"] = len(calendar_events) + 1
    calendar_events.append(event)
    return event


@app.put("/api/calendar/events/{event_id}")
async def update_calendar_event(event_id: int, event_data: dict):
    event = next((event for event in calendar_events if event["id"] == event_id), None)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    event.update(event_data)
    return event


@app.delete("/api/calendar/events/{event_id}")
async def delete_calendar_event(event_id: int):
    global calendar_events
    calendar_events = [event for event in calendar_events if event["id"] != event_id]
    return {"message": "Event deleted"}


@app.get("/api/notifications")
async def get_notifications():
    return notifications


@app.post("/api/notifications")
async def create_notification(notification: dict):
    notifications.append(notification)
    return notification


# @app.delete("/api/notifications/{notification_id}")
# async def delete_notification(notification_id: int):
#     global notifications
#     notifications = [notification for notification in notifications if notification['id'] != notification_id]
#     return {"message": "Notification deleted"}


@app.get("/api/settings")
async def get_settings():
    return settings


@app.put("/api/settings")
async def update_settings(settings_data: dict):
    settings.update(settings_data)
    return settings


@app.get(
    "/api/tasks",
    dependencies=[Depends(get_api_key)],
    tags=["Tasks"],
    summary="List all tasks",
    description="Retrieve a list of all tasks.",
)
async def get_tasks():
    return tasks


@app.post(
    "/api/tasks",
    tags=["Tasks"],
    summary="Create a new task",
    description="Create a new task.",
    responses={
        200: {
            "description": "Task created successfully",
            "content": {
                "application/json": {"example": {"id": 1, "title": "New Task"}}
            },
        },
        422: {"description": "Validation Error"},
    },
)
@rate_limit_if_enabled(app, "20/minute")
async def create_task(new_task: dict):
    new_task["id"] = len(tasks) + 1
    tasks.append(new_task)
    return new_task


@app.put("/api/tasks/{task_id}")
async def update_task(task_id: int, task_data: dict):
    task = next((task for task in tasks if task["id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task.update(task_data)
    return task


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    global tasks
    tasks = [task for task in tasks if task["id"] != task_id]
    return {"message": "Task deleted"}


# Model Validation
supported_models = ["gpt-3.5-turbo", "gpt-4"]


@app.middleware("http")
async def lifespan_middleware(request: Request, call_next):
    if request.scope["type"] == "lifespan":
        if request.scope["asgi"]["spec_version"] == "2.0":
            if request.scope["lifespan"]["type"] == "startup":
                logger.info("Application startup")
                if not OPENAI_API_KEY:
                    raise RuntimeError("Missing OpenAI API key")
            elif request.scope["lifespan"]["type"] == "shutdown":
                logger.info("Application shutdown")
    response = await call_next(request)
    return response


@app.post(
    "/generate-text",
    response_model=TextGenerationResponse,
    tags=["AI"],
    summary="Generate text using GPT",
    description="Generate text using OpenAI's GPT model based on the provided prompt.",
)
@rate_limit_if_enabled(app, "3/minute")
async def generate_text_endpoint(request: Request, api_key: str = Depends(get_api_key)):
    try:
        request_data = await request.json()  # Parse the request body
        model = request_data.get("model")
        prompt = request_data.get("prompt")
        max_tokens = request_data.get("max_tokens")
        temperature = request_data.get("temperature")
        stop = request_data.get("stop")

        logger.info(f"Received request for model: {model} with prompt: {prompt}")
        # Validate model
        if model not in supported_models:
            raise HTTPException(status_code=400, detail="Unsupported model")

        # Normalize prompt
        normalized_prompt = prompt.strip().lower()
        cache_key = f"{model}:{normalized_prompt}"
        cached_response = redis_client.get(cache_key)
        if cached_response:
            logger.info("Cache hit")
            return TextGenerationResponse(**json.loads(cached_response))

        # Asynchronous OpenAI call
        loop = asyncio.get_event_loop()
        logger.info("Attempting to call OpenAI API")
        result, total_tokens = await loop.run_in_executor(
            None,
            functools.partial(
                generate_text,
                prompt=normalized_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
            ),
        )

        # Cache the response
        response_data = TextGenerationResponse(
            original_prompt=prompt,
            model=model,
            generated_text=result,
            total_tokens=total_tokens,
        )
        redis_client.setex(cache_key, 3600, response_data.json())  # Cache for 1 hour

        logger.info("Response cached")

        # Return a structured response
        return response_data
    except HTTPException as e:
        logger.error(f"HTTP error: {str(e)}")
        raise e
    except ValueError as e:
        logger.error(f"Error processing request: {str(e)}")
        error_response = ErrorResponse(error="OpenAI API Error", detail=str(e))
        return JSONResponse(status_code=400, content=error_response.dict())
    except Exception as e:
        logger.error("🔥 Exception raised during OpenAI API call")
        logger.error(f"OpenAI API Error: {str(e)}")
        error_response = ErrorResponse(
            error="OpenAI API Error", detail="AI service temporarily unavailable"
        )
        return JSONResponse(status_code=503, content=error_response.dict())


# Streaming Response Example
async def stream_data():
    # Example streaming logic
    yield b"some data"


@app.get("/stream")
async def get_stream():
    return StreamingResponse(stream_data(), media_type="application/octet-stream")


# @app.post("/generate-flashcards", tags=["AI"], summary="Generate flashcards from notes", description="Turn raw notes or textbook content into flashcards.")
# async def generate_flashcards(notes: str, topic_tags: Optional[List[str]] = None):
#     try:
#         flashcards = []
#         for note in notes.split("\n"):
#             question = f"What is the key point of: {note}?"
#             answer = note
#             flashcards.append({"question": question, "answer": answer})
#         return {"flashcards": flashcards}
#     except Exception as e:
#         logger.error(f"Error generating flashcards: {str(e)}")
#         error_response = ErrorResponse(error="Flashcard Generation Error", detail=str(e))
#         return JSONResponse(status_code=500, content=error_response.dict())


# Example of adding examples to a Pydantic model
class TaskUpdate(BaseModel):
    title: str = Field(..., json_schema_extra={"example": "Update notes for biology"})
    completed: bool = Field(..., json_schema_extra={"example": True})


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
async def custom_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."},
    )


@app.get(
    "/daily-brief",
    tags=["AI"],
    summary="Generate a daily brief",
    description="Generate a daily summary of tasks, priorities, missed tasks, and a reflection.",
)
async def daily_brief():
    try:
        today = datetime.now().date()

        # Get real data from database instead of in-memory storage
        from services.supabase import get_supabase_client

        supabase = get_supabase_client()

        # Fetch all tasks (in a real app, this would be filtered by user_id)
        result = supabase.table("tasks").select("*").execute()
        all_tasks = result.data if result.data else []

        # Filter tasks by completion status and due date
        completed_tasks = [
            task for task in all_tasks if task.get("status") == "completed"
        ]
        pending_tasks = [task for task in all_tasks if task.get("status") == "pending"]

        # Calculate missed tasks (due date is in the past and not completed)
        missed_tasks = []
        for task in all_tasks:
            if task.get("due_date"):
                due_date = datetime.fromisoformat(
                    task["due_date"].replace("Z", "+00:00")
                ).date()
                if due_date < today and task.get("status") != "completed":
                    missed_tasks.append(task)

        # Generate AI-powered reflection
        from services.openai_integration import generate_openai_text

        task_summary = f"""
Completed Tasks: {len(completed_tasks)}
- {', '.join([task.get('title', 'Unknown') for task in completed_tasks[:5]])}

Pending Tasks: {len(pending_tasks)}
- {', '.join([task.get('title', 'Unknown') for task in pending_tasks[:5]])}

Missed Tasks: {len(missed_tasks)}
- {', '.join([task.get('title', 'Unknown') for task in missed_tasks[:5]])}
"""

        reflection_prompt = f"""Based on the following task summary for {today}, provide a brief, encouraging reflection:

{task_summary}

Write a 2-3 sentence reflection that:
1. Acknowledges accomplishments
2. Provides gentle encouragement for missed tasks
3. Suggests one actionable improvement for tomorrow

Keep it positive and actionable."""

        try:
            reflection_response = await generate_openai_text(
                prompt=reflection_prompt,
                model="gpt-4-turbo-preview",
                max_tokens=150,
                temperature=0.7,
            )
            reflection = reflection_response.get(
                "generated_text",
                "Reflect on your day: What went well? What could be improved?",
            )
        except Exception as e:
            logging.error(f"Error generating reflection: {str(e)}")
            reflection = "Reflect on your day: What went well? What could be improved?"

        return {
            "date": today.isoformat(),
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "missed_tasks": missed_tasks,
            "reflection": reflection,
            "summary": {
                "total_tasks": len(all_tasks),
                "completion_rate": (
                    len(completed_tasks) / len(all_tasks) * 100 if all_tasks else 0
                ),
                "missed_rate": (
                    len(missed_tasks) / len(all_tasks) * 100 if all_tasks else 0
                ),
            },
        }
    except Exception as e:
        logging.error(f"Error generating daily brief: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Include the generate router to access /quiz-me endpoint
app.include_router(generate.router)


# Custom rate limit exceeded handler
async def custom_rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    return JSONResponse(
        status_code=429, content={"detail": "Rate limit exceeded. Please slow down."}
    )


@app.post("/simulate-openai-failure")
async def simulate_openai_failure():
    raise HTTPException(status_code=503, detail="OpenAI is currently unavailable")


@app.get("/force-error")
async def force_error():
    # Instead of raising an exception, return a 500 JSON response
    return JSONResponse(
        status_code=500,
        content={"message": "Simulated error for testing error handling"},
    )


# Ensure the generic exception handler is registered
app.add_exception_handler(Exception, custom_exception_handler)

# Register all modular routers
app.include_router(generate.router)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        return response


# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware with strict settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Replace with your actual domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)
