"""
Notion flashcard generator for Cognie.
Converts Notion notes and content into flashcards using AI.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict

from .notion_client import NotionClient
from services.ai.openai_service import get_openai_service
from services.cost_tracking import cost_tracking_service

logger = logging.getLogger(__name__)


class FlashcardData(BaseModel):
    """Flashcard data model."""

    model_config = ConfigDict(from_attributes=True)

    question: str
    answer: str
    tags: List[str]
    difficulty: str = "medium"
    source_page_id: Optional[str] = None
    source_page_title: Optional[str] = None
    created_at: datetime = datetime.now(UTC)


class NotionFlashcardGenerator:
    """Generates flashcards from Notion content using AI."""

    def __init__(self, notion_client: NotionClient, openai_service=None):
        """Initialize the flashcard generator."""
        self.notion_client = notion_client
        self.openai_service = openai_service or get_openai_service()
        self.cost_tracker = cost_tracking_service

    async def generate_flashcards_from_page(
        self, page_id: str, count: int = 5, difficulty: str = "medium"
    ) -> List[FlashcardData]:
        """Generate flashcards from a Notion page."""
        try:
            # Get the page content
            page = await self.notion_client.get_page(page_id)

            # Generate flashcards using AI
            flashcards = await self._generate_flashcards_with_ai(
                content=page.content,
                title=page.title,
                count=count,
                difficulty=difficulty,
                source_page_id=page_id,
                source_page_title=page.title,
            )

            # Track cost (this will be done by the OpenAI service)
            # The cost tracking is handled automatically in the OpenAI service

            return flashcards

        except Exception as e:
            logger.error(f"Failed to generate flashcards from page {page_id}: {e}")
            raise

    async def generate_flashcards_from_database(
        self, database_id: str, count: int = 10, difficulty: str = "medium"
    ) -> List[FlashcardData]:
        """Generate flashcards from a Notion database."""
        try:
            # Get database and its pages
            database = await self.notion_client.get_database(database_id)
            pages = await self.notion_client.query_database(database_id)

            all_content = []
            for page in pages:
                page_content = await self._extract_page_content_from_database_item(page)
                all_content.append(
                    {
                        "title": page.get("properties", {})
                        .get("Name", {})
                        .get("title", [{}])[0]
                        .get("plain_text", "Untitled"),
                        "content": page_content,
                    }
                )

            # Generate flashcards from all content
            flashcards = await self._generate_flashcards_from_multiple_sources(
                content_items=all_content,
                count=count,
                difficulty=difficulty,
                source_database_id=database_id,
                source_database_title=database.title,
            )

            return flashcards

        except Exception as e:
            logger.error(
                f"Failed to generate flashcards from database {database_id}: {e}"
            )
            raise

    async def _extract_page_content_from_database_item(
        self, page_data: Dict[str, Any]
    ) -> str:
        """Extract content from a database page item."""
        content_parts = []

        # Extract properties
        properties = page_data.get("properties", {})
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "rich_text":
                text = "".join(
                    [
                        text.get("plain_text", "")
                        for text in prop_data.get("rich_text", [])
                    ]
                )
                if text:
                    content_parts.append(f"{prop_name}: {text}")
            elif prop_data.get("type") == "title":
                text = "".join(
                    [text.get("plain_text", "") for text in prop_data.get("title", [])]
                )
                if text:
                    content_parts.append(f"{prop_name}: {text}")
            elif prop_data.get("type") == "select":
                select_data = prop_data.get("select", {})
                if select_data:
                    content_parts.append(f"{prop_name}: {select_data.get('name', '')}")
            elif prop_data.get("type") == "multi_select":
                multi_select = prop_data.get("multi_select", [])
                if multi_select:
                    values = [item.get("name", "") for item in multi_select]
                    content_parts.append(f"{prop_name}: {', '.join(values)}")

        return "\n".join(content_parts)

    async def _generate_flashcards_with_ai(
        self,
        content: str,
        title: str,
        count: int,
        difficulty: str,
        source_page_id: str,
        source_page_title: str,
    ) -> List[FlashcardData]:
        """Generate flashcards using OpenAI."""
        try:
            # Prepare the prompt
            prompt = self._create_flashcard_prompt(content, title, count, difficulty)

            # Generate flashcards using AI
            response = await self.openai_service.generate_content(
                prompt=prompt, max_tokens=2000, temperature=0.7
            )

            # Parse the response
            flashcards = self._parse_ai_response(
                response, source_page_id, source_page_title
            )

            return flashcards[:count]  # Ensure we don't exceed requested count

        except Exception as e:
            logger.error(f"Failed to generate flashcards with AI: {e}")
            raise

    async def _generate_flashcards_from_multiple_sources(
        self,
        content_items: List[Dict[str, str]],
        count: int,
        difficulty: str,
        source_database_id: str,
        source_database_title: str,
    ) -> List[FlashcardData]:
        """Generate flashcards from multiple content sources."""
        try:
            # Combine all content
            combined_content = "\n\n---\n\n".join(
                [
                    f"Title: {item['title']}\nContent: {item['content']}"
                    for item in content_items
                ]
            )

            # Generate flashcards
            flashcards = await self._generate_flashcards_with_ai(
                content=combined_content,
                title=f"Database: {source_database_title}",
                count=count,
                difficulty=difficulty,
                source_page_id=source_database_id,
                source_page_title=source_database_title,
            )

            return flashcards

        except Exception as e:
            logger.error(f"Failed to generate flashcards from multiple sources: {e}")
            raise

    def _create_flashcard_prompt(
        self, content: str, title: str, count: int, difficulty: str
    ) -> str:
        """Create a prompt for generating flashcards."""
        return f"""
You are an expert at creating educational flashcards from notes and content. Create {count} high-quality flashcards from the following content.

Content Title: {title}
Content:
{content}

Difficulty Level: {difficulty}

Instructions:
1. Create {count} flashcards that test understanding of key concepts
2. Questions should be clear and specific
3. Answers should be concise but complete
4. Include a mix of question types (definition, concept, application)
5. Add relevant tags for categorization
6. Format each flashcard as: Q: [question] | A: [answer] | TAGS: [comma-separated tags] | DIFFICULTY: [easy/medium/hard]

Example format:
Q: What is the main function of mitochondria? | A: Mitochondria are the powerhouse of the cell, producing energy through cellular respiration | TAGS: biology, cell biology, energy | DIFFICULTY: medium

Generate the flashcards now:
"""

    def _parse_ai_response(
        self, response: str, source_page_id: str, source_page_title: str
    ) -> List[FlashcardData]:
        """Parse AI response into FlashcardData objects."""
        flashcards = []

        # Split response into lines
        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or not line.startswith("Q:"):
                continue

            try:
                # Parse the flashcard
                flashcard = self._parse_flashcard_line(
                    line, source_page_id, source_page_title
                )
                if flashcard:
                    flashcards.append(flashcard)
            except Exception as e:
                logger.warning(f"Failed to parse flashcard line: {line}, error: {e}")
                continue

        return flashcards

    def _parse_flashcard_line(
        self, line: str, source_page_id: str, source_page_title: str
    ) -> Optional[FlashcardData]:
        """Parse a single flashcard line."""
        try:
            # Extract question
            question_match = re.search(r"Q:\s*(.*?)\s*\|\s*A:", line)
            if not question_match:
                return None
            question = question_match.group(1).strip()

            # Extract answer
            answer_match = re.search(r"A:\s*(.*?)\s*\|\s*TAGS:", line)
            if not answer_match:
                return None
            answer = answer_match.group(1).strip()

            # Extract tags
            tags_match = re.search(r"TAGS:\s*(.*?)\s*\|\s*DIFFICULTY:", line)
            tags = []
            if tags_match:
                tags_str = tags_match.group(1).strip()
                tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

            # Extract difficulty
            difficulty_match = re.search(
                r"DIFFICULTY:\s*(easy|medium|hard)", line, re.IGNORECASE
            )
            difficulty = (
                difficulty_match.group(1).lower() if difficulty_match else "medium"
            )

            return FlashcardData(
                question=question,
                answer=answer,
                tags=tags,
                difficulty=difficulty,
                source_page_id=source_page_id,
                source_page_title=source_page_title,
            )

        except Exception as e:
            logger.warning(f"Failed to parse flashcard line: {line}, error: {e}")
            return None

    async def generate_flashcards_from_text(
        self,
        text: str,
        title: str = "Manual Input",
        count: int = 5,
        difficulty: str = "medium",
    ) -> List[FlashcardData]:
        """Generate flashcards from plain text input."""
        try:
            flashcards = await self._generate_flashcards_with_ai(
                content=text,
                title=title,
                count=count,
                difficulty=difficulty,
                source_page_id="manual",
                source_page_title=title,
            )

            return flashcards

        except Exception as e:
            logger.error(f"Failed to generate flashcards from text: {e}")
            raise

    def extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content for tag generation."""
        # Simple keyword extraction (could be enhanced with NLP)
        words = re.findall(r"\b\w+\b", content.lower())
        word_freq = {}

        # Filter out common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
        }

        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Return top concepts
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10]]
