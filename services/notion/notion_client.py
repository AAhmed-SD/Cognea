"""
Notion API client for Cognie.
Handles authentication, rate limiting, and basic API operations.
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from .rate_limited_queue import get_notion_queue

logger = logging.getLogger(__name__)


class NotionConfig(BaseModel):
    """Notion API configuration."""

    model_config = ConfigDict(from_attributes=True)

    api_key: str
    base_url: str = "https://api.notion.com/v1"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 0.1  # 100ms between requests


class NotionPage(BaseModel):
    """Notion page data model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    properties: dict[str, Any]
    created_time: datetime
    last_edited_time: datetime
    url: str
    parent_type: str
    parent_id: str | None = None


class NotionDatabase(BaseModel):
    """Notion database data model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    properties: dict[str, Any]
    created_time: datetime
    last_edited_time: datetime
    url: str


class NotionClient:
    """Notion API client with rate limiting."""

    def __init__(self, api_key: str):
    pass
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        # Initialize rate-limited queue
        self.queue = get_notion_queue(self)

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> dict[str, Any]:
        """Make a rate-limited request to the Notion API."""
        try:
            # Use rate-limited queue for all API calls
            future = await self.queue.enqueue_request(
                method=method, endpoint=endpoint, headers=self.headers, **kwargs
            )
            return await future
        except Exception as e:
            logger.error(f"Notion API request failed: {e}")
            raise

    async def search(
        self, query: str = "", filter_params: dict | None = None
    ) -> list[dict[str, Any]]:
        """Search for pages and databases."""
        data = {"query": query}
        if filter_params:
            data["filter"] = filter_params

        response = await self._make_request("POST", "/search", data=data)
        return response.get("results", [])

    async def get_page(self, page_id: str) -> dict[str, Any]:
        """Get a specific page."""
        return await self._make_request("GET", f"/pages/{page_id}")

    async def get_database(self, database_id: str) -> dict[str, Any]:
        """Get a specific database."""
        return await self._make_request("GET", f"/databases/{database_id}")

    async def query_database(
        self, database_id: str, filter_params: dict | None = None
    ) -> list[dict[str, Any]]:
        """Query a database."""
        data = {}
        if filter_params:
            data["filter"] = filter_params

        response = await self._make_request(
            "POST", f"/databases/{database_id}/query", data=data
        )
        return response.get("results", [])

    async def create_page(
        self, parent_id: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new page."""
        data = {"parent": {"database_id": parent_id}, "properties": properties}
        return await self._make_request("POST", "/pages", data=data)

    async def update_page(
        self, page_id: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a page."""
        data = {"properties": properties}
        return await self._make_request("PATCH", f"/pages/{page_id}", data=data)

    async def delete_page(self, page_id: str) -> dict[str, Any]:
        """Delete a page."""
        return await self._make_request("DELETE", f"/pages/{page_id}")

    async def get_block_children(self, block_id: str) -> list[dict[str, Any]]:
        """Get children of a block."""
        response = await self._make_request("GET", f"/blocks/{block_id}/children")
        return response.get("results", [])

    async def append_block_children(
        self, block_id: str, children: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Append children to a block."""
        data = {"children": children}
        return await self._make_request(
            "PATCH", f"/blocks/{block_id}/children", data=data
        )

    async def get_user(self, user_id: str) -> dict[str, Any]:
        """Get user information."""
        return await self._make_request("GET", f"/users/{user_id}")

    async def list_users(self) -> list[dict[str, Any]]:
        """List all users."""
        response = await self._make_request("GET", "/users")
        return response.get("results", [])


# Import asyncio for the sleep function
