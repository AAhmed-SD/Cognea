"""
Rate-limited queue service for API calls.
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime, UTC
from .redis_client import get_redis_client

logger = logging.getLogger(__name__)


class RateLimitedQueue:
    """Rate-limited queue for API calls with exponential back-off."""

    def __init__(self, service_name: str, rate_limit: int = 3):
        """
        Initialize rate-limited queue.

        Args:
            service_name: Name of the service (e.g., 'openai', 'notion')
            rate_limit: Requests per second
        """
        self.service_name = service_name
        self.rate_limit = rate_limit
        self.redis_client = get_redis_client()
        self.queue = asyncio.Queue()
        self._running = False

    async def enqueue_request(
        self, method: str, endpoint: str, api_key: str, **kwargs
    ) -> asyncio.Future:
        """
        Enqueue a request for processing.

        Args:
            method: HTTP method
            endpoint: API endpoint
            api_key: API key for authentication
            **kwargs: Additional request parameters

        Returns:
            Future that will resolve with the response
        """
        future = asyncio.Future()
        await self.queue.put(
            {
                "method": method,
                "endpoint": endpoint,
                "api_key": api_key,
                "kwargs": kwargs,
                "future": future,
                "timestamp": datetime.now(UTC),
            }
        )
        return future

    async def _process_queue(self):
        """Process the request queue with rate limiting."""
        while self._running:
            try:
                # Get next request from queue
                request_data = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                # Use safe_call for rate limiting and back-off
                result = await self.redis_client.safe_call(
                    self.service_name,
                    self._make_api_request,
                    request_data["method"],
                    request_data["endpoint"],
                    request_data["api_key"],
                    **request_data["kwargs"],
                )

                # Set result on future
                if not request_data["future"].done():
                    request_data["future"].set_result(result)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                if not request_data["future"].done():
                    request_data["future"].set_exception(e)

    async def _make_api_request(
        self, method: str, endpoint: str, api_key: str, **kwargs
    ):
        """
        Make the actual API request.
        This is a placeholder - implement actual API calls here.
        """
        # Placeholder implementation
        logger.info(f"Making {method} request to {endpoint}")
        return {"status": "success", "data": "placeholder"}

    async def start(self):
        """Start the queue processor."""
        self._running = True
        asyncio.create_task(self._process_queue())
        logger.info(f"Started rate-limited queue for {self.service_name}")

    async def stop(self):
        """Stop the queue processor."""
        self._running = False
        logger.info(f"Stopped rate-limited queue for {self.service_name}")


# Global queue instances
_openai_queue: Optional[RateLimitedQueue] = None
_notion_queue: Optional[RateLimitedQueue] = None
_stripe_queue: Optional[RateLimitedQueue] = None


def get_openai_queue() -> RateLimitedQueue:
    """Get the OpenAI rate-limited queue."""
    global _openai_queue
    if _openai_queue is None:
        _openai_queue = RateLimitedQueue("openai", rate_limit=3)
    return _openai_queue


def get_notion_queue() -> RateLimitedQueue:
    """Get the Notion rate-limited queue."""
    global _notion_queue
    if _notion_queue is None:
        _notion_queue = RateLimitedQueue("notion", rate_limit=3)
    return _notion_queue


def get_stripe_queue() -> RateLimitedQueue:
    """Get the Stripe rate-limited queue."""
    global _stripe_queue
    if _stripe_queue is None:
        _stripe_queue = RateLimitedQueue("stripe", rate_limit=10)
    return _stripe_queue
