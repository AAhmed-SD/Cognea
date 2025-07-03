"""
Simple test to check coverage without full app dependencies.
"""

import pytest

from services.redis_client import RedisClient


def test_redis_client_basic():
    """Test basic Redis client functionality."""
    client = RedisClient()
    assert client.redis_url == "redis://localhost:6379"
    # Test without actual Redis connection
    assert not client.is_connected()


def test_rate_limit_check():
    """Test rate limit checking logic."""
    client = RedisClient()
    # Should return True when Redis is not connected (fallback behavior)
    assert client.check_rate_limit("test_key", 10, 60) is True


def test_token_tracking():
    """Test token tracking methods."""
    client = RedisClient()
    # Should not fail when Redis is not connected
    client.track_token_usage("user1", 100, 0.01, "gpt-4")

    # Should return default values when Redis is not connected
    usage = client.get_token_usage("user1", "daily")
    assert usage["tokens"] == 0
    assert usage["cost"] == 0.0


def test_budget_limit_check():
    """Test budget limit checking."""
    client = RedisClient()
    # Should return True when Redis is not connected (allow by default)
    assert client.check_budget_limit("user1", 0.01) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
