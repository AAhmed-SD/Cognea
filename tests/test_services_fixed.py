from typing import Any, Dict, List, Optional
"""
Fixed comprehensive tests for services with proper async mocking
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.ai.context_manager import AdvancedContextManager
from services.ai.openai_service import EnhancedOpenAIService
from services.ai_cache import AICacheService, ai_cached
from services.auth_service import AuthService
from services.cost_tracking import CostTracker
from services.redis_cache import EnhancedRedisCache, enhanced_cached


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
            # Create a mock response with the proper structure
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
            # Create a mock response with the proper structure
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
            # Create a mock response with function calls
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
            mock_cache.set.return_value = True
            mock_cache.get.return_value = {"cached_data": "test"}

            # Test set
            await cache_service.set_cache("test_key", {"data": "test"}, ttl=300)
            mock_cache.set.assert_called_once()

            # Test get
            result = await cache_service.get_cache("test_key")
            assert result == {"cached_data": "test"}

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_service: AICacheService) -> None:
        """Test cache miss scenario."""
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.get.return_value = None

            result = await cache_service.get_cache("nonexistent_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache_service: AICacheService) -> None:
        """Test cache invalidation."""
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.clear_pattern.return_value = True

            await cache_service.invalidate_user_cache("user-123", "test_operation")
            mock_cache.clear_pattern.assert_called_once()

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
    async def test_verify_password(self, auth_service: AuthService) -> None:
        """Test password verification."""
        password = "test_password"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrong_password", hashed) is False

    @pytest.mark.asyncio
    async def test_create_access_token(self, auth_service: AuthService) -> None:
        """Test access token creation."""
        user_data = {"user_id": "123", "email": "test@example.com"}

        token = auth_service.create_access_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_verify_token(self, auth_service: AuthService) -> None:
        """Test token verification."""
        user_data = {"user_id": "123", "email": "test@example.com"}
        token = auth_service.create_access_token(user_data)

        payload = auth_service.verify_token(token)

        assert payload["user_id"] == "123"
        assert payload["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, auth_service: AuthService) -> None:
        """Test invalid token verification."""
        with pytest.raises(Exception):
            auth_service.verify_token("invalid_token")


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


class TestRedisCache:
    """Test Redis cache functionality."""

    @pytest.fixture
    def redis_cache(self) -> EnhancedRedisCache:
        """Create Redis cache instance."""
        return EnhancedRedisCache(redis_url="redis://localhost:6379")

    @pytest.mark.asyncio
    async def test_set_get(self, redis_cache: EnhancedRedisCache) -> None:
        """Test cache set and get operations."""
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.set.return_value = True
            mock_cache.get.return_value = "cached_value"

            # Test set
            await redis_cache.set("test_key", "test_value", ttl=300)
            mock_cache.set.assert_called_once()

            # Test get
            result = await redis_cache.get("test_key")
            assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_cache_miss(self, redis_cache: EnhancedRedisCache) -> None:
        """Test cache miss scenario."""
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.get.return_value = None

            result = await redis_cache.get("nonexistent_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_decorator(self) -> None:
        """Test cache decorator functionality."""
        with patch("services.redis_cache.enhanced_cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True

            @enhanced_cached("test_operation", ttl=300)
            async def test_function() -> str:
                return "test_result"

            result = await test_function()
            assert result == "test_result"
