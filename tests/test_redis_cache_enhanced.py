import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from services.redis_cache import EnhancedRedisCache


class TestRedisCacheServiceEnhanced:
    """Enhanced tests for Redis cache service."""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.client = MagicMock()
        return mock_client

    @pytest.fixture
    def cache_service(self, mock_redis_client):
        """Create cache service with mocked Redis."""
        with patch('services.redis_cache.redis.Redis') as mock_redis:
            mock_redis.return_value = mock_redis_client.client
            return EnhancedRedisCache()

    def test_init(self, cache_service):
        """Test RedisCacheService initialization."""
        assert cache_service.redis_client is not None
        assert cache_service.default_ttl == 3600

    @pytest.mark.asyncio
    async def test_get_success(self, cache_service):
        """Test successful cache get operation."""
        test_data = {"key": "value", "number": 42}
        cache_service.redis_client.client.get.return_value = json.dumps(test_data)
        
        result = await cache_service.get("test_key")
        
        assert result == test_data
        cache_service.redis_client.client.get.assert_called_with("test_key")

    @pytest.mark.asyncio
    async def test_get_not_found(self, cache_service):
        """Test cache get when key not found."""
        cache_service.redis_client.client.get.return_value = None
        
        result = await cache_service.get("nonexistent_key")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_invalid_json(self, cache_service):
        """Test cache get with invalid JSON data."""
        cache_service.redis_client.client.get.return_value = "invalid_json"
        
        result = await cache_service.get("test_key")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_disconnected(self, cache_service):
        """Test cache get when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.get("test_key")
        
        assert result is None
        cache_service.redis_client.client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_success(self, cache_service):
        """Test successful cache set operation."""
        test_data = {"key": "value", "list": [1, 2, 3]}
        
        await cache_service.set("test_key", test_data, ttl=300)
        
        cache_service.redis_client.client.setex.assert_called_with(
            "test_key", 300, json.dumps(test_data)
        )

    @pytest.mark.asyncio
    async def test_set_default_ttl(self, cache_service):
        """Test cache set with default TTL."""
        test_data = {"key": "value"}
        
        await cache_service.set("test_key", test_data)
        
        cache_service.redis_client.client.setex.assert_called_with(
            "test_key", 3600, json.dumps(test_data)
        )

    @pytest.mark.asyncio
    async def test_set_redis_disconnected(self, cache_service):
        """Test cache set when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        await cache_service.set("test_key", {"data": "value"})
        
        cache_service.redis_client.client.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_success(self, cache_service):
        """Test successful cache delete operation."""
        cache_service.redis_client.client.delete.return_value = 1
        
        result = await cache_service.delete("test_key")
        
        assert result is True
        cache_service.redis_client.client.delete.assert_called_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_not_found(self, cache_service):
        """Test cache delete when key not found."""
        cache_service.redis_client.client.delete.return_value = 0
        
        result = await cache_service.delete("nonexistent_key")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_redis_disconnected(self, cache_service):
        """Test cache delete when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.delete("test_key")
        
        assert result is False
        cache_service.redis_client.client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_exists_true(self, cache_service):
        """Test cache exists when key exists."""
        cache_service.redis_client.client.exists.return_value = 1
        
        result = await cache_service.exists("test_key")
        
        assert result is True
        cache_service.redis_client.client.exists.assert_called_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_false(self, cache_service):
        """Test cache exists when key doesn't exist."""
        cache_service.redis_client.client.exists.return_value = 0
        
        result = await cache_service.exists("test_key")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_redis_disconnected(self, cache_service):
        """Test cache exists when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.exists("test_key")
        
        assert result is False
        cache_service.redis_client.client.exists.assert_not_called()

    @pytest.mark.asyncio
    async def test_expire_success(self, cache_service):
        """Test successful cache expire operation."""
        cache_service.redis_client.client.expire.return_value = 1
        
        result = await cache_service.expire("test_key", 600)
        
        assert result is True
        cache_service.redis_client.client.expire.assert_called_with("test_key", 600)

    @pytest.mark.asyncio
    async def test_expire_key_not_found(self, cache_service):
        """Test cache expire when key not found."""
        cache_service.redis_client.client.expire.return_value = 0
        
        result = await cache_service.expire("nonexistent_key", 600)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_expire_redis_disconnected(self, cache_service):
        """Test cache expire when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.expire("test_key", 600)
        
        assert result is False
        cache_service.redis_client.client.expire.assert_not_called()

    @pytest.mark.asyncio
    async def test_ttl_success(self, cache_service):
        """Test successful TTL retrieval."""
        cache_service.redis_client.client.ttl.return_value = 300
        
        result = await cache_service.ttl("test_key")
        
        assert result == 300
        cache_service.redis_client.client.ttl.assert_called_with("test_key")

    @pytest.mark.asyncio
    async def test_ttl_key_not_found(self, cache_service):
        """Test TTL when key not found."""
        cache_service.redis_client.client.ttl.return_value = -2
        
        result = await cache_service.ttl("nonexistent_key")
        
        assert result == -2

    @pytest.mark.asyncio
    async def test_ttl_no_expiry(self, cache_service):
        """Test TTL when key has no expiry."""
        cache_service.redis_client.client.ttl.return_value = -1
        
        result = await cache_service.ttl("test_key")
        
        assert result == -1

    @pytest.mark.asyncio
    async def test_ttl_redis_disconnected(self, cache_service):
        """Test TTL when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.ttl("test_key")
        
        assert result == -2
        cache_service.redis_client.client.ttl.assert_not_called()

    @pytest.mark.asyncio
    async def test_keys_pattern_success(self, cache_service):
        """Test successful keys pattern search."""
        cache_service.redis_client.client.keys.return_value = [
            b"user:123", b"user:456", b"user:789"
        ]
        
        result = await cache_service.keys("user:*")
        
        assert result == ["user:123", "user:456", "user:789"]
        cache_service.redis_client.client.keys.assert_called_with("user:*")

    @pytest.mark.asyncio
    async def test_keys_no_matches(self, cache_service):
        """Test keys pattern search with no matches."""
        cache_service.redis_client.client.keys.return_value = []
        
        result = await cache_service.keys("nonexistent:*")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_keys_redis_disconnected(self, cache_service):
        """Test keys pattern search when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.keys("test:*")
        
        assert result == []
        cache_service.redis_client.client.keys.assert_not_called()

    @pytest.mark.asyncio
    async def test_flush_all_success(self, cache_service):
        """Test successful flush all operation."""
        cache_service.redis_client.client.flushall.return_value = True
        
        result = await cache_service.flush_all()
        
        assert result is True
        cache_service.redis_client.client.flushall.assert_called_once()

    @pytest.mark.asyncio
    async def test_flush_all_redis_disconnected(self, cache_service):
        """Test flush all when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.flush_all()
        
        assert result is False
        cache_service.redis_client.client.flushall.assert_not_called()

    @pytest.mark.asyncio
    async def test_mget_success(self, cache_service):
        """Test successful multi-get operation."""
        cache_service.redis_client.client.mget.return_value = [
            json.dumps({"id": 1}),
            json.dumps({"id": 2}),
            None
        ]
        
        result = await cache_service.mget(["key1", "key2", "key3"])
        
        assert result == [{"id": 1}, {"id": 2}, None]
        cache_service.redis_client.client.mget.assert_called_with(["key1", "key2", "key3"])

    @pytest.mark.asyncio
    async def test_mget_invalid_json(self, cache_service):
        """Test multi-get with invalid JSON data."""
        cache_service.redis_client.client.mget.return_value = [
            "invalid_json",
            json.dumps({"id": 2})
        ]
        
        result = await cache_service.mget(["key1", "key2"])
        
        assert result == [None, {"id": 2}]

    @pytest.mark.asyncio
    async def test_mget_redis_disconnected(self, cache_service):
        """Test multi-get when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.mget(["key1", "key2"])
        
        assert result == []
        cache_service.redis_client.client.mget.assert_not_called()

    @pytest.mark.asyncio
    async def test_mset_success(self, cache_service):
        """Test successful multi-set operation."""
        data = {
            "key1": {"id": 1},
            "key2": {"id": 2}
        }
        
        await cache_service.mset(data, ttl=300)
        
        # Should call pipeline operations
        assert cache_service.redis_client.client.pipeline.called

    @pytest.mark.asyncio
    async def test_mset_redis_disconnected(self, cache_service):
        """Test multi-set when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        await cache_service.mset({"key1": {"data": "value"}})
        
        cache_service.redis_client.client.pipeline.assert_not_called()

    @pytest.mark.asyncio
    async def test_increment_success(self, cache_service):
        """Test successful increment operation."""
        cache_service.redis_client.client.incr.return_value = 5
        
        result = await cache_service.increment("counter", amount=2)
        
        assert result == 5
        cache_service.redis_client.client.incr.assert_called_with("counter", 2)

    @pytest.mark.asyncio
    async def test_increment_default_amount(self, cache_service):
        """Test increment with default amount."""
        cache_service.redis_client.client.incr.return_value = 1
        
        result = await cache_service.increment("counter")
        
        assert result == 1
        cache_service.redis_client.client.incr.assert_called_with("counter", 1)

    @pytest.mark.asyncio
    async def test_increment_redis_disconnected(self, cache_service):
        """Test increment when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.increment("counter")
        
        assert result == 0
        cache_service.redis_client.client.incr.assert_not_called()

    @pytest.mark.asyncio
    async def test_decrement_success(self, cache_service):
        """Test successful decrement operation."""
        cache_service.redis_client.client.decr.return_value = 3
        
        result = await cache_service.decrement("counter", amount=2)
        
        assert result == 3
        cache_service.redis_client.client.decr.assert_called_with("counter", 2)

    @pytest.mark.asyncio
    async def test_decrement_redis_disconnected(self, cache_service):
        """Test decrement when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.decrement("counter")
        
        assert result == 0
        cache_service.redis_client.client.decr.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_info(self, cache_service):
        """Test getting Redis info."""
        mock_info = {
            "redis_version": "6.2.0",
            "used_memory": "1024000",
            "connected_clients": "5"
        }
        cache_service.redis_client.client.info.return_value = mock_info
        
        result = await cache_service.get_info()
        
        assert result == mock_info
        cache_service.redis_client.client.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_info_redis_disconnected(self, cache_service):
        """Test getting info when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.get_info()
        
        assert result == {}
        cache_service.redis_client.client.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_ping_success(self, cache_service):
        """Test successful ping operation."""
        cache_service.redis_client.client.ping.return_value = True
        
        result = await cache_service.ping()
        
        assert result is True
        cache_service.redis_client.client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_ping_redis_disconnected(self, cache_service):
        """Test ping when Redis is disconnected."""
        cache_service.redis_client.is_connected.return_value = False
        
        result = await cache_service.ping()
        
        assert result is False
        cache_service.redis_client.client.ping.assert_not_called()

    @pytest.mark.asyncio
    async def test_error_handling_redis_exception(self, cache_service):
        """Test error handling when Redis raises exception."""
        cache_service.redis_client.client.get.side_effect = Exception("Redis error")
        
        with patch('services.redis_cache.logger') as mock_logger:
            result = await cache_service.get("test_key")
            
            assert result is None
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_complex_data_serialization(self, cache_service):
        """Test serialization of complex data structures."""
        complex_data = {
            "nested": {
                "list": [1, 2, {"inner": "value"}],
                "datetime": datetime.now().isoformat(),
                "null_value": None,
                "boolean": True
            }
        }
        
        await cache_service.set("complex_key", complex_data)
        
        # Verify JSON serialization was called
        cache_service.redis_client.client.setex.assert_called()
        call_args = cache_service.redis_client.client.setex.call_args[0]
        assert call_args[0] == "complex_key"
        
        # Verify data can be deserialized
        serialized_data = call_args[2]
        deserialized = json.loads(serialized_data)
        assert deserialized == complex_data