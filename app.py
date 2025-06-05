import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from openai_integration import generate_text

# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

app = FastAPI()

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

# In-memory data storage
users = []
tasks = [
    {'id': 1, 'title': 'Task 1', 'completed': False},
    {'id': 2, 'title': 'Task 2', 'completed': True}
]
calendar_events = []
notifications = []
settings = {}

@app.get("/api/users")
async def get_users():
    return users

@app.get("/api/users/{user_id}")
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

@app.get("/api/tasks")
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

@app.post("/generate-text", response_model=TextGenerationResponse, tags=["Text Generation"], summary="Generate text using OpenAI API")
async def generate_text_endpoint(request: TextGenerationRequest):
    try:
        # Validate max_tokens
        if request.max_tokens > 4096:
            raise HTTPException(status_code=400, detail="max_tokens exceeds model limit")
        # Validate model
        if request.model not in ["gpt-3.5-turbo", "gpt-4"]:
            raise HTTPException(status_code=400, detail="Invalid model selection")
        # Call the generate_text function
        result, total_tokens = generate_text(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop
        )
        # Return a structured response
        return TextGenerationResponse(
            original_prompt=request.prompt,
            model=request.model,
            generated_text=result,
            total_tokens=total_tokens
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def load_openai_key():
    if not OPENAI_API_KEY:
        raise RuntimeError("Missing OpenAI API key") 