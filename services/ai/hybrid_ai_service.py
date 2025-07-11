"""
Hybrid AI Service - Multi-Provider AI Router
Implements cost-optimized AI routing with quality assurance and fallback logic.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any
import time

from services.cost_tracking import cost_tracking_service
from services.redis_cache import enhanced_cache
from services.prometheus_integration import get_prometheus_service

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """AI task types for routing decisions"""

    FLASHCARD = "flashcard"
    EXAM_QUESTION = "exam_question"
    PRODUCTIVITY_ANALYSIS = "productivity_analysis"
    TASK_GENERATION = "task_generation"
    SCHEDULE_OPTIMIZATION = "schedule_optimization"
    SMART_SCHEDULING = "smart_scheduling"  # New specialized task type
    MEMORY_ANALYSIS = "memory_analysis"  # New for memory tracking
    REVISION_PLANNING = "revision_planning"  # New for exam-focused planning
    SUMMARIZATION = "summarization"
    GENERAL_QA = "general_qa"
    CONVERSATION = "conversation"


class ModelProvider(str, Enum):
    """Available AI model providers"""

    LLAMA_SELF_HOSTED = "llama_self_hosted"
    MISTRAL_SELF_HOSTED = "mistral_self_hosted"
    DEEPSEEK_API = "deepseek_api"
    CLAUDE_API = "claude_api"
    OPENAI_API = "openai_api"


@dataclass
class ModelConfig:
    """Configuration for each model provider"""

    provider: ModelProvider
    model_name: str
    cost_per_1m_tokens: float
    quality_score: float
    latency_ms: int
    max_tokens: int
    temperature: float
    is_available: bool = True


@dataclass
class AIResponse:
    """Standardized AI response format"""

    content: str
    model_used: str
    provider: ModelProvider
    tokens_used: int
    cost_usd: float
    quality_score: float
    response_time_ms: int
    metadata: dict[str, Any] = None


class BaseAIClient(ABC):
    """Abstract base class for AI providers"""

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


class HybridAIService:
    """
    Hybrid AI service that routes requests to optimal providers
    based on cost, quality, and availability.
    """

    def __init__(self):
        self.model_configs = self._initialize_model_configs()
        self.clients = self._initialize_clients()
        self.quality_thresholds = self._get_quality_thresholds()
        self.cost_tracker = cost_tracking_service

    def _initialize_model_configs(self) -> dict[ModelProvider, ModelConfig]:
        """Initialize model configurations with pricing and capabilities"""
        return {
            ModelProvider.LLAMA_SELF_HOSTED: ModelConfig(
                provider=ModelProvider.LLAMA_SELF_HOSTED,
                model_name="llama-3-8b",
                cost_per_1m_tokens=0.10,  # £0.10 per 1M tokens
                quality_score=0.85,
                latency_ms=2000,
                max_tokens=4096,
                temperature=0.7,
            ),
            ModelProvider.MISTRAL_SELF_HOSTED: ModelConfig(
                provider=ModelProvider.MISTRAL_SELF_HOSTED,
                model_name="mistral-7b",
                cost_per_1m_tokens=0.10,
                quality_score=0.82,
                latency_ms=1800,
                max_tokens=4096,
                temperature=0.7,
            ),
            ModelProvider.DEEPSEEK_API: ModelConfig(
                provider=ModelProvider.DEEPSEEK_API,
                model_name="deepseek-chat",
                cost_per_1m_tokens=0.20,  # £0.20 per 1M tokens
                quality_score=0.88,
                latency_ms=1500,
                max_tokens=4096,
                temperature=0.7,
            ),
            ModelProvider.CLAUDE_API: ModelConfig(
                provider=ModelProvider.CLAUDE_API,
                model_name="claude-3-haiku",
                cost_per_1m_tokens=0.25,  # £0.25 per 1M tokens
                quality_score=0.90,
                latency_ms=1200,
                max_tokens=4096,
                temperature=0.7,
            ),
            ModelProvider.OPENAI_API: ModelConfig(
                provider=ModelProvider.OPENAI_API,
                model_name="gpt-4-turbo",
                cost_per_1m_tokens=10.00,  # £10.00 per 1M tokens
                quality_score=0.95,
                latency_ms=1000,
                max_tokens=4096,
                temperature=0.7,
            ),
        }

    def _initialize_clients(self) -> dict[ModelProvider, BaseAIClient]:
        """Initialize AI provider clients"""
        from .providers.claude_client import ClaudeClient
        from .providers.deepseek_client import DeepSeekClient
        from .providers.llama_client import LlamaClient
        from .providers.openai_client import OpenAIClient

        return {
            ModelProvider.LLAMA_SELF_HOSTED: LlamaClient(),
            ModelProvider.MISTRAL_SELF_HOSTED: LlamaClient(),  # Use Llama client for Mistral too
            ModelProvider.DEEPSEEK_API: DeepSeekClient(),
            ModelProvider.CLAUDE_API: ClaudeClient(),
            ModelProvider.OPENAI_API: OpenAIClient(),
        }

    def _get_quality_thresholds(self) -> dict[TaskType, float]:
        """Get quality thresholds for different task types"""
        return {
            TaskType.FLASHCARD: 0.85,
            TaskType.EXAM_QUESTION: 0.90,
            TaskType.PRODUCTIVITY_ANALYSIS: 0.80,
            TaskType.TASK_GENERATION: 0.85,
            TaskType.SCHEDULE_OPTIMIZATION: 0.85,
            TaskType.SMART_SCHEDULING: 0.92,  # High threshold for critical scheduling
            TaskType.MEMORY_ANALYSIS: 0.88,  # High threshold for memory insights
            TaskType.REVISION_PLANNING: 0.90,  # High threshold for exam planning
            TaskType.SUMMARIZATION: 0.80,
            TaskType.GENERAL_QA: 0.80,
            TaskType.CONVERSATION: 0.75,
        }

    def _get_optimal_models(self, task_type: TaskType) -> list[ModelProvider]:
        """Get optimal model sequence for a given task type"""
        # Define optimal model sequences for each task type
        model_sequences = {
            TaskType.FLASHCARD: [
                ModelProvider.LLAMA_SELF_HOSTED,
                ModelProvider.MISTRAL_SELF_HOSTED,
                ModelProvider.DEEPSEEK_API,
                ModelProvider.OPENAI_API,
            ],
            TaskType.EXAM_QUESTION: [
                ModelProvider.DEEPSEEK_API,
                ModelProvider.CLAUDE_API,
                ModelProvider.LLAMA_SELF_HOSTED,
                ModelProvider.OPENAI_API,
            ],
            TaskType.PRODUCTIVITY_ANALYSIS: [
                ModelProvider.LLAMA_SELF_HOSTED,
                ModelProvider.MISTRAL_SELF_HOSTED,
                ModelProvider.DEEPSEEK_API,
                ModelProvider.OPENAI_API,
            ],
            TaskType.TASK_GENERATION: [
                ModelProvider.LLAMA_SELF_HOSTED,
                ModelProvider.DEEPSEEK_API,
                ModelProvider.CLAUDE_API,
                ModelProvider.OPENAI_API,
            ],
            TaskType.SCHEDULE_OPTIMIZATION: [
                ModelProvider.LLAMA_SELF_HOSTED,
                ModelProvider.DEEPSEEK_API,
                ModelProvider.CLAUDE_API,
                ModelProvider.OPENAI_API,
            ],
            # Smart scheduling tasks prioritize Claude for superior reasoning
            TaskType.SMART_SCHEDULING: [
                ModelProvider.CLAUDE_API,  # Primary: Best reasoning
                ModelProvider.DEEPSEEK_API,  # Secondary: Good reasoning, cheaper
                ModelProvider.OPENAI_API,  # Fallback: Reliable but expensive
            ],
            TaskType.MEMORY_ANALYSIS: [
                ModelProvider.CLAUDE_API,  # Primary: Best pattern recognition
                ModelProvider.DEEPSEEK_API,  # Secondary: Good analysis
                ModelProvider.OPENAI_API,  # Fallback
            ],
            TaskType.REVISION_PLANNING: [
                ModelProvider.CLAUDE_API,  # Primary: Best planning capabilities
                ModelProvider.DEEPSEEK_API,  # Secondary: Good planning
                ModelProvider.OPENAI_API,  # Fallback
            ],
            TaskType.SUMMARIZATION: [
                ModelProvider.DEEPSEEK_API,
                ModelProvider.LLAMA_SELF_HOSTED,
                ModelProvider.MISTRAL_SELF_HOSTED,
                ModelProvider.OPENAI_API,
            ],
            TaskType.GENERAL_QA: [
                ModelProvider.LLAMA_SELF_HOSTED,
                ModelProvider.DEEPSEEK_API,
                ModelProvider.CLAUDE_API,
                ModelProvider.OPENAI_API,
            ],
            TaskType.CONVERSATION: [
                ModelProvider.LLAMA_SELF_HOSTED,
                ModelProvider.DEEPSEEK_API,
                ModelProvider.CLAUDE_API,
                ModelProvider.OPENAI_API,
            ],
        }

        return model_sequences.get(task_type, [ModelProvider.OPENAI_API])

    async def generate_response(
        self,
        task_type: TaskType,
        prompt: str,
        user_id: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stop: list[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate AI response using optimal provider for task type."""
        start_time = time.time()
        prometheus_service = get_prometheus_service()
        
        try:
            # Get optimal models for task type
            models = self._get_optimal_models(task_type)
            
            # Try each model until one succeeds
            for model in models:
                try:
                    logger.info(f"Attempting AI request with {model.value} for {task_type.value}")
                    
                    # Record AI request start
                    prometheus_service.record_ai_request(
                        provider=model.value,
                        task_type=task_type.value,
                        status="started",
                        duration=0,
                        user_id=user_id
                    )
                    
                    # Generate response
                    response = await self._generate_with_model(
                        model, prompt, max_tokens, temperature, stop, **kwargs
                    )
                    
                    # Calculate duration
                    duration = time.time() - start_time
                    
                    # Record successful AI request
                    prometheus_service.record_ai_request(
                        provider=model.value,
                        task_type=task_type.value,
                        status="success",
                        duration=duration,
                        user_id=user_id
                    )
                    
                    # Record token usage
                    if response.tokens_used:
                        prometheus_service.record_ai_tokens(
                            provider=model.value,
                            task_type=task_type.value,
                            token_type="total",
                            tokens=response.tokens_used,
                            user_id=user_id
                        )
                    
                    # Record cost
                    if response.cost_usd:
                        prometheus_service.record_ai_cost(
                            provider=model.value,
                            task_type=task_type.value,
                            cost=response.cost_usd,
                            user_id=user_id
                        )
                    
                    return response
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # Record failed AI request
                    prometheus_service.record_ai_request(
                        provider=model.value,
                        task_type=task_type.value,
                        status="failed",
                        duration=duration,
                        user_id=user_id
                    )
                    
                    logger.warning(f"Failed with {model.value}: {e}")
                    continue
            
            # If all models failed
            raise Exception(f"All AI providers failed for task type {task_type.value}")
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record overall failure
            prometheus_service.record_ai_request(
                provider="unknown",
                task_type=task_type.value,
                status="failed",
                duration=duration,
                user_id=user_id
            )
            
            raise

    async def _track_usage(
        self, user_id: str, provider: ModelProvider, response: AIResponse
    ):
        """Track AI usage and costs"""
        try:
            await self.cost_tracker.track_api_call(
                user_id=user_id,
                endpoint=f"/ai/{task_type}",
                model=response.model_used,
                input_tokens=response.tokens_used // 2,  # Estimate input tokens
                output_tokens=response.tokens_used // 2,  # Estimate output tokens
                cost_usd=response.cost_usd,
            )
        except Exception as e:
            logger.error(f"Failed to track usage: {str(e)}")

    async def get_cost_analysis(
        self, task_type: TaskType, prompt: str
    ) -> dict[str, Any]:
        """Get cost analysis for different providers"""
        analysis = {}

        for provider in self._get_optimal_models(task_type):
            if provider in self.clients:
                config = self.model_configs[provider]
                estimated_cost = self.clients[provider].get_cost_estimate(prompt)

                analysis[provider.value] = {
                    "estimated_cost_usd": estimated_cost,
                    "quality_score": config.quality_score,
                    "latency_ms": config.latency_ms,
                    "is_available": await self.clients[provider].is_available(),
                }

        return analysis

    async def get_monthly_costs(self, user_id: str) -> dict[str, Any]:
        """Get monthly cost breakdown by provider"""
        # This would query the cost tracking database
        # For now, return mock data
        return {
            "llama_self_hosted": {"cost": 50.0, "requests": 1000},
            "deepseek_api": {"cost": 30.0, "requests": 500},
            "claude_api": {"cost": 20.0, "requests": 200},
            "openai_api": {"cost": 10.0, "requests": 50},
            "total": {"cost": 110.0, "requests": 1750},
        }


# Note: Mock clients have been replaced with real implementations in the providers/ directory


# Global instance
_hybrid_ai_service = None


def get_hybrid_ai_service() -> HybridAIService:
    """Get the global hybrid AI service instance"""
    global _hybrid_ai_service
    if _hybrid_ai_service is None:
        _hybrid_ai_service = HybridAIService()
    return _hybrid_ai_service
