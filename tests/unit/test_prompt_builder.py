"""Unit tests for PromptBuilder."""

import pytest
from datetime import datetime
from src.trading_bot.ai.prompt_builder import PromptBuilder
from src.trading_bot.models.market_data import AccountInfo, Position


class TestPromptBuilder:
    """Test PromptBuilder."""

    @pytest.fixture
    def builder(self):
        """Create PromptBuilder instance."""
        return PromptBuilder()

    @pytest.fixture
    def mock_agent(self):
        """Create mock trading agent."""
        class MockAgent:
            name = "Test Agent"
            max_position_size = 20.0
            max_leverage = 10
            stop_loss_pct = 2.0
            take_profit_pct = 5.0
            strategy_description = "Follow technical indicators"

        return MockAgent()

    @pytest.fixture
    def mock_account(self):
        """Create mock account info."""
        return AccountInfo(
            account_value=10000.0,
            withdrawable=8000.0,
            margin_used=2000.0,
            unrealized_pnl=500.0
        )

    @pytest.fixture
    def mock_positions(self):
        """Create mock positions."""
        return [
            Position(
                coin="BTC",
                side="long",
                size=0.1,
                entry_price=50000.0,
                mark_price=51000.0,
                position_value=5100.0,
                unrealized_pnl=100.0,
                leverage=5,
                liquidation_price=45000.0
            ),
            Position(
                coin="ETH",
                side="short",
                size=2.0,
                entry_price=3000.0,
                mark_price=2950.0,
                position_value=5900.0,
                unrealized_pnl=100.0,
                leverage=3,
                liquidation_price=3500.0
            )
        ]

    @pytest.fixture
    def mock_market_data(self):
        """Create mock market data."""
        return {
            "BTC": {
                "price": 51000.0,
                "3m": {
                    "ema": 50500.0,
                    "macd": 150.5,
                    "macd_signal": 120.0,
                    "rsi": 65.5,
                    "atr": 500.0
                },
                "4h": {
                    "ema": 50000.0,
                    "macd": 200.0,
                    "macd_signal": 180.0,
                    "rsi": 60.0,
                    "atr": 800.0
                }
            },
            "ETH": {
                "price": 2950.0,
                "3m": {
                    "ema": 2980.0,
                    "macd": -20.5,
                    "macd_signal": -15.0,
                    "rsi": 45.0,
                    "atr": 50.0
                },
                "4h": {
                    "ema": 3000.0,
                    "macd": -50.0,
                    "macd_signal": -40.0,
                    "rsi": 42.0,
                    "atr": 80.0
                }
            },
            "SOL": {
                "price": 150.0,
                "3m": {
                    "ema": 149.0,
                    "macd": 2.5,
                    "macd_signal": 2.0,
                    "rsi": 55.0,
                    "atr": 5.0
                },
                "4h": {
                    "ema": 148.0,
                    "macd": 5.0,
                    "macd_signal": 4.0,
                    "rsi": 58.0,
                    "atr": 8.0
                }
            },
            "BNB": {
                "price": 300.0,
                "3m": {
                    "ema": 298.0,
                    "macd": 1.5,
                    "macd_signal": 1.0,
                    "rsi": 52.0,
                    "atr": 3.0
                },
                "4h": {
                    "ema": 297.0,
                    "macd": 3.0,
                    "macd_signal": 2.5,
                    "rsi": 54.0,
                    "atr": 5.0
                }
            },
            "DOGE": {
                "price": 0.08,
                "3m": {
                    "ema": 0.079,
                    "macd": 0.001,
                    "macd_signal": 0.0008,
                    "rsi": 50.0,
                    "atr": 0.002
                },
                "4h": {
                    "ema": 0.078,
                    "macd": 0.002,
                    "macd_signal": 0.0015,
                    "rsi": 51.0,
                    "atr": 0.003
                }
            },
            "XRP": {
                "price": 0.55,
                "3m": {
                    "ema": 0.54,
                    "macd": 0.01,
                    "macd_signal": 0.008,
                    "rsi": 58.0,
                    "atr": 0.01
                },
                "4h": {
                    "ema": 0.53,
                    "macd": 0.02,
                    "macd_signal": 0.015,
                    "rsi": 60.0,
                    "atr": 0.015
                }
            }
        }

    def test_build_prompt_structure(
        self,
        builder,
        mock_market_data,
        mock_positions,
        mock_account,
        mock_agent
    ):
        """Test that build() returns a well-structured prompt."""
        prompt = builder.build(
            market_data=mock_market_data,
            positions=mock_positions,
            account=mock_account,
            agent=mock_agent
        )

        # Check that prompt is a string
        assert isinstance(prompt, str)

        # Check that prompt is long enough (should be ~11k chars)
        assert len(prompt) > 5000

        # Check that all major sections are present
        assert "HyperLiquid AI Trading System" in prompt
        assert "Portfolio Status" in prompt
        assert "Market Data" in prompt
        assert "Risk Management Constraints" in prompt
        assert "Your Task" in prompt

    def test_build_header_section(self, builder, mock_agent):
        """Test _build_header creates proper header."""
        header = builder._build_header(mock_agent)

        assert "HyperLiquid AI Trading System" in header
        assert "Current Time:" in header
        assert "UTC" in header
        assert "trading agent" in header.lower()
        # Should include strategy description
        assert "Follow technical indicators" in header

    def test_build_portfolio_section_with_positions(
        self,
        builder,
        mock_account,
        mock_positions
    ):
        """Test _build_portfolio_section with positions."""
        section = builder._build_portfolio_section(mock_account, mock_positions)

        # Check account balance info
        assert "$10,000.00" in section
        assert "$8,000.00" in section
        assert "$2,000.00" in section
        assert "$500.00" in section

        # Check positions
        assert "BTC" in section
        assert "ETH" in section
        assert "long" in section.lower()
        assert "short" in section.lower()
        assert "50,000.00" in section  # BTC entry price
        assert "3,000.00" in section  # ETH entry price

    def test_build_portfolio_section_no_positions(self, builder, mock_account):
        """Test _build_portfolio_section with no positions."""
        section = builder._build_portfolio_section(mock_account, [])

        assert "None (all cash)" in section
        assert "$10,000.00" in section

    def test_build_market_data_section(self, builder, mock_market_data):
        """Test _build_market_data_section includes all coins."""
        section = builder._build_market_data_section(mock_market_data)

        # Check all coins are included
        for coin in ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"]:
            assert coin in section

        # Check technical indicators are included
        assert "EMA" in section
        assert "MACD" in section
        assert "RSI" in section
        assert "ATR" in section

        # Check timeframes are included
        assert "3M" in section
        assert "4H" in section

        # Check specific values
        assert "51,000.00" in section  # BTC price
        assert "2,950.00" in section  # ETH price

    def test_build_market_data_section_missing_coin(self, builder):
        """Test _build_market_data_section handles missing coin data."""
        market_data = {
            "BTC": {
                "price": 51000.0,
                "3m": {"ema": 50500.0, "macd": 150.5, "macd_signal": 120.0, "rsi": 65.5, "atr": 500.0},
                "4h": {"ema": 50000.0, "macd": 200.0, "macd_signal": 180.0, "rsi": 60.0, "atr": 800.0}
            }
            # Missing ETH, SOL, etc.
        }

        section = builder._build_market_data_section(market_data)

        # Should only include BTC
        assert "BTC" in section
        assert "ETH" not in section

    def test_build_constraints_section(self, builder, mock_agent):
        """Test _build_constraints_section includes risk rules."""
        section = builder._build_constraints_section(mock_agent)

        # Check risk management rules
        assert "Risk Management Constraints" in section
        assert "20.0%" in section  # max_position_size
        assert "10x" in section  # max_leverage
        assert "2.0%" in section  # stop_loss_pct
        assert "5.0%" in section  # take_profit_pct
        assert "Follow technical indicators" in section  # strategy_description

    def test_build_task_section(self, builder):
        """Test _build_task_section includes JSON format."""
        section = builder._build_task_section()

        # Check task instructions
        assert "Your Task" in section
        assert "JSON object" in section

        # Check JSON fields are documented
        assert "reasoning" in section
        assert "action" in section
        assert "coin" in section
        assert "size_usd" in section
        assert "leverage" in section
        assert "stop_loss_price" in section
        assert "take_profit_price" in section
        assert "confidence" in section

        # Check action types
        assert "OPEN_LONG" in section
        assert "OPEN_SHORT" in section
        assert "CLOSE_POSITION" in section
        assert "HOLD" in section

        # Check examples are present
        assert "Example" in section

    def test_build_full_prompt_length(
        self,
        builder,
        mock_market_data,
        mock_positions,
        mock_account,
        mock_agent
    ):
        """Test that full prompt is reasonable length (~11k chars)."""
        prompt = builder.build(
            market_data=mock_market_data,
            positions=mock_positions,
            account=mock_account,
            agent=mock_agent
        )

        # Should be between 5k and 20k characters
        assert 5000 < len(prompt) < 20000

    def test_build_prompt_no_positions(
        self,
        builder,
        mock_market_data,
        mock_account,
        mock_agent
    ):
        """Test building prompt with no positions."""
        prompt = builder.build(
            market_data=mock_market_data,
            positions=[],
            account=mock_account,
            agent=mock_agent
        )

        assert "None (all cash)" in prompt
        assert len(prompt) > 5000
