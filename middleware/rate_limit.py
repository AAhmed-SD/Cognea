"""
Rate Limiting Middleware with Enhanced Redis Cache
- Global rate limiting
- User-specific rate limiting
- Enhanced Redis integration
- Performance monitoring
"""

import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse

from services.performance_monitor import get_performance_monitor
from services.redis_cache import enhanced_cache

logger = logging.getLogger(__name__)


class RateLimiter:
    """Enhanced rate limiter with Redis backend"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
        window_size: int = 60,
    ):
        pass
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        self.window_size = window_size

    async def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limits"""
        try:
            current_time = int(time.time())
            window_start = current_time - self.window_size

            # Get current request count
            key = f"rate_limit:{identifier}:{window_start}"
            current_count = await enhanced_cache.get("rate_limit", key) or 0

            # Check limits
            if current_count >= self.requests_per_minute:
                return False

            # Increment counter
            await enhanced_cache.set(
                "rate_limit", current_count + 1, self.window_size, key
            )

            return True

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request if rate limiting fails
            return True

    async def check_burst_limit(self, identifier: str) -> bool:
        """Check burst limit for rapid requests"""
        try:
            current_time = int(time.time())
            burst_window = 10  # 10 seconds for burst detection

            # Get burst count
            key = f"burst_limit:{identifier}:{current_time // burst_window}"
            burst_count = await enhanced_cache.get("rate_limit", key) or 0

            if burst_count >= self.burst_limit:
                return False

            # Increment burst counter
            await enhanced_cache.set("rate_limit", burst_count + 1, burst_window, key)

            return True

        except Exception as e:
            logger.error(f"Burst limit check error: {e}")
            return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next) -> None:
    """Rate limiting middleware"""
    try:
        # Get client identifier
        client_id = _get_client_identifier(request)

        # Check burst limit first
        burst_allowed = await rate_limiter.check_burst_limit(client_id)
        if not burst_allowed:
            await get_performance_monitor().record_metric(
                "rate_limit_burst_exceeded", 1, "requests", {"client_id": client_id}
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests in short time. Please slow down.",
                    "retry_after": 10,
                },
            )

        # Check rate limit
        rate_allowed = await rate_limiter.check_rate_limit(client_id)
        if not rate_allowed:
            await get_performance_monitor().record_metric(
                "rate_limit_exceeded", 1, "requests", {"client_id": client_id}
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60,
                },
            )

        # Record successful request
        await get_performance_monitor().record_metric(
            "rate_limit_allowed", 1, "requests", {"client_id": client_id}
        )

        # Continue with request
        response = await call_next(request)
        return response

    except Exception as e:
        logger.error(f"Rate limiting middleware error: {e}")
        # Continue with request if rate limiting fails
        return await call_next(request)


def _get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting"""
    # Try to get user ID from authenticated request
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.get('id', 'unknown')}"

    # Try to get API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"

    # Use IP address as fallback
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)  # type: ignore
    return f"ip:{client_ip}"


def setup_rate_limiting(app) -> None:
    """Setup rate limiting middleware"""
    app.middleware("http")(rate_limit_middleware)
    logger.info("Rate limiting middleware configured")
