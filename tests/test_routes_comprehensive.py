"""
Comprehensive tests for all route modules.
Aims to achieve >90% coverage across all routes.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from main import create_app

# from routes.mood import router as mood_router  # Route not implemented yet


@pytest.fixture
def app():
    """Create test app instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {"id": "user-123", "email": "test@example.com", "name": "Test User"}


@pytest.fixture
def mock_auth_dependency():
    """Mock authentication dependency."""

    def _mock_auth():
        return {"id": "user-123", "email": "test@example.com", "name": "Test User"}

    return _mock_auth


class TestAIRoutes:
    """Test AI routes functionality."""

    @pytest.mark.asyncio
    async def test_plan_day_success(self, client, mock_auth_dependency):
        """Test successful daily plan generation."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch(
                "services.cost_tracking.cost_tracking_service.check_budget_limits"
            ) as mock_budget:
                mock_budget.return_value = {
                    "daily_exceeded": False,
                    "monthly_exceeded": False,
                }

                with patch(
                    "services.ai.hybrid_ai_service.get_hybrid_ai_service"
                ) as mock_openai:
                    mock_openai.return_value = Mock()
                    mock_openai.return_value.generate_text.return_value = {
                        "generated_text": '[{"time": "09:00-10:30", "activity": "Work", "focus_area": "work"}]'
                    }

                    response = client.post(
                        "/ai/plan-day",
                        json={
                            "date": "2024-01-01",
                            "preferences": {
                                "focus_areas": ["work", "health"],
                                "duration": "8h",
                            },
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert "schedule" in data

    @pytest.mark.asyncio
    async def test_plan_day_budget_exceeded(self, client, mock_auth_dependency):
        """Test daily plan with budget exceeded."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch(
                "services.cost_tracking.cost_tracking_service.check_budget_limits"
            ) as mock_budget:
                mock_budget.return_value = {
                    "daily_exceeded": True,
                    "monthly_exceeded": False,
                }

                response = client.post(
                    "/ai/plan-day",
                    json={
                        "date": "2024-01-01",
                        "preferences": {"focus_areas": ["work"], "duration": "8h"},
                    },
                )

                assert response.status_code == 429
                assert "Budget limit exceeded" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_flashcards_success(self, client, mock_auth_dependency):
        """Test successful flashcard generation."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch(
                "services.cost_tracking.cost_tracking_service.check_budget_limits"
            ) as mock_budget:
                mock_budget.return_value = {
                    "daily_exceeded": False,
                    "monthly_exceeded": False,
                }

                with patch(
                    "services.ai.hybrid_ai_service.get_hybrid_ai_service"
                ) as mock_openai:
                    mock_openai.return_value = Mock()
                    mock_openai.return_value.generate_text.return_value = {
                        "generated_text": '[{"question": "What is X?", "answer": "X is Y"}]'
                    }

                    response = client.post(
                        "/ai/generate-flashcards",
                        json={
                            "topic": "Python Programming",
                            "difficulty": "medium",
                            "count": 5,
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "flashcards" in data

    @pytest.mark.asyncio
    async def test_get_ai_insights_success(self, client, mock_auth_dependency):
        """Test successful AI insights retrieval."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch("services.ai.openai_service.get_openai_service") as mock_openai:
                mock_service = Mock()
                mock_openai.return_value = mock_service
                mock_service.generate_text.return_value = {
                    "generated_text": "Productivity insights for the user"
                }

                response = client.post(
                    "/ai/insights",
                    json={
                        "insight_type": "productivity",
                        "user_data": {"tasks": [], "goals": []},
                        "parameters": {"date_range": "7d"},
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert "insights" in data

    @pytest.mark.asyncio
    async def test_suggest_habits_success(self, client, mock_auth_dependency):
        """Test successful habit suggestions."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch("services.ai.openai_service.get_openai_service") as mock_openai:
                mock_service = Mock()
                mock_openai.return_value = mock_service
                mock_service.generate_text.return_value = {
                    "generated_text": '[{"habit": "Morning exercise", "benefit": "Energy boost"}]'
                }

                response = client.post(
                    "/ai/habits/suggest",
                    json={
                        "user_preferences": ["health", "productivity"],
                        "current_habits": ["reading"],
                        "available_time": 60,
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert "suggestions" in data

    @pytest.mark.asyncio
    async def test_analyze_productivity_success(self, client, mock_auth_dependency):
        """Test successful productivity analysis."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch("services.ai.openai_service.get_openai_service") as mock_openai:
                mock_service = Mock()
                mock_openai.return_value = mock_service
                mock_service.generate_text.return_value = {
                    "generated_text": "Productivity analysis results"
                }

                response = client.post(
                    "/ai/productivity/analyze",
                    json={
                        "date_range": "7d",
                        "include_calendar": True,
                        "include_habits": True,
                        "include_learning": True,
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert "analysis" in data

    @pytest.mark.asyncio
    async def test_optimize_schedule_success(self, client, mock_auth_dependency):
        """Test successful schedule optimization."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch(
                "services.cost_tracking.cost_tracking_service.check_budget_limits"
            ) as mock_budget:
                mock_budget.return_value = {
                    "daily_exceeded": False,
                    "monthly_exceeded": False,
                }

                with patch(
                    "services.ai.hybrid_ai_service.get_hybrid_ai_service"
                ) as mock_openai:
                    mock_openai.return_value = Mock()
                    mock_openai.return_value.generate_text.return_value = {
                        "generated_text": '[{"task": "Work", "start_time": "09:00", "end_time": "12:00"}]'
                    }

                    response = client.post(
                        "/ai/schedule/optimize",
                        json={
                            "tasks": [
                                {"title": "Work", "priority": "high", "duration": 180}
                            ],
                            "available_time": {"start": "09:00", "end": "17:00"},
                            "preferences": {"focus_hours": "morning"},
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "optimized_schedule" in data

    @pytest.mark.asyncio
    async def test_get_weekly_summary_success(self, client, mock_auth_dependency):
        """Test successful weekly summary retrieval."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch("services.ai.openai_service.get_openai_service") as mock_openai:
                mock_service = Mock()
                mock_openai.return_value = mock_service
                mock_service.generate_text.return_value = {
                    "generated_text": "Weekly summary for the user"
                }

                response = client.get("/ai/insights/weekly-summary")

                assert response.status_code == 200
                data = response.json()
                assert "summary" in data

    @pytest.mark.asyncio
    async def test_invalidate_cache_success(self, client, mock_auth_dependency):
        """Test successful cache invalidation."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch("services.ai_cache.invalidate_user_cache") as mock_invalidate:
                mock_invalidate.return_value = None

                response = client.post(
                    "/ai/cache/invalidate",
                    json={"operations": ["ai_planning", "ai_flashcards"]},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_cache_stats_success(self, client, mock_auth_dependency):
        """Test successful cache stats retrieval."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch("services.ai_cache.ai_cache_service.get_stats") as mock_stats:
                mock_stats.return_value = {
                    "total_operations": 100,
                    "cache_hits": 80,
                    "cache_misses": 20,
                }

                response = client.get("/ai/cache/stats")

                assert response.status_code == 200
                data = response.json()
                assert "stats" in data

    @pytest.mark.asyncio
    async def test_start_batch_processing_success(self, client, mock_auth_dependency):
        """Test successful batch processing start."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch("services.background_workers.BackgroundWorker") as mock_worker:
                mock_worker_instance = Mock()
                mock_worker.return_value = mock_worker_instance
                mock_worker_instance.enqueue_task.return_value = "task-123"

                response = client.post(
                    "/ai/batch-process",
                    json={
                        "operation_type": "productivity_analysis",
                        "parameters": {"date_range": "7d"},
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "task_id" in data


class TestAuthRoutes:
    """Test authentication routes functionality."""

    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """Test successful user registration."""
        with patch("services.auth_service.AuthService.register_user") as mock_register:
            mock_register.return_value = {
                "user_id": "user-123",
                "email": "test@example.com",
                "access_token": "token-123",
            }

            response = client.post(
                "/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "securepassword123",
                    "name": "Test User",
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert "access_token" in data
            assert "user_id" in data

    @pytest.mark.asyncio
    async def test_register_invalid_password(self, client):
        """Test registration with invalid password."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "123",  # Too short
                "name": "Test User",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        """Test successful user login."""
        with patch("services.auth_service.AuthService.authenticate_user") as mock_auth:
            mock_auth.return_value = {
                "user_id": "user-123",
                "email": "test@example.com",
                "access_token": "token-123",
            }

            response = client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "securepassword123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        with patch("services.auth_service.AuthService.authenticate_user") as mock_auth:
            mock_auth.return_value = None

            response = client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": "wrongpassword"},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, mock_auth_dependency):
        """Test successful token refresh."""
        with patch("routes.auth.get_current_user", return_value=mock_auth_dependency()):
            with patch(
                "services.auth_service.AuthService.create_access_token"
            ) as mock_token:
                mock_token.return_value = "new-token-123"

                response = client.post("/auth/refresh")

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data

    @pytest.mark.asyncio
    async def test_forgot_password_success(self, client):
        """Test successful forgot password request."""
        with patch(
            "services.auth_service.AuthService.send_password_reset"
        ) as mock_reset:
            mock_reset.return_value = True

            response = client.post(
                "/auth/forgot-password", json={"email": "test@example.com"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Password reset email sent"

    @pytest.mark.asyncio
    async def test_reset_password_success(self, client):
        """Test successful password reset."""
        with patch("services.auth_service.AuthService.reset_password") as mock_reset:
            mock_reset.return_value = True

            response = client.post(
                "/auth/reset-password",
                json={"token": "reset-token-123", "new_password": "newpassword123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Password reset successful"


class TestTasksRoutes:
    """Test tasks routes functionality."""

    @pytest.mark.asyncio
    async def test_create_task_success(self, client, mock_auth_dependency):
        """Test successful task creation."""
        with patch(
            "routes.tasks.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch("services.supabase.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_supabase.return_value = mock_client
                mock_client.table().insert().execute.return_value = Mock(
                    data=[
                        {
                            "id": "task-123",
                            "title": "Test Task",
                            "description": "Test Description",
                            "user_id": "user-123",
                            "status": "pending",
                        }
                    ]
                )

                response = client.post(
                    "/tasks/",
                    json={
                        "title": "Test Task",
                        "description": "Test Description",
                        "user_id": "user-123",
                        "priority": "medium",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["title"] == "Test Task"

    @pytest.mark.asyncio
    async def test_get_tasks_success(self, client, mock_auth_dependency):
        """Test successful tasks retrieval."""
        with patch(
            "routes.tasks.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch("services.supabase.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_supabase.return_value = mock_client
                mock_client.table().select().eq().range().order().execute.return_value = Mock(
                    data=[
                        {
                            "id": "task-1",
                            "title": "Task 1",
                            "user_id": "user-123",
                            "status": "pending",
                        },
                        {
                            "id": "task-2",
                            "title": "Task 2",
                            "user_id": "user-123",
                            "status": "completed",
                        },
                    ]
                )

                response = client.get("/tasks/")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["title"] == "Task 1"

    @pytest.mark.asyncio
    async def test_get_tasks_with_filters(self, client, mock_auth_dependency):
        """Test tasks retrieval with filters."""
        with patch(
            "routes.tasks.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch("services.supabase.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_supabase.return_value = mock_client
                mock_client.table().select().eq().eq().range().order().execute.return_value = Mock(
                    data=[{"id": "task-1", "title": "Task 1", "status": "pending"}]
                )

                response = client.get("/tasks/?status=pending&priority=high")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1

    @pytest.mark.asyncio
    async def test_update_task_success(self, client, mock_auth_dependency):
        """Test successful task update."""
        with patch(
            "routes.tasks.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch("services.supabase.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_supabase.return_value = mock_client
                mock_client.table().update().eq().eq().execute.return_value = Mock(
                    data=[
                        {
                            "id": "task-123",
                            "title": "Updated Task",
                            "status": "completed",
                        }
                    ]
                )

                response = client.put(
                    "/tasks/task-123",
                    json={"title": "Updated Task", "status": "completed"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["title"] == "Updated Task"

    @pytest.mark.asyncio
    async def test_delete_task_success(self, client, mock_auth_dependency):
        """Test successful task deletion."""
        with patch(
            "routes.tasks.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch("services.supabase.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_supabase.return_value = mock_client
                mock_client.table().delete().eq().eq().execute.return_value = Mock(
                    data=[]
                )

                response = client.delete("/tasks/task-123")

                assert response.status_code == 204


# class TestMoodRoutes:
#     """Test mood tracking routes functionality."""
#     # Mood routes not implemented yet
#     pass


class TestGenerateRoutes:
    """Test content generation routes functionality."""

    @pytest.mark.asyncio
    async def test_generate_daily_brief_success(self, client, mock_auth_dependency):
        """Test successful daily brief generation."""
        with patch(
            "routes.generate.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch(
                "services.ai.hybrid_ai_service.get_hybrid_ai_service"
            ) as mock_openai:
                mock_openai.return_value = Mock()
                mock_openai.return_value.generate_text.return_value = {
                    "generated_text": "Daily brief content"
                }

                response = client.post(
                    "/generate/daily-brief", json={"date": "2024-01-01"}
                )

                assert response.status_code == 200
                data = response.json()
                assert "message" in data

    @pytest.mark.asyncio
    async def test_extract_tasks_from_text_success(self, client, mock_auth_dependency):
        """Test successful task extraction from text."""
        with patch(
            "routes.generate.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch(
                "services.ai.hybrid_ai_service.get_hybrid_ai_service"
            ) as mock_openai:
                mock_openai.return_value = Mock()
                mock_openai.return_value.generate_text.return_value = {
                    "generated_text": '[{"task": "Complete project", "priority": "high"}]'
                }

                response = client.post(
                    "/generate/extract-tasks-from-text",
                    json={
                        "text": "I need to complete the project and review the code",
                        "goal_context": "Finish Q1 deliverables",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert "extracted_tasks" in data

    @pytest.mark.asyncio
    async def test_plan_my_day_success(self, client, mock_auth_dependency):
        """Test successful daily planning."""
        with patch(
            "routes.generate.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch(
                "services.ai.hybrid_ai_service.get_hybrid_ai_service"
            ) as mock_openai:
                mock_openai.return_value = Mock()
                mock_openai.return_value.generate_text.return_value = {
                    "generated_text": '{"timeblocks": [{"start_time": "09:00", "end_time": "10:30", "task_name": "Work"}]}'
                }

                response = client.post(
                    "/generate/plan-my-day",
                    json={
                        "date": "2024-01-01",
                        "focus_hours": "morning",
                        "preferred_working_hours": "09:00-17:00",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert "timeblocks" in data


class TestNotionRoutes:
    """Test Notion integration routes functionality."""

    @pytest.mark.asyncio
    async def test_get_notion_auth_url_success(self, client, mock_auth_dependency):
        """Test successful Notion auth URL generation."""
        with patch(
            "routes.notion.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch.dict("os.environ", {"NOTION_CLIENT_ID": "test-client-id"}):
                response = client.get("/notion/auth/url")

                assert response.status_code == 200
                data = response.json()
                assert "auth_url" in data
                assert "state" in data

    @pytest.mark.asyncio
    async def test_notion_auth_callback_success(self, client, mock_auth_dependency):
        """Test successful Notion auth callback."""
        with patch(
            "routes.notion.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch("services.rate_limited_queue.get_notion_queue") as mock_queue:
                mock_queue_instance = Mock()
                mock_queue.return_value = mock_queue_instance
                mock_queue_instance.enqueue_request.return_value = AsyncMock()
                mock_queue_instance.enqueue_request.return_value.__await__ = (
                    lambda: iter(
                        [
                            Mock(
                                status_code=200,
                                json=lambda: {
                                    "access_token": "notion-token",
                                    "workspace_id": "workspace-123",
                                },
                            )
                        ]
                    )
                )

                with patch("services.supabase.get_supabase_client") as mock_supabase:
                    mock_client = Mock()
                    mock_supabase.return_value = mock_client
                    mock_client.table().select().eq().execute.return_value = Mock(
                        data=[]
                    )
                    mock_client.table().insert().execute.return_value = Mock(
                        data=[{"id": "1"}]
                    )

                    response = client.post(
                        "/notion/auth/callback",
                        json={
                            "code": "auth-code-123",
                            "state": "user_user-123_1234567890.0",
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True

    @pytest.mark.asyncio
    async def test_list_notion_databases_success(self, client, mock_auth_dependency):
        """Test successful Notion databases listing."""
        with patch(
            "routes.notion.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch("services.notion.NotionClient") as mock_notion_client:
                mock_client = Mock()
                mock_notion_client.return_value = mock_client
                mock_client.get_databases.return_value = [
                    {"id": "db-1", "title": "Tasks"},
                    {"id": "db-2", "title": "Notes"},
                ]

                response = client.get("/notion/databases")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2

    @pytest.mark.asyncio
    async def test_sync_notion_database_success(self, client, mock_auth_dependency):
        """Test successful Notion database sync."""
        with patch(
            "routes.notion.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch("services.notion.NotionSyncManager") as mock_sync_manager:
                mock_manager = Mock()
                mock_sync_manager.return_value = mock_manager
                mock_manager.sync_database.return_value = {
                    "status": "success",
                    "items_synced": 10,
                }

                response = client.post(
                    "/notion/sync/database",
                    json={"database_id": "db-123", "sync_type": "bidirectional"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"

    @pytest.mark.asyncio
    async def test_generate_flashcards_from_notion_success(
        self, client, mock_auth_dependency
    ):
        """Test successful flashcard generation from Notion."""
        with patch(
            "routes.notion.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch("services.notion.NotionFlashcardGenerator") as mock_generator:
                mock_gen = Mock()
                mock_generator.return_value = mock_gen
                mock_gen.generate_flashcards.return_value = [
                    {"question": "What is X?", "answer": "X is Y"}
                ]

                response = client.post(
                    "/notion/generate-flashcards",
                    json={"page_id": "page-123", "count": 5, "difficulty": "medium"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "flashcards" in data


# Error Handling Tests
class TestRouteErrorHandling:
    """Error handling tests for routes."""

    @pytest.mark.asyncio
    async def test_ai_route_openai_error(self, client, mock_auth_dependency):
        """Test AI route with OpenAI error."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch(
                "services.cost_tracking.cost_tracking_service.check_budget_limits"
            ) as mock_budget:
                mock_budget.return_value = {
                    "daily_exceeded": False,
                    "monthly_exceeded": False,
                }

                with patch(
                    "services.ai.hybrid_ai_service.get_hybrid_ai_service"
                ) as mock_openai:
                    mock_openai.return_value = Mock()
                    mock_openai.return_value.generate_text.return_value = {
                        "error": "OpenAI API error"
                    }

                    response = client.post(
                        "/ai/plan-day",
                        json={
                            "date": "2024-01-01",
                            "preferences": {"focus_areas": ["work"], "duration": "8h"},
                        },
                    )

                    assert response.status_code == 500
                    assert "Failed to generate daily plan" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_auth_route_database_error(self, client):
        """Test auth route with database error."""
        with patch("services.auth_service.AuthService.register_user") as mock_register:
            mock_register.side_effect = Exception("Database error")

            response = client.post(
                "/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "securepassword123",
                    "name": "Test User",
                },
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_tasks_route_supabase_error(self, client, mock_auth_dependency):
        """Test tasks route with Supabase error."""
        with patch(
            "routes.tasks.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch("services.supabase.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_supabase.return_value = mock_client
                mock_client.table().insert().execute.side_effect = Exception(
                    "Supabase error"
                )

                response = client.post(
                    "/tasks/",
                    json={
                        "title": "Test Task",
                        "description": "Test Description",
                        "user_id": "user-123",
                        "priority": "medium",
                    },
                )

                assert response.status_code == 500
                assert "Failed to create task" in response.json()["detail"]


# Edge Case Tests
class TestRouteEdgeCases:
    """Edge case tests for routes."""

    @pytest.mark.asyncio
    async def test_ai_route_empty_preferences(self, client, mock_auth_dependency):
        """Test AI route with empty preferences."""
        with patch("routes.ai.get_current_user", return_value=mock_auth_dependency()):
            with patch(
                "services.cost_tracking.cost_tracking_service.check_budget_limits"
            ) as mock_budget:
                mock_budget.return_value = {
                    "daily_exceeded": False,
                    "monthly_exceeded": False,
                }

                with patch(
                    "services.ai.hybrid_ai_service.get_hybrid_ai_service"
                ) as mock_openai:
                    mock_openai.return_value = Mock()
                    mock_openai.return_value.generate_text.return_value = {
                        "generated_text": '[{"time": "09:00-10:30", "activity": "Work", "focus_area": "work"}]'
                    }

                    response = client.post(
                        "/ai/plan-day",
                        json={
                            "date": "2024-01-01",
                            "preferences": {"focus_areas": [], "duration": None},
                        },
                    )

                    assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_tasks_route_large_limit(self, client, mock_auth_dependency):
        """Test tasks route with large limit."""
        with patch(
            "routes.tasks.get_current_user", return_value=mock_auth_dependency()
        ):
            with patch("services.supabase.get_supabase_client") as mock_supabase:
                mock_client = Mock()
                mock_supabase.return_value = mock_client
                mock_client.table().select().eq().range().order().execute.return_value = Mock(
                    data=[]
                )

                response = client.get("/tasks/?limit=1000")

                assert response.status_code == 200

    # @pytest.mark.asyncio
    # async def test_mood_route_invalid_score(self, client, mock_auth_dependency):
    #     """Test mood route with invalid score."""
    #     # Mood routes not implemented yet
    #     pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
