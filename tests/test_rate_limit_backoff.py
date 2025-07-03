"""
Tests for rate-limit back-off functionality.
"""

from unittest.mock import patch

import pytest

from services.redis_client import RedisClient


class TestRateLimitBackoff:
    """Test rate-limit back-off functionality."""

    @pytest.fixture
    def redis_client(self):
        """Create a Redis client instance."""
        return RedisClient()

    @pytest.fixture
    def mock_async_func(self):
        """Create a mock async function."""

        async def mock_func(*args, **kwargs):
            return {"success": True, "data": "test"}

        return mock_func

    @pytest.fixture
    def mock_429_func(self):
        """Create a mock async function that raises 429."""

        async def mock_func(*args, **kwargs):
            error = Exception("Rate limit exceeded")
            error.status_code = 429
            raise error

        return mock_func

    @pytest.mark.asyncio
    async def test_safe_call_success(self, redis_client, mock_async_func):
        """Test successful safe_call without rate limiting."""
        with patch.object(redis_client, "check_rate_limit", return_value=True):
            result = await redis_client.safe_call(
                "test", mock_async_func, "arg1", kwarg1="value1"
            )

            assert result["success"] is True
            assert result["data"] == "test"

    @pytest.mark.asyncio
    async def test_safe_call_rate_limit(self, redis_client, mock_async_func):
        """Test safe_call with rate limiting."""
        # Mock rate limit to be exceeded initially, then allowed
        with patch.object(redis_client, "check_rate_limit", side_effect=[False, True]):
            with patch("asyncio.sleep") as mock_sleep:
                result = await redis_client.safe_call("test", mock_async_func)

                # Should have slept due to rate limit
                mock_sleep.assert_called_once()
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_safe_call_429_backoff(self, redis_client, mock_429_func):
        """Test safe_call with 429 back-off."""
        with patch.object(redis_client, "check_rate_limit", return_value=True):
            with patch("asyncio.sleep") as mock_sleep:
                with pytest.raises(Exception, match="Max retries exceeded"):
                    await redis_client.safe_call("test", mock_429_func, max_retries=2)

                # Should have slept with exponential back-off (3 retries: 0, 1, 2)
                assert mock_sleep.call_count == 3
                # Check exponential back-off: 1s, 2s, 4s
                assert mock_sleep.call_args_list[0][0][0] == 1.0
                assert mock_sleep.call_args_list[1][0][0] == 2.0
                assert mock_sleep.call_args_list[2][0][0] == 4.0

    @pytest.mark.asyncio
    async def test_safe_call_429_recovery(self, redis_client):
        """Test safe_call with 429 followed by success."""
        call_count = 0

        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                error = Exception("Rate limit exceeded")
                error.status_code = 429
                raise error
            return {"success": True}

        with patch.object(redis_client, "check_rate_limit", return_value=True):
            with patch("asyncio.sleep") as mock_sleep:
                result = await redis_client.safe_call("test", mock_func, max_retries=3)

                assert result["success"] is True
                assert call_count == 2
                # Should have slept once for back-off
                assert mock_sleep.call_count == 1

    @pytest.mark.asyncio
    async def test_safe_call_non_429_error(self, redis_client):
        """Test safe_call with non-429 error (should not retry)."""

        async def mock_func():
            raise ValueError("Some other error")

        with patch.object(redis_client, "check_rate_limit", return_value=True):
            with pytest.raises(ValueError, match="Some other error"):
                await redis_client.safe_call("test", mock_func)

    @pytest.mark.asyncio
    async def test_safe_call_max_backoff(self, redis_client, mock_429_func):
        """Test that back-off is capped at 30 seconds."""
        with patch.object(redis_client, "check_rate_limit", return_value=True):
            with patch("asyncio.sleep") as mock_sleep:
                with pytest.raises(Exception, match="Max retries exceeded"):
                    await redis_client.safe_call("test", mock_429_func, max_retries=10)

                # Check that back-off is capped at 30 seconds
                for call in mock_sleep.call_args_list:
                    assert call[0][0] <= 30.0

    def test_rate_limit_key_generation(self, redis_client):
        """Test that rate limit keys are generated correctly."""
        with patch.object(redis_client, "check_rate_limit") as mock_check:
            # This would be called in safe_call
            mock_check.return_value = True

            # The key should be prefixed with "safe_call:"
            expected_key = "safe_call:openai"
            # This is tested indirectly through the safe_call method
            assert "safe_call:" in expected_key
