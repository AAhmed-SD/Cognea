import os
from unittest.mock import AsyncMock, patch

import pytest

from openai_integration import generate_text


# Helper to return a coroutine that yields the response
async def return_response(resp):
    pass
    return resp


@pytest.mark.asyncio
async def test_generate_text_success():
    pass
    mock_response = {
        "choices": [{"message": {"content": "The weather is sunny today."}}],
        "usage": {"total_tokens": 15},
    }
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch("openai_integration.get_openai_queue") as mock_get_queue:
            mock_queue = AsyncMock()
            mock_queue.enqueue_request.side_effect = lambda *a, **k: return_response(
                mock_response
            )
            mock_get_queue.return_value = mock_queue
            text, tokens = await generate_text("What is the weather like?")
            assert text == "The weather is sunny today."
            assert tokens == 15


@pytest.mark.asyncio
async def test_generate_text_with_custom_parameters():
    pass
    mock_response = {
        "choices": [{"message": {"content": "Custom response."}}],
        "usage": {"total_tokens": 10},
    }
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch("openai_integration.get_openai_queue") as mock_get_queue:
            mock_queue = AsyncMock()
            mock_queue.enqueue_request.side_effect = lambda *a, **k: return_response(
                mock_response
            )
            mock_get_queue.return_value = mock_queue
            text, tokens = await generate_text(
                "Test prompt",
                model="gpt-4",
                max_tokens=1000,
                temperature=0.3,
                stop=["."],
            )
            assert text == "Custom response."
            assert tokens == 10


@pytest.mark.asyncio
async def test_generate_text_missing_api_key():
    pass
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            await generate_text("Test prompt")


@pytest.mark.asyncio
async def test_generate_text_queue_error():
    pass
    async def raise_error(*a, **k):
        pass
        raise Exception("Queue error")

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch("openai_integration.get_openai_queue") as mock_get_queue:
            mock_queue = AsyncMock()
            mock_queue.enqueue_request.side_effect = raise_error
            mock_get_queue.return_value = mock_queue
            with pytest.raises(ValueError, match="OpenAI error: Queue error"):
                await generate_text("Test prompt")


@pytest.mark.asyncio
async def test_generate_text_invalid_response_format():
    pass
    mock_response = {"invalid": "response"}
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch("openai_integration.get_openai_queue") as mock_get_queue:
            mock_queue = AsyncMock()
            mock_queue.enqueue_request.side_effect = lambda *a, **k: return_response(
                mock_response
            )
            mock_get_queue.return_value = mock_queue
            with pytest.raises(ValueError, match="OpenAI error"):
                await generate_text("Test prompt")


@pytest.mark.asyncio
async def test_generate_text_empty_choices():
    pass
    mock_response = {"choices": [], "usage": {"total_tokens": 0}}
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch("openai_integration.get_openai_queue") as mock_get_queue:
            mock_queue = AsyncMock()
            mock_queue.enqueue_request.side_effect = lambda *a, **k: return_response(
                mock_response
            )
            mock_get_queue.return_value = mock_queue
            with pytest.raises(ValueError, match="OpenAI error"):
                await generate_text("Test prompt")


@pytest.mark.asyncio
async def test_generate_text_default_parameters():
    pass
    mock_response = {
        "choices": [{"message": {"content": "Default response."}}],
        "usage": {"total_tokens": 12},
    }
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch("openai_integration.get_openai_queue") as mock_get_queue:
            mock_queue = AsyncMock()
            mock_queue.enqueue_request.side_effect = lambda *a, **k: return_response(
                mock_response
            )
            mock_get_queue.return_value = mock_queue
            text, tokens = await generate_text("Test prompt")
            assert text == "Default response."
            assert tokens == 12


@pytest.mark.asyncio
async def test_generate_text_with_stop_sequences():
    pass
    mock_response = {
        "choices": [{"message": {"content": "Response with stop."}}],
        "usage": {"total_tokens": 8},
    }
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch("openai_integration.get_openai_queue") as mock_get_queue:
            mock_queue = AsyncMock()
            mock_queue.enqueue_request.side_effect = lambda *a, **k: return_response(
                mock_response
            )
            mock_get_queue.return_value = mock_queue
            text, tokens = await generate_text("Test prompt", stop=["END", "STOP"])
            assert text == "Response with stop."
            assert tokens == 8


@pytest.mark.asyncio
async def test_generate_text_system_message_included():
    pass
    mock_response = {
        "choices": [{"message": {"content": "System response."}}],
        "usage": {"total_tokens": 14},
    }
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch("openai_integration.get_openai_queue") as mock_get_queue:
            mock_queue = AsyncMock()
            mock_queue.enqueue_request.side_effect = lambda *a, **k: return_response(
                mock_response
            )
            mock_get_queue.return_value = mock_queue
            await generate_text("Test prompt")
            # The test passes if no exception is raised
