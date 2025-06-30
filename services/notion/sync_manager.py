"""
Notion sync manager for Cognie.
Handles two-way synchronization between Cognie and Notion.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict

from .notion_client import NotionClient
from .flashcard_generator import NotionFlashcardGenerator, FlashcardData
from services.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class SyncStatus(BaseModel):
    """Sync status model."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    notion_page_id: str
    last_sync_time: datetime
    sync_direction: str  # "notion_to_cognie", "cognie_to_notion", "bidirectional"
    status: str  # "success", "failed", "in_progress"
    error_message: Optional[str] = None
    items_synced: int = 0


class NotionSyncManager:
    """Manages synchronization between Cognie and Notion."""

    def __init__(
        self, notion_client: NotionClient, flashcard_generator: NotionFlashcardGenerator
    ):
        """Initialize the sync manager."""
        self.notion_client = notion_client
        self.flashcard_generator = flashcard_generator
        self.supabase = get_supabase_client()

    async def sync_page_to_flashcards(
        self,
        user_id: str,
        notion_page_id: str,
        sync_direction: str = "notion_to_cognie",
    ) -> SyncStatus:
        """Sync a Notion page to Cognie flashcards with debounce/echo prevention."""
        try:
            # Get local last_synced_ts
            local_flashcard = (
                self.supabase.table("flashcards")
                .select("last_synced_ts")
                .eq("user_id", user_id)
                .eq("source_page_id", notion_page_id)
                .order("last_synced_ts", desc=True)
                .limit(1)
                .execute()
            )
            local_last_synced_ts = None
            if local_flashcard.data:
                local_last_synced_ts = local_flashcard.data[0].get("last_synced_ts")

            # Get Notion page
            page = await self.notion_client.get_page(notion_page_id)
            notion_last_edited = page.last_edited_time.isoformat()

            # Debounce: Only sync if Notion's last_edited_time > local last_synced_ts
            if local_last_synced_ts and notion_last_edited <= local_last_synced_ts:
                logger.info(f"No new changes to sync for page {notion_page_id}")
                return SyncStatus(
                    user_id=user_id,
                    notion_page_id=notion_page_id,
                    last_sync_time=datetime.now(UTC),
                    sync_direction=sync_direction,
                    status="success",
                    error_message=None,
                    items_synced=0,
                )

            # Generate flashcards
            flashcards = await self.flashcard_generator.generate_flashcards_from_page(
                page_id=notion_page_id, count=10, difficulty="medium"  # Default count
            )

            # Save flashcards to Cognie database and update last_synced_ts
            saved_flashcards = []
            for flashcard in flashcards:
                saved_flashcard = await self._save_flashcard_to_cognie(
                    user_id, flashcard
                )
                if saved_flashcard:
                    # Update last_synced_ts
                    self.supabase.table("flashcards").update(
                        {
                            "last_synced_ts": page.last_edited_time.isoformat(),
                            "updated_by": "cognie-sync",
                        }
                    ).eq("id", saved_flashcard["id"]).execute()
                    saved_flashcards.append(saved_flashcard)

            # Update sync status
            sync_status = SyncStatus(
                user_id=user_id,
                notion_page_id=notion_page_id,
                last_sync_time=datetime.now(UTC),
                sync_direction=sync_direction,
                status="success",
                error_message=None,
                items_synced=len(saved_flashcards),
            )
            await self._save_sync_status(sync_status)
            logger.info(
                f"Successfully synced {len(saved_flashcards)} flashcards from Notion page {notion_page_id}"
            )
            return sync_status
        except Exception as e:
            logger.error(f"Failed to sync page {notion_page_id}: {e}")
            sync_status = SyncStatus(
                user_id=user_id,
                notion_page_id=notion_page_id,
                last_sync_time=datetime.now(UTC),
                sync_direction=sync_direction,
                status="failed",
                error_message=str(e),
                items_synced=0,
            )
            await self._save_sync_status(sync_status)
            raise

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
