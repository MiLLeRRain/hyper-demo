"""Base LLM Provider abstract class."""

from abc import ABC, abstractmethod
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers.

    All LLM providers (OfficialAPIProvider, OpenRouterProvider) must inherit
    from this class and implement the generate() and generate_async() methods.
    """

    def __init__(self, model_name: str):
        """Initialize the LLM provider.

        Args:
            model_name: The name of the LLM model (e.g., "deepseek-chat", "qwen-plus")
        """
        self.model_name = model_name
        self.total_calls = 0
        self.total_tokens = 0
        self.total_time_ms = 0

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Generate AI response synchronously.

        Args:
            prompt: The input prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional provider-specific parameters

        Returns:
            The generated text response

        Raises:
            Exception: If the API call fails after retries
        """
        pass

    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Generate AI response asynchronously.

        Args:
            prompt: The input prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional provider-specific parameters

        Returns:
            The generated text response

        Raises:
            Exception: If the API call fails after retries
        """
        pass

    def _log_request_start(self, prompt_length: int):
        """Log the start of an API request."""
        logger.info(
            f"[{self.model_name}] Starting generation | "
            f"Prompt length: {prompt_length} chars"
        )

    def _log_request_end(
        self,
        response_length: int,
        tokens_used: Optional[int],
        duration_ms: int
    ):
        """Log the completion of an API request."""
        self.total_calls += 1
        self.total_time_ms += duration_ms

        if tokens_used:
            self.total_tokens += tokens_used

        logger.info(
            f"[{self.model_name}] Generation complete | "
            f"Response: {response_length} chars | "
            f"Tokens: {tokens_used or 'N/A'} | "
            f"Time: {duration_ms}ms"
        )

    def get_stats(self) -> dict:
        """Get provider statistics.

        Returns:
            Dictionary containing usage statistics
        """
        return {
            "model_name": self.model_name,
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "total_time_ms": self.total_time_ms,
            "avg_time_ms": self.total_time_ms / self.total_calls if self.total_calls > 0 else 0
        }
