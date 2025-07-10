import pytest
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from tenacity import RetryError

from services.openai_integration import generate_openai_text


class TestOpenAIIntegration:
    """Test OpenAI integration functionality."""

    @pytest.fixture
    def mock_openai_queue(self):
        """Mock OpenAI queue."""
        mock_queue = AsyncMock()
        return mock_queue

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        return {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response from OpenAI."
                    }
                }
            ],
            "usage": {
                "total_tokens": 25,
                "prompt_tokens": 10,
                "completion_tokens": 15
            }
        }

    @pytest.fixture
    def mock_openai_response_no_usage(self):
        """Mock OpenAI API response without usage info."""
        return {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response from OpenAI."
                    }
                }
            ]
        }

    @pytest.fixture
    def mock_env_with_api_key(self):
        """Mock environment with API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"}):
            yield

    @pytest.fixture
    def mock_env_without_api_key(self):
        """Mock environment without API key."""
        with patch.dict(os.environ, {}, clear=True):
            yield

    @pytest.mark.asyncio
    async def test_generate_openai_text_success(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test successful OpenAI text generation."""
        # Mock the queue to return our mock response
        mock_openai_queue.enqueue_request.return_value = mock_openai_response
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert result is not None
            assert result["generated_text"] == "This is a test response from OpenAI."
            assert result["total_tokens"] == 25
            
            # Verify queue was called with correct parameters
            mock_openai_queue.enqueue_request.assert_called_once()
            call_args = mock_openai_queue.enqueue_request.call_args
            
            assert call_args[1]["method"] == "POST"
            assert call_args[1]["endpoint"] == "chat/completions"
            assert call_args[1]["api_key"] == "test-api-key"
            assert call_args[1]["model"] == "gpt-3.5-turbo"
            assert call_args[1]["max_tokens"] == 500
            assert call_args[1]["temperature"] == 0.7
            assert call_args[1]["n"] == 1

    @pytest.mark.asyncio
    async def test_generate_openai_text_custom_parameters(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test OpenAI text generation with custom parameters."""
        mock_openai_queue.enqueue_request.return_value = mock_openai_response
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text(
                "Custom prompt",
                model="gpt-4",
                max_tokens=1000,
                temperature=0.2,
                stop=[".", "!"]
            )
            
            assert error is None
            assert result is not None
            assert result["generated_text"] == "This is a test response from OpenAI."
            
            # Verify custom parameters were passed
            call_args = mock_openai_queue.enqueue_request.call_args
            assert call_args[1]["model"] == "gpt-4"
            assert call_args[1]["max_tokens"] == 1000
            assert call_args[1]["temperature"] == 0.2
            assert call_args[1]["stop"] == [".", "!"]

    @pytest.mark.asyncio
    async def test_generate_openai_text_no_usage_info(self, mock_openai_queue, mock_openai_response_no_usage, mock_env_with_api_key):
        """Test OpenAI text generation when response has no usage info."""
        mock_openai_queue.enqueue_request.return_value = mock_openai_response_no_usage
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert result is not None
            assert result["generated_text"] == "This is a test response from OpenAI."
            assert result["total_tokens"] is None

    @pytest.mark.asyncio
    async def test_generate_openai_text_no_api_key(self, mock_openai_queue, mock_env_without_api_key):
        """Test OpenAI text generation without API key."""
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                await generate_openai_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_openai_text_queue_error(self, mock_openai_queue, mock_env_with_api_key):
        """Test OpenAI text generation with queue error."""
        mock_openai_queue.enqueue_request.side_effect = Exception("Queue error")
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert result is not None
            assert "error" in result
            assert result["error"] == "Queue error"
            assert result["type"] == "OpenAIError"

    @pytest.mark.asyncio
    async def test_generate_openai_text_response_parsing_error(self, mock_openai_queue, mock_env_with_api_key):
        """Test OpenAI text generation with response parsing error."""
        # Mock malformed response
        malformed_response = {
            "choices": [
                {
                    "message": {}  # Missing content
                }
            ]
        }
        mock_openai_queue.enqueue_request.return_value = malformed_response
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert result is not None
            assert "error" in result
            assert result["type"] == "OpenAIError"

    @pytest.mark.asyncio
    async def test_generate_openai_text_empty_response(self, mock_openai_queue, mock_env_with_api_key):
        """Test OpenAI text generation with empty response."""
        empty_response = {"choices": []}
        mock_openai_queue.enqueue_request.return_value = empty_response
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert result is not None
            assert "error" in result
            assert result["type"] == "OpenAIError"

    @pytest.mark.asyncio
    async def test_generate_openai_text_message_structure(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test that correct message structure is sent to OpenAI."""
        mock_openai_queue.enqueue_request.return_value = mock_openai_response
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            await generate_openai_text("Test user prompt")
            
            call_args = mock_openai_queue.enqueue_request.call_args
            messages = call_args[1]["messages"]
            
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "You are a helpful productivity assistant."
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "Test user prompt"

    @pytest.mark.asyncio
    async def test_generate_openai_text_with_whitespace(self, mock_openai_queue, mock_env_with_api_key):
        """Test OpenAI text generation with whitespace in response."""
        response_with_whitespace = {
            "choices": [
                {
                    "message": {
                        "content": "  \n  This is a test response with whitespace.  \n  "
                    }
                }
            ],
            "usage": {
                "total_tokens": 25
            }
        }
        mock_openai_queue.enqueue_request.return_value = response_with_whitespace
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert result is not None
            assert result["generated_text"] == "This is a test response with whitespace."

    @pytest.mark.asyncio
    async def test_generate_openai_text_retry_mechanism(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test retry mechanism on failures."""
        # First two calls fail, third succeeds
        mock_openai_queue.enqueue_request.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            mock_openai_response
        ]
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert result is not None
            assert result["generated_text"] == "This is a test response from OpenAI."
            
            # Should have been called 3 times (2 failures + 1 success)
            assert mock_openai_queue.enqueue_request.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_openai_text_retry_exhausted(self, mock_openai_queue, mock_env_with_api_key):
        """Test behavior when retry attempts are exhausted."""
        # All calls fail
        mock_openai_queue.enqueue_request.side_effect = Exception("Persistent failure")
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert result is not None
            assert "error" in result
            assert "Persistent failure" in result["error"]
            assert result["type"] == "OpenAIError"
            
            # Should have been called 3 times (max retry attempts)
            assert mock_openai_queue.enqueue_request.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_openai_text_different_models(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test OpenAI text generation with different models."""
        models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        
        for model in models:
            mock_openai_queue.enqueue_request.return_value = mock_openai_response
            
            with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
                result, error = await generate_openai_text("Test prompt", model=model)
                
                assert error is None
                assert result is not None
                
                call_args = mock_openai_queue.enqueue_request.call_args
                assert call_args[1]["model"] == model

    @pytest.mark.asyncio
    async def test_generate_openai_text_temperature_range(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test OpenAI text generation with different temperature values."""
        temperatures = [0.0, 0.5, 1.0, 2.0]
        
        for temp in temperatures:
            mock_openai_queue.enqueue_request.return_value = mock_openai_response
            
            with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
                result, error = await generate_openai_text("Test prompt", temperature=temp)
                
                assert error is None
                assert result is not None
                
                call_args = mock_openai_queue.enqueue_request.call_args
                assert call_args[1]["temperature"] == temp

    @pytest.mark.asyncio
    async def test_generate_openai_text_max_tokens_range(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test OpenAI text generation with different max_tokens values."""
        max_tokens_values = [10, 100, 500, 1000, 4000]
        
        for max_tokens in max_tokens_values:
            mock_openai_queue.enqueue_request.return_value = mock_openai_response
            
            with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
                result, error = await generate_openai_text("Test prompt", max_tokens=max_tokens)
                
                assert error is None
                assert result is not None
                
                call_args = mock_openai_queue.enqueue_request.call_args
                assert call_args[1]["max_tokens"] == max_tokens

    @pytest.mark.asyncio
    async def test_generate_openai_text_stop_sequences(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test OpenAI text generation with different stop sequences."""
        stop_sequences = [
            None,
            ".",
            [".", "!"],
            ["END", "STOP", "\n\n"]
        ]
        
        for stop in stop_sequences:
            mock_openai_queue.enqueue_request.return_value = mock_openai_response
            
            with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
                result, error = await generate_openai_text("Test prompt", stop=stop)
                
                assert error is None
                assert result is not None
                
                call_args = mock_openai_queue.enqueue_request.call_args
                assert call_args[1]["stop"] == stop

    @pytest.mark.asyncio
    async def test_generate_openai_text_long_prompt(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test OpenAI text generation with long prompt."""
        long_prompt = "This is a very long prompt. " * 100
        mock_openai_queue.enqueue_request.return_value = mock_openai_response
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text(long_prompt)
            
            assert error is None
            assert result is not None
            
            call_args = mock_openai_queue.enqueue_request.call_args
            messages = call_args[1]["messages"]
            assert messages[1]["content"] == long_prompt

    @pytest.mark.asyncio
    async def test_generate_openai_text_empty_prompt(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test OpenAI text generation with empty prompt."""
        mock_openai_queue.enqueue_request.return_value = mock_openai_response
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text("")
            
            assert error is None
            assert result is not None
            
            call_args = mock_openai_queue.enqueue_request.call_args
            messages = call_args[1]["messages"]
            assert messages[1]["content"] == ""

    @pytest.mark.asyncio
    async def test_generate_openai_text_special_characters(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test OpenAI text generation with special characters in prompt."""
        special_prompt = "Test with émojis 🚀 and spëcial chars: @#$%^&*()[]{}|\\:;\"'<>,.?/~`"
        mock_openai_queue.enqueue_request.return_value = mock_openai_response
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text(special_prompt)
            
            assert error is None
            assert result is not None
            
            call_args = mock_openai_queue.enqueue_request.call_args
            messages = call_args[1]["messages"]
            assert messages[1]["content"] == special_prompt

    @pytest.mark.asyncio
    async def test_generate_openai_text_concurrent_requests(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test concurrent OpenAI text generation requests."""
        mock_openai_queue.enqueue_request.return_value = mock_openai_response
        
        async def make_request(prompt):
            with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
                return await generate_openai_text(f"Prompt {prompt}")
        
        # Make 5 concurrent requests
        tasks = [make_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for result, error in results:
            assert error is None
            assert result is not None
            assert result["generated_text"] == "This is a test response from OpenAI."
        
        # Queue should have been called 5 times
        assert mock_openai_queue.enqueue_request.call_count == 5

    def test_openai_integration_imports(self):
        """Test that OpenAI integration imports correctly."""
        from services.openai_integration import generate_openai_text
        assert callable(generate_openai_text)

    def test_openai_integration_logging_setup(self):
        """Test that logging is set up correctly."""
        from services.openai_integration import logger
        assert logger.name == "services.openai_integration"

    @pytest.mark.asyncio
    async def test_generate_openai_text_api_key_from_env(self, mock_openai_queue, mock_openai_response):
        """Test that API key is correctly retrieved from environment."""
        test_api_key = "test-env-api-key-123"
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": test_api_key}):
            mock_openai_queue.enqueue_request.return_value = mock_openai_response
            
            with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
                result, error = await generate_openai_text("Test prompt")
                
                assert error is None
                assert result is not None
                
                call_args = mock_openai_queue.enqueue_request.call_args
                assert call_args[1]["api_key"] == test_api_key

    @pytest.mark.asyncio
    async def test_generate_openai_text_return_format(self, mock_openai_queue, mock_openai_response, mock_env_with_api_key):
        """Test that the return format is consistent."""
        mock_openai_queue.enqueue_request.return_value = mock_openai_response
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text("Test prompt")
            
            # Should always return a tuple of (result, error)
            assert isinstance(result, dict)
            assert error is None
            
            # Result should have expected keys
            assert "generated_text" in result
            assert "total_tokens" in result
            
            # Values should be of expected types
            assert isinstance(result["generated_text"], str)
            assert isinstance(result["total_tokens"], (int, type(None)))

    @pytest.mark.asyncio
    async def test_generate_openai_text_error_format(self, mock_openai_queue, mock_env_with_api_key):
        """Test that error format is consistent."""
        mock_openai_queue.enqueue_request.side_effect = Exception("Test error")
        
        with patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            result, error = await generate_openai_text("Test prompt")
            
            # Should always return a tuple of (result, error)
            assert isinstance(result, dict)
            assert error is None
            
            # Error result should have expected keys
            assert "error" in result
            assert "type" in result
            
            # Values should be of expected types
            assert isinstance(result["error"], str)
            assert result["type"] == "OpenAIError"
