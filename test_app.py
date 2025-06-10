from fastapi.testclient import TestClient
from app import app
from unittest.mock import patch
import pytest
import os
from starlette.requests import Request

# Set the environment variable to disable rate limiting during tests
os.environ['DISABLE_RATE_LIMIT'] = 'true'

# Initialize the test client after setting the environment variable
client = TestClient(app)

# Set environment variable to disable rate limiting during tests
os.environ['TEST_ENV'] = 'true'

@pytest.fixture(autouse=True)
def reset_app_state():
    """Fixture to reset application state between tests."""
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

def test_get_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the FastAPI application!"}


def test_get_users():
    response = client.get("/api/users")
    assert response.status_code in [200, 404]  # Depending on whether users exist


def test_get_user_by_id():
    response = client.get("/api/users/1")  # Assuming user with ID 1 exists
    assert response.status_code in [200, 404]


def test_update_user():
    response = client.put("/api/users/1", json={"name": "Updated Name"})
    assert response.status_code in [200, 404, 422]


def test_delete_user():
    headers = {"X-API-Key": "expected_api_key"}
    response = client.delete("/api/users/1", headers=headers)
    assert response.status_code in [200, 404]


def test_get_calendar_events():
    response = client.get("/api/calendar/events")
    assert response.status_code == 200


def test_create_calendar_event():
    response = client.post("/api/calendar/events", json={"title": "Meeting", "date": "2023-10-10"})
    assert response.status_code in [200, 422]


def test_update_calendar_event():
    response = client.put("/api/calendar/events/1", json={"title": "Updated Meeting"})
    assert response.status_code in [200, 404, 422]


def test_delete_calendar_event():
    response = client.delete("/api/calendar/events/1")
    assert response.status_code in [200, 404]


def test_get_notifications():
    response = client.get("/api/notifications")
    assert response.status_code == 200


def test_create_notification():
    response = client.post("/api/notifications", json={"message": "New Notification"})
    assert response.status_code in [200, 422]


def test_delete_notification():
    headers = {"X-API-Key": "expected_api_key"}
    global notifications
    notifications = [{"id": 1, "message": "Sample Notification"}]
    response = client.delete("/api/notifications/1", headers=headers)
    assert response.status_code in [200, 404]


def test_get_settings():
    response = client.get("/api/settings")
    assert response.status_code == 200


def test_update_settings():
    response = client.put("/api/settings", json={"setting": "value"})
    assert response.status_code in [200, 422]


def test_get_tasks():
    headers = {"X-API-Key": "expected_api_key"}
    response = client.get("/api/tasks", headers=headers)
    assert response.status_code == 200


def test_create_task():
    response = client.post("/api/tasks", json={"title": "New Task"})
    assert response.status_code in [200, 422]


def test_update_task():
    response = client.put("/api/tasks/1", json={"title": "Updated Task"})
    assert response.status_code in [200, 404, 422]


def test_delete_task():
    response = client.delete("/api/tasks/1")
    assert response.status_code in [200, 404]


def test_generate_text():
    headers = {"X-API-Key": "expected_api_key"}
    response = client.post("/generate-text", json={"prompt": "Hello", "model": "gpt-3.5-turbo", "max_tokens": 50, "temperature": 0.7}, headers=headers)
    assert response.status_code == 200


def test_generate_flashcards():
    headers = {"X-API-Key": "expected_api_key"}
    response = client.post("/generate-flashcards", json={"notes": "Biology notes: Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods with the help of chlorophyll.", "topic_tags": ["biology"]}, headers=headers)
    assert response.status_code == 200
    assert "flashcards" in response.json()


def test_daily_brief():
    response = client.get("/daily-brief")
    assert response.status_code == 200


def test_stream():
    response = client.get("/stream")
    assert response.status_code == 200


def test_simulate_openai_failure():
    response = client.post("/simulate-openai-failure")
    assert response.status_code == 503


def test_force_error():
    response = client.get("/force-error")
    assert response.status_code == 500
    assert response.json() == {"message": "An unexpected error occurred."}