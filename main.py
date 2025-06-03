from fastapi import FastAPI
from routes import generate

app = FastAPI()

# Include the generate-text route
app.include_router(generate.router)

# Example usage
# Run the FastAPI server with: uvicorn main:app --reload 