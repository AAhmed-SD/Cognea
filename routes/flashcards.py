"""
Flashcards router for the Personal Agent application.
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from models.flashcard import Flashcard, FlashcardCreate, FlashcardUpdate
from services.auth import get_current_user
from services.supabase import get_supabase_client

router = APIRouter(tags=["Flashcards"])

logger = logging.getLogger(__name__)


@router.post("/", response_model=Flashcard, summary="Create a new flashcard")
async def create_flashcard(
    flashcard: FlashcardCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new flashcard for the current user."""
    try:
        supabase = get_supabase_client()

        flashcard_data = {
            "user_id": str(flashcard.user_id),
            "question": flashcard.question,
            "answer": flashcard.answer,
            "tags": flashcard.tags,
            "deck_id": str(flashcard.deck_id) if flashcard.deck_id else None,
            "deck_name": flashcard.deck_name,
            "last_reviewed_at": None,
            "next_review_date": datetime.now().isoformat(),  # Review immediately
            "ease_factor": 2.5,
            "interval": 1,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table("flashcards").insert(flashcard_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create flashcard")

        created_flashcard = result.data[0]
        return Flashcard(**created_flashcard)

    except Exception as e:
        logger.error(f"Error creating flashcard: {e}")
        raise HTTPException(status_code=500, detail="Failed to create flashcard")


@router.get("/", response_model=list[Flashcard], summary="Get flashcards for user")
async def get_flashcards(
    current_user: dict = Depends(get_current_user),
    deck_id: UUID | None = Query(None, description="Filter by deck ID"),
    deck_name: str | None = Query(None, description="Filter by deck name"),
    tags: list[str] | None = Query(None, description="Filter by tags"),
    due_for_review: bool = Query(False, description="Only return cards due for review"),
    limit: int = Query(
        100, ge=1, le=1000, description="Number of flashcards to return"
    ),
    offset: int = Query(0, ge=0, description="Number of flashcards to skip"),
):
    """Get flashcards for the current user with optional filtering."""
    try:
        supabase = get_supabase_client()

        query = (
            supabase.table("flashcards").select("*").eq("user_id", current_user["id"])
        )

        if deck_id:
            query = query.eq("deck_id", str(deck_id))
        if deck_name:
            query = query.eq("deck_name", deck_name)
        if due_for_review:
            query = query.lte("next_review_date", datetime.now().isoformat())

        query = query.range(offset, offset + limit - 1).order("created_at", desc=True)
        result = query.execute()

        flashcards = [Flashcard(**card) for card in result.data]

        # Filter by tags if specified
        if tags:
            flashcards = [
                card for card in flashcards if any(tag in card.tags for tag in tags)
            ]

        return flashcards

    except Exception as e:
        logger.error(f"Error fetching flashcards: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch flashcards")


@router.get(
    "/{flashcard_id}", response_model=Flashcard, summary="Get a specific flashcard"
)
async def get_flashcard(
    flashcard_id: UUID, current_user: dict = Depends(get_current_user)
):
    """Get a specific flashcard by ID."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("flashcards")
            .select("*")
            .eq("id", str(flashcard_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Flashcard not found")

        return Flashcard(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching flashcard {flashcard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch flashcard")


@router.put("/{flashcard_id}", response_model=Flashcard, summary="Update a flashcard")
async def update_flashcard(
    flashcard_id: UUID,
    flashcard_update: FlashcardUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a specific flashcard."""
    try:
        supabase = get_supabase_client()

        # First check if flashcard exists and belongs to user
        existing = (
            supabase.table("flashcards")
            .select("*")
            .eq("id", str(flashcard_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Flashcard not found")

        # Prepare update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}

        if flashcard_update.question is not None:
            update_data["question"] = flashcard_update.question
        if flashcard_update.answer is not None:
            update_data["answer"] = flashcard_update.answer
        if flashcard_update.tags is not None:
            update_data["tags"] = flashcard_update.tags
        if flashcard_update.deck_id is not None:
            update_data["deck_id"] = str(flashcard_update.deck_id)
        if flashcard_update.deck_name is not None:
            update_data["deck_name"] = flashcard_update.deck_name
        if flashcard_update.last_reviewed_at is not None:
            update_data["last_reviewed_at"] = (
                flashcard_update.last_reviewed_at.isoformat()
            )
        if flashcard_update.next_review_date is not None:
            update_data["next_review_date"] = (
                flashcard_update.next_review_date.isoformat()
            )
        if flashcard_update.ease_factor is not None:
            update_data["ease_factor"] = flashcard_update.ease_factor
        if flashcard_update.interval is not None:
            update_data["interval"] = flashcard_update.interval

        result = (
            supabase.table("flashcards")
            .update(update_data)
            .eq("id", str(flashcard_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update flashcard")

        return Flashcard(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating flashcard {flashcard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update flashcard")


@router.delete("/{flashcard_id}", summary="Delete a flashcard")
async def delete_flashcard(
    flashcard_id: UUID, current_user: dict = Depends(get_current_user)
):
    """Delete a specific flashcard."""
    try:
        supabase = get_supabase_client()

        # Check if flashcard exists and belongs to user
        existing = (
            supabase.table("flashcards")
            .select("*")
            .eq("id", str(flashcard_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Flashcard not found")

        result = (  # noqa: F841
            supabase.table("flashcards")
            .delete()
            .eq("id", str(flashcard_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        return {"message": "Flashcard deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting flashcard {flashcard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete flashcard")


@router.post(
    "/{flashcard_id}/review", response_model=Flashcard, summary="Review a flashcard"
)
async def review_flashcard(
    flashcard_id: UUID,
    quality: int = Query(
        ..., ge=0, le=5, description="Review quality (0-5, where 5 is perfect)"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Review a flashcard using spaced repetition algorithm."""
    try:
        supabase = get_supabase_client()

        # Get current flashcard
        existing = (
            supabase.table("flashcards")
            .select("*")
            .eq("id", str(flashcard_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Flashcard not found")

        current_card = existing.data[0]
        current_ease_factor = current_card.get("ease_factor", 2.5)
        current_interval = current_card.get("interval", 1)

        # Calculate new interval and ease factor based on quality
        if quality >= 3:  # Good response
            if current_interval == 1:
                new_interval = 6
            else:
                new_interval = int(current_interval * current_ease_factor)
            new_ease_factor = current_ease_factor + (
                0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
            )
        else:  # Poor response
            new_interval = 1
            new_ease_factor = max(1.3, current_ease_factor - 0.2)

        # Calculate next review date
        next_review = datetime.now() + timedelta(days=new_interval)

        update_data = {
            "last_reviewed_at": datetime.now().isoformat(),
            "next_review_date": next_review.isoformat(),
            "ease_factor": round(new_ease_factor, 2),
            "interval": new_interval,
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = (
            supabase.table("flashcards")
            .update(update_data)
            .eq("id", str(flashcard_id))
            .eq("user_id", current_user["id"])
            .execute()
        )

        return Flashcard(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing flashcard {flashcard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to review flashcard")


@router.get(
    "/due/review",
    response_model=list[Flashcard],
    summary="Get flashcards due for review",
)
async def get_due_flashcards(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100, description="Number of cards to return"),
):
    """Get flashcards that are due for review."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("flashcards")
            .select("*")
            .eq("user_id", current_user["id"])
            .lte("next_review_date", datetime.now().isoformat())
            .order("next_review_date", desc=False)
            .limit(limit)
            .execute()
        )

        flashcards = [Flashcard(**card) for card in result.data]
        return flashcards

    except Exception as e:
        logger.error(f"Error fetching due flashcards: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch due flashcards")


@router.get("/decks/list", summary="Get list of flashcard decks")
async def get_flashcard_decks(current_user: dict = Depends(get_current_user)):
    """Get all flashcard decks for the current user."""
    try:
        supabase = get_supabase_client()

        result = (
            supabase.table("flashcards")
            .select("deck_id, deck_name")
            .eq("user_id", current_user["id"])
            .not_.is_("deck_id", "null")
            .execute()
        )

        # Group by deck
        decks = {}
        for card in result.data:
            deck_id = card["deck_id"]
            deck_name = card["deck_name"] or "Untitled Deck"

            if deck_id not in decks:
                decks[deck_id] = {
                    "deck_id": deck_id,
                    "deck_name": deck_name,
                    "card_count": 0,
                }
            decks[deck_id]["card_count"] += 1

        return list(decks.values())

    except Exception as e:
        logger.error(f"Error fetching flashcard decks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch flashcard decks")


@router.get("/stats/summary", summary="Get flashcard statistics")
async def get_flashcard_stats(current_user: dict = Depends(get_current_user)):
    """Get flashcard statistics for the current user."""
    try:
        supabase = get_supabase_client()

        # Get all flashcards for user
        result = (
            supabase.table("flashcards")
            .select("*")
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not result.data:
            return {
                "total_cards": 0,
                "due_cards": 0,
                "total_decks": 0,
                "average_ease_factor": 0.0,
                "cards_reviewed_today": 0,
            }

        cards = result.data
        total_cards = len(cards)
        due_cards = len(
            [
                c
                for c in cards
                if c.get("next_review_date")
                and datetime.fromisoformat(c["next_review_date"].replace("Z", "+00:00"))
                <= datetime.now()
            ]
        )

        # Count unique decks
        decks = set()
        for card in cards:
            if card.get("deck_id"):
                decks.add(card["deck_id"])
        total_decks = len(decks)

        # Calculate average ease factor
        ease_factors = [c.get("ease_factor", 2.5) for c in cards]
        average_ease_factor = (
            sum(ease_factors) / len(ease_factors) if ease_factors else 0
        )

        # Count cards reviewed today
        today = datetime.now().date()
        cards_reviewed_today = 0
        for card in cards:
            if card.get("last_reviewed_at"):
                review_date = datetime.fromisoformat(
                    card["last_reviewed_at"].replace("Z", "+00:00")
                ).date()
                if review_date == today:
                    cards_reviewed_today += 1

        return {
            "total_cards": total_cards,
            "due_cards": due_cards,
            "total_decks": total_decks,
            "average_ease_factor": round(average_ease_factor, 2),
            "cards_reviewed_today": cards_reviewed_today,
        }

    except Exception as e:
        logger.error(f"Error fetching flashcard stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch flashcard statistics"
        )
