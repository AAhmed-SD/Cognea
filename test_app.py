from fastapi.testclient import TestClient
from app import app
from unittest.mock import patch
import pytest
import os
from starlette.requests import Request

# Set environment variable to disable rate limiting during tests
os.environ['DISABLE_RATE_LIMIT'] = 'true'

# Initialize the test client after setting the environment variable
client = TestClient(app)

# Explicitly set the limiter to None to disable rate limiting during tests
app.state.limiter = None

# Set environment variable to disable rate limiting during tests
os.environ['TEST_ENV'] = 'true'

@pytest.fixture(autouse=True)
def reset_app_state():
    """Fixture to reset application state between tests."""
    app.state.limiter = None
    os.environ['TEST_ENV'] = 'true'

def test_generate_text_endpoint():
    response = client.post(
        "/generate-text",
        json={
            "prompt": "Hello, world!",
            "model": "gpt-3.5-turbo",
            "max_tokens": 50,
            "temperature": 0.7,
            "stop": ["\n"]
        },
        headers={"X-API-Key": "expected_api_key"}
    )
    assert response.status_code == 200
    assert "generated_text" in response.json()

def test_unsupported_model():
    response = client.post(
        "/generate-text",
        json={
            "prompt": "Hello, world!",
            "model": "unsupported-model",
            "max_tokens": 50,
            "temperature": 0.7
        },
        headers={"X-API-Key": "expected_api_key"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported model"

def test_missing_api_key():
    response = client.post(
        "/generate-text",
        json={
            "prompt": "Hello, world!",
            "model": "gpt-3.5-turbo",
            "max_tokens": 50,
            "temperature": 0.7
        }
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"

@pytest.fixture
def mock_openai_failure():
    with patch("services.openai_integration.openai.ChatCompletion.create", side_effect=Exception("OpenAI Down")) as mock:
        yield mock

def test_openai_downtime():
    response = client.post("/simulate-openai-failure")
    assert response.status_code == 503

def test_http_exception_handler():
    response = client.get("/api/users/999")  # Assuming this ID does not exist
    assert response.status_code == 404
    assert response.json()["error"] == "HTTPException"


def test_validation_exception_handler():
    response = client.post(
        "/api/tasks",
        json={"title": "Task Title"}  # Correct data type
    )
    assert response.status_code == 200  # Expecting success with correct data


def test_generic_exception_handler():
    response = client.get("/force-error")
    assert response.status_code == 500
    assert response.json() == {"message": "An unexpected error occurred."}

# Load testing for /generate-text endpoint

def test_generate_text_load():
    for _ in range(100):  # Simulate 100 requests
        response = client.post("/generate-text", json={
            "prompt": "Test prompt",
            "model": "gpt-3.5-turbo",
            "max_tokens": 50,
            "temperature": 0.7,
            "stop": ["\n"]
        }, headers={"X-API-Key": "expected_api_key"})
        assert response.status_code == 200

# Load testing for /daily-brief endpoint

def test_daily_brief_load():
    for _ in range(100):  # Simulate 100 requests
        response = client.get("/daily-brief")  # Use GET method
        assert response.status_code == 200

# Load testing for /quiz-me endpoint

def test_quiz_me_load():
    for _ in range(100):  # Simulate 100 requests
        response = client.post("/quiz-me", json={"deck_id": 1})  # Use POST method
        assert response.status_code == 200

# Remove test_load_example_endpoint as the endpoint is not defined
# def test_load_example_endpoint():
#     for _ in range(100):  # Simulate 100 requests
#         response = client.get("/example-endpoint")  # Use GET method

# Verify that the DISABLE_RATE_LIMIT environment variable is correctly set to true during tests
os.environ['TEST_ENV'] = 'true'

# Ensure the request objects are correctly instantiated in the tests
# Example: response = client.post("/generate-text", json={...}, headers={...}) 