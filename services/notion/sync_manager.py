"""
Notion sync manager for Cognie.
Handles two-way synchronization between Cognie and Notion.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC, timedelta
from pydantic import BaseModel, ConfigDict
from enum import Enum
import asyncio

from .notion_client import NotionClient
from .flashcard_generator import NotionFlashcardGenerator, FlashcardData
from services.supabase import get_supabase_client
from services.rate_limited_queue import get_notion_queue

logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """Sync direction enumeration."""

    NOTION_TO_COGNIE = "notion_to_cognie"
    COGNIE_TO_NOTION = "cognie_to_notion"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(BaseModel):
    """Sync status model."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    notion_page_id: str
    last_sync_time: datetime
    sync_direction: str  # "notion_to_cognie", "cognie_to_notion", "bidirectional"
    status: str  # "success", "failed", "in_progress", "conflict_resolved"
    error_message: Optional[str] = None
    items_synced: int = 0
    conflicts_resolved: int = 0
    retry_count: int = 0
    sync_version: str = "1.0"


class ConflictResolution(BaseModel):
    """Conflict resolution strategy."""

    strategy: str  # "notion_wins", "cognie_wins", "manual", "merge"
    resolved_at: datetime
    resolved_by: str
    details: Optional[Dict[str, Any]] = None


class NotionSyncManager:
    """Enhanced manager for synchronization between Cognie and Notion."""

    def __init__(
        self, notion_client: NotionClient, flashcard_generator: NotionFlashcardGenerator
    ):
        """Initialize the sync manager."""
        self.notion_client = notion_client
        self.flashcard_generator = flashcard_generator
        self.supabase = get_supabase_client()
        self.sync_cache = {}  # Cache for incremental sync
        self.conflict_resolutions = {}  # Track conflict resolutions

    async def sync_page_to_flashcards(
        self,
        user_id: str,
        notion_page_id: str,
        sync_direction: str = "notion_to_cognie",
        incremental: bool = True,
        conflict_strategy: str = "notion_wins",
    ) -> SyncStatus:
        """Sync a Notion page to Cognie flashcards with enhanced error recovery and incremental sync."""
        sync_status = SyncStatus(
            user_id=user_id,
            notion_page_id=notion_page_id,
            last_sync_time=datetime.now(UTC),
            sync_direction=sync_direction,
            status="in_progress",
            retry_count=0,
        )

        try:
            # Get local last_synced_ts
            local_last_synced_ts = await self._get_local_last_synced_ts(
                user_id, notion_page_id
            )

            # Get Notion page using the rate-limited queue with retry logic
            page = await self._get_notion_page_with_retry(notion_page_id)
            notion_last_edited = page.last_edited_time.isoformat()

            # Incremental sync check
            if (
                incremental
                and local_last_synced_ts
                and notion_last_edited <= local_last_synced_ts
            ):
                logger.info(f"No new changes to sync for page {notion_page_id}")
                sync_status.status = "success"
                sync_status.items_synced = 0
                await self._save_sync_status(sync_status)
                return sync_status

            # Check for conflicts in bidirectional sync
            if sync_direction == SyncDirection.BIDIRECTIONAL.value:
                conflicts = await self._detect_conflicts(user_id, notion_page_id, page)
                if conflicts:
                    resolved_count = await self._resolve_conflicts(
                        conflicts, conflict_strategy, user_id
                    )
                    sync_status.conflicts_resolved = resolved_count

            # Generate flashcards with error handling
            flashcards = await self._generate_flashcards_with_retry(
                notion_page_id, count=10, difficulty="medium"
            )

            # Save flashcards with conflict resolution
            saved_flashcards = await self._save_flashcards_with_conflict_resolution(
                user_id, flashcards, notion_last_edited
            )

            # Update sync status
            sync_status.status = "success"
            sync_status.items_synced = len(saved_flashcards)
            await self._save_sync_status(sync_status)

            logger.info(
                f"Successfully synced {len(saved_flashcards)} flashcards from Notion page {notion_page_id}"
            )
            return sync_status

        except Exception as e:
            logger.error(f"Failed to sync page {notion_page_id}: {e}")
            sync_status.status = "failed"
            sync_status.error_message = str(e)
            sync_status.retry_count += 1
            await self._save_sync_status(sync_status)

            # Implement retry logic for recoverable errors
            if self._is_recoverable_error(e) and sync_status.retry_count < 3:
                await self._schedule_retry(user_id, notion_page_id, sync_direction)

            raise

    async def _get_notion_page_with_retry(
        self, page_id: str, max_retries: int = 3
    ) -> Any:
        """Get Notion page with retry logic for network errors."""
        for attempt in range(max_retries):
            try:
                notion_queue = get_notion_queue()
                result_future = await notion_queue.enqueue_request(
                    method="GET",
                    endpoint=f"pages/{page_id}",
                    api_key=self.notion_client.api_key,
                )
                return await result_future
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                if self._is_recoverable_error(e):
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for page {page_id}: {e}"
                    )
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    raise

    async def _generate_flashcards_with_retry(
        self,
        page_id: str,
        count: int = 10,
        difficulty: str = "medium",
        max_retries: int = 3,
    ) -> List[FlashcardData]:
        """Generate flashcards with retry logic."""
        for attempt in range(max_retries):
            try:
                return await self.flashcard_generator.generate_flashcards_from_page(
                    page_id=page_id, count=count, difficulty=difficulty
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                if self._is_recoverable_error(e):
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for flashcard generation: {e}"
                    )
                    await asyncio.sleep(2**attempt)
                else:
                    raise

    async def _detect_conflicts(
        self, user_id: str, notion_page_id: str, notion_page: Any
    ) -> List[Dict[str, Any]]:
        """Detect conflicts between Notion and Cognie data."""
        conflicts = []

        try:
            # Get local flashcards for this page
            local_flashcards = (
                self.supabase.table("flashcards")
                .select("*")
                .eq("user_id", user_id)
                .eq("source_page_id", notion_page_id)
                .execute()
            )

            if not local_flashcards.data:
                return conflicts

            # Compare timestamps and content
            for flashcard in local_flashcards.data:
                local_updated = flashcard.get("updated_at")
                notion_updated = notion_page.last_edited_time.isoformat()

                # Check if there are conflicting changes
                if local_updated and notion_updated:
                    local_dt = datetime.fromisoformat(
                        local_updated.replace("Z", "+00:00")
                    )
                    notion_dt = datetime.fromisoformat(
                        notion_updated.replace("Z", "+00:00")
                    )

                    # If both were updated within a short time window, potential conflict
                    if abs((local_dt - notion_dt).total_seconds()) < 300:  # 5 minutes
                        conflicts.append(
                            {
                                "flashcard_id": flashcard["id"],
                                "local_content": flashcard.get("content"),
                                "notion_content": notion_page.properties.get(
                                    "title", {}
                                )
                                .get("title", [{}])[0]
                                .get("plain_text", ""),
                                "local_updated": local_updated,
                                "notion_updated": notion_updated,
                                "conflict_type": "content_mismatch",
                            }
                        )

        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")

        return conflicts

    async def _resolve_conflicts(
        self, conflicts: List[Dict[str, Any]], strategy: str, user_id: str
    ) -> int:
        """Resolve conflicts using the specified strategy."""
        resolved_count = 0

        for conflict in conflicts:
            try:
                resolution = ConflictResolution(
                    strategy=strategy,
                    resolved_at=datetime.now(UTC),
                    resolved_by="system",
                    details=conflict,
                )

                if strategy == "notion_wins":
                    # Update local flashcard with Notion content
                    await self._update_flashcard_content(
                        conflict["flashcard_id"], conflict["notion_content"]
                    )
                elif strategy == "cognie_wins":
                    # Keep local content, mark as resolved
                    pass
                elif strategy == "merge":
                    # Merge content intelligently
                    merged_content = await self._merge_content(
                        conflict["local_content"], conflict["notion_content"]
                    )
                    await self._update_flashcard_content(
                        conflict["flashcard_id"], merged_content
                    )

                # Record resolution
                self.conflict_resolutions[conflict["flashcard_id"]] = resolution
                resolved_count += 1

            except Exception as e:
                logger.error(
                    f"Error resolving conflict for flashcard {conflict['flashcard_id']}: {e}"
                )

        return resolved_count

    async def _merge_content(self, local_content: str, notion_content: str) -> str:
        """Intelligently merge conflicting content."""
        # Simple merge strategy - combine unique parts
        local_lines = set(local_content.split("\n"))
        notion_lines = set(notion_content.split("\n"))

        # Combine unique lines
        merged_lines = list(local_lines.union(notion_lines))
        merged_lines.sort()  # Sort for consistency

        return "\n".join(merged_lines)

    async def _update_flashcard_content(self, flashcard_id: str, new_content: str):
        """Update flashcard content in database."""
        self.supabase.table("flashcards").update(
            {
                "content": new_content,
                "updated_at": datetime.now(UTC).isoformat(),
                "updated_by": "conflict-resolution",
            }
        ).eq("id", flashcard_id).execute()

    async def _save_flashcards_with_conflict_resolution(
        self, user_id: str, flashcards: List[FlashcardData], notion_last_edited: str
    ) -> List[Dict[str, Any]]:
        """Save flashcards with conflict resolution."""
        saved_flashcards = []

        for flashcard in flashcards:
            try:
                saved_flashcard = await self._save_flashcard_to_cognie(
                    user_id, flashcard
                )
                if saved_flashcard:
                    # Update last_synced_ts
                    self.supabase.table("flashcards").update(
                        {
                            "last_synced_ts": notion_last_edited,
                            "updated_by": "cognie-sync",
                        }
                    ).eq("id", saved_flashcard["id"]).execute()
                    saved_flashcards.append(saved_flashcard)
            except Exception as e:
                logger.error(f"Error saving flashcard: {e}")
                # Continue with other flashcards

        return saved_flashcards

    async def _get_local_last_synced_ts(
        self, user_id: str, notion_page_id: str
    ) -> Optional[str]:
        """Get local last synced timestamp."""
        try:
            local_flashcard = (
                self.supabase.table("flashcards")
                .select("last_synced_ts")
                .eq("user_id", user_id)
                .eq("source_page_id", notion_page_id)
                .order("last_synced_ts", desc=True)
                .limit(1)
                .execute()
            )

            if local_flashcard.data:
                return local_flashcard.data[0].get("last_synced_ts")
        except Exception as e:
            logger.error(f"Error getting local last synced timestamp: {e}")

        return None

    def _is_recoverable_error(self, error: Exception) -> bool:
        """Check if error is recoverable (network, timeout, rate limit)."""
        error_message = str(error).lower()
        recoverable_keywords = [
            "timeout",
            "connection",
            "network",
            "rate limit",
            "temporary",
            "service unavailable",
        ]
        return any(keyword in error_message for keyword in recoverable_keywords)

    async def _schedule_retry(
        self, user_id: str, notion_page_id: str, sync_direction: str
    ):
        """Schedule a retry for failed sync."""
        try:
            # Add to retry queue with exponential backoff
            retry_delay = 300  # 5 minutes
            retry_time = datetime.now(UTC) + timedelta(seconds=retry_delay)

            # Store retry information
            retry_info = {
                "user_id": user_id,
                "notion_page_id": notion_page_id,
                "sync_direction": sync_direction,
                "retry_time": retry_time.isoformat(),
                "attempt": 1,
            }

            # Store in database or cache for later processing
            self.supabase.table("sync_retries").insert(retry_info).execute()

            logger.info(f"Scheduled retry for page {notion_page_id} at {retry_time}")

        except Exception as e:
            logger.error(f"Error scheduling retry: {e}")

    async def get_sync_health_status(self, user_id: str) -> Dict[str, Any]:
        """Get sync health status for a user."""
        try:
            # Get recent sync history
            recent_syncs = await self.get_user_sync_history(user_id, limit=10)

            # Calculate success rate
            total_syncs = len(recent_syncs)
            successful_syncs = len([s for s in recent_syncs if s.status == "success"])
            success_rate = (
                (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
            )

            # Check for recent conflicts
            recent_conflicts = len(
                [s for s in recent_syncs if s.conflicts_resolved > 0]
            )

            # Determine overall health
            if success_rate >= 90:
                health_status = "healthy"
            elif success_rate >= 70:
                health_status = "degraded"
            else:
                health_status = "unhealthy"

            return {
                "status": health_status,
                "success_rate": success_rate,
                "total_syncs": total_syncs,
                "successful_syncs": successful_syncs,
                "recent_conflicts": recent_conflicts,
                "last_sync": recent_syncs[0].last_sync_time if recent_syncs else None,
                "pending_retries": await self._get_pending_retries_count(user_id),
            }

        except Exception as e:
            logger.error(f"Error getting sync health status: {e}")
            return {"status": "unknown", "error": str(e)}

    async def _get_pending_retries_count(self, user_id: str) -> int:
        """Get count of pending retries for a user."""
        try:
            result = (
                self.supabase.table("sync_retries")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            return result.count or 0
        except Exception:
            return 0

    async def sync_database_to_flashcards(
        self,
        user_id: str,
        notion_database_id: str,
        sync_direction: str = "notion_to_cognie",
    ) -> SyncStatus:
        """Sync a Notion database to Cognie flashcards."""
        try:
            # Create sync status
            sync_status = SyncStatus(
                user_id=user_id,
                notion_page_id=notion_database_id,  # Using page_id field for database_id
                last_sync_time=datetime.now(UTC),
                sync_direction=sync_direction,
                status="in_progress",
            )

            # Generate flashcards from database
            flashcards = (
                await self.flashcard_generator.generate_flashcards_from_database(
                    database_id=notion_database_id,
                    count=20,  # More flashcards for databases
                    difficulty="medium",
                )
            )

            # Save flashcards to Cognie database
            saved_flashcards = []
            for flashcard in flashcards:
                saved_flashcard = await self._save_flashcard_to_cognie(
                    user_id, flashcard
                )
                if saved_flashcard:
                    saved_flashcards.append(saved_flashcard)

            # Update sync status
            sync_status.status = "success"
            sync_status.items_synced = len(saved_flashcards)

            # Save sync status
            await self._save_sync_status(sync_status)

            logger.info(
                f"Successfully synced {len(saved_flashcards)} flashcards from Notion database {notion_database_id}"
            )
            return sync_status

        except Exception as e:
            logger.error(f"Failed to sync database {notion_database_id}: {e}")

            # Update sync status with error
            sync_status.status = "failed"
            sync_status.error_message = str(e)
            await self._save_sync_status(sync_status)

            raise

    async def sync_flashcards_to_notion(
        self, user_id: str, flashcard_ids: List[str], target_page_id: str
    ) -> SyncStatus:
        """Sync Cognie flashcards back to Notion."""
        try:
            # Create sync status
            sync_status = SyncStatus(
                user_id=user_id,
                notion_page_id=target_page_id,
                last_sync_time=datetime.now(UTC),
                sync_direction="cognie_to_notion",
                status="in_progress",
            )

            # Get flashcards from Cognie
            flashcards = await self._get_flashcards_from_cognie(user_id, flashcard_ids)

            # Create content for Notion
            content = self._create_notion_content_from_flashcards(flashcards)

            # Create or update Notion page
            await self.notion_client.create_page(
                parent_id=target_page_id,
                properties={
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": f"Flashcards - {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"
                                }
                            }
                        ]
                    }
                },
                content=content,
            )

            # Update sync status
            sync_status.status = "success"
            sync_status.items_synced = len(flashcards)

            # Save sync status
            await self._save_sync_status(sync_status)

            logger.info(
                f"Successfully synced {len(flashcards)} flashcards to Notion page {target_page_id}"
            )
            return sync_status

        except Exception as e:
            logger.error(f"Failed to sync flashcards to Notion: {e}")

            # Update sync status with error
            sync_status.status = "failed"
            sync_status.error_message = str(e)
            await self._save_sync_status(sync_status)

            raise

    async def _save_flashcard_to_cognie(
        self, user_id: str, flashcard: FlashcardData
    ) -> Optional[Dict[str, Any]]:
        """Save a flashcard to the Cognie database."""
        try:
            flashcard_data = {
                "user_id": user_id,
                "question": flashcard.question,
                "answer": flashcard.answer,
                "tags": flashcard.tags,
                "difficulty": flashcard.difficulty,
                "source_page_id": flashcard.source_page_id,
                "source_page_title": flashcard.source_page_title,
                "created_at": flashcard.created_at.isoformat(),
                "updated_at": flashcard.created_at.isoformat(),
            }

            result = self.supabase.table("flashcards").insert(flashcard_data).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Failed to save flashcard to Cognie: {e}")
            return None

    async def _get_flashcards_from_cognie(
        self, user_id: str, flashcard_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Get flashcards from Cognie database."""
        try:
            result = (
                self.supabase.table("flashcards")
                .select("*")
                .eq("user_id", user_id)
                .in_("id", flashcard_ids)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get flashcards from Cognie: {e}")
            return []

    def _create_notion_content_from_flashcards(
        self, flashcards: List[Dict[str, Any]]
    ) -> str:
        """Create Notion content from flashcards."""
        content_lines = []

        for i, flashcard in enumerate(flashcards, 1):
            content_lines.append(f"## Flashcard {i}")
            content_lines.append(f"**Question:** {flashcard.get('question', '')}")
            content_lines.append(f"**Answer:** {flashcard.get('answer', '')}")

            tags = flashcard.get("tags", [])
            if tags:
                content_lines.append(f"**Tags:** {', '.join(tags)}")

            difficulty = flashcard.get("difficulty", "medium")
            content_lines.append(f"**Difficulty:** {difficulty}")
            content_lines.append("")  # Empty line for spacing

        return "\n".join(content_lines)

    async def _save_sync_status(self, sync_status: SyncStatus):
        """Save sync status to database."""
        try:
            sync_data = {
                "user_id": sync_status.user_id,
                "notion_page_id": sync_status.notion_page_id,
                "last_sync_time": sync_status.last_sync_time.isoformat(),
                "sync_direction": sync_status.sync_direction,
                "status": sync_status.status,
                "error_message": sync_status.error_message,
                "items_synced": sync_status.items_synced,
                "updated_by": "cognie-sync",
            }

            # Check if sync status already exists
            existing = (
                self.supabase.table("notion_sync_status")
                .select("*")
                .eq("user_id", sync_status.user_id)
                .eq("notion_page_id", sync_status.notion_page_id)
                .execute()
            )

            if existing.data:
                # Update existing
                self.supabase.table("notion_sync_status").update(sync_data).eq(
                    "user_id", sync_status.user_id
                ).eq("notion_page_id", sync_status.notion_page_id).execute()
            else:
                # Insert new
                self.supabase.table("notion_sync_status").insert(sync_data).execute()

        except Exception as e:
            logger.error(f"Failed to save sync status: {e}")

    async def get_sync_status(
        self, user_id: str, notion_page_id: str
    ) -> Optional[SyncStatus]:
        """Get sync status for a specific page."""
        try:
            result = (
                self.supabase.table("notion_sync_status")
                .select("*")
                .eq("user_id", user_id)
                .eq("notion_page_id", notion_page_id)
                .execute()
            )

            if result.data:
                data = result.data[0]
                return SyncStatus(
                    user_id=data["user_id"],
                    notion_page_id=data["notion_page_id"],
                    last_sync_time=datetime.fromisoformat(data["last_sync_time"]),
                    sync_direction=data["sync_direction"],
                    status=data["status"],
                    error_message=data.get("error_message"),
                    items_synced=data.get("items_synced", 0),
                )
            return None

        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return None

    async def get_user_sync_history(self, user_id: str) -> List[SyncStatus]:
        """Get sync history for a user."""
        try:
            result = (
                self.supabase.table("notion_sync_status")
                .select("*")
                .eq("user_id", user_id)
                .order("last_sync_time", desc=True)
                .execute()
            )

            sync_statuses = []
            for data in result.data or []:
                sync_statuses.append(
                    SyncStatus(
                        user_id=data["user_id"],
                        notion_page_id=data["notion_page_id"],
                        last_sync_time=datetime.fromisoformat(data["last_sync_time"]),
                        sync_direction=data["sync_direction"],
                        status=data["status"],
                        error_message=data.get("error_message"),
                        items_synced=data.get("items_synced", 0),
                    )
                )

            return sync_statuses

        except Exception as e:
            logger.error(f"Failed to get user sync history: {e}")
            return []

    async def setup_webhook(self, user_id: str, page_id: str, webhook_url: str) -> bool:
        """Setup Notion webhook for real-time sync (placeholder for future implementation)."""
        # This would require Notion's webhook API which is currently in beta
        # For now, we'll implement manual sync
        logger.info(f"Webhook setup requested for user {user_id}, page {page_id}")
        return True
