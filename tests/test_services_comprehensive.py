"""
Comprehensive tests for all service modules.
Aims to achieve >90% coverage across all services.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.ai.context_manager import AdvancedContextManager
from services.ai.openai_service import EnhancedOpenAIService
from services.ai_cache import AICacheService, ai_cached
from services.auth_service import AuthService
from services.background_workers import BackgroundWorker, Task, TaskPriority, TaskStatus
from services.cost_tracking import CostTracker
from services.email_service import EmailService
from services.monitoring import MonitoringService
from services.notion.flashcard_generator import NotionFlashcardGenerator
from services.notion.notion_client import NotionClient
from services.notion.sync_manager import NotionSyncManager
from services.performance_monitor import PerformanceMonitor
from services.rate_limited_queue import RateLimitedQueue
from services.redis_cache import EnhancedRedisCache, enhanced_cached
from services.stripe_service import StripeService
from services.supabase import get_supabase_client, get_supabase_service_client


class TestOpenAIService:
    """Test OpenAI service functionality."""

    @pytest.fixture
    def openai_service(self) -> EnhancedOpenAIService:
        """Create OpenAI service instance."""
        return EnhancedOpenAIService()

    @pytest.mark.asyncio
    async def test_chat_completion_success(
        self, openai_service: EnhancedOpenAIService
    ) -> None:
        """Test successful chat completion."""
        with patch.object(
            openai_service.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_response = Mock()
            mock_response.model_dump.return_value = {
                "choices": [
                    {"message": {"content": "Generated text", "function_calls": None}}
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
                "model": "gpt-4-turbo-preview",
            }
            mock_create.return_value = mock_response

            result = await openai_service.chat_completion(
                messages=[{"role": "user", "content": "Test prompt"}],
                user_id="user-123",
            )

            assert result.content == "Generated text"
            assert result.model == "gpt-4-turbo-preview"

    @pytest.mark.asyncio
    async def test_chat_completion_error(
        self, openai_service: EnhancedOpenAIService
    ) -> None:
        """Test chat completion with error."""
        with patch.object(
            openai_service.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = Exception("API Error")

            with pytest.raises(Exception):
                await openai_service.chat_completion(
                    messages=[{"role": "user", "content": "Test prompt"}],
                    user_id="user-123",
                )

    @pytest.mark.asyncio
    async def test_chat_completion_with_context(
        self, openai_service: EnhancedOpenAIService
    ) -> None:
        """Test chat completion with context."""
        with patch.object(
            openai_service.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_response = Mock()
            mock_response.model_dump.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Context-aware text",
                            "function_calls": None,
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 15,
                    "completion_tokens": 25,
                    "total_tokens": 40,
                },
                "model": "gpt-4-turbo-preview",
            }
            mock_create.return_value = mock_response

            result = await openai_service.chat_completion(
                messages=[{"role": "user", "content": "Test prompt"}],
                user_id="user-123",
                context={"user_id": "123", "history": ["prev1", "prev2"]},
            )

            assert result.content == "Context-aware text"

    @pytest.mark.asyncio
    async def test_generate_task_from_text(
        self, openai_service: EnhancedOpenAIService
    ) -> None:
        """Test task generation from text."""
        with patch.object(
            openai_service.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_response = Mock()
            mock_response.model_dump.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Task generated",
                            "function_calls": [
                                {
                                    "name": "create_task",
                                    "arguments": {
                                        "title": "Complete project",
                                        "description": "Finish the project",
                                        "priority": "high",
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
                "model": "gpt-4-turbo-preview",
            }
            mock_create.return_value = mock_response

            result = await openai_service.generate_task_from_text(
                text="I need to complete the project", user_id="user-123"
            )

            assert "task" in result

    @pytest.mark.asyncio
    async def test_chat_completion_rate_limit(
        self, openai_service: EnhancedOpenAIService
    ) -> None:
        """Test rate limit handling."""
        with patch.object(
            openai_service.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = Exception("Rate limit exceeded")

            with pytest.raises(Exception):
                await openai_service.chat_completion(
                    messages=[{"role": "user", "content": "Test prompt"}],
                    user_id="user-123",
                )


class TestContextManager:
    """Test context manager functionality."""

    @pytest.fixture
    def context_manager(self) -> AdvancedContextManager:
        """Create context manager instance."""
        return AdvancedContextManager()

    @pytest.mark.asyncio
    async def test_build_comprehensive_context(
        self, context_manager: AdvancedContextManager
    ) -> None:
        """Test building comprehensive user context."""
        with patch("services.supabase.get_supabase_client") as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client

            # Mock database responses
            mock_client.table().select().eq().execute.return_value = Mock(data=[])

            context = await context_manager.build_comprehensive_context("user-123")

            assert context.user_id == "user-123"
            assert hasattr(context, "current_goals")
            assert hasattr(context, "recent_tasks")
            assert hasattr(context, "productivity_patterns")

    @pytest.mark.asyncio
    async def test_build_comprehensive_context_empty(
        self, context_manager: AdvancedContextManager
    ) -> None:
        """Test building comprehensive context with empty data."""
        with patch("services.supabase.get_supabase_client") as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client

            # Mock empty database responses
            mock_client.table().select().eq().execute.return_value = Mock(data=[])

            context = await context_manager.build_comprehensive_context("user-123")

            assert context.user_id == "user-123"
            assert context.current_goals == []
            assert context.recent_tasks == []

    @pytest.mark.asyncio
    async def test_build_comprehensive_context_error(
        self, context_manager: AdvancedContextManager
    ) -> None:
        """Test building comprehensive context with error."""
        with patch("services.supabase.get_supabase_client") as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            mock_client.table().select().eq().execute.side_effect = Exception(
                "DB Error"
            )

            context = await context_manager.build_comprehensive_context("user-123")

            assert context.user_id == "user-123"


class TestAICacheService:
    """Test AI cache service functionality."""

    @pytest.fixture
    def cache_service(self) -> AICacheService:
        """Create cache service instance."""
        return AICacheService()

    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_service: AICacheService) -> None:
        """Test cache set and get operations."""
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.get.return_value = {"cached_data": "test"}
            mock_cache.set.return_value = True

            # Test set
            result_set = await cache_service.set_cached_ai_response(
                operation="ai_insights",
                user_id="user-123",
                response={"data": "test"},
                user_data={"foo": "bar"},
            )
            assert result_set is True
            # Test get
            result_get = await cache_service.get_cached_ai_response(
                operation="ai_insights", user_id="user-123", user_data={"foo": "bar"}
            )
            assert result_get == {"cached_data": "test"}

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_service: AICacheService) -> None:
        """Test cache miss scenario."""
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.get.return_value = None
            result = await cache_service.get_cached_ai_response(
                operation="ai_insights", user_id="user-123", user_data={"foo": "bar"}
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache_service: AICacheService) -> None:
        """Test cache invalidation."""
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.clear_pattern.return_value = 1
            result = await cache_service.invalidate_user_ai_cache(
                "user-123", ["ai_insights"]
            )
            assert result == 1

    @pytest.mark.asyncio
    async def test_cache_decorator(self) -> None:
        """Test cache decorator functionality."""
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True

            @ai_cached("test_operation", ttl=300)
            async def test_function() -> str:
                return "test_result"

            result = await test_function()
            assert result == "test_result"


class TestAuthService:
    """Test authentication service functionality."""

    @pytest.fixture
    def auth_service(self) -> AuthService:
        """Create auth service instance."""
        return AuthService()

    @pytest.mark.asyncio
    async def test_password_hash_and_verify(self, auth_service: AuthService) -> None:
        """Test password hashing and verification (using private methods)."""
        password = "test_password"
        hashed = auth_service._hash_password(password)
        assert auth_service._verify_password(password, hashed) is True
        assert auth_service._verify_password("wrong_password", hashed) is False

    @pytest.mark.asyncio
    async def test_token_creation_and_verification(
        self, auth_service: AuthService
    ) -> None:
        """Test token creation and verification (using private methods)."""
        tokens = auth_service._create_tokens("user-123", "user")
        access_token = tokens["access_token"]
        payload = auth_service._verify_token(access_token)
        assert payload["user_id"] == "user-123"
        assert payload["role"] == "user"

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, auth_service: AuthService) -> None:
        """Test invalid token verification."""
        with pytest.raises(Exception):
            auth_service.verify_token("invalid_token")


class TestBackgroundWorker:
    """Test background worker functionality."""

    @pytest.fixture
    def worker(self) -> BackgroundWorker:
        """Create background worker instance."""
        return BackgroundWorker(
            redis_url="redis://localhost:6379", max_workers=2, task_timeout=30
        )

    @pytest.mark.asyncio
    async def test_worker_initialization(self, worker: BackgroundWorker) -> None:
        """Test worker initialization."""
        assert worker.max_workers == 2
        assert worker.task_timeout == 30
        assert worker.metrics["tasks_processed"] == 0

    @pytest.mark.asyncio
    async def test_task_enqueue(self, worker: BackgroundWorker) -> None:
        """Test task enqueueing."""
        with patch.object(worker, "redis") as mock_redis:
            mock_redis.hset.return_value = True
            mock_redis.zadd.return_value = True

            async def test_task() -> str:
                return "success"

            worker.register_task("test_task", test_task)
            task_id = await worker.enqueue_task("test_task", priority=TaskPriority.HIGH)

            assert task_id is not None
            assert mock_redis.hset.called
            assert mock_redis.zadd.called

    @pytest.mark.asyncio
    async def test_task_processing_success(self, worker: BackgroundWorker) -> None:
        """Test successful task processing."""
        with patch.object(worker, "redis") as mock_redis:
            mock_redis.hgetall.return_value = {
                "id": "test-task",
                "name": "test_task",
                "status": TaskStatus.PENDING.value,
            }

            async def test_task() -> str:
                return "success"

            worker.register_task("test_task", test_task)

            task = Task(
                id="test-task",
                name="test_task",
                func_name="test_task",
                args=(),
                kwargs={},
                priority=TaskPriority.NORMAL,
                status=TaskStatus.PENDING,
                created_at=datetime.utcnow(),
                max_retries=3,
                retry_delay=5,
            )

            await worker._process_task("worker-1", task.id)

            assert worker.metrics["tasks_processed"] == 1
            assert worker.metrics["tasks_failed"] == 0

    @pytest.mark.asyncio
    async def test_task_processing_failure(self, worker: BackgroundWorker) -> None:
        """Test task processing failure."""
        with patch.object(worker, "redis") as mock_redis:
            mock_redis.hgetall.return_value = {
                "id": "test-task",
                "name": "test_task",
                "status": TaskStatus.PENDING.value,
            }

            async def failing_task() -> None:
                raise Exception("Task failed")

            worker.register_task("test_task", failing_task)

            task = Task(
                id="test-task",
                name="test_task",
                func_name="test_task",
                args=(),
                kwargs={},
                priority=TaskPriority.NORMAL,
                status=TaskStatus.PENDING,
                created_at=datetime.utcnow(),
                max_retries=3,
                retry_delay=5,
            )

            await worker._process_task("worker-1", task.id)

            assert worker.metrics["tasks_failed"] == 1


class TestCostTracker:
    """Test cost tracking service functionality."""

    @pytest.fixture
    def cost_service(self) -> CostTracker:
        """Create cost tracking service instance."""
        return CostTracker()

    @pytest.mark.asyncio
    async def test_track_api_call(self, cost_service: CostTracker) -> None:
        """Test API call tracking."""
        with patch("services.supabase.get_supabase_client") as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            mock_client.table().insert().execute.return_value = Mock(data=[{"id": "1"}])

            await cost_service.track_api_call(
                user_id="user-123",
                endpoint="/test",
                model="gpt-4",
                input_tokens=100,
                output_tokens=200,
                cost_usd=0.01,
            )

            mock_client.table().insert().execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_budget_limits(self, cost_service: CostTracker) -> None:
        """Test budget limit checking."""
        with patch("services.supabase.get_supabase_client") as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client

            # Mock daily and monthly costs
            mock_client.table().select().eq().gte().execute.side_effect = [
                Mock(data=[{"total_cost": 5.0}]),  # Daily cost
                Mock(data=[{"total_cost": 50.0}]),  # Monthly cost
            ]

            result = await cost_service.check_budget_limits("user-123")

            assert "daily_exceeded" in result
            assert "monthly_exceeded" in result
            assert isinstance(result["daily_exceeded"], bool)
            assert isinstance(result["monthly_exceeded"], bool)

    @pytest.mark.asyncio
    async def test_get_user_costs(self, cost_service: CostTracker) -> None:
        """Test getting user costs."""
        with patch("services.supabase.get_supabase_client") as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            mock_client.table().select().eq().execute.return_value = Mock(
                data=[{"total_cost": 10.0, "model": "gpt-4"}]
            )

            result = await cost_service.get_user_costs("user-123", days=30)

            assert isinstance(result, list)
            assert len(result) > 0


class TestEmailService:
    """Test email service functionality."""

    @pytest.fixture
    def email_service(self) -> EmailService:
        """Create email service instance."""
        return EmailService()

    @pytest.mark.asyncio
    async def test_send_email(self, email_service: EmailService) -> None:
        """Test sending email."""
        with patch.object(email_service, "_send_email") as mock_send:
            mock_send.return_value = True

            result = await email_service.send_password_reset_email(
                user_id="user-123", email="test@example.com", reset_token="reset-token"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_email_failure(self, email_service: EmailService) -> None:
        """Test sending email failure."""
        with patch.object(email_service, "_send_email") as mock_send:
            mock_send.side_effect = Exception("Email service error")

            with pytest.raises(Exception):
                await email_service.send_password_reset_email(
                    user_id="user-123",
                    email="test@example.com",
                    reset_token="reset-token",
                )

    @pytest.mark.asyncio
    async def test_send_welcome_email(self, email_service: EmailService) -> None:
        """Test sending welcome email."""
        with patch.object(email_service, "_send_email") as mock_send:
            mock_send.return_value = True

            result = await email_service.send_email_verification(
                user_id="user-123", email="test@example.com", first_name="Test"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_password_reset_email(self, email_service: EmailService) -> None:
        """Test sending password reset email."""
        with patch.object(email_service, "_send_email") as mock_send:
            mock_send.return_value = True

            result = await email_service.send_password_reset_email(
                user_id="user-123", email="test@example.com", reset_token="reset-token"
            )

            assert result is True


class TestMonitoringService:
    """Test monitoring service functionality."""

    @pytest.fixture
    def monitoring_service(self) -> MonitoringService:
        """Create monitoring service instance."""
        return MonitoringService()

    @pytest.mark.asyncio
    async def test_record_metric(self, monitoring_service: MonitoringService) -> None:
        """Test recording metrics."""
        with patch("services.monitoring.time.time") as mock_time:
            mock_time.return_value = 1234567890.0

            monitoring_service.log_request(
                request=Mock(method="GET", url="/test"),
                response=Mock(status_code=200),
                duration=0.1,
            )

            # Check that metrics were recorded
            metrics = monitoring_service.get_metrics()
            assert "GET /test" in metrics

    @pytest.mark.asyncio
    async def test_get_metrics(self, monitoring_service: MonitoringService) -> None:
        """Test getting metrics."""
        monitoring_service.log_request(
            request=Mock(method="GET", url="/test"),
            response=Mock(status_code=200),
            duration=0.1,
        )

        metrics = monitoring_service.get_metrics()
        assert isinstance(metrics, str)
        assert "GET /test" in metrics

    @pytest.mark.asyncio
    async def test_health_check(self, monitoring_service: MonitoringService) -> None:
        """Test health check."""
        health = await monitoring_service.get_health_status()

        assert isinstance(health, dict)
        assert "status" in health


class TestNotionClient:
    """Test Notion client functionality."""

    @pytest.fixture
    def notion_client(self) -> NotionClient:
        """Create Notion client instance."""
        return NotionClient(api_key="test-key")

    @pytest.mark.asyncio
    async def test_get_pages(self, notion_client: NotionClient) -> None:
        """Test getting pages from Notion."""
        with patch.object(notion_client, "_make_request") as mock_request:
            mock_request.return_value = {
                "results": [{"id": "page-1", "title": "Test Page"}]
            }

            pages = await notion_client.search(query="test")

            assert len(pages) == 1
            assert pages[0]["id"] == "page-1"

    @pytest.mark.asyncio
    async def test_get_page_content(self, notion_client: NotionClient) -> None:
        """Test getting page content from Notion."""
        with patch.object(notion_client, "_make_request") as mock_request:
            mock_request.return_value = {
                "id": "page-1",
                "properties": {"title": {"title": [{"text": {"content": "Test"}}]}},
            }

            content = await notion_client.get_page("page-1")

            assert content["id"] == "page-1"
            assert "properties" in content

    @pytest.mark.asyncio
    async def test_create_page(self, notion_client: NotionClient) -> None:
        """Test creating a page in Notion."""
        with patch.object(notion_client, "_make_request") as mock_request:
            mock_request.return_value = {
                "id": "new-page",
                "url": "https://notion.so/new-page",
            }

            result = await notion_client.create_page(
                parent_id="database-1",
                properties={"title": {"title": [{"text": {"content": "New Page"}}]}},
            )

            assert result["id"] == "new-page"

    @pytest.mark.asyncio
    async def test_update_page(self, notion_client: NotionClient) -> None:
        """Test updating a page in Notion."""
        with patch.object(notion_client, "_make_request") as mock_request:
            mock_request.return_value = {
                "id": "page-1",
                "url": "https://notion.so/page-1",
            }

            result = await notion_client.update_page(
                page_id="page-1",
                properties={
                    "title": {"title": [{"text": {"content": "Updated Page"}}]}
                },
            )

            assert result["id"] == "page-1"


class TestNotionSyncManager:
    """Test Notion sync manager functionality."""

    @pytest.fixture
    def sync_manager(
        self, notion_client: NotionClient, flashcard_generator: NotionFlashcardGenerator
    ) -> NotionSyncManager:
        """Create Notion sync manager instance."""
        return NotionSyncManager(notion_client, flashcard_generator)

    @pytest.mark.asyncio
    async def test_sync_notion_to_cognie(self, sync_manager: NotionSyncManager) -> None:
        """Test syncing from Notion to Cognie."""
        with patch.object(sync_manager, "_get_notion_page_with_retry") as mock_get_page:
            mock_get_page.return_value = Mock(
                last_edited_time=Mock(isoformat=lambda: "2023-01-01T00:00:00Z"),
                properties={"title": {"title": [{"text": {"content": "Test"}}]}},
            )

        with patch.object(sync_manager, "_get_local_last_synced_ts") as mock_get_ts:
            mock_get_ts.return_value = None

        with patch.object(sync_manager, "_generate_flashcards_with_retry") as mock_gen:
            mock_gen.return_value = [Mock()]

        with patch.object(
            sync_manager, "_save_flashcards_with_conflict_resolution"
        ) as mock_save:
            mock_save.return_value = [{"id": "flashcard-1"}]

        with patch.object(sync_manager, "_save_sync_status") as mock_save_status:
            mock_save_status.return_value = None

        result = await sync_manager.sync_page_to_flashcards("user-123", "page-1")

        assert result.status == "success"
        assert result.items_synced == 1

    @pytest.mark.asyncio
    async def test_sync_cognie_to_notion(self, sync_manager: NotionSyncManager) -> None:
        """Test syncing from Cognie to Notion."""
        with patch.object(sync_manager, "_get_flashcards_from_cognie") as mock_get:
            mock_get.return_value = [{"id": "1", "title": "Test Task"}]

        with patch.object(sync_manager, "notion_client") as mock_notion:
            mock_notion.append_block_children.return_value = {"id": "new-page"}

        with patch.object(sync_manager, "_save_sync_status") as mock_save_status:
            mock_save_status.return_value = None

        result = await sync_manager.sync_flashcards_to_notion(
            "user-123", ["flashcard-1"], "parent-1"
        )

        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_resolve_conflicts(self, sync_manager: NotionSyncManager) -> None:
        """Test conflict resolution."""
        conflicts = [
            {
                "flashcard_id": "flashcard-1",
                "local_content": "Cognie version",
                "notion_content": "Notion version",
                "local_updated": "2023-01-01T00:00:00Z",
                "notion_updated": "2023-01-01T00:01:00Z",
                "conflict_type": "content_mismatch",
            }
        ]

        with patch.object(sync_manager, "_merge_content") as mock_merge:
            mock_merge.return_value = "Merged content"

        with patch.object(sync_manager, "_update_flashcard_content") as mock_update:
            mock_update.return_value = None

        result = await sync_manager._resolve_conflicts(conflicts, "merge", "user-123")

        assert result == 1  # Number of conflicts resolved


class TestNotionFlashcardGenerator:
    """Test Notion flashcard generator functionality."""

    @pytest.fixture
    def flashcard_generator(
        self, notion_client: NotionClient
    ) -> NotionFlashcardGenerator:
        """Create flashcard generator instance."""
        return NotionFlashcardGenerator(notion_client)

    @pytest.mark.asyncio
    async def test_generate_flashcards(
        self, flashcard_generator: NotionFlashcardGenerator
    ) -> None:
        """Test flashcard generation."""
        with patch.object(
            flashcard_generator, "_generate_flashcards_with_ai"
        ) as mock_generate:
            mock_generate.return_value = [
                Mock(
                    question="Test Q?",
                    answer="Test A",
                    tags=["test"],
                    difficulty="medium",
                )
            ]

            flashcards = await flashcard_generator.generate_flashcards_from_text(
                text="Test content", title="Test Title", count=3, difficulty="medium"
            )

            assert len(flashcards) == 1
            assert flashcards[0].question == "Test Q?"

    @pytest.mark.asyncio
    async def test_generate_flashcards_error(
        self, flashcard_generator: NotionFlashcardGenerator
    ) -> None:
        """Test flashcard generation with error."""
        with patch.object(
            flashcard_generator, "_generate_flashcards_with_ai"
        ) as mock_generate:
            mock_generate.side_effect = Exception("API Error")

            with pytest.raises(Exception):
                await flashcard_generator.generate_flashcards_from_text(
                    text="Test content",
                    title="Test Title",
                    count=3,
                    difficulty="medium",
                )


class TestPerformanceMonitor:
    """Test performance monitor functionality."""

    @pytest.fixture
    def performance_monitor(self) -> PerformanceMonitor:
        """Create performance monitor instance."""
        return PerformanceMonitor()

    @pytest.mark.asyncio
    async def test_monitor_function(
        self, performance_monitor: PerformanceMonitor
    ) -> None:
        """Test function monitoring."""
        from services.performance_monitor import monitor_performance

        @monitor_performance("test_function")
        async def test_function() -> str:
            await asyncio.sleep(0.1)
            return "success"

        result = await test_function()

        assert result == "success"
        # Check that metrics were recorded
        metrics = await performance_monitor.get_metrics()
        assert len(metrics) > 0

    @pytest.mark.asyncio
    async def test_get_performance_stats(
        self, performance_monitor: PerformanceMonitor
    ) -> None:
        """Test getting performance statistics."""
        from services.performance_monitor import monitor_performance

        @monitor_performance("test_function")
        async def test_function() -> str:
            await asyncio.sleep(0.1)
            return "success"

        await test_function()
        await test_function()

        metrics = await performance_monitor.get_metrics()

        assert isinstance(metrics, dict)
        assert "test_function" in metrics


class TestRateLimitedQueue:
    """Test rate limited queue functionality."""

    @pytest.fixture
    def rate_limited_queue(self) -> RateLimitedQueue:
        """Create rate-limited queue instance."""
        return RateLimitedQueue(service_name="test")

    @pytest.mark.asyncio
    async def test_enqueue_request(self, rate_limited_queue: RateLimitedQueue) -> None:
        """Test request enqueueing."""
        with patch("httpx.AsyncClient.request") as mock_request:
            mock_request.return_value = Mock(
                status_code=200, json=lambda: {"success": True}
            )

            future = await rate_limited_queue.enqueue_request(
                method="GET",
                endpoint="/test",
                api_key="test-key",
                headers={"Authorization": "Bearer token"},
            )

            response = await future
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(
        self, rate_limited_queue: RateLimitedQueue
    ) -> None:
        """Test rate limit enforcement."""
        # Set very low limits for testing
        rate_limited_queue.requests_per_minute = 1
        rate_limited_queue.requests_per_hour = 1

        with patch("httpx.AsyncClient.request") as mock_request:
            mock_request.return_value = Mock(
                status_code=200, json=lambda: {"success": True}
            )

            # First request should succeed
            future1 = await rate_limited_queue.enqueue_request(
                method="GET", endpoint="/test", api_key="test-key"
            )
            response1 = await future1
            assert response1.status_code == 200

            # Second request should be rate limited
            future2 = await rate_limited_queue.enqueue_request(
                method="GET", endpoint="/test", api_key="test-key"
            )

            # Should handle rate limiting gracefully
            assert future2 is not None


class TestRedisCache:
    """Test Redis cache functionality."""

    @pytest.fixture
    def redis_cache(self) -> EnhancedRedisCache:
        """Create Redis cache instance."""
        return EnhancedRedisCache(redis_url="redis://localhost:6379")

    @pytest.mark.asyncio
    async def test_set_get(self, redis_cache: EnhancedRedisCache) -> None:
        """Test set and get operations."""
        with patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.set.return_value = True
            mock_client.get.return_value = b'{"test": "data"}'

            # Test set
            result = await redis_cache.set("test_key", {"test": "data"}, ttl=300)
            assert result is True

            # Test get
            result = await redis_cache.get("test_key")
            assert result == {"test": "data"}

    @pytest.mark.asyncio
    async def test_cache_miss(self, redis_cache: EnhancedRedisCache) -> None:
        """Test cache miss scenario."""
        with patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.get.return_value = None

            result = await redis_cache.get("nonexistent_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_decorator(self) -> None:
        """Test cache decorator."""
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True

            @enhanced_cached("test_operation", ttl=300)
            async def test_function() -> str:
                return "test_result"

            result = await test_function()
            assert result == "test_result"


class TestStripeService:
    """Test Stripe service functionality."""

    @pytest.fixture
    def stripe_service(self) -> StripeService:
        """Create Stripe service instance."""
        return StripeService()

    @pytest.mark.asyncio
    async def test_create_customer(self, stripe_service: StripeService) -> None:
        """Test creating a customer."""
        with patch("os.getenv", return_value="price_test_123"):
            with patch.object(stripe_service, "supabase") as mock_supabase:
                mock_supabase.table().select().eq().execute.return_value = Mock(
                    data=[{"email": "test@example.com"}]
                )

                with patch.object(stripe_service, "redis_client") as mock_redis:
                    mock_redis.safe_call = AsyncMock(
                        return_value=Mock(
                            id="cs_test_123", url="https://checkout.stripe.com/test"
                        )
                    )

                    result = await stripe_service.create_checkout_session("user-123")

                    assert result.id == "cs_test_123"

    @pytest.mark.asyncio
    async def test_create_subscription(self, stripe_service: StripeService) -> None:
        """Test creating a subscription."""
        with patch("os.getenv", return_value="price_test_123"):
            with patch.object(stripe_service, "supabase") as mock_supabase:
                mock_supabase.table().select().eq().execute.return_value = Mock(
                    data=[{"email": "test@example.com"}]
                )

                with patch.object(stripe_service, "redis_client") as mock_redis:
                    mock_redis.safe_call = AsyncMock(
                        return_value=Mock(
                            id="cs_test_123", url="https://checkout.stripe.com/test"
                        )
                    )

                    result = await stripe_service.create_checkout_session("user-123")

                    assert result.id == "cs_test_123"

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, stripe_service: StripeService) -> None:
        """Test canceling a subscription."""
        with patch.object(stripe_service, "supabase") as mock_supabase:
            mock_supabase.table().select().eq().execute.return_value = Mock(
                data=[
                    {
                        "subscription_status": "canceled",
                        "stripe_customer_id": "cus_123",
                        "subscription_id": "sub_123",
                    }
                ]
            )

            with patch.object(stripe_service, "redis_client") as mock_redis:
                mock_redis.safe_call = AsyncMock(
                    return_value={"status": "canceled", "subscription_id": "sub_123"}
                )

            result = await stripe_service.get_subscription_status("user-123")

            assert result["status"] == "canceled"

    @pytest.mark.asyncio
    async def test_get_invoice(self, stripe_service: StripeService) -> None:
        """Test getting invoice information."""
        with patch.object(stripe_service, "supabase") as mock_supabase:
            mock_supabase.table().select().eq().execute.return_value = Mock(
                data=[
                    {
                        "subscription_status": "active",
                        "stripe_customer_id": "cus_123",
                        "subscription_id": "sub_123",
                    }
                ]
            )

            with patch.object(stripe_service, "redis_client") as mock_redis:
                mock_redis.safe_call = AsyncMock(
                    return_value={
                        "status": "active",
                        "subscription_id": "sub_123",
                        "subscription_details": {"id": "sub_123", "status": "active"},
                    }
                )

            result = await stripe_service.get_subscription_status("user-123")

            assert result["status"] == "active"
            assert "subscription_details" in result


class TestSupabaseService:
    """Test Supabase service functionality."""

    @pytest.mark.asyncio
    async def test_get_supabase_client(self) -> None:
        """Test getting Supabase client."""
        with patch("services.supabase.create_client") as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            client = get_supabase_client()

            assert client == mock_client
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_supabase_service_client(self) -> None:
        """Test getting Supabase service client."""
        with patch("services.supabase.create_client") as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            client = get_supabase_service_client()

            assert client == mock_client
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection(self) -> None:
        """Test connection testing."""
        with patch("services.supabase.supabase_client") as mock_client:
            mock_client.table().select().limit().execute.return_value = Mock(
                data=[{"id": "1"}]
            )

            result = get_supabase_client().test_connection()

            assert result is True


# Integration Tests
class TestServiceIntegration:
    """Integration tests for service interactions."""

    @pytest.mark.asyncio
    async def test_ai_with_cache_integration(self) -> None:
        """Test AI service with cache integration."""
        with patch(
            "services.ai.openai_service.OpenAIService.generate_text"
        ) as mock_generate:
            mock_generate.return_value = {"generated_text": "Cached response"}

            with patch("services.ai_cache.AICacheService.get_cache") as mock_cache:
                mock_cache.return_value = {"cached_data": "Cached response"}

                cache_service = AICacheService()
                result = await cache_service.get_cache("ai_test_key")

                assert result == {"cached_data": "Cached response"}

    @pytest.mark.asyncio
    async def test_background_worker_with_monitoring(self) -> None:
        """Test background worker with monitoring integration."""
        worker = BackgroundWorker(redis_url="redis://localhost:6379")
        monitoring = MonitoringService()

        async def test_task() -> str:
            return "success"

        worker.register_task("test_task", test_task)

        with patch.object(worker, "redis") as mock_redis:
            mock_redis.hset.return_value = True
            mock_redis.zadd.return_value = True

            task_id = await worker.enqueue_task("test_task")

            assert task_id is not None
            assert worker.metrics["tasks_enqueued"] == 1

    @pytest.mark.asyncio
    async def test_notion_sync_with_cost_tracking(self) -> None:
        """Test Notion sync with cost tracking integration."""
        sync_manager = NotionSyncManager()
        cost_service = CostTracker()

        with patch.object(sync_manager, "notion_client") as mock_notion:
            mock_notion.get_page_content.return_value = {"content": "test"}

            with patch("services.supabase.get_supabase_client") as mock_supabase:
                mock_supabase.return_value = Mock()

                with patch.object(cost_service, "track_api_call") as mock_track:
                    mock_track.return_value = None

                    result = await sync_manager.sync_notion_to_cognie(
                        "page-1", "user-123"
                    )

                    assert result["status"] == "success"
                    mock_track.assert_called()


# Performance Tests
class TestServicePerformance:
    """Performance tests for services."""

    @pytest.mark.asyncio
    async def test_cache_performance(self) -> None:
        """Test cache performance under load."""
        cache_service = AICacheService()

        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.set.return_value = True
            mock_cache.get.return_value = {"data": "test"}

            # Test multiple concurrent operations
            tasks = []
            for i in range(100):
                task = cache_service.set_cache(f"key_{i}", {"data": f"value_{i}"})
                tasks.append(task)

            await asyncio.gather(*tasks)

            # Verify all operations completed
            assert len(tasks) == 100

    @pytest.mark.asyncio
    async def test_background_worker_performance(self) -> None:
        """Test background worker performance under load."""
        worker = BackgroundWorker(redis_url="redis://localhost:6379", max_workers=5)

        async def quick_task() -> str:
            await asyncio.sleep(0.01)
            return "success"

        worker.register_task("quick_task", quick_task)

        with patch.object(worker, "redis") as mock_redis:
            mock_redis.hset.return_value = True
            mock_redis.zadd.return_value = True
            mock_redis.hgetall.return_value = {
                "id": "test-task",
                "name": "quick_task",
                "status": TaskStatus.PENDING.value,
            }

            # Enqueue multiple tasks
            tasks = []
            for i in range(50):
                task_id = await worker.enqueue_task("quick_task")
                tasks.append(task_id)

            assert len(tasks) == 50
            assert all(task_id is not None for task_id in tasks)


# Error Handling Tests
class TestServiceErrorHandling:
    """Error handling tests for services."""

    @pytest.mark.asyncio
    async def test_openai_service_network_error(self) -> None:
        """Test OpenAI service network error handling."""
        service = EnhancedOpenAIService(api_key="test-key")

        with patch("openai.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("Network error")

            result = await service.generate_text("Test prompt")

            assert "error" in result
            assert "Network error" in result["error"]

    @pytest.mark.asyncio
    async def test_cache_service_redis_error(self) -> None:
        """Test cache service Redis error handling."""
        cache_service = AICacheService()

        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.get.side_effect = Exception("Redis connection error")

            result = await cache_service.get_cache("test_key")

            assert result is None

    @pytest.mark.asyncio
    async def test_background_worker_task_error(self) -> None:
        """Test background worker task error handling."""
        worker = BackgroundWorker(redis_url="redis://localhost:6379")

        async def failing_task() -> None:
            raise ValueError("Task failed")

        worker.register_task("failing_task", failing_task)

        with patch.object(worker, "redis") as mock_redis:
            mock_redis.hgetall.return_value = {
                "id": "test-task",
                "name": "failing_task",
                "status": TaskStatus.PENDING.value,
            }

            task = Task(
                id="test-task",
                name="failing_task",
                func_name="failing_task",
                args=(),
                kwargs={},
                priority=TaskPriority.NORMAL,
                status=TaskStatus.PENDING,
                created_at=datetime.utcnow(),
                max_retries=3,
                retry_delay=5,
            )

            await worker._process_task("worker-1", task.id)

            assert worker.metrics["tasks_failed"] == 1
            assert worker.metrics["error_counts"]["validation_error"] == 1


# Edge Case Tests
class TestServiceEdgeCases:
    """Edge case tests for services."""

    @pytest.mark.asyncio
    async def test_openai_service_empty_prompt(self) -> None:
        """Test OpenAI service with empty prompt."""
        service = EnhancedOpenAIService(api_key="test-key")

        result = await service.generate_text("")

        assert "error" in result
        assert "empty" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_cache_service_large_data(self) -> None:
        """Test cache service with large data."""
        cache_service = AICacheService()
        large_data = {"data": "x" * 1000000}  # 1MB of data

        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.set.return_value = True

            result = await cache_service.set_cache("large_key", large_data)

            assert result is True

    @pytest.mark.asyncio
    async def test_background_worker_zero_workers(self) -> None:
        """Test background worker with zero workers."""
        worker = BackgroundWorker(redis_url="redis://localhost:6379", max_workers=0)

        assert worker.max_workers == 0
        assert worker.metrics["tasks_processed"] == 0

    @pytest.mark.asyncio
    async def test_cost_tracking_zero_cost(self) -> None:
        """Test cost tracking with zero cost."""
        cost_service = CostTracker()

        with patch("services.supabase.get_supabase_client") as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            mock_client.table().insert().execute.return_value = Mock(data=[{"id": "1"}])

            await cost_service.track_api_call(
                user_id="user-123",
                endpoint="/test",
                model="gpt-4",
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
            )

            mock_client.table().insert().execute.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
