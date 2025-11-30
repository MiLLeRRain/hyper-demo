"""Security Layer - Audits and sanitizes prompts before LLM submission."""

import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class PromptAuditor:
    """Audits and sanitizes prompts to prevent PII leakage and injection attacks.

    This layer sits between the PromptBuilder and the LLM Provider.
    It ensures that:
    1. No sensitive PII (like private keys or wallet addresses) is sent to the LLM.
    2. Potential prompt injection attempts are detected (basic heuristic).
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Prompt Auditor.

        Args:
            config: Security configuration dictionary
        """
        self.enabled = config.get("enabled", True)
        self.mask_pii = config.get("mask_pii", True)
        self.block_injection = config.get("block_injection", True)
        self.pii_patterns = config.get("pii_patterns", [])
        
        # Compile regex patterns
        self._pii_regexes = []
        if self.mask_pii:
            for pattern in self.pii_patterns:
                try:
                    self._pii_regexes.append(re.compile(pattern))
                except re.error as e:
                    logger.error(f"Invalid PII regex pattern '{pattern}': {e}")

        # Basic injection keywords (heuristic)
        self._injection_keywords = [
            "ignore previous instructions",
            "system override",
            "delete your instructions",
            "you are now a cat",
            # Add more as needed
        ]

    def audit(self, prompt: str) -> str:
        """Audit and sanitize the prompt.

        Args:
            prompt: The raw prompt string

        Returns:
            Sanitized prompt string
        """
        if not self.enabled:
            return prompt

        audited_prompt = prompt

        # 1. Check for Injection (Logging only for now, or raise exception)
        if self.block_injection:
            if self._detect_injection(audited_prompt):
                logger.warning("Potential prompt injection detected! Proceeding with caution.")
                # We could raise an exception here to block the request entirely
                # raise ValueError("Prompt injection detected")

        # 2. Mask PII
        if self.mask_pii:
            audited_prompt = self._mask_pii(audited_prompt)

        return audited_prompt

    def _detect_injection(self, prompt: str) -> bool:
        """Detect potential prompt injection attempts."""
        prompt_lower = prompt.lower()
        for keyword in self._injection_keywords:
            if keyword in prompt_lower:
                return True
        return False

    def _mask_pii(self, prompt: str) -> str:
        """Mask PII in the prompt."""
        masked_prompt = prompt
        for regex in self._pii_regexes:
            masked_prompt = regex.sub("[REDACTED_PII]", masked_prompt)
        return masked_prompt
