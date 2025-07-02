import os
import logging
from dotenv import load_dotenv
from services.rate_limited_queue import get_openai_queue

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

logger.info("OpenAI integration initialized successfully")


async def generate_text(
    prompt, model="gpt-3.5-turbo", max_tokens=500, temperature=0.7, stop=None
):
    """
    Generate text using OpenAI's GPT model, using the rate-limited queue.

    :param prompt: The input prompt for text generation.
    :param model: The OpenAI model to use (default is gpt-3.5-turbo).
    :param max_tokens: The maximum number of tokens to generate.
    :param temperature: Controls the randomness of the output (default is 0.7).
    :param stop: Sequences where the API will stop generating further tokens.
    :return: Generated text or an error message.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OpenAI API key not found in environment variables")
        raise ValueError("OpenAI API key is required")

    openai_queue = get_openai_queue()
    try:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful productivity assistant.",
                },
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
            **payload,
        )
        response = await result_future
        generated_text = response["choices"][0]["message"]["content"].strip()
        total_tokens = response["usage"]["total_tokens"]
        return generated_text, total_tokens
    except Exception as e:
        raise ValueError(f"OpenAI error: {str(e)}")


# Example usage
if __name__ == "__main__":
    import asyncio

    prompt = "What is the weather like today?"
    text, tokens = asyncio.run(generate_text(prompt, temperature=0.5, stop=["."]))
    print(f"Generated Text: {text}")
    print(f"Total Tokens: {tokens}")

# Placeholder for OpenAI API integration logic
# def generate_text(prompt):
#     # Implement the function to call OpenAI API
#     pass
