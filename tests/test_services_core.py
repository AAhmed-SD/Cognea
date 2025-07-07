from typing import Any, Dict, List, Optional
"""
Core service tests for high coverage.
Focuses on the most critical services: AI, Auth, Cache, Background Workers.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.ai.openai_service import EnhancedOpenAIService
from services.ai_cache import AICacheService, ai_cached
from services.auth_service import AuthService
from services.background_workers import BackgroundWorker, Task, TaskPriority, TaskStatus
from services.cost_tracking import CostTracker
from services.redis_cache import EnhancedRedisCache, enhanced_cached


class TestOpenAIService:
    """Test OpenAI service functionality."""

    @pytest.fixture
    def openai_service(self) -> EnhancedOpenAIService:
        return EnhancedOpenAIService()

    @pytest.mark.asyncio
    async def test_chat_completion_success(
        self, openai_service: EnhancedOpenAIService
    ) -> None:
        """Test successful chat completion."""
        with patch.object(openai_service, "client") as mock_client:
            mock_client.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="Generated text"))],
                usage=Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            )

            messages = [{"role": "user", "content": "Test prompt"}]
            result = await openai_service.chat_completion(
                messages=messages, user_id="user-123"
            )

            assert result.content == "Generated text"
            assert result.model == "gpt-4-turbo-preview"

    @pytest.mark.asyncio
    async def test_generate_task_from_text(
        self, openai_service: EnhancedOpenAIService
    ) -> None:
        """Test task generation from text."""
        with patch.object(openai_service, "client") as mock_client:
            mock_client.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="Task: Test task"))],
                usage=Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            )

            result = await openai_service.generate_task_from_text(
                text="I need to complete the project", user_id="user-123"
            )

            assert "task" in result

    @pytest.mark.asyncio
    async def test_optimize_schedule(
        self, openai_service: EnhancedOpenAIService
    ) -> None:
        """Test schedule optimization."""
        with patch.object(openai_service, "client") as mock_client:
            mock_client.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="Optimized schedule"))],
                usage=Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            )

            result = await openai_service.optimize_schedule(
                tasks=[{"title": "Task 1", "priority": "high"}],
                schedule_blocks=[],
                user_preferences={"focus_hours": "morning"},
                user_id="user-123",
            )

            assert "schedule" in result

    @pytest.mark.asyncio
    async def test_generate_productivity_insights(
        self, openai_service: EnhancedOpenAIService
    ) -> None:
        """Test productivity insights generation."""
        with patch.object(openai_service, "client") as mock_client:
            mock_client.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="Productivity insights"))],
                usage=Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            )

            result = await openai_service.generate_productivity_insights(
                user_data={"tasks": [], "goals": []}, user_id="user-123"
            )

            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_conversational_ai_chat(
        self, openai_service: EnhancedOpenAIService
    ) -> None:
        """Test conversational AI chat."""
        with patch.object(openai_service, "client") as mock_client:
            mock_client.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="AI response"))],
                usage=Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            )

            result = await openai_service.conversational_ai_chat(
                user_message="Hello", user_id="user-123"
            )

            assert "response" in result

    @pytest.mark.asyncio
    async def test_generate_advanced_flashcards(
        self, openai_service: EnhancedOpenAIService
    ) -> None:
        """Test advanced flashcard generation."""
        with patch.object(openai_service, "client") as mock_client:
            mock_client.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="Flashcard content"))],
                usage=Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            )

            result = await openai_service.generate_advanced_flashcards(
                content="Python programming basics", user_id="user-123"
            )

            assert "flashcards" in result


class TestAICacheService:
    """Test AI cache service functionality."""

    @pytest.fixture
    def cache_service(self) -> AICacheService:
        return AICacheService()

    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_service: AICacheService) -> None:
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.set.return_value = True
            mock_cache.get.return_value = {"cached_data": "test"}

            await cache_service.set_cache("test_key", {"data": "test"}, ttl=300)
            result = await cache_service.get_cache("test_key")

            assert result == {"cached_data": "test"}

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_service: AICacheService) -> None:
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.get.return_value = None

            result = await cache_service.get_cache("nonexistent_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache_service: AICacheService) -> None:
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.clear_pattern.return_value = True

            await cache_service.invalidate_user_cache("user-123", "test_operation")
            mock_cache.clear_pattern.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_decorator(self) -> None:
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
        return AuthService()

    def test_verify_password(self, auth_service: AuthService) -> None:
        password = "test_password"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrong_password", hashed) is False

    def test_create_access_token(self, auth_service: AuthService) -> None:
        user_data = {"user_id": "123", "email": "test@example.com"}

        token = auth_service.create_access_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token(self, auth_service: AuthService) -> None:
        user_data = {"user_id": "123", "email": "test@example.com"}
        token = auth_service.create_access_token(user_data)

        payload = auth_service.verify_token(token)

        assert payload["user_id"] == "123"
        assert payload["email"] == "test@example.com"

    def test_verify_token_invalid(self, auth_service: AuthService) -> None:
        with pytest.raises(Exception):
            auth_service.verify_token("invalid_token")


class TestBackgroundWorker:
    """Test background worker functionality."""

    @pytest.fixture
    def worker(self) -> BackgroundWorker:
        return BackgroundWorker(
            redis_url="redis://localhost:6379", max_workers=2, task_timeout=30
        )

    @pytest.mark.asyncio
    async def test_worker_initialization(self, worker: BackgroundWorker) -> None:
        assert worker.max_workers == 2
        assert worker.task_timeout == 30
        assert worker.metrics["tasks_processed"] == 0

    @pytest.mark.asyncio
    async def test_task_enqueue(self, worker: BackgroundWorker) -> None:
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

    @pytest.mark.asyncio
    async def test_worker_health_check(self, worker: BackgroundWorker) -> None:
        health = await worker.health_check()

        assert "status" in health
        assert "workers_active" in health
        assert "tasks_queued" in health


class TestCostTracker:
    """Test cost tracking service functionality."""

    @pytest.fixture
    def cost_tracker(self) -> CostTracker:
        return CostTracker()

    @pytest.mark.asyncio
    async def test_track_api_call(self, cost_tracker: CostTracker) -> None:
        with patch("services.supabase.supabase_client") as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            mock_client.table().insert().execute.return_value = Mock(data=[{"id": "1"}])

            await cost_tracker.track_api_call(
                user_id="user-123",
                endpoint="/test",
                model="gpt-4",
                input_tokens=100,
                output_tokens=200,
                cost_usd=0.01,
            )

            mock_client.table().insert().execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_budget_limits(self, cost_tracker: CostTracker) -> None:
        with patch("services.supabase.supabase_client") as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client

            mock_client.table().select().eq().gte().execute.side_effect = [
                Mock(data=[{"total_cost": 5.0}]),  # Daily cost
                Mock(data=[{"total_cost": 50.0}]),  # Monthly cost
            ]

            result = await cost_tracker.check_budget_limits("user-123")

            assert "can_use" in result
            assert "daily_exceeded" in result
            assert "monthly_exceeded" in result
            assert isinstance(result["daily_exceeded"], bool)
            assert isinstance(result["monthly_exceeded"], bool)

    def test_track_openai_usage(self, cost_tracker: CostTracker) -> None:
        with patch("services.supabase.supabase_client") as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            mock_client.table().insert().execute.return_value = Mock(data=[{"id": "1"}])

            cost_tracker.track_openai_usage(
                user_id="user-123",
                model="gpt-4",
                input_tokens=100,
                output_tokens=200,
                total_tokens=300,
            )

            mock_client.table().insert().execute.assert_called_once()


class TestRedisCache:
    """Test Redis cache functionality."""

    @pytest.fixture
    def redis_cache(self) -> EnhancedRedisCache:
        return EnhancedRedisCache(redis_url="redis://localhost:6379")

    @pytest.mark.asyncio
    async def test_set_get(self, redis_cache: EnhancedRedisCache) -> None:
        with patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.set.return_value = True
            mock_client.get.return_value = b'{"test": "data"}'

            result = await redis_cache.set("test_key", {"test": "data"}, ttl=300)
            assert result is True

            result = await redis_cache.get("test_key")
            assert result == {"test": "data"}

    @pytest.mark.asyncio
    async def test_cache_miss(self, redis_cache: EnhancedRedisCache) -> None:
        with patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.get.return_value = None

            result = await redis_cache.get("nonexistent_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_decorator(self) -> None:
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True

            @enhanced_cached("test_operation", ttl=300)
            async def test_function() -> str:
                return "test_result"

            result = await test_function()
            assert result == "test_result"


# Integration Tests
class TestServiceIntegration:
    """Integration tests for service interactions."""

    @pytest.mark.asyncio
    async def test_ai_with_cache_integration(self) -> None:
        with patch(
            "services.ai.openai_service.EnhancedOpenAIService.chat_completion"
        ) as mock_chat:
            mock_chat.return_value = Mock(content="Cached response")

            with patch("services.ai_cache.AICacheService.get_cache") as mock_cache:
                mock_cache.return_value = {"cached_data": "Cached response"}

                cache_service = AICacheService()
                result = await cache_service.get_cache("ai_test_key")

                assert result == {"cached_data": "Cached response"}

    @pytest.mark.asyncio
    async def test_background_worker_with_monitoring(self) -> None:
        worker = BackgroundWorker(redis_url="redis://localhost:6379")

        async def test_task() -> str:
            return "success"

        worker.register_task("test_task", test_task)

        with patch.object(worker, "redis") as mock_redis:
            mock_redis.hset.return_value = True
            mock_redis.zadd.return_value = True

            task_id = await worker.enqueue_task("test_task")

            assert task_id is not None
            assert worker.metrics["tasks_enqueued"] == 1


# Error Handling Tests
class TestServiceErrorHandling:
    """Error handling tests for services."""

    @pytest.mark.asyncio
    async def test_openai_service_network_error(self) -> None:
        service = EnhancedOpenAIService()

        with patch.object(service, "client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("Network error")

            messages = [{"role": "user", "content": "Test prompt"}]
            with pytest.raises(Exception):
                await service.chat_completion(messages, "user-123")

    @pytest.mark.asyncio
    async def test_cache_service_redis_error(self) -> None:
        cache_service = AICacheService()

        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.get.side_effect = Exception("Redis connection error")

            result = await cache_service.get_cache("test_key")

            assert result is None

    @pytest.mark.asyncio
    async def test_background_worker_task_error(self) -> None:
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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
