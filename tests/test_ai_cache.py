import pytest
import json
import hashlib
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

from services.ai_cache import (
    AICacheService,
    ai_cache_service,
    ai_cached,
    invalidate_ai_cache_for_user
)


class TestAICacheService:
    """Test AICacheService functionality."""

    @pytest.fixture
    def cache_service(self):
        """Create an AICacheService instance for testing."""
        return AICacheService()

    @pytest.fixture
    def mock_enhanced_cache(self):
        """Mock enhanced_cache for testing."""
        with patch('services.ai_cache.enhanced_cache') as mock_cache:
            mock_cache.get = AsyncMock()
            mock_cache.set = AsyncMock()
            mock_cache.clear_pattern = AsyncMock()
            mock_cache.client = MagicMock()
            yield mock_cache

    @pytest.fixture
    def mock_supabase(self):
        """Mock supabase client for testing."""
        with patch('services.ai_cache.get_supabase_client') as mock_client:
            mock_supabase = MagicMock()
            mock_client.return_value = mock_supabase
            yield mock_supabase

    def test_ai_cache_service_initialization(self, cache_service, mock_supabase):
        """Test AICacheService initialization."""
        assert cache_service is not None
        assert hasattr(cache_service, 'ttl_config')
        assert hasattr(cache_service, 'supabase')
        assert isinstance(cache_service.ttl_config, dict)

    def test_ttl_config_values(self, cache_service):
        """Test TTL configuration values."""
        expected_operations = [
            'ai_insights', 'ai_planning', 'ai_flashcards', 'ai_analysis',
            'ai_suggestions', 'ai_summary', 'ai_optimization', 'ai_feedback',
            'ai_review'
        ]
        
        for operation in expected_operations:
            assert operation in cache_service.ttl_config
            assert isinstance(cache_service.ttl_config[operation], int)
            assert cache_service.ttl_config[operation] > 0

    def test_generate_ai_cache_key_basic(self, cache_service):
        """Test basic AI cache key generation."""
        key = cache_service._generate_ai_cache_key("ai_insights", "user123")
        expected = "ai_cache:ai:ai_insights:user:user123"
        assert key == expected

    def test_generate_ai_cache_key_with_data_hash(self, cache_service):
        """Test AI cache key generation with data hash."""
        key = cache_service._generate_ai_cache_key(
            "ai_insights", "user123", data_hash="abc123"
        )
        expected = "ai_cache:ai:ai_insights:user:user123:data:abc123"
        assert key == expected

    def test_generate_ai_cache_key_with_kwargs(self, cache_service):
        """Test AI cache key generation with additional kwargs."""
        key = cache_service._generate_ai_cache_key(
            "ai_insights", "user123", param1="value1", param2="value2"
        )
        assert "ai_cache:ai:ai_insights:user:user123" in key
        assert "param1:value1" in key
        assert "param2:value2" in key

    def test_generate_ai_cache_key_with_complex_kwargs(self, cache_service):
        """Test AI cache key generation with complex kwargs."""
        key = cache_service._generate_ai_cache_key(
            "ai_insights", "user123", 
            complex_param={"nested": {"key": "value"}},
            list_param=["item1", "item2"]
        )
        assert "ai_cache:ai:ai_insights:user:user123" in key
        assert "complex_param:" in key
        assert "list_param:" in key

    def test_hash_user_data_empty(self, cache_service):
        """Test hashing empty user data."""
        result = cache_service._hash_user_data({})
        assert result == "empty"
        
        result = cache_service._hash_user_data(None)
        assert result == "empty"

    def test_hash_user_data_with_data(self, cache_service):
        """Test hashing user data with actual data."""
        user_data = {"name": "John", "age": 30, "tasks": ["task1", "task2"]}
        result = cache_service._hash_user_data(user_data)
        
        assert isinstance(result, str)
        assert len(result) == 16  # Should be 16 characters

    def test_hash_user_data_consistency(self, cache_service):
        """Test that hashing produces consistent results."""
        user_data = {"name": "John", "age": 30}
        result1 = cache_service._hash_user_data(user_data)
        result2 = cache_service._hash_user_data(user_data)
        
        assert result1 == result2

    def test_hash_user_data_different_order(self, cache_service):
        """Test that hashing produces same result regardless of dict order."""
        user_data1 = {"name": "John", "age": 30}
        user_data2 = {"age": 30, "name": "John"}
        
        result1 = cache_service._hash_user_data(user_data1)
        result2 = cache_service._hash_user_data(user_data2)
        
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_get_cached_ai_response_hit(self, cache_service, mock_enhanced_cache):
        """Test getting cached AI response when cache hit."""
        mock_enhanced_cache.get.return_value = {"response": "cached_result"}
        
        result = await cache_service.get_cached_ai_response(
            "ai_insights", "user123", {"data": "test"}
        )
        
        assert result == {"response": "cached_result"}
        mock_enhanced_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_ai_response_miss(self, cache_service, mock_enhanced_cache):
        """Test getting cached AI response when cache miss."""
        mock_enhanced_cache.get.return_value = None
        
        result = await cache_service.get_cached_ai_response(
            "ai_insights", "user123", {"data": "test"}
        )
        
        assert result is None
        mock_enhanced_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_ai_response_exception(self, cache_service, mock_enhanced_cache):
        """Test getting cached AI response with exception."""
        mock_enhanced_cache.get.side_effect = Exception("Cache error")
        
        result = await cache_service.get_cached_ai_response(
            "ai_insights", "user123", {"data": "test"}
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_cached_ai_response_success(self, cache_service, mock_enhanced_cache):
        """Test setting cached AI response successfully."""
        mock_enhanced_cache.set.return_value = True
        
        result = await cache_service.set_cached_ai_response(
            "ai_insights", "user123", "response_data", {"data": "test"}
        )
        
        assert result is True
        mock_enhanced_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_cached_ai_response_failure(self, cache_service, mock_enhanced_cache):
        """Test setting cached AI response with failure."""
        mock_enhanced_cache.set.return_value = False
        
        result = await cache_service.set_cached_ai_response(
            "ai_insights", "user123", "response_data", {"data": "test"}
        )
        
        assert result is False
        mock_enhanced_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_cached_ai_response_exception(self, cache_service, mock_enhanced_cache):
        """Test setting cached AI response with exception."""
        mock_enhanced_cache.set.side_effect = Exception("Cache error")
        
        result = await cache_service.set_cached_ai_response(
            "ai_insights", "user123", "response_data", {"data": "test"}
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_set_cached_ai_response_metadata(self, cache_service, mock_enhanced_cache):
        """Test that cached response includes metadata."""
        mock_enhanced_cache.set.return_value = True
        
        await cache_service.set_cached_ai_response(
            "ai_insights", "user123", "response_data", {"data": "test"}
        )
        
        # Check that set was called with metadata
        call_args = mock_enhanced_cache.set.call_args
        cached_data = call_args[0][1]  # Second argument is the data
        
        assert "response" in cached_data
        assert "cached_at" in cached_data
        assert "operation" in cached_data
        assert "user_id" in cached_data
        assert "ttl" in cached_data
        assert cached_data["response"] == "response_data"
        assert cached_data["operation"] == "ai_insights"
        assert cached_data["user_id"] == "user123"

    @pytest.mark.asyncio
    async def test_set_cached_ai_response_ttl(self, cache_service, mock_enhanced_cache):
        """Test that cached response uses correct TTL."""
        mock_enhanced_cache.set.return_value = True
        
        await cache_service.set_cached_ai_response(
            "ai_insights", "user123", "response_data"
        )
        
        # Check that set was called with correct TTL
        call_args = mock_enhanced_cache.set.call_args
        ttl = call_args[0][2]  # Third argument is the TTL
        
        assert ttl == cache_service.ttl_config["ai_insights"]

    @pytest.mark.asyncio
    async def test_set_cached_ai_response_unknown_operation_ttl(self, cache_service, mock_enhanced_cache):
        """Test that unknown operation uses default TTL."""
        mock_enhanced_cache.set.return_value = True
        
        await cache_service.set_cached_ai_response(
            "unknown_operation", "user123", "response_data"
        )
        
        # Check that set was called with default TTL
        call_args = mock_enhanced_cache.set.call_args
        ttl = call_args[0][2]  # Third argument is the TTL
        
        assert ttl == 1800  # Default TTL

    @pytest.mark.asyncio
    async def test_invalidate_user_ai_cache_specific_operations(self, cache_service, mock_enhanced_cache):
        """Test invalidating cache for specific operations."""
        mock_enhanced_cache.clear_pattern.return_value = 5
        
        result = await cache_service.invalidate_user_ai_cache(
            "user123", ["ai_insights", "ai_planning"]
        )
        
        assert result == 10  # 5 * 2 operations
        assert mock_enhanced_cache.clear_pattern.call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_user_ai_cache_all_operations(self, cache_service, mock_enhanced_cache):
        """Test invalidating cache for all operations."""
        mock_enhanced_cache.clear_pattern.return_value = 10
        
        result = await cache_service.invalidate_user_ai_cache("user123")
        
        assert result == 10
        mock_enhanced_cache.clear_pattern.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_user_ai_cache_exception(self, cache_service, mock_enhanced_cache):
        """Test invalidating cache with exception."""
        mock_enhanced_cache.clear_pattern.side_effect = Exception("Cache error")
        
        result = await cache_service.invalidate_user_ai_cache("user123")
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_should_use_cache_default(self, cache_service):
        """Test should_use_cache returns True by default."""
        with patch.object(cache_service, '_check_recent_user_changes', return_value=False), \
             patch.object(cache_service, '_get_user_cache_usage', return_value=50):
            
            result = await cache_service.should_use_cache("ai_insights", "user123")
            assert result is True

    @pytest.mark.asyncio
    async def test_should_use_cache_recent_changes(self, cache_service):
        """Test should_use_cache returns False with recent changes."""
        with patch.object(cache_service, '_check_recent_user_changes', return_value=True), \
             patch.object(cache_service, '_get_user_cache_usage', return_value=50):
            
            result = await cache_service.should_use_cache("ai_insights", "user123")
            assert result is False

    @pytest.mark.asyncio
    async def test_should_use_cache_high_usage(self, cache_service):
        """Test should_use_cache returns False with high cache usage."""
        with patch.object(cache_service, '_check_recent_user_changes', return_value=False), \
             patch.object(cache_service, '_get_user_cache_usage', return_value=150):
            
            result = await cache_service.should_use_cache("ai_insights", "user123")
            assert result is False

    @pytest.mark.asyncio
    async def test_should_use_cache_exception(self, cache_service):
        """Test should_use_cache handles exceptions gracefully."""
        with patch.object(cache_service, '_check_recent_user_changes', side_effect=Exception("Error")):
            
            result = await cache_service.should_use_cache("ai_insights", "user123")
            assert result is True  # Should default to True on exception

    @pytest.mark.asyncio
    async def test_check_recent_user_changes_no_changes(self, cache_service, mock_supabase):
        """Test checking recent user changes with no changes."""
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.limit.return_value.execute.return_value = mock_result
        
        result = await cache_service._check_recent_user_changes("user123", "ai_insights")
        assert result is False

    @pytest.mark.asyncio
    async def test_check_recent_user_changes_with_changes(self, cache_service, mock_supabase):
        """Test checking recent user changes with changes."""
        mock_result = MagicMock()
        mock_result.data = [{"updated_at": "2024-01-01T00:00:00Z"}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.limit.return_value.execute.return_value = mock_result
        
        result = await cache_service._check_recent_user_changes("user123", "ai_insights")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_recent_user_changes_exception(self, cache_service, mock_supabase):
        """Test checking recent user changes with exception."""
        mock_supabase.table.side_effect = Exception("Database error")
        
        result = await cache_service._check_recent_user_changes("user123", "ai_insights")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_cache_usage(self, cache_service, mock_enhanced_cache):
        """Test getting user cache usage."""
        mock_enhanced_cache.client.keys.return_value = ["key1", "key2", "key3"]
        
        result = await cache_service._get_user_cache_usage("user123")
        assert result == 3

    @pytest.mark.asyncio
    async def test_get_user_cache_usage_no_client(self, cache_service, mock_enhanced_cache):
        """Test getting user cache usage with no client."""
        mock_enhanced_cache.client = None
        
        result = await cache_service._get_user_cache_usage("user123")
        assert result == 0

    @pytest.mark.asyncio
    async def test_get_user_cache_usage_exception(self, cache_service, mock_enhanced_cache):
        """Test getting user cache usage with exception."""
        mock_enhanced_cache.client.keys.side_effect = Exception("Redis error")
        
        result = await cache_service._get_user_cache_usage("user123")
        assert result == 0

    def test_get_cache_stats_success(self, cache_service, mock_enhanced_cache):
        """Test getting cache stats successfully."""
        mock_enhanced_cache.client.keys.return_value = [
            "ai_cache:ai:ai_insights:user:user1",
            "ai_cache:ai:ai_insights:user:user2",
            "ai_cache:ai:ai_planning:user:user1"
        ]
        
        result = cache_service.get_cache_stats()
        
        assert result["total_ai_cache_entries"] == 3
        assert result["cache_enabled"] is True
        assert "operations" in result

    def test_get_cache_stats_no_client(self, cache_service, mock_enhanced_cache):
        """Test getting cache stats with no client."""
        mock_enhanced_cache.client = None
        
        result = cache_service.get_cache_stats()
        
        assert "error" in result
        assert result["error"] == "Cache not available"

    def test_get_cache_stats_exception(self, cache_service, mock_enhanced_cache):
        """Test getting cache stats with exception."""
        mock_enhanced_cache.client.keys.side_effect = Exception("Redis error")
        
        result = cache_service.get_cache_stats()
        
        assert "error" in result


class TestAICacheDecorator:
    """Test ai_cached decorator functionality."""

    @pytest.mark.asyncio
    async def test_ai_cached_decorator_cache_hit(self, mock_enhanced_cache):
        """Test ai_cached decorator with cache hit."""
        mock_enhanced_cache.get.return_value = {"response": "cached_result"}
        
        @ai_cached("ai_insights")
        async def test_function(user_id: str, data: str):
            return f"processed_{data}"
        
        with patch('services.ai_cache.ai_cache_service') as mock_service:
            mock_service.should_use_cache.return_value = True
            mock_service.get_cached_ai_response.return_value = {"response": "cached_result"}
            
            result = await test_function("user123", "test_data")
            assert result == "cached_result"

    @pytest.mark.asyncio
    async def test_ai_cached_decorator_cache_miss(self, mock_enhanced_cache):
        """Test ai_cached decorator with cache miss."""
        @ai_cached("ai_insights")
        async def test_function(user_id: str, data: str):
            return f"processed_{data}"
        
        with patch('services.ai_cache.ai_cache_service') as mock_service:
            mock_service.should_use_cache.return_value = True
            mock_service.get_cached_ai_response.return_value = None
            mock_service.set_cached_ai_response.return_value = True
            
            result = await test_function("user123", "test_data")
            assert result == "processed_test_data"
            mock_service.set_cached_ai_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_cached_decorator_no_cache(self, mock_enhanced_cache):
        """Test ai_cached decorator when cache should not be used."""
        @ai_cached("ai_insights")
        async def test_function(user_id: str, data: str):
            return f"processed_{data}"
        
        with patch('services.ai_cache.ai_cache_service') as mock_service:
            mock_service.should_use_cache.return_value = False
            
            result = await test_function("user123", "test_data")
            assert result == "processed_test_data"
            mock_service.get_cached_ai_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_ai_cached_decorator_no_user_id(self, mock_enhanced_cache):
        """Test ai_cached decorator with no user_id."""
        @ai_cached("ai_insights")
        async def test_function(data: str):
            return f"processed_{data}"
        
        result = await test_function("test_data")
        assert result == "processed_test_data"

    @pytest.mark.asyncio
    async def test_ai_cached_decorator_user_id_from_object(self, mock_enhanced_cache):
        """Test ai_cached decorator with user_id from object attribute."""
        class UserObject:
            def __init__(self, user_id: str):
                self.user_id = user_id
        
        @ai_cached("ai_insights")
        async def test_function(user_obj: UserObject, data: str):
            return f"processed_{data}"
        
        with patch('services.ai_cache.ai_cache_service') as mock_service:
            mock_service.should_use_cache.return_value = True
            mock_service.get_cached_ai_response.return_value = None
            mock_service.set_cached_ai_response.return_value = True
            
            user_obj = UserObject("user123")
            result = await test_function(user_obj, "test_data")
            assert result == "processed_test_data"
            mock_service.should_use_cache.assert_called_once()


class TestAICacheUtilityFunctions:
    """Test utility functions."""

    @pytest.mark.asyncio
    async def test_invalidate_ai_cache_for_user(self):
        """Test invalidate_ai_cache_for_user function."""
        with patch('services.ai_cache.ai_cache_service') as mock_service:
            mock_service.invalidate_user_ai_cache.return_value = 5
            
            result = await invalidate_ai_cache_for_user("user123", ["ai_insights"])
            assert result == 5
            mock_service.invalidate_user_ai_cache.assert_called_once_with("user123", ["ai_insights"])

    def test_global_ai_cache_service_instance(self):
        """Test that global ai_cache_service instance exists."""
        assert ai_cache_service is not None
        assert isinstance(ai_cache_service, AICacheService)


class TestAICacheIntegration:
    """Integration tests for AI cache functionality."""

    @pytest.mark.asyncio
    async def test_full_cache_workflow(self, mock_enhanced_cache, mock_supabase):
        """Test complete cache workflow."""
        cache_service = AICacheService()
        
        # Mock cache miss first
        mock_enhanced_cache.get.return_value = None
        mock_enhanced_cache.set.return_value = True
        
        # Mock no recent changes
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.limit.return_value.execute.return_value = mock_result
        
        # Mock low cache usage
        mock_enhanced_cache.client.keys.return_value = ["key1", "key2"]
        
        # First call should miss cache and set result
        user_data = {"tasks": ["task1", "task2"]}
        result1 = await cache_service.get_cached_ai_response(
            "ai_insights", "user123", user_data
        )
        assert result1 is None
        
        # Set the response
        await cache_service.set_cached_ai_response(
            "ai_insights", "user123", "ai_response", user_data
        )
        
        # Mock cache hit for second call
        mock_enhanced_cache.get.return_value = {"response": "ai_response"}
        
        # Second call should hit cache
        result2 = await cache_service.get_cached_ai_response(
            "ai_insights", "user123", user_data
        )
        assert result2 == {"response": "ai_response"}

    @pytest.mark.asyncio
    async def test_cache_key_consistency(self, cache_service):
        """Test that cache keys are consistent across calls."""
        user_data = {"name": "John", "tasks": ["task1", "task2"]}
        
        key1 = cache_service._generate_ai_cache_key(
            "ai_insights", "user123", 
            cache_service._hash_user_data(user_data),
            param="value"
        )
        
        key2 = cache_service._generate_ai_cache_key(
            "ai_insights", "user123", 
            cache_service._hash_user_data(user_data),
            param="value"
        )
        
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_different_operations_different_keys(self, cache_service):
        """Test that different operations generate different cache keys."""
        user_data = {"name": "John"}
        data_hash = cache_service._hash_user_data(user_data)
        
        key1 = cache_service._generate_ai_cache_key(
            "ai_insights", "user123", data_hash
        )
        
        key2 = cache_service._generate_ai_cache_key(
            "ai_planning", "user123", data_hash
        )
        
        assert key1 != key2
        assert "ai_insights" in key1
        assert "ai_planning" in key2