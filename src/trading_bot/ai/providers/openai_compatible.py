"""OpenAI Compatible API Provider."""

import time
import logging

from openai import OpenAI, AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseLLMProvider):
    """Base provider for OpenAI-compatible APIs."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        timeout: int = 30
    ):
        """Initialize the OpenAI-compatible provider.

        Args:
            api_key: API key for authentication
            base_url: Base URL for the API endpoint
            model_name: Model name to use
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
        """Generate AI response synchronously.

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
                "[%s] API call failed after %dms: %s",
                self.model_name, duration_ms, e
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
        """Generate AI response asynchronously.

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
                "[%s] Async API call failed after %dms: %s",
                self.model_name, duration_ms, e
            )
            raise
