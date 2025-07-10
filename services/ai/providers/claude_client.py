"""
Claude API Client
Implements Anthropic Claude API integration for high-quality AI responses.
"""

import logging
import os
import time

import aiohttp

from .base_client import AIResponse, BaseAIClient

logger = logging.getLogger(__name__)


class ClaudeClient(BaseAIClient):
    """Claude API client implementation"""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        super().__init__(api_key=api_key, base_url="https://api.anthropic.com/v1")

        # Claude pricing (as of 2024) - Haiku model
        self.input_cost_per_1m_tokens = 0.25  # $0.25 per 1M input tokens
        self.output_cost_per_1m_tokens = 1.25  # $1.25 per 1M output tokens

        # Default model
        self.default_model = "claude-3-haiku-20240307"

    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        """Generate response using Claude API"""
        start_time = time.time()

        model = kwargs.get("model", self.default_model)
        max_tokens = kwargs.get("max_tokens", 2048)
        temperature = kwargs.get("temperature", 0.7)

        # Prepare request payload
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Claude API error: {response.status} - {error_text}"
                        )

                    data = await response.json()

                    # Extract response content
                    content = data["content"][0]["text"]

                    # Calculate usage
                    usage = data.get("usage", {})
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    total_tokens = input_tokens + output_tokens

                    # Calculate cost
                    input_cost = (
                        input_tokens / 1_000_000
                    ) * self.input_cost_per_1m_tokens
                    output_cost = (
                        output_tokens / 1_000_000
                    ) * self.output_cost_per_1m_tokens
                    total_cost = input_cost + output_cost

                    # Calculate response time
                    response_time_ms = int((time.time() - start_time) * 1000)

                    # Calculate quality score
                    quality_score = self._calculate_quality_score(content, prompt)

                    return AIResponse(
                        content=content,
                        model_used=model,
                        provider="claude_api",
                        tokens_used=total_tokens,
                        cost_usd=total_cost,
                        quality_score=quality_score,
                        response_time_ms=response_time_ms,
                        metadata={
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "stop_reason": data.get("stop_reason"),
                        },
                    )

        except Exception as e:
            logger.error(f"Claude API request failed: {e}")
            self.is_healthy = False
            self.last_error = str(e)
            raise

    async def is_available(self) -> bool:
        """Check if Claude API is available"""
        if not self.api_key:
            return False

        try:
            # Simple health check - try to get models list
            headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"Claude availability check failed: {e}")
            return False

    def get_cost_estimate(self, prompt: str) -> float:
        """Estimate cost for the given prompt"""
        input_tokens = self._estimate_tokens(prompt)

        # Estimate output tokens (typically 1.5x input tokens for responses)
        estimated_output_tokens = int(input_tokens * 1.5)

        # Calculate estimated cost
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_1m_tokens
        output_cost = (
            estimated_output_tokens / 1_000_000
        ) * self.output_cost_per_1m_tokens

        return input_cost + output_cost

    async def get_available_models(self) -> list:
        """Get list of available Claude models"""
        if not self.api_key:
            return []

        try:
            headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        return [model["id"] for model in data.get("data", [])]
                    else:
                        logger.error(f"Failed to get Claude models: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error getting Claude models: {e}")
            return []
