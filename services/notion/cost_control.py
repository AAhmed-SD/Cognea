"""
Cost control service for Notion flashcard generation.
Implements compression, chunking, and caching to minimize OpenAI token usage.
"""

import hashlib
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC, timedelta
import json

from services.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class CostControlService:
    """Cost control service for flashcard generation."""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.max_chunk_tokens = 1500
        self.cache_ttl_hours = 24  # Cache for 24 hours

    def compress_content(self, content: str) -> str:
        """Compress content by removing unnecessary whitespace and formatting."""
        # Remove extra whitespace
        content = re.sub(r"\s+", " ", content)

        # Remove HTML tags if present
        content = re.sub(r"<[^>]+>", "", content)

        # Remove markdown formatting (keep the text)
        content = re.sub(r"[*_`~#]+", "", content)

        # Remove URLs (keep domain names)
        content = re.sub(r"https?://[^\s]+", "", content)

        # Remove email addresses
        content = re.sub(r"\S+@\S+", "", content)

        # Remove special characters that don't add meaning
        content = re.sub(r"[^\w\s\.\,\!\?\;\:\-\(\)]", "", content)

        # Trim and normalize
        content = content.strip()

        return content

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimate: 1 token ≈ 4 characters for English text
        return len(text) // 4

    def chunk_content(self, content: str, max_tokens: int = None) -> List[str]:
        """Split content into chunks that fit within token limits."""
        if max_tokens is None:
            max_tokens = self.max_chunk_tokens

        # Compress content first
        compressed_content = self.compress_content(content)

        # Split by paragraphs first
        paragraphs = compressed_content.split("\n\n")
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Estimate tokens for current chunk + new paragraph
            test_chunk = (
                current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            )
            estimated_tokens = self.estimate_tokens(test_chunk)

            if estimated_tokens <= max_tokens:
                # Add paragraph to current chunk
                current_chunk = test_chunk
            else:
                # Current chunk is full, save it and start new one
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)

        # If we still have chunks that are too large, split by sentences
        final_chunks = []
        for chunk in chunks:
            if self.estimate_tokens(chunk) <= max_tokens:
                final_chunks.append(chunk)
            else:
                # Split by sentences
                sentences = re.split(r"[.!?]+", chunk)
                current_sentence_chunk = ""

                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    test_chunk = (
                        current_sentence_chunk + ". " + sentence
                        if current_sentence_chunk
                        else sentence
                    )
                    estimated_tokens = self.estimate_tokens(test_chunk)

                    if estimated_tokens <= max_tokens:
                        current_sentence_chunk = test_chunk
                    else:
                        if current_sentence_chunk:
                            final_chunks.append(current_sentence_chunk)
                        current_sentence_chunk = sentence

                if current_sentence_chunk:
                    final_chunks.append(current_sentence_chunk)

        return final_chunks

    def generate_cache_key(self, content: str, count: int, difficulty: str) -> str:
        """Generate a cache key for the flashcard generation request."""
        # Create a hash of the content and parameters
        cache_data = {"content": content, "count": count, "difficulty": difficulty}
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()

    async def get_cached_flashcards(self, cache_key: str) -> Optional[List[Dict]]:
        """Get cached flashcards if they exist and are not expired."""
        try:
            # Check if cache entry exists and is not expired
            cutoff_time = datetime.now(UTC) - timedelta(hours=self.cache_ttl_hours)

            result = (
                self.supabase.table("flashcard_cache")
                .select("*")
                .eq("cache_key", cache_key)
                .gte("created_at", cutoff_time.isoformat())
                .execute()
            )

            if result.data:
                cached_data = result.data[0]
                return json.loads(cached_data["flashcards"])

            return None

        except Exception as e:
            logger.error(f"Error getting cached flashcards: {e}")
            return None

    async def cache_flashcards(self, cache_key: str, flashcards: List[Dict]):
        """Cache flashcards for future use."""
        try:
            cache_data = {
                "cache_key": cache_key,
                "flashcards": json.dumps(flashcards),
                "created_at": datetime.now(UTC).isoformat(),
            }

            # Upsert to avoid duplicates
            self.supabase.table("flashcard_cache").upsert(cache_data).execute()

            logger.info(
                f"Cached {len(flashcards)} flashcards with key {cache_key[:8]}..."
            )

        except Exception as e:
            logger.error(f"Error caching flashcards: {e}")

    async def process_content_for_flashcards(
        self, content: str, title: str, count: int, difficulty: str
    ) -> Dict[str, Any]:
        """Process content for flashcard generation with cost control."""
        # Generate cache key
        cache_key = self.generate_cache_key(content, count, difficulty)

        # Check cache first
        cached_flashcards = await self.get_cached_flashcards(cache_key)
        if cached_flashcards:
            logger.info(f"Returning {len(cached_flashcards)} cached flashcards")
            return {
                "flashcards": cached_flashcards,
                "from_cache": True,
                "tokens_used": 0,
                "cost_saved": True,
            }

        # Compress and chunk content
        compressed_content = self.compress_content(content)
        chunks = self.chunk_content(compressed_content)

        logger.info(
            f"Processing content: {len(content)} chars -> {len(compressed_content)} chars -> {len(chunks)} chunks"
        )

        # Estimate tokens
        total_tokens = sum(self.estimate_tokens(chunk) for chunk in chunks)

        return {
            "compressed_content": compressed_content,
            "chunks": chunks,
            "total_tokens": total_tokens,
            "from_cache": False,
            "cache_key": cache_key,
        }

    async def save_flashcards_to_cache(self, cache_key: str, flashcards: List[Dict]):
        """Save generated flashcards to cache."""
        await self.cache_flashcards(cache_key, flashcards)

    def calculate_cost_savings(
        self, original_tokens: int, compressed_tokens: int
    ) -> Dict[str, float]:
        """Calculate cost savings from compression."""
        # OpenAI GPT-4 pricing (approximate)
        input_cost_per_1k = 0.03  # $0.03 per 1K input tokens
        output_cost_per_1k = 0.06  # $0.06 per 1K output tokens

        original_cost = (original_tokens / 1000) * input_cost_per_1k
        compressed_cost = (compressed_tokens / 1000) * input_cost_per_1k

        savings = original_cost - compressed_cost
        savings_percentage = (savings / original_cost * 100) if original_cost > 0 else 0

        return {
            "original_cost_usd": round(original_cost, 6),
            "compressed_cost_usd": round(compressed_cost, 6),
            "savings_usd": round(savings, 6),
            "savings_percentage": round(savings_percentage, 2),
        }


# Global instance
cost_control_service = CostControlService()
