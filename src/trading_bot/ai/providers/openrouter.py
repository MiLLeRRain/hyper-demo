"""OpenRouter API Provider for accessing multiple LLM models."""

import logging

from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(OpenAICompatibleProvider):
    """LLM Provider for OpenRouter API.

    OpenRouter provides unified access to 400+ LLM models including:
    - DeepSeek (deepseek/deepseek-chat)
    - Qwen (qwen/qwen-2.5-72b-instruct)
    - Claude (anthropic/claude-3.5-sonnet)
    - GPT-4 (openai/gpt-4)
    - And many more...

    Features:
    - Zero data retention (ZDR) option
    - Pay-per-use pricing
    - Unified API for all models
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        timeout: int = 30
    ):
        """Initialize the OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            base_url: OpenRouter API base URL (usually https://openrouter.ai/api/v1)
            model_name: Full model name (e.g., "deepseek/deepseek-chat", "anthropic/claude-3.5-sonnet")
            timeout: Request timeout in seconds
        """
        super().__init__(api_key, base_url, model_name, timeout)

        logger.info(
            "Initialized OpenRouterProvider: %s via OpenRouter",
            model_name
        )
