from fastapi.testclient import TestClient
from app import app
from unittest.mock import patch

client = TestClient(app)

def test_generate_text_endpoint():
    response = client.post(
        "/generate-text",
        json={
            "prompt": "Hello, world!",
            "model": "gpt-3.5-turbo",
            "max_tokens": 50,
            "temperature": 0.7
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
    assert response.json()["detail"] == "Could not validate credentials"

@patch("openai.ChatCompletion.create", side_effect=Exception("OpenAI down"))
def test_openai_downtime(mock_openai):
    response = client.post(
        "/generate-text",
        json={
            "prompt": "Hello, world!",
            "model": "gpt-3.5-turbo",
            "max_tokens": 50,
            "temperature": 0.7
        },
        headers={"X-API-Key": "expected_api_key"}
    )
    assert response.status_code == 500
    assert response.json()["error"] == "OpenAI API Error" 