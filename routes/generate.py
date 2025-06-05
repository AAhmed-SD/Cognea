from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks
from models.text import TextGenerationRequest, TextGenerationResponse
from services.openai_integration import generate_openai_text
import logging
import os
from starlette.status import HTTP_401_UNAUTHORIZED
from pydantic import BaseModel

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