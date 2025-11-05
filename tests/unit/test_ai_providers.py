"""Unit tests for AI LLM providers."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.completion_usage import CompletionUsage

from src.trading_bot.ai.providers import BaseLLMProvider, OfficialAPIProvider, OpenRouterProvider


class TestBaseLLMProvider:
    """Test BaseLLMProvider abstract class."""

    def test_cannot_instantiate_directly(self):
        """Test that BaseLLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseLLMProvider("test-model")

    def test_get_stats(self):
        """Test get_stats returns correct statistics."""
        # Create a concrete implementation for testing
        class ConcreteProvider(BaseLLMProvider):
            def generate(self, prompt, max_tokens, temperature, **kwargs):
                return "test response"

            async def generate_async(self, prompt, max_tokens, temperature, **kwargs):
                return "test response"

        provider = ConcreteProvider("test-model")

        # Initial stats
        stats = provider.get_stats()
        assert stats["model_name"] == "test-model"
        assert stats["total_calls"] == 0
        assert stats["total_tokens"] == 0
        assert stats["total_time_ms"] == 0
        assert stats["avg_time_ms"] == 0

        # Simulate a request
        provider._log_request_start(100)
        provider._log_request_end(200, 50, 1000)

        stats = provider.get_stats()
        assert stats["total_calls"] == 1
        assert stats["total_tokens"] == 50
        assert stats["total_time_ms"] == 1000
        assert stats["avg_time_ms"] == 1000


class TestOfficialAPIProvider:
    """Test OfficialAPIProvider."""

    @pytest.fixture
    def mock_openai_response(self):
        """Create a mock OpenAI response."""
        return ChatCompletion(
            id="test-id",
            object="chat.completion",
            created=1234567890,
            model="deepseek-chat",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content="Test response content"
                    ),
                    finish_reason="stop"
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150
            )
        )

    def test_init(self):
        """Test provider initialization."""
        provider = OfficialAPIProvider(
            api_key="test-key",
            base_url="https://api.test.com/v1",
            model_name="test-model",
            timeout=30
        )

        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.test.com/v1"
        assert provider.model_name == "test-model"
        assert provider.timeout == 30
        assert provider.client is not None
        assert provider.async_client is not None

    @patch("src.trading_bot.ai.providers.official.OpenAI")
    def test_generate_success(self, mock_openai_class, mock_openai_response):
        """Test successful generate call."""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        provider = OfficialAPIProvider(
            api_key="test-key",
            base_url="https://api.test.com/v1",
            model_name="test-model"
        )

        # Test generate
        result = provider.generate(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )

        assert result == "Test response content"
        assert provider.total_calls == 1
        assert provider.total_tokens == 150

        # Verify API was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "test-model"
        assert call_kwargs["max_tokens"] == 100
        assert call_kwargs["temperature"] == 0.7

    @patch("src.trading_bot.ai.providers.official.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_generate_async_success(self, mock_async_openai_class, mock_openai_response):
        """Test successful generate_async call."""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_async_openai_class.return_value = mock_client

        provider = OfficialAPIProvider(
            api_key="test-key",
            base_url="https://api.test.com/v1",
            model_name="test-model"
        )

        # Test generate_async
        result = await provider.generate_async(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )

        assert result == "Test response content"
        assert provider.total_calls == 1
        assert provider.total_tokens == 150


class TestOpenRouterProvider:
    """Test OpenRouterProvider."""

    def test_init(self):
        """Test provider initialization."""
        provider = OpenRouterProvider(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model_name="deepseek/deepseek-chat",
            timeout=30
        )

        assert provider.api_key == "test-key"
        assert provider.base_url == "https://openrouter.ai/api/v1"
        assert provider.model_name == "deepseek/deepseek-chat"
        assert provider.timeout == 30
        assert provider.client is not None
        assert provider.async_client is not None

    @patch("src.trading_bot.ai.providers.openrouter.OpenAI")
    def test_generate_with_retry(self, mock_openai_class):
        """Test that generate retries on failure."""
        # Setup mock to fail twice then succeed
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            ChatCompletion(
                id="test-id",
                object="chat.completion",
                created=1234567890,
                model="deepseek/deepseek-chat",
                choices=[
                    Choice(
                        index=0,
                        message=ChatCompletionMessage(
                            role="assistant",
                            content="Success after retries"
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=CompletionUsage(
                    prompt_tokens=100,
                    completion_tokens=50,
                    total_tokens=150
                )
            )
        ]
        mock_openai_class.return_value = mock_client

        provider = OpenRouterProvider(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model_name="deepseek/deepseek-chat"
        )

        # Test generate with retries
        result = provider.generate(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )

        assert result == "Success after retries"
        assert mock_client.chat.completions.create.call_count == 3
