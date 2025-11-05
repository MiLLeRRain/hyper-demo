"""OpenRouter API Provider for accessing multiple LLM models."""

import time
import logging
from typing import Optional

from openai import OpenAI, AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseLLMProvider):
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
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

        # Initialize sync and async clients
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )

        logger.info(
            f"Initialized OpenRouterProvider: {model_name} via OpenRouter"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Generate AI response synchronously via OpenRouter.

        Args:
            prompt: The input prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional parameters for the API

        Returns:
            The generated text response

        Raises:
            Exception: If the API call fails after 3 retries
        """
        start_time = time.time()
        self._log_request_start(len(prompt))

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            duration_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None

            self._log_request_end(len(content), tokens_used, duration_ms)

            return content

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[{self.model_name}] OpenRouter API call failed after {duration_ms}ms: {e}"
            )
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def generate_async(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Generate AI response asynchronously via OpenRouter.

        Args:
            prompt: The input prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional parameters for the API

        Returns:
            The generated text response

        Raises:
            Exception: If the API call fails after 3 retries
        """
        start_time = time.time()
        self._log_request_start(len(prompt))

        try:
            response = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            duration_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None

            self._log_request_end(len(content), tokens_used, duration_ms)

            return content

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[{self.model_name}] Async OpenRouter API call failed after {duration_ms}ms: {e}"
            )
            raise
