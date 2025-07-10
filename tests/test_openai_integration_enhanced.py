import pytest
import asyncio
import os
from unittest.mock import MagicMock, patch, AsyncMock
from tenacity import RetryError

from services.openai_integration import generate_openai_text


class TestOpenAIIntegration:
    """Test OpenAI integration functionality."""

    @pytest.fixture
    def mock_openai_queue(self):
        """Mock OpenAI queue."""
        mock_queue = MagicMock()
        mock_queue.enqueue_request = AsyncMock()
        return mock_queue

    @pytest.fixture
    def sample_openai_response(self):
        """Sample OpenAI API response."""
        return {
            "choices": [
                {
                    "message": {
                        "content": "This is a generated response from OpenAI."
                    }
                }
            ],
            "usage": {
                "total_tokens": 50,
                "prompt_tokens": 20,
                "completion_tokens": 30
            }
        }

    @pytest.mark.asyncio
    async def test_generate_openai_text_success(self, mock_openai_queue, sample_openai_response):
        """Test successful OpenAI text generation."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            # Mock successful response
            mock_openai_queue.enqueue_request.return_value = sample_openai_response
            
            result, error = await generate_openai_text("Test prompt")
            
            # Verify result
            assert error is None
            assert "generated_text" in result
            assert "total_tokens" in result
            assert result["generated_text"] == "This is a generated response from OpenAI."
            assert result["total_tokens"] == 50
            
            # Verify queue was called correctly
            mock_openai_queue.enqueue_request.assert_called_once()
            call_args = mock_openai_queue.enqueue_request.call_args
            assert call_args[1]["method"] == "POST"
            assert call_args[1]["endpoint"] == "chat/completions"
            assert call_args[1]["api_key"] == "test_key"

    @pytest.mark.asyncio
    async def test_generate_openai_text_custom_parameters(self, mock_openai_queue, sample_openai_response):
        """Test OpenAI text generation with custom parameters."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            mock_openai_queue.enqueue_request.return_value = sample_openai_response
            
            result, error = await generate_openai_text(
                prompt="Custom prompt",
                model="gpt-4",
                max_tokens=1000,
                temperature=0.9,
                stop=[".", "!"]
            )
            
            # Verify custom parameters were passed
            call_args = mock_openai_queue.enqueue_request.call_args[1]
            assert call_args["model"] == "gpt-4"
            assert call_args["max_tokens"] == 1000
            assert call_args["temperature"] == 0.9
            assert call_args["stop"] == [".", "!"]
            
            # Verify messages structure
            messages = call_args["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "You are a helpful productivity assistant."
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "Custom prompt"

    @pytest.mark.asyncio
    async def test_generate_openai_text_missing_api_key(self, mock_openai_queue):
        """Test OpenAI text generation without API key."""
        with patch.dict('os.environ', {}, clear=True), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                await generate_openai_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_openai_text_empty_api_key(self, mock_openai_queue):
        """Test OpenAI text generation with empty API key."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': ''}), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                await generate_openai_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_openai_text_queue_error(self, mock_openai_queue):
        """Test OpenAI text generation with queue error."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            # Mock queue error
            mock_openai_queue.enqueue_request.side_effect = Exception("Queue error")
            
            result, error = await generate_openai_text("Test prompt")
            
            # Verify error handling
            assert error is None  # Function returns (result, None) even on error
            assert "error" in result
            assert "type" in result
            assert result["error"] == "Queue error"
            assert result["type"] == "OpenAIError"

    @pytest.mark.asyncio
    async def test_generate_openai_text_response_without_usage(self, mock_openai_queue):
        """Test OpenAI text generation with response missing usage data."""
        response_without_usage = {
            "choices": [
                {
                    "message": {
                        "content": "Response without usage data."
                    }
                }
            ]
        }
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            mock_openai_queue.enqueue_request.return_value = response_without_usage
            
            result, error = await generate_openai_text("Test prompt")
            
            # Verify handling of missing usage data
            assert error is None
            assert result["generated_text"] == "Response without usage data."
            assert result["total_tokens"] is None

    @pytest.mark.asyncio
    async def test_generate_openai_text_whitespace_handling(self, mock_openai_queue):
        """Test OpenAI text generation with whitespace in response."""
        response_with_whitespace = {
            "choices": [
                {
                    "message": {
                        "content": "  \n  Response with whitespace  \n  "
                    }
                }
            ],
            "usage": {"total_tokens": 25}
        }
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            mock_openai_queue.enqueue_request.return_value = response_with_whitespace
            
            result, error = await generate_openai_text("Test prompt")
            
            # Verify whitespace is stripped
            assert result["generated_text"] == "Response with whitespace"

    @pytest.mark.asyncio
    async def test_generate_openai_text_default_parameters(self, mock_openai_queue, sample_openai_response):
        """Test OpenAI text generation with default parameters."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            mock_openai_queue.enqueue_request.return_value = sample_openai_response
            
            await generate_openai_text("Test prompt")
            
            # Verify default parameters
            call_args = mock_openai_queue.enqueue_request.call_args[1]
            assert call_args["model"] == "gpt-3.5-turbo"
            assert call_args["max_tokens"] == 500
            assert call_args["temperature"] == 0.7
            assert call_args["stop"] is None
            assert call_args["n"] == 1

    @pytest.mark.asyncio
    async def test_generate_openai_text_payload_structure(self, mock_openai_queue, sample_openai_response):
        """Test that the payload structure is correct."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            mock_openai_queue.enqueue_request.return_value = sample_openai_response
            
            await generate_openai_text("Test prompt")
            
            # Verify payload structure
            call_args = mock_openai_queue.enqueue_request.call_args[1]
            
            # Required fields
            assert "model" in call_args
            assert "messages" in call_args
            assert "max_tokens" in call_args
            assert "temperature" in call_args
            assert "stop" in call_args
            assert "n" in call_args
            assert "method" in call_args
            assert "endpoint" in call_args
            assert "api_key" in call_args

    @pytest.mark.asyncio
    async def test_generate_openai_text_retry_mechanism(self, mock_openai_queue):
        """Test retry mechanism with transient failures."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            # Mock transient failure followed by success
            mock_openai_queue.enqueue_request.side_effect = [
                Exception("Temporary error"),
                Exception("Another temporary error"),
                {
                    "choices": [{"message": {"content": "Success after retries"}}],
                    "usage": {"total_tokens": 30}
                }
            ]
            
            result, error = await generate_openai_text("Test prompt")
            
            # Should succeed after retries
            assert error is None
            assert result["generated_text"] == "Success after retries"
            assert mock_openai_queue.enqueue_request.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_openai_text_max_retries_exceeded(self, mock_openai_queue):
        """Test behavior when max retries are exceeded."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            # Mock persistent failure
            mock_openai_queue.enqueue_request.side_effect = Exception("Persistent error")
            
            result, error = await generate_openai_text("Test prompt")
            
            # Should handle max retries gracefully
            assert error is None
            assert "error" in result
            assert "Persistent error" in result["error"]
            assert mock_openai_queue.enqueue_request.call_count == 3  # Default retry count


class TestOpenAIIntegrationLogging:
    """Test OpenAI integration logging."""

    def test_logger_exists(self):
        """Test that logger is properly configured."""
        from services.openai_integration import logger
        
        assert logger is not None
        assert logger.name == "services.openai_integration"

    def test_initialization_logging(self):
        """Test that initialization is logged."""
        with patch('services.openai_integration.logger') as mock_logger:
            # Re-import to trigger initialization
            import importlib
            import services.openai_integration
            importlib.reload(services.openai_integration)
            
            # Verify initialization was logged
            mock_logger.info.assert_called_with("OpenAI integration initialized successfully")

    @pytest.mark.asyncio
    async def test_error_logging(self, mock_openai_queue=None):
        """Test that errors are properly logged."""
        if mock_openai_queue is None:
            mock_openai_queue = MagicMock()
            mock_openai_queue.enqueue_request = AsyncMock()
        
        with patch.dict('os.environ', {}, clear=True), \
             patch('services.openai_integration.logger') as mock_logger, \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            try:
                await generate_openai_text("Test prompt")
            except ValueError:
                pass  # Expected
            
            # Verify error was logged
            mock_logger.error.assert_called_with("OpenAI API key not found in environment variables")


class TestOpenAIIntegrationEnvironment:
    """Test OpenAI integration environment handling."""

    def test_dotenv_loading(self):
        """Test that dotenv is loaded."""
        # Verify load_dotenv is called during import
        with patch('services.openai_integration.load_dotenv') as mock_load_dotenv:
            import importlib
            import services.openai_integration
            importlib.reload(services.openai_integration)
            
            mock_load_dotenv.assert_called_once()

    @pytest.mark.asyncio
    async def test_environment_variable_handling(self, mock_openai_queue=None):
        """Test environment variable handling."""
        if mock_openai_queue is None:
            mock_openai_queue = MagicMock()
            mock_openai_queue.enqueue_request = AsyncMock()
            mock_openai_queue.enqueue_request.return_value = {
                "choices": [{"message": {"content": "Test response"}}],
                "usage": {"total_tokens": 10}
            }
        
        # Test with various API key values
        test_cases = [
            ("valid_key", True),
            ("", False),
            (None, False),
        ]
        
        for api_key, should_succeed in test_cases:
            env_dict = {"OPENAI_API_KEY": api_key} if api_key is not None else {}
            
            with patch.dict('os.environ', env_dict, clear=True), \
                 patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
                
                if should_succeed:
                    result, error = await generate_openai_text("Test")
                    assert error is None
                    assert "generated_text" in result
                else:
                    with pytest.raises(ValueError):
                        await generate_openai_text("Test")


class TestOpenAIIntegrationIntegration:
    """Integration tests for OpenAI integration."""

    def test_module_imports(self):
        """Test that all required modules can be imported."""
        from services.openai_integration import generate_openai_text, logger
        
        assert callable(generate_openai_text)
        assert logger is not None

    def test_queue_integration(self):
        """Test integration with rate limited queue."""
        with patch('services.openai_integration.get_openai_queue') as mock_get_queue:
            mock_queue = MagicMock()
            mock_get_queue.return_value = mock_queue
            
            # Import should call get_openai_queue during function execution
            from services.openai_integration import generate_openai_text
            assert callable(generate_openai_text)

    @pytest.mark.asyncio
    async def test_async_functionality(self, mock_openai_queue=None):
        """Test that async functionality works correctly."""
        if mock_openai_queue is None:
            mock_openai_queue = MagicMock()
            mock_openai_queue.enqueue_request = AsyncMock()
            mock_openai_queue.enqueue_request.return_value = {
                "choices": [{"message": {"content": "Async test response"}}],
                "usage": {"total_tokens": 15}
            }
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}), \
             patch('services.openai_integration.get_openai_queue', return_value=mock_openai_queue):
            
            # Test that function is properly async
            result = generate_openai_text("Test prompt")
            assert asyncio.iscoroutine(result)
            
            # Test that it can be awaited
            response, error = await result
            assert error is None
            assert response["generated_text"] == "Async test response"

    def test_tenacity_configuration(self):
        """Test that tenacity retry configuration is applied."""
        from services.openai_integration import generate_openai_text
        
        # Check that the function has retry decoration
        assert hasattr(generate_openai_text, 'retry')
        
        # Verify retry configuration
        retry_state = generate_openai_text.retry
        assert retry_state.stop.max_attempt_number == 3