"""
Rate-limited queue for Notion API calls.
Handles 3 requests/second limit with batching and exponential backoff.
"""

import asyncio
import logging
import time
import heapq
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


@dataclass
class NotionAPIRequest:
    """Represents a Notion API request."""

    method: str
    endpoint: str
    data: Optional[Dict] = None
    headers: Optional[Dict] = None
    priority: int = 1  # 1 = high, 2 = medium, 3 = low
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(UTC)


class NotionRateLimitedQueue:
    """Rate-limited queue for Notion API calls."""

    def __init__(self, notion_client, max_requests_per_second: int = 3):
        self.notion_client = notion_client
        self.max_requests_per_second = max_requests_per_second
        self.priority_queue: List[
            Tuple[int, float, NotionAPIRequest, asyncio.Future]
        ] = []
        self.queue_lock = asyncio.Lock()
        self.worker_task = None
        self.is_running = False
        self.last_request_time = 0
        self.consecutive_errors = 0
        self.max_retries = 3

    async def start(self):
        """Start the rate-limited queue worker."""
        if not self.is_running:
            self.is_running = True
            self.worker_task = asyncio.create_task(self._worker())
            logger.info("Notion rate-limited queue started")

    async def stop(self):
        """Stop the rate-limited queue worker."""
        if self.is_running:
            self.is_running = False
            if self.worker_task:
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass
            logger.info("Notion rate-limited queue stopped")

    async def enqueue_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        priority: int = 1,
    ) -> asyncio.Future:
        """Enqueue a Notion API request with priority."""
        request = NotionAPIRequest(
            method=method,
            endpoint=endpoint,
            data=data,
            headers=headers,
            priority=priority,
        )

        # Create a future to return the result
        future = asyncio.Future()

        async with self.queue_lock:
            # Use timestamp as tiebreaker for requests with same priority
            timestamp = time.time()
            # heapq uses min-heap, so we negate priority to get highest priority first
            heapq.heappush(self.priority_queue, (-priority, timestamp, request, future))

        return future

    async def _worker(self):
        """Worker that processes requests at the rate limit."""
        while self.is_running:
            try:
                # Process up to max_requests_per_second
                for _ in range(self.max_requests_per_second):
                    if not self.priority_queue:
                        break

                    # Get the highest priority request
                    request, future = await self._get_highest_priority_request()
                    if request is None:
                        break

                    # Rate limiting
                    await self._rate_limit()

                    # Process the request
                    try:
                        result = await self._process_request(request)
                        if not future.done():
                            future.set_result(result)
                        self.consecutive_errors = 0  # Reset error count on success

                    except Exception as e:
                        logger.error(f"Error processing Notion API request: {e}")
                        if not future.done():
                            future.set_exception(e)
                        self.consecutive_errors += 1

                # Wait 1 second before next batch
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Notion queue worker: {e}")
                await asyncio.sleep(1)

    async def _get_highest_priority_request(
        self,
    ) -> Tuple[Optional[NotionAPIRequest], Optional[asyncio.Future]]:
        """Get the highest priority request from the queue."""
        async with self.queue_lock:
            if not self.priority_queue:
                return None, None

            # Get the highest priority request (lowest negative priority = highest actual priority)
            _, timestamp, request, future = heapq.heappop(self.priority_queue)
            logger.debug(
                f"Processing request: {request.method} {request.endpoint} (priority: {request.priority})"
            )
            return request, future

    async def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.max_requests_per_second

        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)

        self.last_request_time = time.time()

    async def _process_request(self, request: NotionAPIRequest) -> Any:
        """Process a single Notion API request with retries and backoff."""
        for attempt in range(self.max_retries):
            try:
                # Make the request using the notion client
                if request.method == "GET":
                    result = await self.notion_client._make_request(
                        "GET", request.endpoint, headers=request.headers
                    )
                elif request.method == "POST":
                    result = await self.notion_client._make_request(
                        "POST",
                        request.endpoint,
                        json=request.data,
                        headers=request.headers,
                    )
                elif request.method == "PUT":
                    result = await self.notion_client._make_request(
                        "PUT",
                        request.endpoint,
                        json=request.data,
                        headers=request.headers,
                    )
                elif request.method == "DELETE":
                    result = await self.notion_client._make_request(
                        "DELETE", request.endpoint, headers=request.headers
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {request.method}")

                return result

            except Exception as e:
                if "429" in str(e):  # Rate limit exceeded
                    # Exponential backoff
                    backoff_time = (2**attempt) * (1 + self.consecutive_errors)
                    logger.warning(f"Rate limit hit, backing off for {backoff_time}s")
                    await asyncio.sleep(backoff_time)
                    continue
                elif attempt == self.max_retries - 1:
                    raise
                else:
                    # For other errors, wait a bit and retry
                    await asyncio.sleep(1)

    async def batch_requests(self, requests: list[NotionAPIRequest]) -> list[Any]:
        """Process multiple requests in a batch."""
        futures = []
        for request in requests:
            future = await self.enqueue_request(
                method=request.method,
                endpoint=request.endpoint,
                data=request.data,
                headers=request.headers,
                priority=request.priority,
            )
            futures.append(future)

        # Wait for all requests to complete
        results = await asyncio.gather(*futures, return_exceptions=True)
        return results

    async def get_queue_size(self) -> int:
        """Get the current size of the priority queue."""
        async with self.queue_lock:
            return len(self.priority_queue)

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about the queue."""
        async with self.queue_lock:
            priorities = [item[0] for item in self.priority_queue]
            return {
                "queue_size": len(self.priority_queue),
                "high_priority_count": sum(1 for p in priorities if p == -1),
                "medium_priority_count": sum(1 for p in priorities if p == -2),
                "low_priority_count": sum(1 for p in priorities if p == -3),
                "consecutive_errors": self.consecutive_errors,
                "is_running": self.is_running,
            }


# Global instance
_notion_queue = None


def get_notion_queue(notion_client) -> NotionRateLimitedQueue:
    """Get the global Notion rate-limited queue instance."""
    global _notion_queue
    if _notion_queue is None:
        _notion_queue = NotionRateLimitedQueue(notion_client)
    return _notion_queue
