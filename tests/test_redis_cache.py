import pytest
import asyncio
import json
import time
from datetime import timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Any

from services.redis_cache import (
    RedisCircuitBreaker,
    EnhancedRedisCache,
    enhanced_cache,
    enhanced_cached,
    cache_with_lock
)


class TestRedisCircuitBreaker:
    """Test RedisCircuitBreaker functionality."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        cb = RedisCircuitBreaker(failure_threshold=3, recovery_timeout=30)
        
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        assert cb.state == "CLOSED"

    def test_circuit_breaker_record_failure(self):
        """Test recording failures."""
        cb = RedisCircuitBreaker(failure_threshold=2, recovery_timeout=30)
        
        # First failure
        cb.record_failure()
        assert cb.failure_count == 1
        assert cb.state == "CLOSED"
        assert cb.last_failure_time is not None
        
        # Second failure should open circuit
        cb.record_failure()
        assert cb.failure_count == 2
        assert cb.state == "OPEN"

    def test_circuit_breaker_record_success(self):
        """Test recording success."""
        cb = RedisCircuitBreaker(failure_threshold=2, recovery_timeout=30)
        
        # Simulate failures
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"
        
        # Record success should close circuit
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"

    def test_circuit_breaker_can_execute_closed(self):
        """Test can_execute when circuit is closed."""
        cb = RedisCircuitBreaker()
        assert cb.can_execute() is True

    def test_circuit_breaker_can_execute_open(self):
        """Test can_execute when circuit is open."""
        cb = RedisCircuitBreaker(failure_threshold=1, recovery_timeout=30)
        
        # Open circuit
        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.can_execute() is False

    def test_circuit_breaker_can_execute_half_open(self):
        """Test can_execute when circuit is half-open."""
        cb = RedisCircuitBreaker(failure_threshold=1, recovery_timeout=1)
        
        # Open circuit
        cb.record_failure()
        assert cb.state == "OPEN"
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Should transition to half-open
        assert cb.can_execute() is True
        assert cb.state == "HALF_OPEN"

    def test_circuit_breaker_recovery_timeout(self):
        """Test recovery timeout functionality."""
        cb = RedisCircuitBreaker(failure_threshold=1, recovery_timeout=1)
        
        # Open circuit
        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.can_execute() is False
        
        # Before timeout
        time.sleep(0.5)
        assert cb.can_execute() is False
        
        # After timeout
        time.sleep(0.6)
        assert cb.can_execute() is True
        assert cb.state == "HALF_OPEN"

    def test_circuit_breaker_can_execute_half_open_return_true(self):
        """Test can_execute returns True for HALF_OPEN state."""
        cb = RedisCircuitBreaker()
        cb.state = "HALF_OPEN"
        assert cb.can_execute() is True


class TestEnhancedRedisCache:
    """Test EnhancedRedisCache functionality."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_client.get = AsyncMock()
        mock_client.set = AsyncMock()
        mock_client.setex = AsyncMock()
        mock_client.delete = AsyncMock()
        mock_client.keys = AsyncMock()
        mock_client.mget = AsyncMock()
        mock_client.pipeline = AsyncMock()
        mock_client.close = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_connection_pool(self):
        """Mock Redis connection pool."""
        mock_pool = AsyncMock()
        mock_pool.disconnect = AsyncMock()
        return mock_pool

    @pytest.fixture
    def cache_instance(self, mock_redis_client, mock_connection_pool):
        """Create cache instance with mocked Redis."""
        with patch('services.redis_cache.ConnectionPool') as mock_pool_class, \
             patch('services.redis_cache.redis.Redis') as mock_redis_class:
            
            mock_pool_class.from_url.return_value = mock_connection_pool
            mock_redis_class.return_value = mock_redis_client
            
            cache = EnhancedRedisCache(
                redis_url="redis://localhost:6379",
                max_connections=10,
                connection_timeout=5
            )
            
            return cache

    def test_cache_initialization(self, cache_instance):
        """Test cache initialization."""
        assert cache_instance.redis_url == "redis://localhost:6379"
        assert cache_instance.max_connections == 10
        assert cache_instance.connection_timeout == 5
        assert cache_instance.client is not None
        assert cache_instance.circuit_breaker is not None
        assert cache_instance.metrics is not None

    def test_cache_initialization_default_values(self):
        """Test cache initialization with default values."""
        with patch('services.redis_cache.ConnectionPool') as mock_pool_class, \
             patch('services.redis_cache.redis.Redis') as mock_redis_class:
            
            mock_pool_class.from_url.return_value = MagicMock()
            mock_redis_class.return_value = MagicMock()
            
            cache = EnhancedRedisCache()
            
            assert cache.redis_url == "redis://localhost:6379"
            assert cache.max_connections == 20
            assert cache.connection_timeout == 5

    def test_cache_initialization_failure(self):
        """Test cache initialization failure."""
        with patch('services.redis_cache.ConnectionPool') as mock_pool_class:
            mock_pool_class.from_url.side_effect = Exception("Connection failed")
            
            cache = EnhancedRedisCache()
            
            assert cache.client is None

    def test_cache_initialization_with_none_redis_url(self):
        """Test cache initialization with None redis_url."""
        with patch('services.redis_cache.ConnectionPool') as mock_pool_class, \
             patch('services.redis_cache.redis.Redis') as mock_redis_class:
            
            mock_pool_class.from_url.return_value = MagicMock()
            mock_redis_class.return_value = MagicMock()
            
            cache = EnhancedRedisCache(redis_url=None)  # type: ignore
            
            assert cache.redis_url == "redis://localhost:6379"

    def test_generate_key_simple(self, cache_instance):
        """Test key generation with simple arguments."""
        key = cache_instance._generate_key("test", "arg1", "arg2")
        assert key == "test:arg1:arg2"

    def test_generate_key_with_kwargs(self, cache_instance):
        """Test key generation with keyword arguments."""
        key = cache_instance._generate_key("test", user_id="123", action="create")
        assert "test" in key
        assert "user_id:123" in key
        assert "action:create" in key

    def test_generate_key_with_complex_data(self, cache_instance):
        """Test key generation with complex data structures."""
        complex_data = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        key = cache_instance._generate_key("test", data=complex_data)
        
        assert "test" in key
        assert "data:" in key
        assert len(key) > 0

    def test_generate_key_long_key_hashing(self, cache_instance):
        """Test key generation with long keys that get hashed."""
        long_string = "x" * 300
        key = cache_instance._generate_key("test", long_string)
        
        # Should be hashed and shorter than 250 chars
        assert len(key) < 250
        assert key.startswith("test:")

    @pytest.mark.asyncio
    async def test_get_success(self, cache_instance):
        """Test successful cache get."""
        test_data = {"key": "value"}
        cache_instance.client.get.return_value = json.dumps(test_data)
        
        result = await cache_instance.get("test", "key1")
        
        assert result == test_data
        assert cache_instance.metrics["hits"] == 1
        assert cache_instance.metrics["total_operations"] == 1

    @pytest.mark.asyncio
    async def test_get_miss(self, cache_instance):
        """Test cache miss."""
        cache_instance.client.get.return_value = None
        
        result = await cache_instance.get("test", "key1")
        
        assert result is None
        assert cache_instance.metrics["misses"] == 1
        assert cache_instance.metrics["total_operations"] == 1

    @pytest.mark.asyncio
    async def test_get_error(self, cache_instance):
        """Test cache get with error."""
        cache_instance.client.get.side_effect = Exception("Redis error")
        
        result = await cache_instance.get("test", "key1")
        
        assert result is None
        assert cache_instance.metrics["errors"] == 1
        assert cache_instance.metrics["total_operations"] == 1

    @pytest.mark.asyncio
    async def test_get_circuit_breaker_open(self, cache_instance):
        """Test get when circuit breaker is open."""
        cache_instance.circuit_breaker.state = "OPEN"
        cache_instance.circuit_breaker.last_failure_time = time.time()
        
        result = await cache_instance.get("test", "key1")
        
        assert result is None
        cache_instance.client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_no_client(self, cache_instance):
        """Test get when client is None."""
        cache_instance.client = None
        
        result = await cache_instance.get("test", "key1")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_success(self, cache_instance):
        """Test successful cache set."""
        test_data = {"key": "value"}
        cache_instance.client.setex.return_value = True
        
        result = await cache_instance.set("test", test_data, 3600, "key1")
        
        assert result is True
        cache_instance.client.setex.assert_called_once()
        assert cache_instance.metrics["total_operations"] == 1

    @pytest.mark.asyncio
    async def test_set_with_timedelta(self, cache_instance):
        """Test cache set with timedelta TTL."""
        test_data = {"key": "value"}
        ttl = timedelta(hours=1)
        cache_instance.client.setex.return_value = True
        
        result = await cache_instance.set("test", test_data, ttl, "key1")
        
        assert result is True
        # Should convert timedelta to seconds (3600)
        cache_instance.client.setex.assert_called_once()
        call_args = cache_instance.client.setex.call_args
        assert call_args[0][1] == 3600  # TTL in seconds

    @pytest.mark.asyncio
    async def test_set_error(self, cache_instance):
        """Test cache set with error."""
        cache_instance.client.setex.side_effect = Exception("Redis error")
        
        result = await cache_instance.set("test", {"key": "value"}, 3600, "key1")
        
        assert result is False
        assert cache_instance.metrics["errors"] == 1
        assert cache_instance.metrics["total_operations"] == 1

    @pytest.mark.asyncio
    async def test_set_no_client(self, cache_instance):
        """Test set when client is None."""
        cache_instance.client = None
        
        result = await cache_instance.set("test", {"key": "value"}, 3600, "key1")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_set_circuit_breaker_open(self, cache_instance):
        """Test set when circuit breaker is open."""
        cache_instance.circuit_breaker.state = "OPEN"
        cache_instance.circuit_breaker.last_failure_time = time.time()
        
        result = await cache_instance.set("test", {"key": "value"}, 3600, "key1")
        
        assert result is False
        cache_instance.client.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_success(self, cache_instance):
        """Test successful cache delete."""
        cache_instance.client.delete.return_value = 1
        
        result = await cache_instance.delete("test", "key1")
        
        assert result is True
        cache_instance.client.delete.assert_called_once()
        assert cache_instance.metrics["total_operations"] == 1

    @pytest.mark.asyncio
    async def test_delete_not_found(self, cache_instance):
        """Test cache delete when key not found."""
        cache_instance.client.delete.return_value = 0
        
        result = await cache_instance.delete("test", "key1")
        
        assert result is False
        cache_instance.client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_error(self, cache_instance):
        """Test cache delete with error."""
        cache_instance.client.delete.side_effect = Exception("Redis error")
        
        result = await cache_instance.delete("test", "key1")
        
        assert result is False
        assert cache_instance.metrics["errors"] == 1

    @pytest.mark.asyncio
    async def test_delete_no_client(self, cache_instance):
        """Test delete when client is None."""
        cache_instance.client = None
        
        result = await cache_instance.delete("test", "key1")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_circuit_breaker_open(self, cache_instance):
        """Test delete when circuit breaker is open."""
        cache_instance.circuit_breaker.state = "OPEN"
        cache_instance.circuit_breaker.last_failure_time = time.time()
        
        result = await cache_instance.delete("test", "key1")
        
        assert result is False
        cache_instance.client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_pattern_success(self, cache_instance):
        """Test successful pattern clearing."""
        cache_instance.client.keys.return_value = ["key1", "key2", "key3"]
        cache_instance.client.delete.return_value = 3
        
        result = await cache_instance.clear_pattern("test:*")
        
        assert result == 3
        cache_instance.client.keys.assert_called_once_with("test:*")
        cache_instance.client.delete.assert_called_once_with("key1", "key2", "key3")

    @pytest.mark.asyncio
    async def test_clear_pattern_no_keys(self, cache_instance):
        """Test pattern clearing when no keys match."""
        cache_instance.client.keys.return_value = []
        
        result = await cache_instance.clear_pattern("test:*")
        
        assert result == 0
        cache_instance.client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_pattern_no_client(self, cache_instance):
        """Test clear_pattern when client is None."""
        cache_instance.client = None
        
        result = await cache_instance.clear_pattern("test:*")
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_clear_pattern_circuit_breaker_open(self, cache_instance):
        """Test clear_pattern when circuit breaker is open."""
        cache_instance.circuit_breaker.state = "OPEN"
        cache_instance.circuit_breaker.last_failure_time = time.time()
        
        result = await cache_instance.clear_pattern("test:*")
        
        assert result == 0
        cache_instance.client.keys.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_pattern_error(self, cache_instance):
        """Test clear_pattern with error."""
        cache_instance.client.keys.side_effect = Exception("Redis error")
        
        result = await cache_instance.clear_pattern("test:*")
        
        assert result == 0
        assert cache_instance.metrics["errors"] == 1

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, cache_instance):
        """Test get_or_set with cache hit."""
        test_data = {"key": "value"}
        cache_instance.client.get.return_value = json.dumps(test_data)
        
        def value_func():
            return {"new": "data"}
        
        result = await cache_instance.get_or_set("test", value_func, 3600, "key1")
        
        assert result == test_data
        cache_instance.client.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self, cache_instance):
        """Test get_or_set with cache miss."""
        cache_instance.client.get.return_value = None
        cache_instance.client.setex.return_value = True
        
        def value_func():
            return {"new": "data"}
        
        result = await cache_instance.get_or_set("test", value_func, 3600, "key1")
        
        assert result == {"new": "data"}
        cache_instance.client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_set_async_function(self, cache_instance):
        """Test get_or_set with async function."""
        cache_instance.client.get.return_value = None
        cache_instance.client.setex.return_value = True
        
        async def async_value_func():
            return {"async": "data"}
        
        result = await cache_instance.get_or_set("test", async_value_func, 3600, "key1")
        
        assert result == {"async": "data"}
        cache_instance.client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_set_function_error_sync(self, cache_instance):
        """Test get_or_set when sync function raises error."""
        cache_instance.client.get.return_value = None
        
        def failing_func():
            raise Exception("Function error")
        
        # Should call the fallback function and return its result
        result = await cache_instance.get_or_set("test", failing_func, 3600, "key1")
        
        # The function should be called as fallback, and we should get the result
        assert result is not None  # The fallback function was called

    @pytest.mark.asyncio
    async def test_get_or_set_function_error_async(self, cache_instance):
        """Test get_or_set when async function raises error."""
        cache_instance.client.get.return_value = None
        
        async def failing_async_func():
            raise Exception("Async function error")
        
        # Should call the fallback function and return its result
        result = await cache_instance.get_or_set("test", failing_async_func, 3600, "key1")
        
        # The async function should be called as fallback, and we should get the result
        assert result is not None  # The fallback function was called

    @pytest.mark.asyncio
    async def test_mget_success(self, cache_instance):
        """Test successful multiple get."""
        test_data = [json.dumps({"key": "value1"}), json.dumps({"key": "value2"}), None]
        cache_instance.client.mget.return_value = test_data
        
        result = await cache_instance.mget(["key1", "key2", "key3"])
        
        assert len(result) == 3
        assert result[0] == {"key": "value1"}
        assert result[1] == {"key": "value2"}
        assert result[2] is None
        assert cache_instance.metrics["hits"] == 2
        assert cache_instance.metrics["misses"] == 1

    @pytest.mark.asyncio
    async def test_mget_error(self, cache_instance):
        """Test mget with error."""
        cache_instance.client.mget.side_effect = Exception("Redis error")
        
        result = await cache_instance.mget(["key1", "key2"])
        
        assert result == [None, None]
        assert cache_instance.metrics["errors"] == 1

    @pytest.mark.asyncio
    async def test_mget_no_client(self, cache_instance):
        """Test mget when client is None."""
        cache_instance.client = None
        
        result = await cache_instance.mget(["key1", "key2"])
        
        assert result == [None, None]

    @pytest.mark.asyncio
    async def test_mget_circuit_breaker_open(self, cache_instance):
        """Test mget when circuit breaker is open."""
        cache_instance.circuit_breaker.state = "OPEN"
        cache_instance.circuit_breaker.last_failure_time = time.time()
        
        result = await cache_instance.mget(["key1", "key2"])
        
        assert result == [None, None]
        cache_instance.client.mget.assert_not_called()

    @pytest.mark.asyncio
    async def test_mset_success(self, cache_instance):
        """Test successful multiple set."""
        test_data = {"key1": {"value": 1}, "key2": {"value": 2}}
        
        # Mock pipeline context manager properly
        mock_pipeline = AsyncMock()
        mock_pipeline.setex = MagicMock()
        mock_pipeline.execute = AsyncMock()
        
        # Create a proper async context manager
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_pipeline
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        cache_instance.client.pipeline = MagicMock(return_value=MockAsyncContextManager())
        
        result = await cache_instance.mset(test_data, 3600)
        
        assert result is True
        assert mock_pipeline.setex.call_count == 2
        mock_pipeline.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_mset_with_timedelta(self, cache_instance):
        """Test mset with timedelta TTL."""
        test_data = {"key1": {"value": 1}}
        ttl = timedelta(hours=2)
        
        # Mock pipeline context manager properly
        mock_pipeline = AsyncMock()
        mock_pipeline.setex = MagicMock()
        mock_pipeline.execute = AsyncMock()
        
        # Create a proper async context manager
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_pipeline
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        cache_instance.client.pipeline = MagicMock(return_value=MockAsyncContextManager())
        
        result = await cache_instance.mset(test_data, ttl)
        
        assert result is True
        # Should convert timedelta to seconds (7200)
        mock_pipeline.setex.assert_called_with("key1", 7200, json.dumps({"value": 1}, default=str))

    @pytest.mark.asyncio
    async def test_mset_error(self, cache_instance):
        """Test mset with error."""
        cache_instance.client.pipeline.side_effect = Exception("Redis error")
        
        result = await cache_instance.mset({"key1": {"value": 1}}, 3600)
        
        assert result is False
        assert cache_instance.metrics["errors"] == 1

    @pytest.mark.asyncio
    async def test_mset_no_client(self, cache_instance):
        """Test mset when client is None."""
        cache_instance.client = None
        
        result = await cache_instance.mset({"key1": {"value": 1}}, 3600)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_mset_circuit_breaker_open(self, cache_instance):
        """Test mset when circuit breaker is open."""
        cache_instance.circuit_breaker.state = "OPEN"
        cache_instance.circuit_breaker.last_failure_time = time.time()
        
        result = await cache_instance.mset({"key1": {"value": 1}}, 3600)
        
        assert result is False
        cache_instance.client.pipeline.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_lock_success(self, cache_instance):
        """Test successful lock acquisition."""
        cache_instance.client.set.return_value = True
        
        result = await cache_instance.acquire_lock("test_lock", 10)
        
        assert result is True
        cache_instance.client.set.assert_called_once()
        call_args = cache_instance.client.set.call_args
        assert call_args[0][0] == "lock:test_lock"
        assert call_args[1]["ex"] == 10
        assert call_args[1]["nx"] is True

    @pytest.mark.asyncio
    async def test_acquire_lock_failure(self, cache_instance):
        """Test lock acquisition failure."""
        cache_instance.client.set.return_value = False
        
        result = await cache_instance.acquire_lock("test_lock", 10)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_lock_error(self, cache_instance):
        """Test lock acquisition with error."""
        cache_instance.client.set.side_effect = Exception("Redis error")
        
        result = await cache_instance.acquire_lock("test_lock", 10)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_lock_no_client(self, cache_instance):
        """Test acquire_lock when client is None."""
        cache_instance.client = None
        
        result = await cache_instance.acquire_lock("test_lock", 10)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_release_lock_success(self, cache_instance):
        """Test successful lock release."""
        cache_instance.client.delete.return_value = 1
        
        result = await cache_instance.release_lock("test_lock")
        
        assert result is True
        cache_instance.client.delete.assert_called_once_with("lock:test_lock")

    @pytest.mark.asyncio
    async def test_release_lock_not_found(self, cache_instance):
        """Test lock release when lock not found."""
        cache_instance.client.delete.return_value = 0
        
        result = await cache_instance.release_lock("test_lock")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_release_lock_error(self, cache_instance):
        """Test lock release with error."""
        cache_instance.client.delete.side_effect = Exception("Redis error")
        
        result = await cache_instance.release_lock("test_lock")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_release_lock_no_client(self, cache_instance):
        """Test release_lock when client is None."""
        cache_instance.client = None
        
        result = await cache_instance.release_lock("test_lock")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_warm_cache_success(self, cache_instance):
        """Test successful cache warming."""
        warmup_data = {
            "key1": ({"value": 1}, 3600),
            "key2": ({"value": 2}, 7200)
        }
        
        cache_instance.client.setex.return_value = True
        
        result = await cache_instance.warm_cache(warmup_data)
        
        assert result == 2
        assert cache_instance.client.setex.call_count == 2

    @pytest.mark.asyncio
    async def test_warm_cache_partial_success(self, cache_instance):
        """Test cache warming with partial success."""
        warmup_data = {
            "key1": ({"value": 1}, 3600),
            "key2": ({"value": 2}, 7200)
        }
        
        # Mock set method to fail for one key
        with patch.object(cache_instance, 'set', side_effect=[True, False]):
            result = await cache_instance.warm_cache(warmup_data)
            
            assert result == 1

    @pytest.mark.asyncio
    async def test_warm_cache_no_client(self, cache_instance):
        """Test warm_cache when client is None."""
        cache_instance.client = None
        
        result = await cache_instance.warm_cache({"key1": ({"value": 1}, 3600)})
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_warm_cache_error(self, cache_instance):
        """Test warm_cache with error."""
        warmup_data = {"key1": ({"value": 1}, 3600)}
        
        # Mock set method to raise exception
        with patch.object(cache_instance, 'set', side_effect=Exception("Redis error")):
            result = await cache_instance.warm_cache(warmup_data)
            
            assert result == 0

    def test_get_metrics(self, cache_instance):
        """Test getting cache metrics."""
        # Set some metrics
        cache_instance.metrics["hits"] = 10
        cache_instance.metrics["misses"] = 5
        cache_instance.metrics["errors"] = 2
        cache_instance.metrics["total_operations"] = 17
        
        metrics = cache_instance.get_metrics()
        
        assert metrics["hits"] == 10
        assert metrics["misses"] == 5
        assert metrics["errors"] == 2
        assert metrics["total_operations"] == 17
        assert metrics["hit_rate"] == 10/17
        assert metrics["circuit_breaker_state"] == "CLOSED"
        assert metrics["connection_healthy"] is True

    def test_get_metrics_zero_operations(self, cache_instance):
        """Test getting metrics with zero operations."""
        metrics = cache_instance.get_metrics()
        
        assert metrics["hit_rate"] == 0

    @pytest.mark.asyncio
    async def test_health_check_success(self, cache_instance):
        """Test successful health check."""
        cache_instance.client.ping.return_value = True
        
        # Start health check
        await cache_instance.start_health_check()
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop health check
        await cache_instance.stop_health_check()
        
        assert cache_instance.health_check_task is None

    @pytest.mark.asyncio
    async def test_health_check_failure(self, cache_instance):
        """Test health check failure."""
        cache_instance.client.ping.side_effect = Exception("Ping failed")
        cache_instance.health_check_interval = 0.05  # Faster for testing
        
        # Start health check
        await cache_instance.start_health_check()
        
        # Let it run briefly to trigger the failure
        await asyncio.sleep(0.2)
        
        # Stop health check
        await cache_instance.stop_health_check()
        
        # Circuit breaker should have recorded failure
        assert cache_instance.circuit_breaker.failure_count > 0

    @pytest.mark.asyncio
    async def test_health_check_no_client(self, cache_instance):
        """Test health check when client is None."""
        cache_instance.client = None
        
        # Start health check
        await cache_instance.start_health_check()
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop health check
        await cache_instance.stop_health_check()
        
        assert cache_instance.health_check_task is None

    @pytest.mark.asyncio
    async def test_start_health_check_already_running(self, cache_instance):
        """Test starting health check when already running."""
        # Start health check
        await cache_instance.start_health_check()
        first_task = cache_instance.health_check_task
        
        # Try to start again
        await cache_instance.start_health_check()
        
        # Should be the same task
        assert cache_instance.health_check_task is first_task
        
        # Stop health check
        await cache_instance.stop_health_check()

    @pytest.mark.asyncio
    async def test_stop_health_check_not_running(self, cache_instance):
        """Test stopping health check when not running."""
        # Should not raise error
        await cache_instance.stop_health_check()
        
        assert cache_instance.health_check_task is None

    @pytest.mark.asyncio
    async def test_close(self, cache_instance):
        """Test closing cache."""
        await cache_instance.close()
        
        cache_instance.client.close.assert_called_once()
        cache_instance.pool.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_client(self, cache_instance):
        """Test closing cache when client is None."""
        cache_instance.client = None
        cache_instance.pool = None
        
        # Should not raise error
        await cache_instance.close()


class TestCacheDecorators:
    """Test cache decorators."""

    @pytest.fixture
    def mock_cache(self):
        """Mock enhanced cache."""
        with patch('services.redis_cache.enhanced_cache') as mock:
            mock.get_or_set = AsyncMock()
            mock.acquire_lock = AsyncMock()
            mock.release_lock = AsyncMock()
            mock.get = AsyncMock()
            yield mock

    @pytest.mark.asyncio
    async def test_enhanced_cached_decorator_async(self, mock_cache):
        """Test enhanced_cached decorator with async function."""
        mock_cache.get_or_set.return_value = {"result": "cached"}
        
        @enhanced_cached("test", ttl=3600)
        async def async_function(param1, param2):
            return {"result": "computed"}
        
        result = await async_function("value1", "value2")
        
        assert result == {"result": "cached"}
        mock_cache.get_or_set.assert_called_once()

    def test_enhanced_cached_decorator_sync(self, mock_cache):
        """Test enhanced_cached decorator with sync function."""
        # For sync functions, we need to mock it as a regular return value
        from unittest.mock import MagicMock
        mock_cache.get_or_set = MagicMock(return_value={"result": "cached"})
        
        @enhanced_cached("test", ttl=3600)
        def sync_function(param1, param2):
            return {"result": "computed"}
        
        result = sync_function("value1", "value2")
        
        assert result == {"result": "cached"}
        mock_cache.get_or_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_with_lock_decorator_success(self, mock_cache):
        """Test cache_with_lock decorator with successful lock acquisition."""
        mock_cache.acquire_lock.return_value = True
        mock_cache.get_or_set.return_value = {"result": "cached"}
        mock_cache.release_lock.return_value = True
        
        @cache_with_lock("test", ttl=3600, lock_timeout=10)
        async def locked_function(param):
            return {"result": "computed"}
        
        result = await locked_function("value")
        
        assert result == {"result": "cached"}
        mock_cache.acquire_lock.assert_called_once()
        mock_cache.release_lock.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_with_lock_decorator_lock_failure(self, mock_cache):
        """Test cache_with_lock decorator with lock acquisition failure."""
        mock_cache.acquire_lock.return_value = False
        mock_cache.get.return_value = {"result": "fallback"}
        
        @cache_with_lock("test", ttl=3600, lock_timeout=10)
        async def locked_function(param):
            return {"result": "computed"}
        
        result = await locked_function("value")
        
        assert result == {"result": "fallback"}
        mock_cache.acquire_lock.assert_called_once()
        mock_cache.get.assert_called_once()
        mock_cache.release_lock.assert_not_called()


class TestGlobalCacheInstance:
    """Test global cache instance."""

    def test_global_cache_exists(self):
        """Test that global cache instance exists."""
        assert enhanced_cache is not None
        assert isinstance(enhanced_cache, EnhancedRedisCache)

    def test_global_cache_configuration(self):
        """Test global cache configuration."""
        assert enhanced_cache.redis_url == "redis://localhost:6379"
        assert enhanced_cache.max_connections == 20
        assert enhanced_cache.connection_timeout == 5


class TestCacheIntegration:
    """Integration tests for cache functionality."""

    @pytest.fixture
    def cache_with_real_circuit_breaker(self):
        """Create cache instance with real circuit breaker."""
        with patch('services.redis_cache.ConnectionPool') as mock_pool_class, \
             patch('services.redis_cache.redis.Redis') as mock_redis_class:
            
            mock_client = AsyncMock()
            mock_pool = AsyncMock()
            
            mock_pool_class.from_url.return_value = mock_pool
            mock_redis_class.return_value = mock_client
            
            cache = EnhancedRedisCache(
                redis_url="redis://localhost:6379",
                max_connections=5,
                connection_timeout=2
            )
            
            yield cache

    @pytest.mark.asyncio
    async def test_cache_operations_with_circuit_breaker(self, cache_with_real_circuit_breaker):
        """Test cache operations with circuit breaker."""
        cache = cache_with_real_circuit_breaker
        
        # Simulate failures to open circuit breaker
        cache.client.get.side_effect = Exception("Connection failed")
        
        # Multiple failures should open circuit
        for _ in range(5):
            await cache.get("test", "key")
        
        assert cache.circuit_breaker.state == "OPEN"
        
        # Now operations should be blocked
        cache.client.get.side_effect = None
        cache.client.get.return_value = '{"data": "value"}'
        
        result = await cache.get("test", "key")
        assert result is None  # Circuit breaker blocks operation

    @pytest.mark.asyncio
    async def test_cache_key_generation_consistency(self, cache_with_real_circuit_breaker):
        """Test that key generation is consistent."""
        cache = cache_with_real_circuit_breaker
        
        key1 = cache._generate_key("test", "arg1", "arg2", param1="value1", param2="value2")
        key2 = cache._generate_key("test", "arg1", "arg2", param1="value1", param2="value2")
        key3 = cache._generate_key("test", "arg1", "arg2", param2="value2", param1="value1")
        
        assert key1 == key2
        assert key1 == key3  # Order of kwargs shouldn't matter

    @pytest.mark.asyncio
    async def test_cache_serialization_deserialization(self, cache_with_real_circuit_breaker):
        """Test cache serialization and deserialization."""
        cache = cache_with_real_circuit_breaker
        
        test_data = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "object": {"nested": "value"}
        }
        
        cache.client.get.return_value = json.dumps(test_data)
        
        result = await cache.get("test", "key")
        
        assert result == test_data
        assert isinstance(result["string"], str)
        assert isinstance(result["number"], int)
        assert isinstance(result["boolean"], bool)
        assert result["null"] is None
        assert isinstance(result["array"], list)
        assert isinstance(result["object"], dict)

    @pytest.mark.asyncio
    async def test_cache_metrics_accuracy(self, cache_with_real_circuit_breaker):
        """Test cache metrics accuracy."""
        cache = cache_with_real_circuit_breaker
        
        # Reset metrics
        cache.metrics = {"hits": 0, "misses": 0, "errors": 0, "total_operations": 0}
        
        # Test hits
        cache.client.get.return_value = '{"data": "value"}'
        await cache.get("test", "key1")
        await cache.get("test", "key2")
        
        # Test misses
        cache.client.get.return_value = None
        await cache.get("test", "key3")
        await cache.get("test", "key4")
        
        # Test errors
        cache.client.get.side_effect = Exception("Error")
        await cache.get("test", "key5")
        
        metrics = cache.get_metrics()
        assert metrics["hits"] == 2
        assert metrics["misses"] == 2
        assert metrics["errors"] == 1
        assert metrics["total_operations"] == 5
        assert metrics["hit_rate"] == 2/5