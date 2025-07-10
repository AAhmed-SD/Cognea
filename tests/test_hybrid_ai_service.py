"""
Test Hybrid AI Service
Tests the hybrid AI routing and provider management functionality.
"""

from unittest.mock import AsyncMock, patch

import pytest

from services.ai.hybrid_ai_service import (
    HybridAIService,
    ModelProvider,
    TaskType,
    get_hybrid_ai_service,
)
from services.ai.providers.base_client import AIResponse


class TestHybridAIService:
    """Test cases for HybridAIService"""

    @pytest.fixture
    def hybrid_service(self):
        """Create a test instance of HybridAIService"""
        return HybridAIService()

    @pytest.fixture
    def mock_ai_response(self):
        """Create a mock AI response"""
        return AIResponse(
            content="Test response content",
            model_used="test-model",
            provider="test_provider",
            tokens_used=100,
            cost_usd=0.001,
            quality_score=0.85,
            response_time_ms=500,
        )

    def test_initialization(self, hybrid_service):
        """Test service initialization"""
        assert hybrid_service is not None
        assert len(hybrid_service.model_configs) == 5  # 5 providers
        assert len(hybrid_service.clients) == 5
        assert len(hybrid_service.quality_thresholds) == 8  # 8 task types

    def test_model_configs(self, hybrid_service):
        """Test model configurations"""
        configs = hybrid_service.model_configs

        # Check Llama config
        llama_config = configs[ModelProvider.LLAMA_SELF_HOSTED]
        assert llama_config.cost_per_1m_tokens == 0.10
        assert llama_config.quality_score == 0.85

        # Check DeepSeek config
        deepseek_config = configs[ModelProvider.DEEPSEEK_API]
        assert deepseek_config.cost_per_1m_tokens == 0.20
        assert deepseek_config.quality_score == 0.88

        # Check OpenAI config (most expensive)
        openai_config = configs[ModelProvider.OPENAI_API]
        assert openai_config.cost_per_1m_tokens == 10.00
        assert openai_config.quality_score == 0.95

    def test_quality_thresholds(self, hybrid_service):
        """Test quality thresholds for different task types"""
        thresholds = hybrid_service.quality_thresholds

        assert thresholds[TaskType.FLASHCARD] == 0.85
        assert thresholds[TaskType.EXAM_QUESTION] == 0.90
        assert thresholds[TaskType.PRODUCTIVITY_ANALYSIS] == 0.80
        assert thresholds[TaskType.GENERAL_QA] == 0.80

    def test_optimal_model_sequences(self, hybrid_service):
        """Test optimal model sequences for different tasks"""

        # Flashcard generation should prioritize self-hosted models
        flashcard_models = hybrid_service._get_optimal_models(TaskType.FLASHCARD)
        assert flashcard_models[0] == ModelProvider.LLAMA_SELF_HOSTED
        assert flashcard_models[1] == ModelProvider.MISTRAL_SELF_HOSTED
        assert flashcard_models[-1] == ModelProvider.OPENAI_API  # Fallback

        # Exam questions should prioritize DeepSeek
        exam_models = hybrid_service._get_optimal_models(TaskType.EXAM_QUESTION)
        assert exam_models[0] == ModelProvider.DEEPSEEK_API
        assert exam_models[1] == ModelProvider.CLAUDE_API

        # OpenAI should always be the last fallback
        for task_type in TaskType:
            models = hybrid_service._get_optimal_models(task_type)
            assert models[-1] == ModelProvider.OPENAI_API

    @pytest.mark.asyncio
    async def test_generate_response_success(self, hybrid_service, mock_ai_response):
        """Test successful response generation"""
        # Mock the first client to return a successful response
        mock_client = AsyncMock()
        mock_client.is_available.return_value = True
        mock_client.generate.return_value = mock_ai_response

        hybrid_service.clients[ModelProvider.LLAMA_SELF_HOSTED] = mock_client

        # Mock cache to return None (no cache hit)
        with patch(
            "services.ai.hybrid_ai_service.enhanced_cache.get", return_value=None
        ):
            with patch("services.ai.hybrid_ai_service.enhanced_cache.set"):
                with patch.object(hybrid_service, "_track_usage"):
                    response = await hybrid_service.generate_response(
                        task_type=TaskType.FLASHCARD,
                        prompt="Test prompt",
                        user_id="test_user",
                    )

        assert response.content == "Test response content"
        assert response.provider == "test_provider"
        assert response.quality_score == 0.85

    @pytest.mark.asyncio
    async def test_generate_response_fallback(self, hybrid_service, mock_ai_response):
        """Test fallback to secondary model when primary fails"""
        # Mock first client to fail
        mock_client1 = AsyncMock()
        mock_client1.is_available.return_value = False

        # Mock second client to succeed
        mock_client2 = AsyncMock()
        mock_client2.is_available.return_value = True
        mock_client2.generate.return_value = mock_ai_response

        hybrid_service.clients[ModelProvider.LLAMA_SELF_HOSTED] = mock_client1
        hybrid_service.clients[ModelProvider.MISTRAL_SELF_HOSTED] = mock_client2

        # Mock cache
        with patch(
            "services.ai.hybrid_ai_service.enhanced_cache.get", return_value=None
        ):
            with patch("services.ai.hybrid_ai_service.enhanced_cache.set"):
                with patch.object(hybrid_service, "_track_usage"):
                    response = await hybrid_service.generate_response(
                        task_type=TaskType.FLASHCARD,
                        prompt="Test prompt",
                        user_id="test_user",
                    )

        assert response.content == "Test response content"
        # Should have used the second model
        mock_client2.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_quality_threshold(self, hybrid_service):
        """Test quality threshold enforcement"""
        # Create response that doesn't meet quality threshold
        low_quality_response = AIResponse(
            content="Bad response",
            model_used="test-model",
            provider="test_provider",
            tokens_used=10,
            cost_usd=0.001,
            quality_score=0.5,  # Below threshold
            response_time_ms=100,
        )

        mock_client = AsyncMock()
        mock_client.is_available.return_value = True
        mock_client.generate.return_value = low_quality_response

        hybrid_service.clients[ModelProvider.LLAMA_SELF_HOSTED] = mock_client

        # Mock cache
        with patch(
            "services.ai.hybrid_ai_service.enhanced_cache.get", return_value=None
        ):
            with patch("services.ai.hybrid_ai_service.enhanced_cache.set"):
                with patch.object(hybrid_service, "_track_usage"):
                    # Should try the next model due to low quality
                    with pytest.raises(Exception, match="All AI providers failed"):
                        await hybrid_service.generate_response(
                            task_type=TaskType.FLASHCARD,
                            prompt="Test prompt",
                            user_id="test_user",
                        )

    @pytest.mark.asyncio
    async def test_cache_hit(self, hybrid_service, mock_ai_response):
        """Test cache hit scenario"""
        # Mock cache to return cached response
        cached_data = mock_ai_response.__dict__
        with patch(
            "services.ai.hybrid_ai_service.enhanced_cache.get", return_value=cached_data
        ):
            response = await hybrid_service.generate_response(
                task_type=TaskType.FLASHCARD, prompt="Test prompt", user_id="test_user"
            )

        assert response.content == "Test response content"
        # Should not call any AI clients
        for client in hybrid_service.clients.values():
            assert not hasattr(client, "generate") or not client.generate.called

    @pytest.mark.asyncio
    async def test_cost_analysis(self, hybrid_service):
        """Test cost analysis functionality"""
        analysis = await hybrid_service.get_cost_analysis(
            task_type=TaskType.FLASHCARD, prompt="Test prompt for cost analysis"
        )

        # Should have analysis for each provider in the sequence
        assert "llama_self_hosted" in analysis
        assert "mistral_self_hosted" in analysis
        assert "deepseek_api" in analysis
        assert "openai_api" in analysis

        # Check structure of analysis
        for provider, data in analysis.items():
            assert "estimated_cost_usd" in data
            assert "quality_score" in data
            assert "latency_ms" in data
            assert "is_available" in data

    @pytest.mark.asyncio
    async def test_monthly_costs(self, hybrid_service):
        """Test monthly cost reporting"""
        costs = await hybrid_service.get_monthly_costs("test_user")

        # Check structure
        assert "llama_self_hosted" in costs
        assert "deepseek_api" in costs
        assert "claude_api" in costs
        assert "openai_api" in costs
        assert "total" in costs

        # Check total calculation
        total = costs["total"]
        assert "cost" in total
        assert "requests" in total

    def test_get_hybrid_ai_service_singleton(self):
        """Test singleton pattern for hybrid AI service"""
        service1 = get_hybrid_ai_service()
        service2 = get_hybrid_ai_service()

        assert service1 is service2


class TestTaskType:
    """Test TaskType enum"""

    def test_task_types(self):
        """Test all task types are defined"""
        assert TaskType.FLASHCARD == "flashcard"
        assert TaskType.EXAM_QUESTION == "exam_question"
        assert TaskType.PRODUCTIVITY_ANALYSIS == "productivity_analysis"
        assert TaskType.TASK_GENERATION == "task_generation"
        assert TaskType.SCHEDULE_OPTIMIZATION == "schedule_optimization"
        assert TaskType.SUMMARIZATION == "summarization"
        assert TaskType.GENERAL_QA == "general_qa"
        assert TaskType.CONVERSATION == "conversation"


class TestModelProvider:
    """Test ModelProvider enum"""

    def test_model_providers(self):
        """Test all model providers are defined"""
        assert ModelProvider.LLAMA_SELF_HOSTED == "llama_self_hosted"
        assert ModelProvider.MISTRAL_SELF_HOSTED == "mistral_self_hosted"
        assert ModelProvider.DEEPSEEK_API == "deepseek_api"
        assert ModelProvider.CLAUDE_API == "claude_api"
        assert ModelProvider.OPENAI_API == "openai_api"


if __name__ == "__main__":
    pytest.main([__file__])
