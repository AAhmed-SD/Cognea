import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.ai_cache import ai_cached, ai_cache_service


class TestAiCacheService:
    """Test AI cache service functionality."""

    def test_cache_key_generation(self):
        """Test cache key generation with different parameters."""
        key1 = ai_cache_service._generate_ai_cache_key("test", "user1", "hash1", kwarg="value")
        key2 = ai_cache_service._generate_ai_cache_key("test", "user1", "hash1", kwarg="value")
        key3 = ai_cache_service._generate_ai_cache_key("test", "user2", "hash1", kwarg="value")
        
        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different inputs should generate different keys

    def test_hash_user_data(self):
        """Test user data hashing."""
        data1 = {"tasks": [1, 2, 3], "goals": ["goal1"]}
        data2 = {"tasks": [1, 2, 3], "goals": ["goal1"]}
        data3 = {"tasks": [1, 2, 4], "goals": ["goal1"]}
        
        hash1 = ai_cache_service._hash_user_data(data1)
        hash2 = ai_cache_service._hash_user_data(data2)
        hash3 = ai_cache_service._hash_user_data(data3)
        
        assert hash1 == hash2  # Same data should produce same hash
        assert hash1 != hash3  # Different data should produce different hash

    @pytest.mark.asyncio
    async def test_get_cached_ai_response(self):
        """Test getting cached AI response."""
        with patch('services.ai_cache.enhanced_cache') as mock_cache:
            mock_cache.get = AsyncMock(return_value={"response": "cached_result"})
            
            result = await ai_cache_service.get_cached_ai_response(
                "ai_insights", "user123", {"tasks": [1, 2]}
            )
            
            assert result == {"response": "cached_result"}
            mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_cached_ai_response(self):
        """Test setting cached AI response."""
        with patch('services.ai_cache.enhanced_cache') as mock_cache:
            mock_cache.set = AsyncMock(return_value=True)
            
            result = await ai_cache_service.set_cached_ai_response(
                "ai_insights", "user123", "test_response", {"tasks": [1, 2]}
            )
            
            assert result is True
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_user_ai_cache(self):
        """Test cache invalidation."""
        with patch('services.ai_cache.enhanced_cache') as mock_cache:
            mock_cache.clear_pattern = AsyncMock(return_value=5)
            
            result = await ai_cache_service.invalidate_user_ai_cache("user123", ["ai_insights"])
            
            assert result == 5
            mock_cache.clear_pattern.assert_called_once()


class TestAiCachedDecorator:
    """Test the ai_cached decorator."""

    @pytest.mark.asyncio
    async def test_decorator_caches_result(self):
        """Test that decorator caches function results."""
        call_count = 0
        
        @ai_cached("test_operation", ttl=300)
        async def test_function(user_id, data):
            nonlocal call_count
            call_count += 1
            return f"result_{user_id}_{data}"
        
        with patch.object(ai_cache_service, 'should_use_cache', return_value=True), \
             patch.object(ai_cache_service, 'get_cached_ai_response', return_value=None), \
             patch.object(ai_cache_service, 'set_cached_ai_response', return_value=True):
            
            # First call should execute function
            result = await test_function(user_id="user123", data="test_data")
            assert result == "result_user123_test_data"
            assert call_count == 1

    @pytest.mark.asyncio
    async def test_decorator_returns_cached_result(self):
        """Test decorator returns cached result when available."""
        call_count = 0
        
        @ai_cached("test_operation", ttl=300)
        async def test_function(user_id, data):
            nonlocal call_count
            call_count += 1
            return f"result_{user_id}_{data}"
        
        cached_response = {"response": "cached_result"}
        
        with patch.object(ai_cache_service, 'should_use_cache', return_value=True), \
             patch.object(ai_cache_service, 'get_cached_ai_response', return_value=cached_response):
            
            result = await test_function("user123", "test_data")
            assert result == "cached_result"
            assert call_count == 0  # Function not called due to cache hit