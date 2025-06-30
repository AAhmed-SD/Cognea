"""
Notion API client for Cognie.
Handles authentication, rate limiting, and basic API operations.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, UTC
import httpx
from pydantic import BaseModel, ConfigDict

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
    properties: Dict[str, Any]
    created_time: datetime
    last_edited_time: datetime
    url: str
    parent_type: str
    parent_id: Optional[str] = None

class NotionDatabase(BaseModel):
    """Notion database data model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    properties: Dict[str, Any]
    created_time: datetime
    last_edited_time: datetime
    url: str

class NotionClient:
    """Notion API client with rate limiting and error handling."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Notion client."""
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("Notion API key is required")
        
        self.config = NotionConfig(api_key=self.api_key)
        self.last_request_time = 0
        self.session = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
        )
    
    async def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Notion API with retries."""
        await self._rate_limit()
        
        url = f"{self.config.base_url}{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    retry_after = int(e.response.headers.get("Retry-After", 1))
                    logger.warning(f"Rate limited, retrying after {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                elif e.response.status_code in [401, 403]:
                    logger.error(f"Authentication error: {e.response.text}")
                    raise
                elif attempt == self.config.max_retries - 1:
                    logger.error(f"Request failed after {self.config.max_retries} attempts: {e}")
                    raise
                else:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    logger.error(f"Request failed: {e}")
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def get_page(self, page_id: str) -> NotionPage:
        """Get a Notion page by ID."""
        try:
            data = await self._make_request("GET", f"/pages/{page_id}")
            
            # Extract title from properties
            title = "Untitled"
            if "properties" in data:
                for prop_name, prop_data in data["properties"].items():
                    if prop_data.get("type") == "title" and prop_data.get("title"):
                        title = "".join([text.get("plain_text", "") for text in prop_data["title"]])
                        break
            
            # Extract content (this would require additional API call to get blocks)
            content = await self._get_page_content(page_id)
            
            return NotionPage(
                id=data["id"],
                title=title,
                content=content,
                properties=data.get("properties", {}),
                created_time=datetime.fromisoformat(data["created_time"].replace("Z", "+00:00")),
                last_edited_time=datetime.fromisoformat(data["last_edited_time"].replace("Z", "+00:00")),
                url=data.get("url", ""),
                parent_type=data.get("parent", {}).get("type", ""),
                parent_id=data.get("parent", {}).get("database_id") or data.get("parent", {}).get("page_id")
            )
        except Exception as e:
            logger.error(f"Failed to get page {page_id}: {e}")
            raise
    
    async def _get_page_content(self, page_id: str) -> str:
        """Get the content of a page by fetching its blocks."""
        try:
            blocks = await self._make_request("GET", f"/blocks/{page_id}/children")
            content_parts = []
            
            for block in blocks.get("results", []):
                content_parts.append(self._extract_block_text(block))
            
            return "\n".join(content_parts)
        except Exception as e:
            logger.error(f"Failed to get page content for {page_id}: {e}")
            return ""
    
    def _extract_block_text(self, block: Dict[str, Any]) -> str:
        """Extract text content from a Notion block."""
        block_type = block.get("type", "")
        
        if block_type == "paragraph":
            return self._extract_rich_text(block.get("paragraph", {}).get("rich_text", []))
        elif block_type == "heading_1":
            return f"# {self._extract_rich_text(block.get('heading_1', {}).get('rich_text', []))}"
        elif block_type == "heading_2":
            return f"## {self._extract_rich_text(block.get('heading_2', {}).get('rich_text', []))}"
        elif block_type == "heading_3":
            return f"### {self._extract_rich_text(block.get('heading_3', {}).get('rich_text', []))}"
        elif block_type == "bulleted_list_item":
            return f"• {self._extract_rich_text(block.get('bulleted_list_item', {}).get('rich_text', []))}"
        elif block_type == "numbered_list_item":
            return f"1. {self._extract_rich_text(block.get('numbered_list_item', {}).get('rich_text', []))}"
        elif block_type == "to_do":
            todo_data = block.get("to_do", {})
            checked = "☑" if todo_data.get("checked") else "☐"
            return f"{checked} {self._extract_rich_text(todo_data.get('rich_text', []))}"
        elif block_type == "code":
            code_data = block.get("code", {})
            language = code_data.get("language", "")
            return f"```{language}\n{self._extract_rich_text(code_data.get('rich_text', []))}\n```"
        elif block_type == "quote":
            return f"> {self._extract_rich_text(block.get('quote', {}).get('rich_text', []))}"
        
        return ""
    
    def _extract_rich_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """Extract plain text from Notion rich text array."""
        return "".join([text.get("plain_text", "") for text in rich_text])
    
    async def get_database(self, database_id: str) -> NotionDatabase:
        """Get a Notion database by ID."""
        try:
            data = await self._make_request("GET", f"/databases/{database_id}")
            
            # Extract title
            title = "Untitled Database"
            if "title" in data:
                title = "".join([text.get("plain_text", "") for text in data["title"]])
            
            return NotionDatabase(
                id=data["id"],
                title=title,
                properties=data.get("properties", {}),
                created_time=datetime.fromisoformat(data["created_time"].replace("Z", "+00:00")),
                last_edited_time=datetime.fromisoformat(data["last_edited_time"].replace("Z", "+00:00")),
                url=data.get("url", "")
            )
        except Exception as e:
            logger.error(f"Failed to get database {database_id}: {e}")
            raise
    
    async def query_database(self, database_id: str, filter_params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Query a Notion database."""
        try:
            payload = {}
            if filter_params:
                payload["filter"] = filter_params
            
            data = await self._make_request("POST", f"/databases/{database_id}/query", json=payload)
            return data.get("results", [])
        except Exception as e:
            logger.error(f"Failed to query database {database_id}: {e}")
            raise
    
    async def search(self, query: str = "", filter_params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search Notion workspace."""
        try:
            payload = {"query": query}
            if filter_params:
                payload["filter"] = filter_params
            
            data = await self._make_request("POST", "/search", json=payload)
            return data.get("results", [])
        except Exception as e:
            logger.error(f"Failed to search Notion: {e}")
            raise
    
    async def create_page(self, parent_id: str, properties: Dict[str, Any], content: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Notion page."""
        try:
            payload = {
                "parent": {"database_id": parent_id} if parent_id.startswith("database_") else {"page_id": parent_id},
                "properties": properties
            }
            
            if content:
                # Add content as blocks
                payload["children"] = self._create_content_blocks(content)
            
            data = await self._make_request("POST", "/pages", json=payload)
            return data
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            raise
    
    def _create_content_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Convert plain text content to Notion blocks."""
        lines = content.split("\n")
        blocks = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("# "):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
                })
            elif line.startswith("## "):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}
                })
            elif line.startswith("### "):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:]}}]}
                })
            elif line.startswith("• ") or line.startswith("- "):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
                })
            elif line.startswith("1. "):
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}
                })
            elif line.startswith("> "):
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
                })
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}
                })
        
        return blocks
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()

# Import asyncio for the sleep function
import asyncio 