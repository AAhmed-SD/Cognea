from fastapi import Request, HTTPException
from redis import Redis
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, redis_client: Redis, requests_per_minute: int = 60):
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute

    async def check_rate_limit(self, request: Request):
        # Get client identifier - use IP or a header for better identification
        client_ip = request.client.host if request.client else "unknown"

        # For test environments, use a consistent identifier
        if client_ip in ["testclient", "127.0.0.1", "localhost"]:
            client_ip = "testclient"

        key = f"rate_limit:{client_ip}"

        # Debug logging
        logger.info(f"Rate limit check for client: {client_ip}, key: {key}")

        # Get current count
        current = self.redis.get(key)

        if current is None:
            # First request
            self.redis.setex(key, 60, 1)
            logger.info(f"First request for {client_ip}, setting count to 1")
            return True

        current_count = int(current)
        logger.info(f"Current count for {client_ip}: {current_count}")

        if current_count >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded for {client_ip}: {current_count} >= {self.requests_per_minute}"
            )
            raise HTTPException(status_code=429, detail="Too many requests")

        # Increment counter
        new_count = self.redis.incr(key)
        logger.info(f"Incremented count for {client_ip}: {new_count}")
        return True
