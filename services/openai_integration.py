import os
from dotenv import load_dotenv
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from services.rate_limited_queue import get_openai_queue

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Load OpenAI API key from environment
# openai_api_key = os.getenv("OPENAI_API_KEY")
# if not openai_api_key:
#     logger.error("OpenAI API key not found in environment variables")
#     raise ValueError("OpenAI API key is required")

# Configure OpenAI client
# openai.api_key = openai_api_key

logger.info("OpenAI integration initialized successfully")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def generate_openai_text(
    prompt, model="gpt-3.5-turbo", max_tokens=500, temperature=0.7, stop=None
):
    """
    Generate text using OpenAI's GPT model, using the rate-limited queue.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OpenAI API key not found in environment variables")
        raise ValueError("OpenAI API key is required")
    openai_queue = get_openai_queue()
    try:
        # Use the queue to make the API call
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful productivity assistant."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop": stop,
            "n": 1,
        }
        result_future = await openai_queue.enqueue_request(
            method="POST",
            endpoint="chat/completions",
            api_key=openai_api_key,
            **payload
        )
        response = await result_future
        # Parse response as if it were the OpenAI API
        generated_text = response["choices"][0]["message"]["content"].strip()
        total_tokens = response["usage"]["total_tokens"] if "usage" in response else None
        return {"generated_text": generated_text, "total_tokens": total_tokens}, None
    except Exception as e:
        return {"error": str(e), "type": "OpenAIError"}, None

# Example usage
if __name__ == "__main__":
    import asyncio
    prompt = "What is the weather like today?"
    text, tokens = asyncio.run(generate_openai_text(prompt, temperature=0.5, stop=["."]))
    print(f"Generated Text: {text}")
    print(f"Total Tokens Used: {tokens}")
