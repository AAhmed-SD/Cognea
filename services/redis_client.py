"""
Redis client service for caching, rate limiting, and token tracking.
"""

import redis
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class RedisConnectionError(Exception):
    """Exception raised when Redis connection fails."""

    pass


class RateLimitExceededError(Exception):
    """Exception raised when rate limit is exceeded."""

    pass


class MaxRetriesExceededError(Exception):
    """Exception raised when maximum retries are exceeded."""

    def __init__(
        self, func_name: str, max_retries: int, last_error: Optional[Exception] = None
    ):
        self.func_name = func_name
        self.max_retries = max_retries
        self.last_error = last_error
        super().__init__(f"Max retries ({max_retries}) exceeded for {func_name}")


class RedisClient:
    """Redis client for caching, rate limiting, and token tracking."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis client."""
        self.redis_url = redis_url or "redis://localhost:6379"
        self.client = None
        self._connect()

    def _connect(self):
        """Connect to Redis."""
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self.client.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    async def safe_call(self, key: str, func, *args, max_retries=5, rate=3, **kwargs):
        """
        Rate-limited async call queue with exponential back-off on 429 errors.
        Args:
            key: Unique key for the queue (e.g., 'openai', 'notion', 'stripe')
            func: The async function to call
            *args, **kwargs: Arguments to pass to func
            max_retries: Maximum number of retries on 429
            rate: Allowed requests per second
        Returns:
            Result of func(*args, **kwargs)
        Raises:
            RateLimitExceededError: When rate limit is exceeded
            MaxRetriesExceededError: When max retries are exceeded
            Exception: Original exception from the function call
        """
        retry = 0
        delay = 1.0 / rate
        last_error = None

        while retry <= max_retries:
            # Global rate limit using Redis
            allowed = self.check_rate_limit(f"safe_call:{key}", rate, 1)
            if not allowed:
                logger.warning(f"Rate limit exceeded for {key}, waiting {delay}s")
                await asyncio.sleep(delay)
                continue

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                last_error = e

                # Check if it's a rate limit error (429)
                if hasattr(e, "status_code") and e.status_code == 429:
                    # Exponential back-off
                    backoff = min(2**retry, 30)
                    logger.warning(
                        f"429 received for {key}, backing off for {backoff}s (retry {retry+1}/{max_retries})"
                    )
                    await asyncio.sleep(backoff)
                    retry += 1
                elif (
                    hasattr(e, "response")
                    and hasattr(e.response, "status_code")
                    and e.response.status_code == 429
                ):
                    # Handle httpx.HTTPStatusError with 429
                    backoff = min(2**retry, 30)
                    logger.warning(
                        f"429 received for {key}, backing off for {backoff}s (retry {retry+1}/{max_retries})"
                    )
                    await asyncio.sleep(backoff)
                    retry += 1
                else:
                    # For other errors, don't retry
                    logger.error(f"Non-retryable error for {key}: {e}")
                    raise

        # If we get here, max retries exceeded
        raise MaxRetriesExceededError(
            func_name=func.__name__, max_retries=max_retries, last_error=last_error
        )

    # Rate Limiting Methods
    def check_rate_limit(
        self, key: str, max_requests: int, window_seconds: int
    ) -> bool:
        """Check if rate limit is exceeded."""
        if not self.is_connected():
            return True  # Allow if Redis is not available

        current_time = datetime.utcnow().timestamp()
        window_start = current_time - window_seconds

        # Remove old entries
        self.client.zremrangebyscore(key, 0, window_start)

        # Count current requests
        current_requests = self.client.zcard(key)

        if current_requests >= max_requests:
            return False  # Rate limit exceeded

        # Add current request
        self.client.zadd(key, {str(current_time): current_time})
        self.client.expire(key, window_seconds)

        return True

    def get_rate_limit_info(self, key: str) -> Dict[str, Any]:
        """Get rate limit information."""
        if not self.is_connected():
            return {"remaining": 999, "reset_time": None}

        current_time = datetime.utcnow().timestamp()
        window_seconds = 60  # Default 1 minute window

        # Remove old entries
        self.client.zremrangebyscore(key, 0, current_time - window_seconds)

        # Count current requests
        current_requests = self.client.zcard(key)
        remaining = max(0, 60 - current_requests)  # Assuming 60 requests per minute

        # Get oldest request to calculate reset time
        oldest = self.client.zrange(key, 0, 0, withscores=True)
        reset_time = None
        if oldest:
            reset_time = datetime.fromtimestamp(
                oldest[0][1] + window_seconds
            ).isoformat()

        return {
            "remaining": remaining,
            "reset_time": reset_time,
            "current_requests": current_requests,
        }

    # Token Tracking Methods
    def track_token_usage(
        self, user_id: str, tokens_used: int, cost_usd: float, model: str
    ):
        """Track token usage and cost for a user."""
        if not self.is_connected():
            return

        today = datetime.utcnow().strftime("%Y-%m-%d")
        month = datetime.utcnow().strftime("%Y-%m")

        # Daily tracking
        daily_key = f"tokens:daily:{user_id}:{today}"
        monthly_key = f"tokens:monthly:{user_id}:{month}"
        cost_key = f"cost:daily:{user_id}:{today}"
        cost_monthly_key = f"cost:monthly:{user_id}:{month}"

        # Increment token counts
        self.client.incrby(daily_key, tokens_used)
        self.client.incrby(monthly_key, tokens_used)
        self.client.incrbyfloat(cost_key, cost_usd)
        self.client.incrbyfloat(cost_monthly_key, cost_usd)

        # Set expiration (30 days for daily, 1 year for monthly)
        self.client.expire(daily_key, 30 * 24 * 3600)
        self.client.expire(monthly_key, 365 * 24 * 3600)
        self.client.expire(cost_key, 30 * 24 * 3600)
        self.client.expire(cost_monthly_key, 365 * 24 * 3600)

        # Track by model
        model_key = f"tokens:model:{user_id}:{model}:{today}"
        self.client.incrby(model_key, tokens_used)
        self.client.expire(model_key, 30 * 24 * 3600)

    def get_token_usage(self, user_id: str, period: str = "daily") -> Dict[str, Any]:
        """Get token usage statistics."""
        if not self.is_connected():
            return {"tokens": 0, "cost": 0.0, "models": {}}

        if period == "daily":
            date = datetime.utcnow().strftime("%Y-%m-%d")
            tokens_key = f"tokens:daily:{user_id}:{date}"
            cost_key = f"cost:daily:{user_id}:{date}"
        else:  # monthly
            month = datetime.utcnow().strftime("%Y-%m")
            tokens_key = f"tokens:monthly:{user_id}:{month}"
            cost_key = f"cost:monthly:{user_id}:{month}"

        tokens = int(self.client.get(tokens_key) or 0)
        cost = float(self.client.get(cost_key) or 0.0)

        # Get model breakdown
        models = {}
        if period == "daily":
            pattern = f"tokens:model:{user_id}:*:{date}"
        else:
            pattern = f"tokens:model:{user_id}:*:{month}"

        for key in self.client.scan_iter(match=pattern):
            model = key.split(":")[3]  # Extract model name
            model_tokens = int(self.client.get(key) or 0)
            models[model] = model_tokens

        return {"tokens": tokens, "cost": cost, "models": models, "period": period}

    def check_budget_limit(
        self,
        user_id: str,
        cost_usd: float,
        daily_limit: float = 10.0,
        monthly_limit: float = 100.0,
    ) -> bool:
        """Check if user has exceeded budget limits."""
        if not self.is_connected():
            return True  # Allow if Redis is not available

        today = datetime.utcnow().strftime("%Y-%m-%d")
        month = datetime.utcnow().strftime("%Y-%m")

        daily_cost_key = f"cost:daily:{user_id}:{today}"
        monthly_cost_key = f"cost:monthly:{user_id}:{month}"

        current_daily_cost = float(self.client.get(daily_cost_key) or 0.0)
        current_monthly_cost = float(self.client.get(monthly_cost_key) or 0.0)

        # Check if adding this cost would exceed limits
        if current_daily_cost + cost_usd > daily_limit:
            logger.warning(f"User {user_id} would exceed daily budget limit")
            return False

        if current_monthly_cost + cost_usd > monthly_limit:
            logger.warning(f"User {user_id} would exceed monthly budget limit")
            return False

        return True

    # Caching Methods
    def set_cache(self, key: str, value: Any, expire_seconds: int = 3600):
        """Set a cache value."""
        if not self.is_connected():
            return

        try:
            serialized_value = json.dumps(value)
            self.client.setex(key, expire_seconds, serialized_value)
        except Exception:
            logger.error("Error setting cache")

    def get_cache(self, key: str) -> Optional[Any]:
        """Get a cache value."""
        if not self.is_connected():
            return None

        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            logger.error("Error getting cache")
            return None

    def delete_cache(self, key: str):
        """Delete a cache value."""
        if not self.is_connected():
            return

        try:
            self.client.delete(key)
        except Exception:
            logger.error("Error deleting cache")

    def clear_user_cache(self, user_id: str):
        """Clear all cache entries for a user."""
        if not self.is_connected():
            return

        try:
            pattern = f"cache:user:{user_id}:*"
            for key in self.client.scan_iter(match=pattern):
                self.client.delete(key)
        except Exception:
            logger.error("Error clearing user cache")


# Global Redis client instance
redis_client = RedisClient()


def get_redis_client() -> RedisClient:
    """Get the global Redis client instance."""
    return redis_client
