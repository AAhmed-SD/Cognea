"""
Base AI Client - Abstract base class for all AI providers
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Standardized AI response format"""

    content: str
    model_used: str
    provider: str
    tokens_used: int
    cost_usd: float
    quality_score: float
    response_time_ms: int
    metadata: dict[str, Any] | None = None


class BaseAIClient(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url
        self.is_healthy = True
        self.last_error = None
        self.error_count = 0
        self.max_retries = 3

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        """Generate response from the AI model"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the model is available"""
        pass

    @abstractmethod
    def get_cost_estimate(self, prompt: str) -> float:
        """Estimate cost for the given prompt"""
        pass

    async def health_check(self) -> bool:
        """Perform health check on the provider"""
        try:
            return await self.is_available()
        except Exception as e:
            logger.error(f"Health check failed for {self.__class__.__name__}: {e}")
            self.is_healthy = False
            return False

    def _calculate_quality_score(self, response: str, prompt: str) -> float:
        """
        Calculate quality score for the response
        This is a basic implementation - can be enhanced with more sophisticated metrics
        """
        try:
            # Basic quality metrics
            response_length = len(response.strip())
            prompt_length = len(prompt.strip())

            # Check for empty or very short responses
            if response_length < 10:
                return 0.1

            # Check for reasonable response length
            if response_length < prompt_length * 0.1:
                return 0.3

            # Check for coherent response (basic check)
            if response.strip().endswith("...") or response.strip().endswith(".."):
                return 0.6

            # Base quality score
            base_score = 0.8

            # Adjust based on response characteristics
            if response_length > prompt_length * 2:
                base_score += 0.1  # Detailed response

            if any(
                keyword in response.lower()
                for keyword in ["because", "therefore", "however", "although"]
            ):
                base_score += 0.05  # Logical connectors

            return min(base_score, 1.0)

        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.5

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                self.error_count += 1
                self.last_error = str(e)

                if attempt == self.max_retries - 1:
                    raise e

                # Exponential backoff
                wait_time = 2**attempt
                logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}"
                )
                await asyncio.sleep(wait_time)

    def get_provider_info(self) -> dict[str, Any]:
        """Get provider information"""
        return {
            "name": self.__class__.__name__,
            "is_healthy": self.is_healthy,
            "error_count": self.error_count,
            "last_error": self.last_error,
        }
