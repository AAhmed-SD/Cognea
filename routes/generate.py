from fastapi import APIRouter, HTTPException, Depends, Header
from models.text import TextGenerationRequest, TextGenerationResponse
from services.openai_integration import generate_openai_text
import logging
import os
from starlette.status import HTTP_401_UNAUTHORIZED

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