"""Official API Provider for LLM models (DeepSeek, Qwen, etc.)."""

import logging

from .openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class OfficialAPIProvider(OpenAICompatibleProvider):
    """LLM Provider for official APIs using OpenAI-compatible interface.

    Supports:
    - DeepSeek official API (https://api.deepseek.com/v1)
    - Qwen official API (https://dashscope-intl.aliyuncs.com/compatible-mode/v1)
    - Any other OpenAI-compatible API
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        timeout: int = 30
    ):
        """Initialize the Official API provider.

        Args:
            api_key: API key for authentication
            base_url: Base URL for the API endpoint
            model_name: Model name to use (e.g., "deepseek-chat", "qwen-plus")
            timeout: Request timeout in seconds
        """
        super().__init__(api_key, base_url, model_name, timeout)

        logger.info(
            "Initialized OfficialAPIProvider: %s at %s",
            model_name, base_url
        )
