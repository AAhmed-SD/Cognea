import os
from dotenv import load_dotenv
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Debug print to verify API key loading
print("🔑 Loaded OpenAI key:", repr(OPENAI_API_KEY))

# Check if the API key is loaded
if OPENAI_API_KEY:
    print("OpenAI API key loaded successfully.")
else:
    print("Error: OpenAI API key not found. Please check your .env file.")

# Initialize OpenAI API client
openai.api_key = OPENAI_API_KEY

# Debug print to confirm API key is set
print("🔑 OpenAI API key set:", repr(openai.api_key))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_openai_text(prompt, model="gpt-3.5-turbo", max_tokens=500, temperature=0.7, stop=None):
    """
    Generate text using OpenAI's GPT model.

    :param prompt: The input prompt for text generation.
    :param model: The OpenAI model to use (default is gpt-3.5-turbo).
    :param max_tokens: The maximum number of tokens to generate.
    :param temperature: Controls the randomness of the output (default is 0.7).
    :param stop: Sequences where the API will stop generating further tokens.
    :return: Tuple of generated text and total tokens used.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful productivity assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
            n=1
        )
        generated_text = response.choices[0].message['content'].strip()
        total_tokens = response.usage.total_tokens if 'usage' in response else None
        return {"generated_text": generated_text, "total_tokens": total_tokens}, None
    except Exception as e:
        return {"error": str(e), "type": "OpenAIError"}, None

# Example usage
if __name__ == "__main__":
    prompt = "What is the weather like today?"
    text, tokens = generate_openai_text(prompt, temperature=0.5, stop=["."])
    print(f"Generated Text: {text}")
    print(f"Total Tokens Used: {tokens}") 