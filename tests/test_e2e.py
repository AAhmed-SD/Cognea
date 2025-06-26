import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from redis import Redis
import os
import json
from datetime import datetime, timedelta

from main import create_app
from models.database import Base, get_db
from middleware.rate_limit import RateLimiter

# Test database URL
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/test_db"
TEST_REDIS_URL = "redis://localhost:6379/1"

# Create test database engine
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    # Ensure rate limiting is enabled for tests
    os.environ["DISABLE_RATE_LIMIT"] = "false"
    yield
    # Clean up
    if "DISABLE_RATE_LIMIT" in os.environ:
        del os.environ["DISABLE_RATE_LIMIT"]

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def redis_client():
    redis = Redis.from_url(TEST_REDIS_URL)
    redis.flushdb()
    yield redis
    redis.flushdb()

@pytest.fixture(scope="function")
def app(redis_client):
    return create_app(redis_client)

@pytest.fixture(scope="function")
def client(app, db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

def test_complete_user_flow(client, redis_client):
    """Test the complete user flow from signup to review completion"""
    
    # Reset rate limit counter
    redis_client.delete("rate_limit:testclient")
    
    # 1. Sign Up
    signup_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    signup_response = client.post("/api/auth/signup", json=signup_data)
    assert signup_response.status_code == 200
    auth_token = signup_response.json()["access_token"]
    
    # Set auth header for subsequent requests
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 2. Plan My Day
    plan_data = {
        "date": datetime.now().isoformat(),
        "preferences": {
            "focus_areas": ["work", "health", "learning"],
            "duration": "8h"
        }
    }
    plan_response = client.post("/api/plan-day", json=plan_data, headers=headers)
    assert plan_response.status_code == 200
    plan_id = plan_response.json()["plan_id"]
    
    # 3. Generate Flashcards
    flashcard_data = {
        "topic": "Python Programming",
        "difficulty": "intermediate",
        "count": 5
    }
    flashcard_response = client.post("/api/generate-flashcards", 
                                   json=flashcard_data, 
                                   headers=headers)
    assert flashcard_response.status_code == 200
    flashcards = flashcard_response.json()["flashcards"]
    assert len(flashcards) == 5
    
    # 4. Complete Review
    review_data = {
        "flashcard_id": flashcards[0]["id"],
        "response": "Correct answer",
        "confidence": 0.8
    }
    review_response = client.post("/api/complete-review",
                                json=review_data,
                                headers=headers)
    assert review_response.status_code == 200
    
    # 5. Test Rate Limiting
    # Reset rate limit counter before testing
    # Use the actual client IP that the rate limiter uses
    client_ip = "testclient"  # This is the IP used by TestClient
    redis_client.delete(f"rate_limit:{client_ip}")
    
    # Make requests up to the limit (10 per minute in test config)
    for i in range(10):  # Make multiple requests quickly
        response = client.get("/api/insights/latest", headers=headers)
        assert response.status_code == 200, f"Request {i+1} should succeed"
    
    # The 11th request should be rate limited
    rate_limit_response = client.get("/api/insights/latest", headers=headers)
    assert rate_limit_response.status_code == 429, "Should be rate limited after 10 requests"
    
    # 6. Test Error Paths
    # Test with invalid token
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    invalid_response = client.get("/api/insights/latest", headers=invalid_headers)
    assert invalid_response.status_code == 401
    
    # Test with missing required fields
    invalid_plan_data = {"date": datetime.now().isoformat()}  # Missing preferences
    invalid_plan_response = client.post("/api/plan-day", 
                                      json=invalid_plan_data, 
                                      headers=headers)
    assert invalid_plan_response.status_code == 422

def test_row_level_security(client, db_session):
    """Test Row Level Security (RLS)"""
    
    # Create two users
    user1_data = {
        "email": "user1@example.com",
        "password": "password123",
        "name": "User 1"
    }
    user2_data = {
        "email": "user2@example.com",
        "password": "password123",
        "name": "User 2"
    }
    
    # Sign up both users
    user1_response = client.post("/api/auth/signup", json=user1_data)
    user2_response = client.post("/api/auth/signup", json=user2_data)
    
    user1_token = user1_response.json()["access_token"]
    user2_token = user2_response.json()["access_token"]
    
    # Create a plan with user1
    plan_data = {
        "date": datetime.now().isoformat(),
        "preferences": {"focus_areas": ["work"]}
    }
    
    # User1 creates a plan
    user1_headers = {"Authorization": f"Bearer {user1_token}"}
    plan_response = client.post("/api/plan-day", 
                              json=plan_data, 
                              headers=user1_headers)
    assert plan_response.status_code == 200
    plan_id = plan_response.json()["plan_id"]
    
    # User2 tries to access user1's plan
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    unauthorized_response = client.get(f"/api/plan/{plan_id}", 
                                     headers=user2_headers)
    assert unauthorized_response.status_code == 403

def test_concurrent_requests(client, redis_client):
    """Test handling of concurrent requests"""
    import threading
    import time
    
    # Sign up a user
    signup_data = {
        "email": "concurrent@example.com",
        "password": "testpassword123",
        "name": "Concurrent User"
    }
    signup_response = client.post("/api/auth/signup", json=signup_data)
    auth_token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Function to make concurrent requests
    def make_request():
        return client.get("/api/insights/latest", headers=headers)
    
    # Create multiple threads
    threads = []
    responses = []
    
    for _ in range(5):
        thread = threading.Thread(target=lambda: responses.append(make_request()))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check that all requests were handled properly
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count > 0  # At least some requests should succeed
    assert len(responses) == 5  # All requests should complete 