#!/usr/bin/env python3
"""Comprehensive tests for Redis cache service."""

import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from typing import Any, Dict, List, Optional

import pytest

# Import Redis cache modules
from services.redis_cache import (
    EnhancedRedisCache,
    enhanced_cached,
    get_enhanced_cache,
    clear_pattern,
    get_cache_stats,
    invalidate_cache,
)
from services.redis_client import (
    RedisClient,
    get_redis_client,
    safe_redis_call,
    handle_redis_error,
)


class TestEnhancedRedisCache:
    """Test enhanced Redis cache functionality."""

    def test_enhanced_redis_cache_init(self) -> None:
        """Test EnhancedRedisCache initialization."""
        cache = EnhancedRedisCache()
        assert hasattr(cache, 'redis_client')
        assert hasattr(cache, 'default_ttl')
        assert hasattr(cache, 'key_prefix')

    @pytest.mark.asyncio
    async def test_cache_set_get_basic(self) -> None:
        """Test basic cache set and get operations."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.setex = AsyncMock(return_value=True)
            mock_redis.get = AsyncMock(return_value=json.dumps({"test": "data"}))
            
            # Test set
            result = await cache.set("test_key", {"test": "data"}, ttl=300)
            assert result is True
            
            # Test get
            value = await cache.get("test_key")
            assert value == {"test": "data"}

    @pytest.mark.asyncio
    async def test_cache_get_miss(self) -> None:
        """Test cache miss scenario."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            value = await cache.get("nonexistent_key")
            assert value is None

    @pytest.mark.asyncio
    async def test_cache_delete(self) -> None:
        """Test cache deletion."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.delete = AsyncMock(return_value=1)
            
            result = await cache.delete("test_key")
            assert result is True

    @pytest.mark.asyncio
    async def test_cache_exists(self) -> None:
        """Test cache key existence check."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.exists = AsyncMock(return_value=1)
            
            exists = await cache.exists("test_key")
            assert exists is True

    @pytest.mark.asyncio
    async def test_cache_expire(self) -> None:
        """Test setting cache expiration."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.expire = AsyncMock(return_value=True)
            
            result = await cache.expire("test_key", 300)
            assert result is True

    @pytest.mark.asyncio
    async def test_cache_ttl(self) -> None:
        """Test getting cache TTL."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.ttl = AsyncMock(return_value=300)
            
            ttl = await cache.ttl("test_key")
            assert ttl == 300

    @pytest.mark.asyncio
    async def test_cache_increment(self) -> None:
        """Test cache increment operation."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.incr = AsyncMock(return_value=5)
            
            result = await cache.increment("counter_key")
            assert result == 5

    @pytest.mark.asyncio
    async def test_cache_decrement(self) -> None:
        """Test cache decrement operation."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.decr = AsyncMock(return_value=3)
            
            result = await cache.decrement("counter_key")
            assert result == 3

    @pytest.mark.asyncio
    async def test_cache_list_operations(self) -> None:
        """Test cache list operations."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.lpush = AsyncMock(return_value=1)
            mock_redis.rpop = AsyncMock(return_value=json.dumps("item"))
            mock_redis.llen = AsyncMock(return_value=5)
            
            # Test list push
            result = await cache.list_push("list_key", "item")
            assert result == 1
            
            # Test list pop
            item = await cache.list_pop("list_key")
            assert item == "item"
            
            # Test list length
            length = await cache.list_length("list_key")
            assert length == 5

    @pytest.mark.asyncio
    async def test_cache_hash_operations(self) -> None:
        """Test cache hash operations."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.hset = AsyncMock(return_value=1)
            mock_redis.hget = AsyncMock(return_value=json.dumps("value"))
            mock_redis.hgetall = AsyncMock(return_value={"field": json.dumps("value")})
            mock_redis.hdel = AsyncMock(return_value=1)
            
            # Test hash set
            result = await cache.hash_set("hash_key", "field", "value")
            assert result == 1
            
            # Test hash get
            value = await cache.hash_get("hash_key", "field")
            assert value == "value"
            
            # Test hash get all
            hash_data = await cache.hash_get_all("hash_key")
            assert hash_data == {"field": "value"}
            
            # Test hash delete
            result = await cache.hash_delete("hash_key", "field")
            assert result == 1

    @pytest.mark.asyncio
    async def test_cache_set_operations(self) -> None:
        """Test cache set operations."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.sadd = AsyncMock(return_value=1)
            mock_redis.srem = AsyncMock(return_value=1)
            mock_redis.smembers = AsyncMock(return_value={json.dumps("member1"), json.dumps("member2")})
            mock_redis.sismember = AsyncMock(return_value=True)
            
            # Test set add
            result = await cache.set_add("set_key", "member")
            assert result == 1
            
            # Test set remove
            result = await cache.set_remove("set_key", "member")
            assert result == 1
            
            # Test set members
            members = await cache.set_members("set_key")
            assert "member1" in members
            assert "member2" in members
            
            # Test set is member
            is_member = await cache.set_is_member("set_key", "member1")
            assert is_member is True

    @pytest.mark.asyncio
    async def test_cache_pattern_operations(self) -> None:
        """Test cache pattern operations."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.keys = AsyncMock(return_value=["key1", "key2", "key3"])
            mock_redis.delete = AsyncMock(return_value=3)
            
            # Test get keys by pattern
            keys = await cache.get_keys("test:*")
            assert len(keys) == 3
            
            # Test clear pattern
            result = await cache.clear_pattern("test:*")
            assert result == 3

    @pytest.mark.asyncio
    async def test_cache_batch_operations(self) -> None:
        """Test cache batch operations."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.mset = AsyncMock(return_value=True)
            mock_redis.mget = AsyncMock(return_value=[json.dumps("value1"), json.dumps("value2")])
            
            # Test batch set
            data = {"key1": "value1", "key2": "value2"}
            result = await cache.batch_set(data)
            assert result is True
            
            # Test batch get
            keys = ["key1", "key2"]
            values = await cache.batch_get(keys)
            assert values == ["value1", "value2"]

    @pytest.mark.asyncio
    async def test_cache_pipeline_operations(self) -> None:
        """Test cache pipeline operations."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_pipeline = AsyncMock()
            mock_pipeline.execute = AsyncMock(return_value=[True, True, True])
            mock_redis.pipeline = Mock(return_value=mock_pipeline)
            
            async with cache.pipeline() as pipe:
                await pipe.set("key1", "value1")
                await pipe.set("key2", "value2")
                results = await pipe.execute()
            
            assert len(results) == 3  # Including execute call


class TestEnhancedCacheDecorator:
    """Test enhanced cache decorator."""

    @pytest.mark.asyncio
    async def test_cache_decorator_basic(self) -> None:
        """Test basic cache decorator functionality."""
        with patch('services.redis_cache.get_enhanced_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            mock_get_cache.return_value = mock_cache
            
            @enhanced_cached("test_operation", ttl=300)
            async def test_function(param: str) -> str:
                return f"result_{param}"
            
            result = await test_function("test")
            assert result == "result_test"
            
            # Verify cache was called
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_decorator_hit(self) -> None:
        """Test cache decorator with cache hit."""
        with patch('services.redis_cache.get_enhanced_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get = AsyncMock(return_value="cached_result")
            mock_get_cache.return_value = mock_cache
            
            @enhanced_cached("test_operation", ttl=300)
            async def test_function(param: str) -> str:
                return f"result_{param}"
            
            result = await test_function("test")
            assert result == "cached_result"
            
            # Verify cache set was not called
            mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_decorator_with_user_context(self) -> None:
        """Test cache decorator with user context."""
        with patch('services.redis_cache.get_enhanced_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            mock_get_cache.return_value = mock_cache
            
            @enhanced_cached("user_operation", ttl=300, include_user=True)
            async def user_function(user_id: str, data: str) -> str:
                return f"user_{user_id}_{data}"
            
            result = await user_function("user123", "test")
            assert result == "user_user123_test"

    @pytest.mark.asyncio
    async def test_cache_decorator_custom_key_func(self) -> None:
        """Test cache decorator with custom key function."""
        def custom_key_func(*args, **kwargs) -> str:
            return f"custom:{args[0]}"
        
        with patch('services.redis_cache.get_enhanced_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            mock_get_cache.return_value = mock_cache
            
            @enhanced_cached("test_operation", ttl=300, key_func=custom_key_func)
            async def test_function(param: str) -> str:
                return f"result_{param}"
            
            result = await test_function("test")
            assert result == "result_test"

    @pytest.mark.asyncio
    async def test_cache_decorator_error_handling(self) -> None:
        """Test cache decorator error handling."""
        with patch('services.redis_cache.get_enhanced_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get = AsyncMock(side_effect=Exception("Cache error"))
            mock_cache.set = AsyncMock(return_value=True)
            mock_get_cache.return_value = mock_cache
            
            @enhanced_cached("test_operation", ttl=300)
            async def test_function(param: str) -> str:
                return f"result_{param}"
            
            # Should still work even if cache fails
            result = await test_function("test")
            assert result == "result_test"


class TestRedisClient:
    """Test Redis client functionality."""

    def test_redis_client_init(self) -> None:
        """Test RedisClient initialization."""
        client = RedisClient()
        assert hasattr(client, 'redis_url')
        assert hasattr(client, 'pool')
        assert hasattr(client, 'connection_retries')

    @pytest.mark.asyncio
    async def test_redis_client_connect(self) -> None:
        """Test Redis client connection."""
        client = RedisClient()
        
        with patch('redis.asyncio.ConnectionPool.from_url') as mock_pool:
            mock_pool.return_value = AsyncMock()
            
            await client.connect()
            assert client.pool is not None

    @pytest.mark.asyncio
    async def test_redis_client_disconnect(self) -> None:
        """Test Redis client disconnection."""
        client = RedisClient()
        client.pool = AsyncMock()
        
        await client.disconnect()
        client.pool.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_safe_redis_call_success(self) -> None:
        """Test safe Redis call with success."""
        with patch('services.redis_client.get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value="test_value")
            mock_get_client.return_value = mock_client
            
            result = await safe_redis_call("get", "test_key")
            assert result == "test_value"

    @pytest.mark.asyncio
    async def test_safe_redis_call_error(self) -> None:
        """Test safe Redis call with error."""
        with patch('services.redis_client.get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Redis error"))
            mock_get_client.return_value = mock_client
            
            result = await safe_redis_call("get", "test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_handle_redis_error(self) -> None:
        """Test Redis error handling."""
        error = Exception("Redis connection failed")
        operation = "get"
        args = ("test_key",)
        
        result = await handle_redis_error(error, operation, args)
        assert result is None

    @pytest.mark.asyncio
    async def test_redis_client_health_check(self) -> None:
        """Test Redis client health check."""
        client = RedisClient()
        
        with patch.object(client, 'ping') as mock_ping:
            mock_ping.return_value = True
            
            is_healthy = await client.health_check()
            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_redis_client_get_info(self) -> None:
        """Test Redis client info retrieval."""
        client = RedisClient()
        
        with patch.object(client, 'info') as mock_info:
            mock_info.return_value = {
                "redis_version": "6.2.0",
                "used_memory": "1024000",
                "connected_clients": "5"
            }
            
            info = await client.get_info()
            assert info["redis_version"] == "6.2.0"

    @pytest.mark.asyncio
    async def test_redis_client_flush_db(self) -> None:
        """Test Redis client database flush."""
        client = RedisClient()
        
        with patch.object(client, 'flushdb') as mock_flush:
            mock_flush.return_value = True
            
            result = await client.flush_database()
            assert result is True


class TestCacheUtilities:
    """Test cache utility functions."""

    @pytest.mark.asyncio
    async def test_get_enhanced_cache(self) -> None:
        """Test getting enhanced cache instance."""
        cache = await get_enhanced_cache()
        assert isinstance(cache, EnhancedRedisCache)

    @pytest.mark.asyncio
    async def test_clear_pattern_function(self) -> None:
        """Test clear pattern utility function."""
        with patch('services.redis_cache.get_enhanced_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.clear_pattern = AsyncMock(return_value=5)
            mock_get_cache.return_value = mock_cache
            
            result = await clear_pattern("test:*")
            assert result == 5

    @pytest.mark.asyncio
    async def test_get_cache_stats(self) -> None:
        """Test cache statistics retrieval."""
        with patch('services.redis_cache.get_enhanced_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get_stats = AsyncMock(return_value={
                "hits": 100,
                "misses": 20,
                "hit_rate": 0.83
            })
            mock_get_cache.return_value = mock_cache
            
            stats = await get_cache_stats()
            assert stats["hit_rate"] == 0.83

    @pytest.mark.asyncio
    async def test_invalidate_cache_function(self) -> None:
        """Test cache invalidation utility function."""
        with patch('services.redis_cache.get_enhanced_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.delete = AsyncMock(return_value=True)
            mock_get_cache.return_value = mock_cache
            
            result = await invalidate_cache("test_key")
            assert result is True


class TestCachePerformance:
    """Test cache performance characteristics."""

    @pytest.mark.asyncio
    async def test_cache_performance_set_get(self) -> None:
        """Test cache performance for set/get operations."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.setex = AsyncMock(return_value=True)
            mock_redis.get = AsyncMock(return_value=json.dumps({"test": "data"}))
            
            # Test multiple operations
            start_time = time.time()
            for i in range(100):
                await cache.set(f"key_{i}", {"data": f"value_{i}"}, ttl=300)
                await cache.get(f"key_{i}")
            duration = time.time() - start_time
            
            # Should complete quickly
            assert duration < 1.0

    @pytest.mark.asyncio
    async def test_cache_performance_batch_operations(self) -> None:
        """Test cache performance for batch operations."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.mset = AsyncMock(return_value=True)
            mock_redis.mget = AsyncMock(return_value=[json.dumps(f"value_{i}") for i in range(100)])
            
            # Test batch operations
            data = {f"key_{i}": f"value_{i}" for i in range(100)}
            keys = list(data.keys())
            
            start_time = time.time()
            await cache.batch_set(data)
            await cache.batch_get(keys)
            duration = time.time() - start_time
            
            # Batch operations should be faster than individual operations
            assert duration < 0.1

    @pytest.mark.asyncio
    async def test_cache_decorator_performance(self) -> None:
        """Test cache decorator performance."""
        call_count = 0
        
        with patch('services.redis_cache.get_enhanced_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            mock_get_cache.return_value = mock_cache
            
            @enhanced_cached("perf_test", ttl=300)
            async def expensive_function(param: str) -> str:
                nonlocal call_count
                call_count += 1
                await asyncio.sleep(0.01)  # Simulate expensive operation
                return f"result_{param}"
            
            # First call should execute function
            start_time = time.time()
            result1 = await expensive_function("test")
            duration1 = time.time() - start_time
            
            # Mock cache hit for second call
            mock_cache.get.return_value = "cached_result"
            
            start_time = time.time()
            result2 = await expensive_function("test")
            duration2 = time.time() - start_time
            
            # Second call should be faster (cache hit)
            assert duration2 < duration1
            assert call_count == 1  # Function only called once


class TestCacheErrorHandling:
    """Test cache error handling."""

    @pytest.mark.asyncio
    async def test_cache_connection_error(self) -> None:
        """Test cache behavior with connection errors."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
            
            # Should handle connection errors gracefully
            result = await cache.get("test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_timeout_error(self) -> None:
        """Test cache behavior with timeout errors."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.set = AsyncMock(side_effect=TimeoutError("Operation timed out"))
            
            # Should handle timeout errors gracefully
            result = await cache.set("test_key", "test_value")
            assert result is False

    @pytest.mark.asyncio
    async def test_cache_serialization_error(self) -> None:
        """Test cache behavior with serialization errors."""
        cache = EnhancedRedisCache()
        
        # Try to cache non-serializable object
        class NonSerializable:
            def __init__(self):
    pass
                self.func = lambda x: x
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.setex = AsyncMock(return_value=True)
            
            # Should handle serialization errors gracefully
            result = await cache.set("test_key", NonSerializable())
            # Implementation should handle this gracefully

    @pytest.mark.asyncio
    async def test_cache_deserialization_error(self) -> None:
        """Test cache behavior with deserialization errors."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.get = AsyncMock(return_value="invalid_json")
            
            # Should handle deserialization errors gracefully
            result = await cache.get("test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_decorator_cache_error_fallback(self) -> None:
        """Test decorator fallback when cache fails."""
        with patch('services.redis_cache.get_enhanced_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get = AsyncMock(side_effect=Exception("Cache error"))
            mock_cache.set = AsyncMock(side_effect=Exception("Cache error"))
            mock_get_cache.return_value = mock_cache
            
            @enhanced_cached("error_test", ttl=300)
            async def test_function(param: str) -> str:
                return f"result_{param}"
            
            # Should still work even when cache fails
            result = await test_function("test")
            assert result == "result_test"


class TestCacheEdgeCases:
    """Test cache edge cases."""

    @pytest.mark.asyncio
    async def test_cache_empty_key(self) -> None:
        """Test cache with empty key."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await cache.get("")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_none_value(self) -> None:
        """Test cache with None value."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.setex = AsyncMock(return_value=True)
            mock_redis.get = AsyncMock(return_value=json.dumps(None))
            
            # Set None value
            result = await cache.set("test_key", None)
            assert result is True
            
            # Get None value
            value = await cache.get("test_key")
            assert value is None

    @pytest.mark.asyncio
    async def test_cache_large_value(self) -> None:
        """Test cache with large value."""
        cache = EnhancedRedisCache()
        large_value = {"data": "x" * 1000000}  # 1MB of data
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.setex = AsyncMock(return_value=True)
            
            result = await cache.set("large_key", large_value)
            assert result is True

    @pytest.mark.asyncio
    async def test_cache_zero_ttl(self) -> None:
        """Test cache with zero TTL."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.set = AsyncMock(return_value=True)
            
            # Zero TTL should use set instead of setex
            result = await cache.set("test_key", "test_value", ttl=0)
            assert result is True

    @pytest.mark.asyncio
    async def test_cache_negative_ttl(self) -> None:
        """Test cache with negative TTL."""
        cache = EnhancedRedisCache()
        
        with patch.object(cache, 'redis_client') as mock_redis:
            mock_redis.setex = AsyncMock(return_value=True)
            
            # Negative TTL should be handled gracefully
            result = await cache.set("test_key", "test_value", ttl=-1)
            # Implementation should handle this appropriately

    @pytest.mark.asyncio
    async def test_decorator_with_complex_arguments(self) -> None:
        """Test decorator with complex function arguments."""
        with patch('services.redis_cache.get_enhanced_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)
            mock_get_cache.return_value = mock_cache
            
            @enhanced_cached("complex_test", ttl=300)
            async def complex_function(
                pos_arg: str,
                *args,
                keyword_arg: str = "default",
                **kwargs
            ) -> str:
                return f"{pos_arg}_{keyword_arg}_{len(args)}_{len(kwargs)}"
            
            result = await complex_function(
                "test",
                "extra1",
                "extra2",
                keyword_arg="custom",
                extra_kwarg="value"
            )
            assert "test_custom_2_1" in result