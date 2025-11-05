"""Unit tests for DecisionParser."""

import pytest
from src.trading_bot.ai.decision_parser import DecisionParser, TradingDecision


class TestTradingDecision:
    """Test TradingDecision Pydantic model validation."""

    def test_valid_open_long_decision(self):
        """Test creating a valid OPEN_LONG decision."""
        decision = TradingDecision(
            reasoning="BTC shows bullish momentum",
            action="OPEN_LONG",
            coin="BTC",
            size_usd=1000.0,
            leverage=3,
            stop_loss_price=49000.0,
            take_profit_price=52000.0,
            confidence=0.75
        )

        assert decision.action == "OPEN_LONG"
        assert decision.coin == "BTC"
        assert decision.size_usd == 1000.0

    def test_valid_hold_decision(self):
        """Test creating a valid HOLD decision."""
        decision = TradingDecision(
            reasoning="No clear trading opportunity",
            action="HOLD",
            coin="BTC",
            size_usd=0.0,
            leverage=1,
            stop_loss_price=0.0,
            take_profit_price=0.0,
            confidence=0.5
        )

        assert decision.action == "HOLD"
        assert decision.size_usd == 0.0

    def test_invalid_action(self):
        """Test that invalid action raises ValueError."""
        with pytest.raises(ValueError, match="Invalid action"):
            TradingDecision(
                reasoning="Test",
                action="INVALID_ACTION",
                coin="BTC",
                size_usd=0.0,
                leverage=1,
                stop_loss_price=0.0,
                take_profit_price=0.0,
                confidence=0.5
            )

    def test_invalid_coin(self):
        """Test that invalid coin raises ValueError."""
        with pytest.raises(ValueError, match="Invalid coin"):
            TradingDecision(
                reasoning="Test",
                action="HOLD",
                coin="INVALID",
                size_usd=0.0,
                leverage=1,
                stop_loss_price=0.0,
                take_profit_price=0.0,
                confidence=0.5
            )

    def test_open_long_requires_positive_size(self):
        """Test that OPEN_LONG requires size_usd > 0."""
        with pytest.raises(ValueError, match="size_usd must be > 0"):
            TradingDecision(
                reasoning="Test",
                action="OPEN_LONG",
                coin="BTC",
                size_usd=0.0,  # Invalid
                leverage=3,
                stop_loss_price=49000.0,
                take_profit_price=52000.0,
                confidence=0.75
            )

    def test_hold_requires_zero_size(self):
        """Test that HOLD requires size_usd = 0."""
        with pytest.raises(ValueError, match="size_usd must be 0"):
            TradingDecision(
                reasoning="Test",
                action="HOLD",
                coin="BTC",
                size_usd=1000.0,  # Invalid
                leverage=1,
                stop_loss_price=0.0,
                take_profit_price=0.0,
                confidence=0.5
            )

    def test_confidence_out_of_range(self):
        """Test that confidence must be 0.0-1.0."""
        with pytest.raises(ValueError):
            TradingDecision(
                reasoning="Test",
                action="HOLD",
                coin="BTC",
                size_usd=0.0,
                leverage=1,
                stop_loss_price=0.0,
                take_profit_price=0.0,
                confidence=1.5  # Invalid
            )

    def test_leverage_out_of_range(self):
        """Test that leverage must be 1-50."""
        with pytest.raises(ValueError):
            TradingDecision(
                reasoning="Test",
                action="OPEN_LONG",
                coin="BTC",
                size_usd=1000.0,
                leverage=100,  # Invalid
                stop_loss_price=49000.0,
                take_profit_price=52000.0,
                confidence=0.75
            )


class TestDecisionParser:
    """Test DecisionParser."""

    @pytest.fixture
    def parser(self):
        """Create DecisionParser instance."""
        return DecisionParser()

    def test_parse_json_in_code_block(self, parser):
        """Test parsing JSON wrapped in markdown code block."""
        llm_response = """
Here's my decision:

```json
{
  "reasoning": "BTC shows bullish momentum with RSI at 45",
  "action": "OPEN_LONG",
  "coin": "BTC",
  "size_usd": 1000.0,
  "leverage": 3,
  "stop_loss_price": 49000.0,
  "take_profit_price": 52000.0,
  "confidence": 0.75
}
```

This is a good opportunity.
"""

        decision = parser.parse(llm_response)

        assert decision is not None
        assert decision.action == "OPEN_LONG"
        assert decision.coin == "BTC"
        assert decision.size_usd == 1000.0

    def test_parse_raw_json(self, parser):
        """Test parsing raw JSON without code block."""
        llm_response = """
{
  "reasoning": "No clear trading opportunity right now",
  "action": "HOLD",
  "coin": "BTC",
  "size_usd": 0.0,
  "leverage": 1,
  "stop_loss_price": 0.0,
  "take_profit_price": 0.0,
  "confidence": 0.5
}
"""

        decision = parser.parse(llm_response)

        assert decision is not None
        assert decision.action == "HOLD"

    def test_parse_json_with_extra_text(self, parser):
        """Test parsing JSON with extra text before and after."""
        llm_response = """
Let me analyze the market conditions...

After careful consideration, here's my decision:

{
  "reasoning": "ETH position has reached take profit target",
  "action": "CLOSE_POSITION",
  "coin": "ETH",
  "size_usd": 0.0,
  "leverage": 1,
  "stop_loss_price": 0.0,
  "take_profit_price": 0.0,
  "confidence": 0.85
}

I recommend taking profits now.
"""

        decision = parser.parse(llm_response)

        assert decision is not None
        assert decision.action == "CLOSE_POSITION"
        assert decision.coin == "ETH"

    def test_parse_invalid_json(self, parser):
        """Test that invalid JSON returns None."""
        llm_response = "This is not JSON at all!"

        decision = parser.parse(llm_response)

        assert decision is None

    def test_parse_json_missing_required_field(self, parser):
        """Test that JSON missing required field returns None."""
        llm_response = """
```json
{
  "action": "OPEN_LONG",
  "coin": "BTC"
}
```
"""

        decision = parser.parse(llm_response)

        assert decision is None

    def test_validate_decision_logic_already_has_position(self, parser):
        """Test validation catches opening position when one exists."""
        decision = TradingDecision(
            reasoning="Test reasoning for validation",
            action="OPEN_LONG",
            coin="BTC",
            size_usd=1000.0,
            leverage=3,
            stop_loss_price=49000.0,
            take_profit_price=52000.0,
            confidence=0.75
        )

        # Mock position
        class MockPosition:
            coin = "BTC"
            side = "long"

        current_positions = [MockPosition()]

        is_valid, error_msg = parser.validate_decision_logic(
            decision=decision,
            current_positions=current_positions,
            account_value=10000.0
        )

        assert not is_valid
        assert "already have" in error_msg

    def test_validate_decision_logic_position_too_large(self, parser):
        """Test validation catches position size exceeding account value."""
        decision = TradingDecision(
            reasoning="Test reasoning for validation",
            action="OPEN_LONG",
            coin="BTC",
            size_usd=20000.0,
            leverage=3,
            stop_loss_price=49000.0,
            take_profit_price=52000.0,
            confidence=0.75
        )

        is_valid, error_msg = parser.validate_decision_logic(
            decision=decision,
            current_positions=[],
            account_value=10000.0
        )

        assert not is_valid
        assert "exceeds account value" in error_msg

    def test_validate_decision_logic_close_nonexistent_position(self, parser):
        """Test validation catches closing position that doesn't exist."""
        decision = TradingDecision(
            reasoning="Test reasoning for validation",
            action="CLOSE_POSITION",
            coin="ETH",
            size_usd=0.0,
            leverage=1,
            stop_loss_price=0.0,
            take_profit_price=0.0,
            confidence=0.85
        )

        is_valid, error_msg = parser.validate_decision_logic(
            decision=decision,
            current_positions=[],
            account_value=10000.0
        )

        assert not is_valid
        assert "no position in" in error_msg

    def test_validate_decision_logic_invalid_long_prices(self, parser):
        """Test validation catches invalid stop/take profit for long."""
        decision = TradingDecision(
            reasoning="Test reasoning for validation",
            action="OPEN_LONG",
            coin="BTC",
            size_usd=1000.0,
            leverage=3,
            stop_loss_price=52000.0,  # Should be < take profit
            take_profit_price=49000.0,
            confidence=0.75
        )

        is_valid, error_msg = parser.validate_decision_logic(
            decision=decision,
            current_positions=[],
            account_value=10000.0
        )

        assert not is_valid
        assert "Invalid prices for LONG" in error_msg

    def test_validate_decision_logic_invalid_short_prices(self, parser):
        """Test validation catches invalid stop/take profit for short."""
        decision = TradingDecision(
            reasoning="Test reasoning for validation",
            action="OPEN_SHORT",
            coin="BTC",
            size_usd=1000.0,
            leverage=3,
            stop_loss_price=49000.0,
            take_profit_price=52000.0,  # Should be < stop loss
            confidence=0.75
        )

        is_valid, error_msg = parser.validate_decision_logic(
            decision=decision,
            current_positions=[],
            account_value=10000.0
        )

        assert not is_valid
        assert "Invalid prices for SHORT" in error_msg

    def test_validate_decision_logic_valid_hold(self, parser):
        """Test validation passes for valid HOLD decision."""
        decision = TradingDecision(
            reasoning="No clear opportunity",
            action="HOLD",
            coin="BTC",
            size_usd=0.0,
            leverage=1,
            stop_loss_price=0.0,
            take_profit_price=0.0,
            confidence=0.5
        )

        is_valid, error_msg = parser.validate_decision_logic(
            decision=decision,
            current_positions=[],
            account_value=10000.0
        )

        assert is_valid
        assert error_msg is None
