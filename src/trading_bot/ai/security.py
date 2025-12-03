"""Security Layer - Audits and sanitizes prompts before LLM submission."""

import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.trading_bot.models.database import SecurityEvent
from src.trading_bot.infrastructure.database import DatabaseManager

logger = logging.getLogger(__name__)


class PromptAuditor:
    """Audits and sanitizes prompts to prevent PII leakage and injection attacks.

    This layer sits between the PromptBuilder and the LLM Provider.
    It ensures that:
    1. No sensitive PII (like private keys or wallet addresses) is sent to the LLM.
    2. Potential prompt injection attempts are detected (basic heuristic).
    """

    def __init__(self, config: Dict[str, Any], db_manager: Optional[DatabaseManager] = None):
        """Initialize the Prompt Auditor.

        Args:
            config: Security configuration dictionary
            db_manager: Database manager for logging events (optional)
        """
        self.enabled = config.get("enabled", True)
        self.mask_pii = config.get("mask_pii", True)
        self.block_injection = config.get("block_injection", True)
        self.pii_patterns = config.get("pii_patterns", [])
        self.db_manager = db_manager
        
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

    def audit(self, prompt: str, agent_id: Optional[str] = None) -> str:
        """Audit and sanitize the prompt.

        Args:
            prompt: The raw prompt string
            agent_id: ID of the agent generating the prompt (optional)

        Returns:
            Sanitized prompt string
        """
        if not self.enabled:
            return prompt

        audited_prompt = prompt

        # 1. Check for Injection (Logging only for now, or raise exception)
        if self.block_injection:
            if self._detect_injection(audited_prompt):
                msg = "Potential prompt injection detected! Proceeding with caution."
                logger.warning(msg)
                self._log_event(
                    event_type="injection_attempt",
                    severity="high",
                    description=msg,
                    original_content=prompt[:1000], # Store snippet
                    agent_id=agent_id
                )
                # We could raise an exception here to block the request entirely
                # raise ValueError("Prompt injection detected")

        # 2. Mask PII
        if self.mask_pii:
            audited_prompt, masked_count = self._mask_pii(audited_prompt)
            if masked_count > 0:
                self._log_event(
                    event_type="pii_leakage",
                    severity="medium",
                    description=f"Masked {masked_count} PII instances",
                    original_content=None, # Don't store PII
                    agent_id=agent_id
                )

        return audited_prompt

    def _detect_injection(self, prompt: str) -> bool:
        """Detect potential prompt injection attempts."""
        prompt_lower = prompt.lower()
        for keyword in self._injection_keywords:
            if keyword in prompt_lower:
                return True
        return False

    def _mask_pii(self, prompt: str) -> tuple[str, int]:
        """Mask PII in the prompt.
        
        Returns:
            Tuple of (masked_prompt, count_of_replacements)
        """
        masked_prompt = prompt
        count = 0
        for regex in self._pii_regexes:
            # Count matches first
            matches = regex.findall(masked_prompt)
            count += len(matches)
            # Replace
            masked_prompt = regex.sub("[REDACTED_PII]", masked_prompt)
        return masked_prompt, count

    def _log_event(
        self, 
        event_type: str, 
        severity: str, 
        description: str, 
        original_content: Optional[str] = None,
        agent_id: Optional[str] = None
    ):
        """Log security event to database."""
        if not self.db_manager:
            return

        try:
            with self.db_manager.session_scope() as session:
                event = SecurityEvent(
                    event_type=event_type,
                    severity=severity,
                    description=description,
                    original_content=original_content,
                    agent_id=agent_id
                )
                session.add(event)
                # Commit handled by session_scope
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

