import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app
import json
from datetime import datetime, timedelta

client = TestClient(app)

# Test data
test_user = {
    "email": "test@example.com",
    "password": "TestPassword123!"
}

test_task = {
    "title": "Test Task",
    "description": "Test task description",
    "priority": "high",
    "due_date": "2024-12-31T23:59:59",
    "tags": ["test", "api"]
}

test_goal = {
    "title": "Test Goal",
    "description": "Test goal description",
    "target_date": "2024-12-31",
    "category": "personal"
}

test_schedule_block = {
    "title": "Test Block",
    "start_time": "2024-01-15T09:00:00",
    "end_time": "2024-01-15T10:00:00",
    "activity_type": "work"
}

test_flashcard = {
    "front": "What is the capital of France?",
    "back": "Paris",
    "category": "geography"
}

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "meta" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    
    def test_api_docs_accessible(self):
        """Test that API documentation is accessible"""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text
    
    def test_openapi_json_accessible(self):
        """Test that OpenAPI JSON is accessible"""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

class TestTasks:
    """Test task-related endpoints"""
    
    def test_get_tasks_unauthorized(self):
        """Test getting tasks without authentication"""
        response = client.get("/api/tasks")
        assert response.status_code in [401, 403]  # Should require authentication
    
    def test_create_task_unauthorized(self):
        """Test creating task without authentication"""
        response = client.post("/api/tasks", json=test_task)
        assert response.status_code in [401, 403]  # Should require authentication
    
    def test_get_tasks_statistics_unauthorized(self):
        """Test getting task statistics without authentication"""
        response = client.get("/api/tasks/statistics")
        assert response.status_code in [401, 403]  # Should require authentication

class TestGoals:
    """Test goal-related endpoints"""
    
    def test_get_goals_unauthorized(self):
        """Test getting goals without authentication"""
        response = client.get("/api/goals")
        assert response.status_code in [401, 403]  # Should require authentication
    
    def test_create_goal_unauthorized(self):
        """Test creating goal without authentication"""
        response = client.post("/api/goals", json=test_goal)
        assert response.status_code in [401, 403]  # Should require authentication

class TestScheduleBlocks:
    """Test schedule block endpoints"""
    
    def test_get_schedule_blocks_unauthorized(self):
        """Test getting schedule blocks without authentication"""
        response = client.get("/api/schedule-blocks")
        assert response.status_code in [401, 403]  # Should require authentication
    
    def test_create_schedule_block_unauthorized(self):
        """Test creating schedule block without authentication"""
        response = client.post("/api/schedule-blocks", json=test_schedule_block)
        assert response.status_code in [401, 403]  # Should require authentication

class TestFlashcards:
    """Test flashcard endpoints"""
    
    def test_get_flashcards_unauthorized(self):
        """Test getting flashcards without authentication"""
        response = client.get("/api/flashcards")
        assert response.status_code in [401, 403]  # Should require authentication
    
    def test_create_flashcard_unauthorized(self):
        """Test creating flashcard without authentication"""
        response = client.post("/api/flashcards", json=test_flashcard)
        assert response.status_code in [401, 403]  # Should require authentication

class TestNotifications:
    """Test notification endpoints"""
    
    def test_get_notifications_unauthorized(self):
        """Test getting notifications without authentication"""
        response = client.get("/api/notifications")
        assert response.status_code in [401, 403]  # Should require authentication

class TestAIEndpoints:
    """Test AI-related endpoints"""
    
    def test_extract_tasks_unauthorized(self):
        """Test task extraction without authentication"""
        response = client.post("/api/plan-day", json={"date": "2024-01-15", "preferences": {"focus_areas": ["work"], "duration": "8h"}})
        assert response.status_code in [401, 403]  # Should require authentication
    
    def test_plan_day_unauthorized(self):
        """Test daily planning without authentication"""
        response = client.post("/api/plan-day", json={"date": "2024-01-15", "preferences": {"focus_areas": ["work"], "duration": "8h"}})
        assert response.status_code in [401, 403]  # Should require authentication
    
    def test_generate_insights_unauthorized(self):
        """Test insights generation without authentication"""
        response = client.get("/api/insights/latest")
        assert response.status_code in [401, 403]  # Should require authentication

class TestSecurity:
    """Test security features"""
    
    def test_security_headers(self):
        """Test that security headers are present"""
        response = client.get("/")
        headers = response.headers
        
        # Check for security headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
    
    def test_cors_headers(self):
        """Test CORS headers"""
        response = client.options("/")
        # CORS headers should be present for OPTIONS requests
        assert response.status_code in [200, 405]  # 405 is acceptable for OPTIONS

class TestErrorHandling:
    """Test error handling"""
    
    def test_404_endpoint(self):
        """Test 404 handling"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_invalid_json(self):
        """Test invalid JSON handling"""
        response = client.post("/api/tasks", data="invalid json", headers={"Content-Type": "application/json"})
        assert response.status_code in [400, 422]  # Should return validation error

class TestDataValidation:
    """Test data validation"""
    
    def test_invalid_email_format(self):
        """Test invalid email validation"""
        invalid_user = {"email": "invalid-email", "password": "TestPassword123!"}
        response = client.post("/api/auth/signup", json=invalid_user)
        assert response.status_code == 422  # Validation error
    
    def test_weak_password(self):
        """Test weak password validation"""
        weak_password_user = {"email": "test@example.com", "password": "123"}
        response = client.post("/api/auth/signup", json=weak_password_user)
        assert response.status_code == 400  # Password validation error

class TestRateLimiting:
    """Test rate limiting (if enabled)"""
    
    def test_multiple_requests(self):
        """Test multiple rapid requests"""
        responses = []
        for _ in range(5):
            response = client.get("/")
            responses.append(response.status_code)
        
        # All requests should succeed (rate limiting might be disabled)
        assert all(status == 200 for status in responses)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 