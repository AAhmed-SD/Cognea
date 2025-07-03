"""
Rate-limited queue service for API calls.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

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

            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                if not request_data["future"].done():
                    request_data["future"].set_exception(e)

    async def _make_api_request(
        self, method: str, endpoint: str, api_key: str, **kwargs
    ) -> dict[str, Any]:
        """
        Make the actual API request using httpx.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint URL
            api_key: API key for authentication
            **kwargs: Additional request parameters (headers, json, data, etc.)

        Returns:
            Dictionary containing response data and metadata

        Raises:
            httpx.HTTPStatusError: For HTTP error responses
            httpx.RequestError: For network/connection errors
        """
        # Prepare headers with authentication
        headers = kwargs.get("headers", {})
        headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"Cognie-{self.service_name}-client/1.0",
            }
        )

        # Extract request parameters
        json_data = kwargs.get("json")
        data = kwargs.get("data")
        params = kwargs.get("params")
        timeout = kwargs.get("timeout", 30.0)

        # Determine base URL based on service
        base_urls = {
            "openai": "https://api.openai.com/v1",
            "notion": "https://api.notion.com/v1",
            "stripe": "https://api.stripe.com/v1",
        }

        base_url = base_urls.get(self.service_name, "")
        if not base_url:
            raise ValueError(f"Unknown service: {self.service_name}")

        full_url = f"{base_url}/{endpoint.lstrip('/')}"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.debug(f"Making {method} request to {full_url}")

                response = await client.request(
                    method=method.upper(),
                    url=full_url,
                    headers=headers,
                    json=json_data,
                    data=data,
                    params=params,
                )

                # Handle different response types
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    response_data = response.json()
                else:
                    response_data = {"content": response.text}

                # Add metadata
                result = {
                    "data": response_data,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                    "method": method.upper(),
                }

                # Log success
                logger.info(
                    f"API request successful: {method} {endpoint} -> {response.status_code}"
                )

                return result

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error for {method} {endpoint}: {e.response.status_code} - {e.response.text}"
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {method} {endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {method} {endpoint}: {e}")
            raise

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
_openai_queue: RateLimitedQueue | None = None
_notion_queue: RateLimitedQueue | None = None
_stripe_queue: RateLimitedQueue | None = None


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
