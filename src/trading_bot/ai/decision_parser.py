"""Decision Parser - Parses and validates JSON decisions from LLM responses."""

import json
import re
import logging
from typing import Optional

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class TradingDecision(BaseModel):
    """Trading decision from an AI agent.

    This model validates the JSON output from LLM agents to ensure
    all required fields are present and valid.
    """

    reasoning: str = Field(..., min_length=10, description="Explanation of the decision")
    action: str = Field(..., description="Trading action to take")
    coin: str = Field(..., description="Cryptocurrency symbol")
    size_usd: float = Field(..., ge=0, description="Position size in USD")
    leverage: int = Field(..., ge=1, le=50, description="Leverage multiplier")
    stop_loss_price: float = Field(..., ge=0, description="Stop loss price")
    take_profit_price: float = Field(..., ge=0, description="Take profit price")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")

    @validator("action")
    def validate_action(cls, v):
        """Validate action is one of the allowed types."""
        allowed_actions = ["OPEN_LONG", "OPEN_SHORT", "CLOSE_POSITION", "HOLD"]
        if v not in allowed_actions:
            raise ValueError(
                f"Invalid action '{v}'. Must be one of: {allowed_actions}"
            )
        return v

    @validator("coin")
    def validate_coin(cls, v):
        """Validate coin is one of the supported coins."""
        allowed_coins = ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"]
        if v not in allowed_coins:
            raise ValueError(
                f"Invalid coin '{v}'. Must be one of: {allowed_coins}"
            )
        return v

    @validator("size_usd")
    def validate_size(cls, v, values):
        """Validate size_usd is appropriate for the action."""
        action = values.get("action")
        if action in ["OPEN_LONG", "OPEN_SHORT"]:
            if v <= 0:
                raise ValueError(
                    f"size_usd must be > 0 for action '{action}', got {v}"
                )
        elif action in ["CLOSE_POSITION", "HOLD"]:
            if v != 0:
                raise ValueError(
                    f"size_usd must be 0 for action '{action}', got {v}"
                )
        return v

    @validator("leverage")
    def validate_leverage(cls, v, values):
        """Validate leverage is appropriate for the action."""
        action = values.get("action")
        if action in ["OPEN_LONG", "OPEN_SHORT"]:
            if v < 1 or v > 50:
                raise ValueError(
                    f"leverage must be 1-50 for action '{action}', got {v}"
                )
        return v

    @validator("stop_loss_price")
    def validate_stop_loss(cls, v, values):
        """Validate stop_loss_price is appropriate for the action."""
        action = values.get("action")
        if action in ["OPEN_LONG", "OPEN_SHORT"]:
            if v <= 0:
                raise ValueError(
                    f"stop_loss_price must be > 0 for action '{action}', got {v}"
                )
        elif action in ["CLOSE_POSITION", "HOLD"]:
            if v != 0:
                raise ValueError(
                    f"stop_loss_price must be 0 for action '{action}', got {v}"
                )
        return v

    @validator("take_profit_price")
    def validate_take_profit(cls, v, values):
        """Validate take_profit_price is appropriate for the action."""
        action = values.get("action")
        if action in ["OPEN_LONG", "OPEN_SHORT"]:
            if v <= 0:
                raise ValueError(
                    f"take_profit_price must be > 0 for action '{action}', got {v}"
                )
        elif action in ["CLOSE_POSITION", "HOLD"]:
            if v != 0:
                raise ValueError(
                    f"take_profit_price must be 0 for action '{action}', got {v}"
                )
        return v


class DecisionParser:
    """Parses JSON trading decisions from LLM responses.

    LLMs often return JSON wrapped in markdown code blocks or with
    additional explanatory text. This parser extracts and validates
    the JSON decision.
    """

    def __init__(self):
        """Initialize the Decision Parser."""
        pass

    def parse(self, llm_response: str) -> Optional[TradingDecision]:
        """Parse and validate a trading decision from LLM response.

        Args:
            llm_response: Raw response string from LLM

        Returns:
            TradingDecision object if parsing succeeds, None otherwise
        """
        try:
            # Extract JSON from response
            json_str = self._extract_json(llm_response)

            if not json_str:
                logger.error("Failed to extract JSON from LLM response")
                logger.debug(f"LLM response: {llm_response[:500]}")
                return None

            # Parse JSON
            decision_dict = json.loads(json_str)

            # Validate with Pydantic model
            decision = TradingDecision(**decision_dict)

            logger.info(
                f"Parsed decision: {decision.action} {decision.coin} "
                f"| Confidence: {decision.confidence:.2f}"
            )

            return decision

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.debug(f"JSON string: {json_str}")
            return None

        except Exception as e:
            logger.error(f"Decision parsing error: {e}")
            logger.debug(f"LLM response: {llm_response[:500]}")
            return None

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON string from LLM response.

        LLMs often wrap JSON in markdown code blocks like:
        ```json
        { ... }
        ```

        Or include extra text before/after the JSON.

        Args:
            text: Raw text from LLM

        Returns:
            JSON string if found, None otherwise
        """
        # Try to find JSON in markdown code block
        # Pattern: ```json ... ``` or ``` ... ```
        code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        match = re.search(code_block_pattern, text, re.DOTALL)

        if match:
            logger.debug("Found JSON in markdown code block")
            return match.group(1).strip()

        # Try to find raw JSON object
        # Pattern: { ... }
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        match = re.search(json_pattern, text, re.DOTALL)

        if match:
            logger.debug("Found raw JSON object")
            return match.group(0).strip()

        # Try to find JSON that spans multiple lines
        # More aggressive pattern for nested structures
        try:
            # Find the first { and last }
            start_idx = text.find("{")
            end_idx = text.rfind("}")

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                potential_json = text[start_idx : end_idx + 1]

                # Validate it's actually JSON
                json.loads(potential_json)

                logger.debug("Found JSON using aggressive search")
                return potential_json

        except (json.JSONDecodeError, Exception):
            pass

        logger.warning("Could not extract JSON from response")
        return None

    def validate_decision_logic(
        self,
        decision: TradingDecision,
        current_positions: list,
        account_value: float
    ) -> tuple[bool, Optional[str]]:
        """Validate decision logic against current portfolio state.

        Additional validation beyond Pydantic schema validation.

        Args:
            decision: Parsed trading decision
            current_positions: List of current positions
            account_value: Current account value in USD

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, "error message") if invalid
        """
        # Check if trying to open position when one already exists
        if decision.action in ["OPEN_LONG", "OPEN_SHORT"]:
            for pos in current_positions:
                if pos.coin == decision.coin:
                    return (
                        False,
                        f"Cannot open new position: already have {pos.side} position in {decision.coin}",
                    )

            # Check if position size is reasonable relative to account
            if decision.size_usd > account_value:
                return (
                    False,
                    f"Position size ${decision.size_usd:.2f} exceeds account value ${account_value:.2f}",
                )

        # Check if trying to close non-existent position
        elif decision.action == "CLOSE_POSITION":
            has_position = any(pos.coin == decision.coin for pos in current_positions)
            if not has_position:
                return (
                    False,
                    f"Cannot close position: no position in {decision.coin}",
                )

        # Validate stop loss and take profit logic
        if decision.action == "OPEN_LONG":
            # For long: stop loss < current price < take profit
            # We don't have current price here, but we can check stop < take
            if decision.stop_loss_price >= decision.take_profit_price:
                return (
                    False,
                    f"Invalid prices for LONG: stop_loss ({decision.stop_loss_price}) must be < take_profit ({decision.take_profit_price})",
                )

        elif decision.action == "OPEN_SHORT":
            # For short: take profit < current price < stop loss
            # Check take < stop
            if decision.take_profit_price >= decision.stop_loss_price:
                return (
                    False,
                    f"Invalid prices for SHORT: take_profit ({decision.take_profit_price}) must be < stop_loss ({decision.stop_loss_price})",
                )

        return (True, None)
