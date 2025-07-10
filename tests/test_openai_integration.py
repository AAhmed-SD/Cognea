import pytest
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from services.openai_integration import generate_openai_text


class TestOpenAIIntegration:
    """Test OpenAI integration functionality."""

    @pytest.fixture
    def mock_openai_queue(self):
        """Mock OpenAI queue for testing."""
        with patch('services.openai_integration.get_openai_queue') as mock_queue_fn:
            mock_queue = MagicMock()
            mock_queue.enqueue_request = AsyncMock()
            mock_queue_fn.return_value = mock_queue
            yield mock_queue

    @pytest.fixture
    def mock_successful_response(self):
        """Mock successful OpenAI API response."""
        return {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response from OpenAI."
                    }
                }
            ],
            "usage": {
                "total_tokens": 25
            }
        }

    @pytest.fixture
    def mock_response_without_usage(self):
        """Mock OpenAI API response without usage information."""
        return {
            "choices": [
                {
                    "message": {
                        "content": "Response without usage data."
                    }
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_generate_openai_text_success(self, mock_openai_queue, mock_successful_response):
        """Test successful OpenAI text generation."""
        mock_openai_queue.enqueue_request.return_value = mock_successful_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
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

    @pytest.mark.asyncio
    async def test_generate_openai_text_custom_parameters(self, mock_openai_queue, mock_successful_response):
        """Test OpenAI text generation with custom parameters."""
        mock_openai_queue.enqueue_request.return_value = mock_successful_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text(
                "Custom prompt",
                model="gpt-4",
                max_tokens=1000,
                temperature=0.3,
                stop=[".", "!"]
            )
            
            assert error is None
            assert result["generated_text"] == "This is a test response from OpenAI."
            
            # Verify custom parameters were passed
            call_args = mock_openai_queue.enqueue_request.call_args
            assert call_args[1]["model"] == "gpt-4"
            assert call_args[1]["max_tokens"] == 1000
            assert call_args[1]["temperature"] == 0.3
            assert call_args[1]["stop"] == [".", "!"]

    @pytest.mark.asyncio
    async def test_generate_openai_text_without_usage(self, mock_openai_queue, mock_response_without_usage):
        """Test OpenAI text generation without usage information."""
        mock_openai_queue.enqueue_request.return_value = mock_response_without_usage
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert result["generated_text"] == "Response without usage data."
            assert result["total_tokens"] is None

    @pytest.mark.asyncio
    async def test_generate_openai_text_no_api_key(self, mock_openai_queue):
        """Test OpenAI text generation without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                await generate_openai_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_openai_text_empty_api_key(self, mock_openai_queue):
        """Test OpenAI text generation with empty API key."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                await generate_openai_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_openai_text_queue_exception(self, mock_openai_queue):
        """Test OpenAI text generation with queue exception."""
        mock_openai_queue.enqueue_request.side_effect = Exception("Queue error")
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert "error" in result
            assert result["error"] == "Queue error"
            assert result["type"] == "OpenAIError"

    @pytest.mark.asyncio
    async def test_generate_openai_text_api_error(self, mock_openai_queue):
        """Test OpenAI text generation with API error."""
        mock_openai_queue.enqueue_request.side_effect = Exception("API rate limit exceeded")
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert "error" in result
            assert result["error"] == "API rate limit exceeded"
            assert result["type"] == "OpenAIError"

    @pytest.mark.asyncio
    async def test_generate_openai_text_message_structure(self, mock_openai_queue, mock_successful_response):
        """Test that messages are structured correctly."""
        mock_openai_queue.enqueue_request.return_value = mock_successful_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            await generate_openai_text("Test prompt")
            
            call_args = mock_openai_queue.enqueue_request.call_args
            messages = call_args[1]["messages"]
            
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "You are a helpful productivity assistant."
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "Test prompt"

    @pytest.mark.asyncio
    async def test_generate_openai_text_default_parameters(self, mock_openai_queue, mock_successful_response):
        """Test default parameters are applied correctly."""
        mock_openai_queue.enqueue_request.return_value = mock_successful_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            await generate_openai_text("Test prompt")
            
            call_args = mock_openai_queue.enqueue_request.call_args
            assert call_args[1]["model"] == "gpt-3.5-turbo"
            assert call_args[1]["max_tokens"] == 500
            assert call_args[1]["temperature"] == 0.7
            assert call_args[1]["stop"] is None
            assert call_args[1]["n"] == 1

    @pytest.mark.asyncio
    async def test_generate_openai_text_response_parsing(self, mock_openai_queue):
        """Test response parsing with different response formats."""
        # Test with whitespace in response
        response_with_whitespace = {
            "choices": [
                {
                    "message": {
                        "content": "  Response with whitespace  "
                    }
                }
            ],
            "usage": {
                "total_tokens": 20
            }
        }
        
        mock_openai_queue.enqueue_request.return_value = response_with_whitespace
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert result["generated_text"] == "Response with whitespace"  # Should be stripped

    @pytest.mark.asyncio
    async def test_generate_openai_text_malformed_response(self, mock_openai_queue):
        """Test handling of malformed API response."""
        malformed_response = {
            "choices": []  # Empty choices
        }
        
        mock_openai_queue.enqueue_request.return_value = malformed_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert "error" in result
            assert result["type"] == "OpenAIError"

    @pytest.mark.asyncio
    async def test_generate_openai_text_retry_behavior(self, mock_openai_queue):
        """Test retry behavior on failures."""
        # Mock to fail first two times, succeed on third
        call_count = 0
        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Success after retries"
                        }
                    }
                ],
                "usage": {
                    "total_tokens": 15
                }
            }
        
        mock_openai_queue.enqueue_request.side_effect = side_effect
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert result["generated_text"] == "Success after retries"
            assert call_count == 3  # Should have retried twice

    @pytest.mark.asyncio
    async def test_generate_openai_text_max_retries_exceeded(self, mock_openai_queue):
        """Test behavior when max retries are exceeded."""
        mock_openai_queue.enqueue_request.side_effect = Exception("Persistent failure")
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert "error" in result
            assert result["error"] == "Persistent failure"
            assert result["type"] == "OpenAIError"

    @pytest.mark.asyncio
    async def test_generate_openai_text_different_models(self, mock_openai_queue, mock_successful_response):
        """Test with different OpenAI models."""
        models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]
        
        for model in models:
            mock_openai_queue.enqueue_request.return_value = mock_successful_response
            
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
                result, error = await generate_openai_text("Test prompt", model=model)
                
                assert error is None
                assert result["generated_text"] == "This is a test response from OpenAI."
                
                call_args = mock_openai_queue.enqueue_request.call_args
                assert call_args[1]["model"] == model

    @pytest.mark.asyncio
    async def test_generate_openai_text_temperature_range(self, mock_openai_queue, mock_successful_response):
        """Test with different temperature values."""
        temperatures = [0.0, 0.5, 1.0, 1.5, 2.0]
        
        for temp in temperatures:
            mock_openai_queue.enqueue_request.return_value = mock_successful_response
            
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
                result, error = await generate_openai_text("Test prompt", temperature=temp)
                
                assert error is None
                call_args = mock_openai_queue.enqueue_request.call_args
                assert call_args[1]["temperature"] == temp

    @pytest.mark.asyncio
    async def test_generate_openai_text_max_tokens_range(self, mock_openai_queue, mock_successful_response):
        """Test with different max_tokens values."""
        max_tokens_values = [1, 100, 500, 1000, 2000]
        
        for max_tokens in max_tokens_values:
            mock_openai_queue.enqueue_request.return_value = mock_successful_response
            
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
                result, error = await generate_openai_text("Test prompt", max_tokens=max_tokens)
                
                assert error is None
                call_args = mock_openai_queue.enqueue_request.call_args
                assert call_args[1]["max_tokens"] == max_tokens

    @pytest.mark.asyncio
    async def test_generate_openai_text_stop_sequences(self, mock_openai_queue, mock_successful_response):
        """Test with different stop sequences."""
        stop_sequences = [
            None,
            ["."],
            [".", "!", "?"],
            ["\n", "\n\n"],
            ["END", "STOP"]
        ]
        
        for stop in stop_sequences:
            mock_openai_queue.enqueue_request.return_value = mock_successful_response
            
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
                result, error = await generate_openai_text("Test prompt", stop=stop)
                
                assert error is None
                call_args = mock_openai_queue.enqueue_request.call_args
                assert call_args[1]["stop"] == stop

    @pytest.mark.asyncio
    async def test_generate_openai_text_empty_prompt(self, mock_openai_queue, mock_successful_response):
        """Test with empty prompt."""
        mock_openai_queue.enqueue_request.return_value = mock_successful_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("")
            
            assert error is None
            call_args = mock_openai_queue.enqueue_request.call_args
            messages = call_args[1]["messages"]
            assert messages[1]["content"] == ""

    @pytest.mark.asyncio
    async def test_generate_openai_text_long_prompt(self, mock_openai_queue, mock_successful_response):
        """Test with very long prompt."""
        long_prompt = "A" * 10000  # 10KB prompt
        mock_openai_queue.enqueue_request.return_value = mock_successful_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text(long_prompt)
            
            assert error is None
            call_args = mock_openai_queue.enqueue_request.call_args
            messages = call_args[1]["messages"]
            assert messages[1]["content"] == long_prompt

    @pytest.mark.asyncio
    async def test_generate_openai_text_special_characters(self, mock_openai_queue, mock_successful_response):
        """Test with special characters in prompt."""
        special_prompt = "Hello 世界! Test with émojis 🚀 and symbols: @#$%^&*()"
        mock_openai_queue.enqueue_request.return_value = mock_successful_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text(special_prompt)
            
            assert error is None
            call_args = mock_openai_queue.enqueue_request.call_args
            messages = call_args[1]["messages"]
            assert messages[1]["content"] == special_prompt

    @pytest.mark.asyncio
    async def test_generate_openai_text_concurrent_requests(self, mock_openai_queue, mock_successful_response):
        """Test concurrent requests to OpenAI."""
        mock_openai_queue.enqueue_request.return_value = mock_successful_response
        
        async def make_request(prompt):
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
                return await generate_openai_text(f"Prompt {prompt}")
        
        # Make 5 concurrent requests
        tasks = [make_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for result, error in results:
            assert error is None
            assert result["generated_text"] == "This is a test response from OpenAI."

    def test_module_initialization(self):
        """Test that module initializes correctly."""
        # Test that the module can be imported without errors
        import services.openai_integration
        
        # Test that the main function exists
        assert hasattr(services.openai_integration, 'generate_openai_text')
        assert callable(services.openai_integration.generate_openai_text)


class TestOpenAIIntegrationEdgeCases:
    """Test edge cases for OpenAI integration."""

    @pytest.mark.asyncio
    async def test_generate_openai_text_response_missing_choices(self, mock_openai_queue):
        """Test handling of response missing choices."""
        response_missing_choices = {
            "usage": {
                "total_tokens": 10
            }
        }
        
        mock_openai_queue.enqueue_request.return_value = response_missing_choices
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert "error" in result
            assert result["type"] == "OpenAIError"

    @pytest.mark.asyncio
    async def test_generate_openai_text_response_missing_message(self, mock_openai_queue):
        """Test handling of response missing message."""
        response_missing_message = {
            "choices": [
                {
                    # Missing message
                }
            ],
            "usage": {
                "total_tokens": 10
            }
        }
        
        mock_openai_queue.enqueue_request.return_value = response_missing_message
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert "error" in result
            assert result["type"] == "OpenAIError"

    @pytest.mark.asyncio
    async def test_generate_openai_text_response_missing_content(self, mock_openai_queue):
        """Test handling of response missing content."""
        response_missing_content = {
            "choices": [
                {
                    "message": {
                        # Missing content
                    }
                }
            ],
            "usage": {
                "total_tokens": 10
            }
        }
        
        mock_openai_queue.enqueue_request.return_value = response_missing_content
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            result, error = await generate_openai_text("Test prompt")
            
            assert error is None
            assert "error" in result
            assert result["type"] == "OpenAIError"

    @pytest.mark.asyncio
    async def test_generate_openai_text_extreme_parameters(self, mock_openai_queue, mock_successful_response):
        """Test with extreme parameter values."""
        mock_openai_queue.enqueue_request.return_value = mock_successful_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            # Test with extreme values
            result, error = await generate_openai_text(
                "Test prompt",
                max_tokens=1,
                temperature=0.0
            )
            
            assert error is None
            assert result["generated_text"] == "This is a test response from OpenAI."
