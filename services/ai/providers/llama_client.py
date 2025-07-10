"""
Llama Self-Hosted Client
Implements local Llama model inference for cost-effective AI responses.
"""

import logging
import os
import time
from typing import Any

import aiohttp

from .base_client import AIResponse, BaseAIClient

logger = logging.getLogger(__name__)


class LlamaClient(BaseAIClient):
    """Llama self-hosted client implementation"""

    def __init__(self):
        # Self-hosted Llama endpoint (configure via environment)
        llama_url = os.getenv("LLAMA_API_URL", "http://localhost:8000")
        super().__init__(base_url=llama_url)

        # Self-hosted costs (estimated infrastructure costs)
        self.cost_per_1m_tokens = 0.10  # £0.10 per 1M tokens (infrastructure cost)

        # Default model
        self.default_model = "llama-3-8b"

    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        """Generate response using self-hosted Llama"""
        start_time = time.time()

        model = kwargs.get("model", self.default_model)
        max_tokens = kwargs.get("max_tokens", 2048)
        temperature = kwargs.get("temperature", 0.7)

        # Prepare request payload for vLLM API
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        headers = {"Content-Type": "application/json"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(
                        total=60
                    ),  # Longer timeout for local inference
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Llama API error: {response.status} - {error_text}"
                        )

                    data = await response.json()

                    # Extract response content
                    content = data["choices"][0]["message"]["content"]

                    # Calculate usage
                    usage = data.get("usage", {})
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)

                    # Calculate cost (infrastructure cost)
                    total_cost = (total_tokens / 1_000_000) * self.cost_per_1m_tokens

                    # Calculate response time
                    response_time_ms = int((time.time() - start_time) * 1000)

                    # Calculate quality score
                    quality_score = self._calculate_quality_score(content, prompt)

                    return AIResponse(
                        content=content,
                        model_used=model,
                        provider="llama_self_hosted",
                        tokens_used=total_tokens,
                        cost_usd=total_cost,
                        quality_score=quality_score,
                        response_time_ms=response_time_ms,
                        metadata={
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "finish_reason": data["choices"][0].get("finish_reason"),
                        },
                    )

        except Exception as e:
            logger.error(f"Llama API request failed: {e}")
            self.is_healthy = False
            self.last_error = str(e)
            raise

    async def is_available(self) -> bool:
        """Check if self-hosted Llama is available"""
        try:
            # Simple health check
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"Llama availability check failed: {e}")
            return False

    def get_cost_estimate(self, prompt: str) -> float:
        """Estimate cost for the given prompt"""
        total_tokens = self._estimate_tokens(prompt) * 2.5  # Estimate total tokens

        # Calculate estimated cost
        return (total_tokens / 1_000_000) * self.cost_per_1m_tokens

    async def get_available_models(self) -> list:
        """Get list of available Llama models"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/v1/models",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        return [model["id"] for model in data.get("data", [])]
                    else:
                        logger.error(f"Failed to get Llama models: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error getting Llama models: {e}")
            return []

    async def get_model_info(self, model_name: str) -> dict[str, Any]:
        """Get detailed information about a specific model"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/v1/models/{model_name}",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:

                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get model info: {response.status}")
                        return {}

        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {}
