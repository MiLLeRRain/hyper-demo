"""Decision Parser - Parses and validates JSON decisions from LLM responses."""

import json
import re
import logging
from typing import Optional, List

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
    chain_of_thought: Optional[dict] = Field(None, description="Structured Chain of Thought for this coin")

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

    def parse(self, llm_response: str) -> List[TradingDecision]:
        """Parse and validate trading decisions from LLM response.

        Args:
            llm_response: Raw response string from LLM

        Returns:
            List of TradingDecision objects
        """
        decisions = []
        try:
            # Extract JSON from response
            json_str = self._extract_json(llm_response)

            if not json_str:
                logger.error("Failed to extract JSON from LLM response")
                return []

            # Parse JSON
            cot_dict = json.loads(json_str)

            # Iterate over each coin in the dictionary
            for coin, decision_data in cot_dict.items():
                try:
                    # Map fields to TradingDecision format
                    signal = decision_data.get("signal", "hold").lower()
                    
                    action_map = {
                        "long": "OPEN_LONG",
                        "short": "OPEN_SHORT",
                        "close": "CLOSE_POSITION",
                        "hold": "HOLD"
                    }
                    action = action_map.get(signal, "HOLD")
                    
                    # Calculate size_usd (Notional)
                    # risk_usd is usually the margin amount. Notional = risk_usd * leverage
                    risk_usd = float(decision_data.get("risk_usd", 0))
                    leverage = int(decision_data.get("leverage", 1))
                    size_usd = risk_usd * leverage
                    
                    # If action is CLOSE or HOLD, size should be 0 for validation
                    if action in ["CLOSE_POSITION", "HOLD"]:
                        size_usd = 0.0
                        stop_loss = 0.0
                        take_profit = 0.0
                        # Ensure leverage is at least 1 for validation, even if not used
                        if leverage < 1:
                            leverage = 1
                    else:
                        stop_loss = float(decision_data.get("stop_loss", 0))
                        take_profit = float(decision_data.get("profit_target", 0))

                    decision = TradingDecision(
                        reasoning=decision_data.get("justification") or decision_data.get("reasoning") or decision_data.get("analysis") or decision_data.get("invalidation_condition") or "No reasoning provided",
                        action=action,
                        coin=decision_data.get("coin", coin),
                        size_usd=size_usd,
                        leverage=leverage,
                        stop_loss_price=stop_loss,
                        take_profit_price=take_profit,
                        confidence=float(decision_data.get("confidence", 0)),
                        chain_of_thought=decision_data
                    )
                    decisions.append(decision)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse decision for {coin}: {e}")
                    continue

            logger.info(f"Parsed {len(decisions)} decisions from response")
            return decisions

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return []

        except Exception as e:
            logger.error(f"Decision parsing error: {e}")
            return []

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON string from LLM response."""
        # Look for CHAIN_OF_THOUGHT block
        if "CHAIN_OF_THOUGHT" in text:
            parts = text.split("CHAIN_OF_THOUGHT")
            if len(parts) > 1:
                # Take the part after CHAIN_OF_THOUGHT
                potential_json = parts[1]
                # If TRADING_DECISIONS exists, take content before it
                if "TRADING_DECISIONS" in potential_json:
                    potential_json = potential_json.split("TRADING_DECISIONS")[0]
                
                return potential_json.strip()

        # Fallback to code block extraction
        code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Fallback to raw JSON object
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            return match.group(0).strip()

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
