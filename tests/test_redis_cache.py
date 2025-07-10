import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from services.redis_cache import EnhancedRedisCache, enhanced_cache


class _InMemoryRedis:
    """A minimal async Redis-like client for testing."""

    def __init__(self):
        self.store: dict[str, str] = {}
        self.connection_error = False

    async def get(self, key):  # noqa: D401
        if self.connection_error:
            raise ConnectionError("Redis connection error")
        return self.store.get(key)

    async def setex(self, key, ttl, value):  # noqa: D401
        if self.connection_error:
            raise ConnectionError("Redis connection error")
        # Ignore ttl for simplicity
        self.store[key] = value
        return True

    async def delete(self, key):  # noqa: D401
        if self.connection_error:
            raise ConnectionError("Redis connection error")
        return 1 if self.store.pop(key, None) is not None else 0

    async def keys(self, pattern):  # noqa: D401
        if self.connection_error:
            raise ConnectionError("Redis connection error")
        # naive pattern handling: only '*' wildcard
        if pattern == "*":
            return list(self.store.keys())
        return [k for k in self.store if pattern in k]

    async def mget(self, keys):  # noqa: D401
        if self.connection_error:
            raise ConnectionError("Redis connection error")
        return [self.store.get(k) for k in keys]

    async def pipeline(self):  # noqa: D401
        if self.connection_error:
            raise ConnectionError("Redis connection error")
        class _Pipe:
            def __init__(self, outer):
                self.outer = outer
                self.cmds = []

            def setex(self, k, ttl, v):
                self.cmds.append((k, v))

            async def execute(self):
                if self.outer.connection_error:
                    raise ConnectionError("Redis connection error")
                for k, v in self.cmds:
                    self.outer.store[k] = v
        pipe = _Pipe(self)
        # context mgr support
        class _CM:  # noqa: D401
            async def __aenter__(self):
                return pipe
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        return _CM()

    async def ping(self):  # noqa: D401
        if self.connection_error:
            raise ConnectionError("Redis connection error")
        return True

    async def close(self):
        pass


@pytest.fixture()
def cache():  # noqa: D401
    c = EnhancedRedisCache()
    c.client = _InMemoryRedis()  # type: ignore
    return c


@pytest.fixture()
def cache_with_no_client():  # noqa: D401
    c = EnhancedRedisCache()
    c.client = None
    return c


@pytest.fixture()
def cache_with_connection_error():  # noqa: D401
    c = EnhancedRedisCache()
    mock_client = _InMemoryRedis()
    mock_client.connection_error = True
    c.client = mock_client  # type: ignore
    return c


class TestEnhancedRedisCache:
    """Test EnhancedRedisCache functionality."""

    @pytest.mark.asyncio
    async def test_set_and_get_roundtrip(self, cache):  # noqa: D401
        assert await cache.set("user", {"name": "Bob"}, 60, 1)
        val = await cache.get("user", 1)
        assert val == {"name": "Bob"}
        metrics = cache.get_metrics()
        assert metrics["hits"] == 1 and metrics["misses"] == 0

    @pytest.mark.asyncio
    async def test_delete_and_clear(self, cache):  # noqa: D401
        await cache.set("demo", 123, 60, "x")
        assert await cache.delete("demo", "x") is True
        assert await cache.get("demo", "x") is None
        # Warmup two keys then clear pattern
        await cache.set("p", "a", 60, 1)
        await cache.set("p", "b", 60, 2)
        cleared = await cache.clear_pattern("p:*")
        assert cleared == 2

    @pytest.mark.asyncio
    async def test_get_or_set(self, cache):  # noqa: D401
        calls = {"count": 0}

        async def producer():
            calls["count"] += 1
            return "value"

        v1 = await cache.get_or_set("key", producer, 60, "a")
        v2 = await cache.get_or_set("key", producer, 60, "a")
        assert v1 == v2 == "value"
        assert calls["count"] == 1  # only produced once

    def test_generate_key_length(self, cache):
        # create long kwargs to trigger hashing
        long_value = "x" * 300
        k = cache._generate_key("prefix", data=long_value)  # type: ignore
        assert len(k) < 250  # should be hashed and shortened

    @pytest.mark.asyncio
    async def test_set_with_no_client(self, cache_with_no_client):
        """Test set operation with no Redis client."""
        result = await cache_with_no_client.set("key", "value", 60, "suffix")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_with_no_client(self, cache_with_no_client):
        """Test get operation with no Redis client."""
        result = await cache_with_no_client.get("key", "suffix")
        assert result is None
        # Should increment miss count
        metrics = cache_with_no_client.get_metrics()
        assert metrics["misses"] == 1

    @pytest.mark.asyncio
    async def test_delete_with_no_client(self, cache_with_no_client):
        """Test delete operation with no Redis client."""
        result = await cache_with_no_client.delete("key", "suffix")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_pattern_with_no_client(self, cache_with_no_client):
        """Test clear_pattern operation with no Redis client."""
        result = await cache_with_no_client.clear_pattern("pattern*")
        assert result == 0

    @pytest.mark.asyncio
    async def test_get_or_set_with_no_client(self, cache_with_no_client):
        """Test get_or_set operation with no Redis client."""
        async def producer():
            return "value"

        result = await cache_with_no_client.get_or_set("key", producer, 60, "suffix")
        assert result == "value"  # Should call producer and return value

    @pytest.mark.asyncio
    async def test_set_with_connection_error(self, cache_with_connection_error):
        """Test set operation with Redis connection error."""
        result = await cache_with_connection_error.set("key", "value", 60, "suffix")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_with_connection_error(self, cache_with_connection_error):
        """Test get operation with Redis connection error."""
        result = await cache_with_connection_error.get("key", "suffix")
        assert result is None
        # Should increment miss count
        metrics = cache_with_connection_error.get_metrics()
        assert metrics["misses"] == 1

    @pytest.mark.asyncio
    async def test_delete_with_connection_error(self, cache_with_connection_error):
        """Test delete operation with Redis connection error."""
        result = await cache_with_connection_error.delete("key", "suffix")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_pattern_with_connection_error(self, cache_with_connection_error):
        """Test clear_pattern operation with Redis connection error."""
        result = await cache_with_connection_error.clear_pattern("pattern*")
        assert result == 0

    @pytest.mark.asyncio
    async def test_get_or_set_with_connection_error(self, cache_with_connection_error):
        """Test get_or_set operation with Redis connection error."""
        async def producer():
            return "value"

        result = await cache_with_connection_error.get_or_set("key", producer, 60, "suffix")
        assert result == "value"  # Should call producer and return value

    @pytest.mark.asyncio
    async def test_set_different_data_types(self, cache):
        """Test setting different data types."""
        test_data = [
            ("string", "hello"),
            ("int", 42),
            ("float", 3.14),
            ("bool", True),
            ("list", [1, 2, 3]),
            ("dict", {"key": "value"}),
            ("none", None),
        ]
        
        for suffix, data in test_data:
            result = await cache.set("test", data, 60, suffix)
            assert result is True
            
            retrieved = await cache.get("test", suffix)
            assert retrieved == data

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache):
        """Test get operation with cache miss."""
        result = await cache.get("nonexistent", "key")
        assert result is None
        
        metrics = cache.get_metrics()
        assert metrics["misses"] == 1
        assert metrics["hits"] == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, cache):
        """Test deleting nonexistent key."""
        result = await cache.delete("nonexistent", "key")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_pattern_no_matches(self, cache):
        """Test clear_pattern with no matching keys."""
        result = await cache.clear_pattern("nonexistent:*")
        assert result == 0

    @pytest.mark.asyncio
    async def test_generate_key_basic(self, cache):
        """Test basic key generation."""
        key = cache._generate_key("prefix", "suffix")
        assert key == "prefix:suffix"

    @pytest.mark.asyncio
    async def test_generate_key_with_kwargs(self, cache):
        """Test key generation with kwargs."""
        key = cache._generate_key("prefix", "suffix", param1="value1", param2="value2")
        assert "prefix:suffix" in key
        assert "param1:value1" in key
        assert "param2:value2" in key

    @pytest.mark.asyncio
    async def test_generate_key_with_complex_kwargs(self, cache):
        """Test key generation with complex kwargs."""
        key = cache._generate_key("prefix", "suffix", 
                                 dict_param={"nested": "value"},
                                 list_param=[1, 2, 3])
        assert "prefix:suffix" in key
        # Complex objects should be hashed
        assert len(key) < 300  # Should be reasonable length

    @pytest.mark.asyncio
    async def test_generate_key_long_value_hashing(self, cache):
        """Test that long values are hashed to keep key length reasonable."""
        long_value = "x" * 500
        key = cache._generate_key("prefix", "suffix", long_param=long_value)
        assert len(key) < 250  # Should be hashed and shortened

    @pytest.mark.asyncio
    async def test_serialize_deserialize_data(self, cache):
        """Test data serialization and deserialization."""
        test_data = {"complex": {"nested": {"data": [1, 2, 3]}}}
        
        # Test _serialize_data
        serialized = cache._serialize_data(test_data)
        assert isinstance(serialized, str)
        
        # Test _deserialize_data
        deserialized = cache._deserialize_data(serialized)
        assert deserialized == test_data

    @pytest.mark.asyncio
    async def test_deserialize_invalid_json(self, cache):
        """Test deserializing invalid JSON."""
        invalid_json = "invalid json string"
        result = cache._deserialize_data(invalid_json)
        assert result == invalid_json  # Should return original string

    @pytest.mark.asyncio
    async def test_get_metrics(self, cache):
        """Test getting cache metrics."""
        # Initial metrics
        metrics = cache.get_metrics()
        assert "hits" in metrics
        assert "misses" in metrics
        assert "sets" in metrics
        assert "deletes" in metrics
        assert "errors" in metrics
        
        # Perform operations and check metrics
        await cache.set("test", "value", 60, "key")
        await cache.get("test", "key")  # Hit
        await cache.get("nonexistent", "key")  # Miss
        await cache.delete("test", "key")
        
        metrics = cache.get_metrics()
        assert metrics["hits"] == 1
        assert metrics["misses"] == 1
        assert metrics["sets"] == 1
        assert metrics["deletes"] == 1

    @pytest.mark.asyncio
    async def test_reset_metrics(self, cache):
        """Test resetting cache metrics."""
        # Perform some operations
        await cache.set("test", "value", 60, "key")
        await cache.get("test", "key")
        
        # Check metrics are not zero
        metrics = cache.get_metrics()
        assert metrics["hits"] > 0
        assert metrics["sets"] > 0
        
        # Reset metrics
        cache.reset_metrics()
        
        # Check metrics are reset
        metrics = cache.get_metrics()
        assert metrics["hits"] == 0
        assert metrics["misses"] == 0
        assert metrics["sets"] == 0
        assert metrics["deletes"] == 0
        assert metrics["errors"] == 0

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, cache):
        """Test get_or_set with cache hit."""
        # First set a value
        await cache.set("test", "cached_value", 60, "key")
        
        producer_called = False
        async def producer():
            nonlocal producer_called
            producer_called = True
            return "new_value"
        
        result = await cache.get_or_set("test", producer, 60, "key")
        assert result == "cached_value"
        assert not producer_called  # Producer should not be called

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self, cache):
        """Test get_or_set with cache miss."""
        producer_called = False
        async def producer():
            nonlocal producer_called
            producer_called = True
            return "new_value"
        
        result = await cache.get_or_set("test", producer, 60, "key")
        assert result == "new_value"
        assert producer_called  # Producer should be called
        
        # Verify value was cached
        cached_value = await cache.get("test", "key")
        assert cached_value == "new_value"

    @pytest.mark.asyncio
    async def test_get_or_set_producer_exception(self, cache):
        """Test get_or_set when producer raises exception."""
        async def failing_producer():
            raise ValueError("Producer failed")
        
        with pytest.raises(ValueError, match="Producer failed"):
            await cache.get_or_set("test", failing_producer, 60, "key")

    @pytest.mark.asyncio
    async def test_bulk_operations(self, cache):
        """Test bulk operations for performance."""
        # Set multiple keys
        keys_values = [
            ("bulk", "value1", "key1"),
            ("bulk", "value2", "key2"),
            ("bulk", "value3", "key3"),
        ]
        
        for prefix, value, suffix in keys_values:
            await cache.set(prefix, value, 60, suffix)
        
        # Get multiple keys
        for prefix, expected_value, suffix in keys_values:
            result = await cache.get(prefix, suffix)
            assert result == expected_value

    @pytest.mark.asyncio
    async def test_cache_expiration_handling(self, cache):
        """Test that cache handles expiration correctly."""
        # Note: Our mock doesn't actually expire keys, but we test the interface
        await cache.set("expiring", "value", 1, "key")  # 1 second TTL
        
        # Should still be available immediately
        result = await cache.get("expiring", "key")
        assert result == "value"

    @pytest.mark.asyncio
    async def test_clear_pattern_with_wildcards(self, cache):
        """Test clear_pattern with different wildcard patterns."""
        # Set up test data
        await cache.set("user", "data1", 60, "123")
        await cache.set("user", "data2", 60, "456")
        await cache.set("session", "data3", 60, "789")
        
        # Clear user:* pattern
        cleared = await cache.clear_pattern("user:*")
        assert cleared == 2
        
        # Verify user keys are gone but session key remains
        assert await cache.get("user", "123") is None
        assert await cache.get("user", "456") is None
        assert await cache.get("session", "789") == "data3"

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, cache):
        """Test concurrent cache operations."""
        async def set_operation(i):
            return await cache.set("concurrent", f"value_{i}", 60, str(i))
        
        async def get_operation(i):
            return await cache.get("concurrent", str(i))
        
        # Run concurrent set operations
        set_tasks = [set_operation(i) for i in range(10)]
        set_results = await asyncio.gather(*set_tasks)
        assert all(set_results)
        
        # Run concurrent get operations
        get_tasks = [get_operation(i) for i in range(10)]
        get_results = await asyncio.gather(*get_tasks)
        
        for i, result in enumerate(get_results):
            assert result == f"value_{i}"

    @pytest.mark.asyncio
    async def test_error_handling_in_set(self, cache):
        """Test error handling in set operation."""
        # Mock client to raise exception
        original_client = cache.client
        cache.client = MagicMock()
        cache.client.setex = AsyncMock(side_effect=Exception("Redis error"))
        
        result = await cache.set("error", "value", 60, "test")
        assert result is False
        
        # Check error was counted
        metrics = cache.get_metrics()
        assert metrics["errors"] > 0
        
        # Restore original client
        cache.client = original_client

    @pytest.mark.asyncio
    async def test_error_handling_in_get(self, cache):
        """Test error handling in get operation."""
        # Mock client to raise exception
        original_client = cache.client
        cache.client = MagicMock()
        cache.client.get = AsyncMock(side_effect=Exception("Redis error"))
        
        result = await cache.get("error", "test")
        assert result is None
        
        # Check error was counted
        metrics = cache.get_metrics()
        assert metrics["errors"] > 0
        
        # Restore original client
        cache.client = original_client

    @pytest.mark.asyncio
    async def test_error_handling_in_delete(self, cache):
        """Test error handling in delete operation."""
        # Mock client to raise exception
        original_client = cache.client
        cache.client = MagicMock()
        cache.client.delete = AsyncMock(side_effect=Exception("Redis error"))
        
        result = await cache.delete("error", "test")
        assert result is False
        
        # Check error was counted
        metrics = cache.get_metrics()
        assert metrics["errors"] > 0
        
        # Restore original client
        cache.client = original_client

    @pytest.mark.asyncio
    async def test_error_handling_in_clear_pattern(self, cache):
        """Test error handling in clear_pattern operation."""
        # Mock client to raise exception
        original_client = cache.client
        cache.client = MagicMock()
        cache.client.keys = AsyncMock(side_effect=Exception("Redis error"))
        
        result = await cache.clear_pattern("error:*")
        assert result == 0
        
        # Check error was counted
        metrics = cache.get_metrics()
        assert metrics["errors"] > 0
        
        # Restore original client
        cache.client = original_client

    def test_global_enhanced_cache_instance(self):
        """Test that global enhanced_cache instance exists."""
        assert enhanced_cache is not None
        assert isinstance(enhanced_cache, EnhancedRedisCache)

    @pytest.mark.asyncio
    async def test_cache_key_collision_handling(self, cache):
        """Test handling of potential key collisions."""
        # Create keys that might collide
        key1 = cache._generate_key("prefix", "suffix", param="value1")
        key2 = cache._generate_key("prefix", "suffix", param="value2")
        
        # Keys should be different
        assert key1 != key2
        
        # Set different values
        await cache.set("prefix", "data1", 60, "suffix", param="value1")
        await cache.set("prefix", "data2", 60, "suffix", param="value2")
        
        # Should get correct values
        result1 = await cache.get("prefix", "suffix", param="value1")
        result2 = await cache.get("prefix", "suffix", param="value2")
        
        assert result1 == "data1"
        assert result2 == "data2"

    @pytest.mark.asyncio
    async def test_cache_with_special_characters(self, cache):
        """Test cache operations with special characters."""
        special_data = {
            "unicode": "Hello 世界",
            "symbols": "!@#$%^&*()",
            "quotes": 'Test "quotes" and \'apostrophes\'',
            "newlines": "Line 1\nLine 2\nLine 3"
        }
        
        await cache.set("special", special_data, 60, "chars")
        result = await cache.get("special", "chars")
        
        assert result == special_data

    @pytest.mark.asyncio
    async def test_cache_large_data(self, cache):
        """Test cache operations with large data."""
        large_data = {"data": "x" * 10000}  # 10KB of data
        
        result = await cache.set("large", large_data, 60, "data")
        assert result is True
        
        retrieved = await cache.get("large", "data")
        assert retrieved == large_data

    @pytest.mark.asyncio
    async def test_cache_empty_values(self, cache):
        """Test cache operations with empty values."""
        empty_values = [
            ("empty_string", ""),
            ("empty_list", []),
            ("empty_dict", {}),
            ("zero", 0),
            ("false", False),
        ]
        
        for suffix, value in empty_values:
            await cache.set("empty", value, 60, suffix)
            result = await cache.get("empty", suffix)
            assert result == value

    @pytest.mark.asyncio
    async def test_pipeline_operations(self, cache):
        """Test pipeline operations if available."""
        # Our mock supports pipeline operations
        assert hasattr(cache.client, 'pipeline')
        
        # Test that pipeline can be used
        async with await cache.client.pipeline() as pipe:
            pipe.setex("pipe:key1", 60, "value1")
            pipe.setex("pipe:key2", 60, "value2")
            await pipe.execute()
        
        # Note: Our mock doesn't actually use pipeline for bulk operations
        # but we test the interface exists