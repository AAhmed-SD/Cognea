"""
User Collections Service
Manages user question collections, organization, and sharing features.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from services.supabase import supabase_client

logger = logging.getLogger(__name__)


class UserCollectionsService:
    """Service for managing user question collections"""

    def __init__(self):
        self.db = supabase_client

    async def create_collection(
        self, user_id: str, name: str, description: str = "", is_public: bool = False
    ) -> dict[str, Any]:
        """Create a new question collection"""
        try:
            collection_id = str(uuid4())

            collection_data = {
                "id": collection_id,
                "user_id": user_id,
                "name": name,
                "description": description,
                "is_public": is_public,
                "questions_count": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            result = (
                await self.db.table("user_question_collections")
                .insert(collection_data)
                .execute()
            )

            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to create collection")

        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise

    async def get_user_collections(self, user_id: str) -> list[dict[str, Any]]:
        """Get all collections for a user"""
        try:
            result = (
                await self.db.table("user_question_collections")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting user collections: {e}")
            return []

    async def get_collection_details(self, collection_id: str) -> dict[str, Any] | None:
        """Get detailed information about a collection"""
        try:
            result = (
                await self.db.table("user_question_collections")
                .select("*")
                .eq("id", collection_id)
                .single()
                .execute()
            )

            return result.data if result.data else None

        except Exception as e:
            logger.error(f"Error getting collection details: {e}")
            return None

    async def add_questions_to_collection(
        self, collection_id: str, question_ids: list[str]
    ) -> bool:
        """Add questions to a collection"""
        try:
            # Create collection-question relationships
            relationships = []
            for question_id in question_ids:
                relationships.append(
                    {
                        "id": str(uuid4()),
                        "collection_id": collection_id,
                        "question_id": question_id,
                        "added_at": datetime.now().isoformat(),
                    }
                )

            # Insert relationships
            await self.db.table("collection_questions").insert(relationships).execute()

            # Update collection question count
            await self._update_collection_count(collection_id)

            return True

        except Exception as e:
            logger.error(f"Error adding questions to collection: {e}")
            return False

    async def remove_questions_from_collection(
        self, collection_id: str, question_ids: list[str]
    ) -> bool:
        """Remove questions from a collection"""
        try:
            # Remove relationships
            await self.db.table("collection_questions").delete().eq(
                "collection_id", collection_id
            ).in_("question_id", question_ids).execute()

            # Update collection question count
            await self._update_collection_count(collection_id)

            return True

        except Exception as e:
            logger.error(f"Error removing questions from collection: {e}")
            return False

    async def get_collection_questions(
        self, collection_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get questions in a collection"""
        try:
            result = (
                await self.db.table("collection_questions")
                .select(
                    """
                question_id,
                added_at,
                extracted_questions (
                    id,
                    question_text,
                    question_number,
                    marks,
                    topic,
                    difficulty,
                    ai_solution,
                    ai_hints,
                    confidence_score,
                    needs_review
                )
                """
                )
                .eq("collection_id", collection_id)
                .range(offset, offset + limit - 1)
                .execute()
            )

            questions = []
            for item in result.data:
                if item.get("extracted_questions"):
                    question = item["extracted_questions"]
                    question["added_to_collection"] = item["added_at"]
                    questions.append(question)

            return questions

        except Exception as e:
            logger.error(f"Error getting collection questions: {e}")
            return []

    async def update_collection(
        self, collection_id: str, updates: dict[str, Any]
    ) -> bool:
        """Update collection details"""
        try:
            updates["updated_at"] = datetime.now().isoformat()

            await self.db.table("user_question_collections").update(updates).eq(
                "id", collection_id
            ).execute()

            return True

        except Exception as e:
            logger.error(f"Error updating collection: {e}")
            return False

    async def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection and all its relationships"""
        try:
            # Delete collection-question relationships
            await self.db.table("collection_questions").delete().eq(
                "collection_id", collection_id
            ).execute()

            # Delete collection
            await self.db.table("user_question_collections").delete().eq(
                "id", collection_id
            ).execute()

            return True

        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False

    async def search_collections(
        self, user_id: str, search_term: str
    ) -> list[dict[str, Any]]:
        """Search user's collections by name or description"""
        try:
            result = (
                await self.db.table("user_question_collections")
                .select("*")
                .eq("user_id", user_id)
                .or_(f"name.ilike.%{search_term}%,description.ilike.%{search_term}%")
                .execute()
            )

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error searching collections: {e}")
            return []

    async def get_public_collections(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get public collections from all users"""
        try:
            result = (
                await self.db.table("user_question_collections")
                .select(
                    """
                *,
                users (
                    id,
                    email
                )
                """
                )
                .eq("is_public", True)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting public collections: {e}")
            return []

    async def _update_collection_count(self, collection_id: str):
        """Update the question count for a collection"""
        try:
            # Count questions in collection
            count_result = (
                await self.db.table("collection_questions")
                .select("id", count="exact")
                .eq("collection_id", collection_id)
                .execute()
            )

            count = count_result.count if count_result.count else 0

            # Update collection
            await self.db.table("user_question_collections").update(
                {"questions_count": count, "updated_at": datetime.now().isoformat()}
            ).eq("id", collection_id).execute()

        except Exception as e:
            logger.error(f"Error updating collection count: {e}")


class SharingService:
    """Service for sharing collections and questions"""

    def __init__(self):
        self.db = supabase_client

    async def create_share_link(
        self, collection_id: str, user_id: str, expires_at: str | None = None
    ) -> dict[str, Any]:
        """Create a shareable link for a collection"""
        try:
            share_id = str(uuid4())

            share_data = {
                "id": share_id,
                "collection_id": collection_id,
                "created_by": user_id,
                "is_active": True,
                "expires_at": expires_at,
                "created_at": datetime.now().isoformat(),
            }

            result = (
                await self.db.table("collection_shares").insert(share_data).execute()
            )

            if result.data:
                share_link = f"/shared-collection/{share_id}"
                return {
                    "share_id": share_id,
                    "share_link": share_link,
                    "expires_at": expires_at,
                }
            else:
                raise Exception("Failed to create share link")

        except Exception as e:
            logger.error(f"Error creating share link: {e}")
            raise

    async def get_shared_collection(self, share_id: str) -> dict[str, Any] | None:
        """Get a shared collection by share ID"""
        try:
            result = (
                await self.db.table("collection_shares")
                .select(
                    """
                *,
                user_question_collections (
                    *,
                    users (
                        id,
                        email
                    )
                )
                """
                )
                .eq("id", share_id)
                .eq("is_active", True)
                .single()
                .execute()
            )

            if result.data:
                share_data = result.data
                collection = share_data.get("user_question_collections")

                # Check if expired
                if share_data.get("expires_at"):
                    expires_at = datetime.fromisoformat(share_data["expires_at"])
                    if datetime.now() > expires_at:
                        return None

                return collection

            return None

        except Exception as e:
            logger.error(f"Error getting shared collection: {e}")
            return None

    async def deactivate_share_link(self, share_id: str, user_id: str) -> bool:
        """Deactivate a share link"""
        try:
            await self.db.table("collection_shares").update({"is_active": False}).eq(
                "id", share_id
            ).eq("created_by", user_id).execute()

            return True

        except Exception as e:
            logger.error(f"Error deactivating share link: {e}")
            return False

    async def get_user_share_links(self, user_id: str) -> list[dict[str, Any]]:
        """Get all share links created by a user"""
        try:
            result = (
                await self.db.table("collection_shares")
                .select(
                    """
                *,
                user_question_collections (
                    id,
                    name,
                    description
                )
                """
                )
                .eq("created_by", user_id)
                .eq("is_active", True)
                .order("created_at", desc=True)
                .execute()
            )

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting user share links: {e}")
            return []


class LegalProtection:
    """Legal protection and compliance service"""

    def __init__(self):
        self.terms_of_service = """
        By uploading exam papers and creating collections, you confirm:
        
        1. OWNERSHIP: You own or have permission to use the uploaded content
        2. PERSONAL USE: Content is for personal educational use only
        3. NO REDISTRIBUTION: You won't publicly share copyrighted content
        4. RESPONSIBILITY: You accept full responsibility for content ownership
        5. COMPLIANCE: You will comply with all applicable copyright laws
        
        Violation of these terms may result in account suspension.
        """

    async def log_upload_agreement(self, user_id: str, file_name: str):
        """Log user agreement to terms for compliance"""
        try:
            await self.db.table("upload_agreements").insert(
                {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "file_name": file_name,
                    "terms_accepted": True,
                    "accepted_at": datetime.now().isoformat(),
                    "ip_address": "logged",  # Would be captured in actual implementation
                    "user_agent": "logged",  # Would be captured in actual implementation
                }
            ).execute()

        except Exception as e:
            logger.error(f"Error logging upload agreement: {e}")

    async def validate_upload_permissions(self, user_id: str) -> bool:
        """Validate user has permission to upload (rate limiting, etc.)"""
        try:
            # Check upload limits
            today = datetime.now().date().isoformat()

            upload_count = (
                await self.db.table("uploaded_papers")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .gte("upload_date", today)
                .execute()
            )

            # Allow 5 uploads per day for free users
            return upload_count.count < 5 if upload_count.count else True

        except Exception as e:
            logger.error(f"Error validating upload permissions: {e}")
            return False


# Global instances
_user_collections_service = None
_sharing_service = None
_legal_protection = None


def get_user_collections_service() -> UserCollectionsService:
    """Get the global user collections service instance"""
    global _user_collections_service
    if _user_collections_service is None:
        _user_collections_service = UserCollectionsService()
    return _user_collections_service


def get_sharing_service() -> SharingService:
    """Get the global sharing service instance"""
    global _sharing_service
    if _sharing_service is None:
        _sharing_service = SharingService()
    return _sharing_service


def get_legal_protection() -> LegalProtection:
    """Get the global legal protection service instance"""
    global _legal_protection
    if _legal_protection is None:
        _legal_protection = LegalProtection()
    return _legal_protection
