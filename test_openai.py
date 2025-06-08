from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.models.list()
print(response)

# Verify the API key
print(f"Using OpenAI API Key: {os.getenv('OPENAI_API_KEY')}") 