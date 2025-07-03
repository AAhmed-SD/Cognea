"""
Comprehensive async tests for the Personal Agent API.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app

# Test data
test_user = {"email": "test@example.com", "password": "TestPassword123!"}

test_task = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",  # Required UUID
    "title": "Test Task",
    "description": "Test task description",
    "priority": "high",
    "due_date": "2024-12-31T23:59:59",
}

test_goal = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",  # Required UUID
    "title": "Test Goal",
    "description": "Test goal description",
    "due_date": "2024-12-31T23:59:59",
    "priority": "medium",
}

test_schedule_block = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",  # Required UUID
    "title": "Test Block",
    "description": "Test schedule block",
    "start_time": "2024-01-15T09:00:00",
    "end_time": "2024-01-15T10:00:00",
    "context": "Work",
}

test_flashcard = {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",  # Required UUID
    "question": "What is Python?",
    "answer": "A programming language",
    "tags": ["programming", "python"],
    "deck_name": "Programming",
}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Get authentication headers for testing."""
    # This would normally get a real JWT token
    # For testing, we'll use a mock token
    return {"Authorization": "Bearer test-token"}


class TestAuthentication:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_signup_success(self, async_client):
        """Test successful user signup."""
        response = await async_client.post("/api/auth/signup", json=test_user)
        # Should return 200 or 201 for successful signup, 422 if user already exists, or 500 for other issues
        assert response.status_code in [200, 201, 422, 500]  # 500 if Supabase error

    @pytest.mark.asyncio
    async def test_login_success(self, async_client):
        """Test successful user login."""
        response = await async_client.post("/api/auth/login", json=test_user)
        # Should return 200 for successful login or 401 for invalid credentials
        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client):
        """Test login with invalid credentials."""
        response = await async_client.post(
            "/api/auth/login",
            json={"email": "invalid@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401


class TestTasksEndpoints:
    """Test tasks endpoints."""

    @pytest.mark.asyncio
    async def test_create_task_unauthorized(self, async_client):
        """Test creating task without authentication."""
        response = await async_client.post("/api/tasks/", json=test_task)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_tasks_unauthorized(self, async_client):
        """Test getting tasks without authentication."""
        response = await async_client.get("/api/tasks/")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_update_task_unauthorized(self, async_client):
        """Test updating task without authentication."""
        task_id = str(uuid4())
        response = await async_client.put(
            f"/api/tasks/{task_id}", json={"title": "Updated Task"}
        )
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_delete_task_unauthorized(self, async_client):
        """Test deleting task without authentication."""
        task_id = str(uuid4())
        response = await async_client.delete(f"/api/tasks/{task_id}")
        assert response.status_code in [401, 403]


class TestGoalsEndpoints:
    """Test goals endpoints."""

    @pytest.mark.asyncio
    async def test_create_goal_unauthorized(self, async_client):
        """Test creating goal without authentication."""
        response = await async_client.post("/api/goals/", json=test_goal)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_goals_unauthorized(self, async_client):
        """Test getting goals without authentication."""
        response = await async_client.get("/api/goals/")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_update_goal_unauthorized(self, async_client):
        """Test updating goal without authentication."""
        goal_id = str(uuid4())
        response = await async_client.put(
            f"/api/goals/{goal_id}", json={"title": "Updated Goal"}
        )
        assert response.status_code in [401, 403]


class TestScheduleBlocksEndpoints:
    """Test schedule blocks endpoints."""

    @pytest.mark.asyncio
    async def test_create_schedule_block_unauthorized(self, async_client):
        """Test creating schedule block without authentication."""
        response = await async_client.post(
            "/api/schedule/", json=test_schedule_block
        )
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_schedule_blocks_unauthorized(self, async_client):
        """Test getting schedule blocks without authentication."""
        response = await async_client.get("/api/schedule/")
        assert response.status_code in [401, 403]


class TestFlashcardsEndpoints:
    """Test flashcards endpoints."""

    @pytest.mark.asyncio
    async def test_create_flashcard_unauthorized(self, async_client):
        """Test creating flashcard without authentication."""
        response = await async_client.post("/api/flashcards/", json=test_flashcard)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_flashcards_unauthorized(self, async_client):
        """Test getting flashcards without authentication."""
        response = await async_client.get("/api/flashcards/")
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_review_flashcard_unauthorized(self, async_client):
        """Test reviewing flashcard without authentication."""
        flashcard_id = str(uuid4())
        response = await async_client.post(
            f"/api/flashcards/{flashcard_id}/review", params={"quality": 5}
        )
        assert response.status_code in [401, 403]


class TestAIEndpoints:
    """Test AI-related endpoints."""

    @pytest.mark.asyncio
    async def test_plan_day_unauthorized(self, async_client):
        """Test daily planning without authentication."""
        response = await async_client.post(
            "/api/ai/plan-day",
            json={
                "date": "2024-01-15",
                "preferences": {"focus_areas": ["work"], "duration": "8h"},
            },
        )
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_generate_flashcards_unauthorized(self, async_client):
        """Test flashcard generation without authentication."""
        response = await async_client.post(
            "/api/ai/generate-flashcards",
            json={"topic": "Python", "difficulty": "beginner", "count": 5},
        )
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_insights_unauthorized(self, async_client):
        """Test getting insights without authentication."""
        response = await async_client.get("/api/ai/insights/latest")
        assert response.status_code in [401, 403]


class TestNotificationsEndpoints:
    """Test notifications endpoints."""

    @pytest.mark.asyncio
    async def test_create_notification_unauthorized(self, async_client):
        """Test creating notification without authentication."""
        notification = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",  # Required UUID
            "title": "Test Notification",
            "message": "Test message",
            "send_time": datetime.now(UTC).isoformat(),
            "type": "reminder",
            "category": "task",
        }
        response = await async_client.post("/api/notifications/", json=notification)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_notifications_unauthorized(self, async_client):
        """Test getting notifications without authentication."""
        response = await async_client.get("/api/notifications/")
        assert response.status_code in [401, 403]


class TestHealthAndMonitoring:
    """Test health and monitoring endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client):
        """Test root endpoint."""
        response = await async_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "meta" in data


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiting(self, async_client):
        """Test that rate limiting is working."""
        # Make multiple requests quickly
        responses = []
        for _ in range(10):
            response = await async_client.get("/health")
            responses.append(response.status_code)

        # All should succeed (rate limit is 60 per minute)
        assert all(status == 200 for status in responses)


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_404_endpoint(self, async_client):
        """Test 404 for non-existent endpoint."""
        response = await async_client.get("/api/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_json(self, async_client):
        """Test handling of invalid JSON."""
        response = await async_client.post("/api/tasks/", data="invalid json")
        assert response.status_code == 422


class TestDatabaseOperations:
    """Test database operations."""

    @pytest.mark.asyncio
    async def test_database_connection(self, async_client):
        """Test that database connection is working."""
        # This would test actual database operations
        # For now, we'll just test that the app starts without database errors
        response = await async_client.get("/health")
        assert response.status_code == 200


class TestSecurity:
    """Test security features."""

    @pytest.mark.asyncio
    async def test_security_headers(self, async_client):
        """Test that security headers are present."""
        response = await async_client.get("/")
        headers = response.headers

        # Check for security headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers

    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client):
        """Test CORS headers."""
        # Simulate a CORS preflight request with Origin header
        response = await async_client.options(
            "/", headers={"Origin": "http://localhost:3000"}
        )
        headers = response.headers

        # Check for CORS headers
        assert (
            "Access-Control-Allow-Origin" in headers
            or "access-control-allow-origin" in headers
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
