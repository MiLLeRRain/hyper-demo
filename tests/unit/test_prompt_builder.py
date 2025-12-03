"""Unit tests for PromptBuilder."""

import pytest
import pandas as pd
from datetime import datetime
from src.trading_bot.ai.prompt_builder import PromptBuilder
from src.trading_bot.models.market_data import AccountInfo, Position, MarketData, Price


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
        data = {}
        coins = ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"]
        prices = {
            "BTC": 51000.0, "ETH": 2950.0, "SOL": 150.0,
            "BNB": 300.0, "DOGE": 0.08, "XRP": 0.55
        }
        
        for coin in coins:
            price_val = prices[coin]
            data[coin] = MarketData(
                coin=coin,
                price=Price(coin=coin, price=price_val, timestamp=datetime.utcnow()),
                klines_3m=pd.DataFrame(),
                klines_4h=pd.DataFrame(),
                indicators_3m={
                    "ema_20": price_val * 0.99,
                    "macd": 10.0,
                    "rsi_7": 60.0,
                    "ema_20_list": [price_val * 0.99],
                    "macd_list": [10.0],
                    "rsi_7_list": [60.0],
                    "rsi_14_list": [55.0]
                },
                indicators_4h={
                    "ema_20": price_val * 0.98,
                    "ema_50": price_val * 0.95,
                    "atr_3": price_val * 0.01,
                    "atr_14": price_val * 0.02,
                    "macd_list": [20.0],
                    "rsi_14_list": [58.0]
                },
                open_interest=1000000.0,
                funding_rate=0.0001,
                volume_current_4h=500000.0,
                volume_average_4h=450000.0,
                mid_prices_list=[price_val]
            )
        return data

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
        assert "Portfolio Status" not in prompt # Renamed/Changed
        assert "Market Data" not in prompt # Renamed/Changed
        assert "Risk Management Constraints" not in prompt # Renamed/Changed
        assert "Your Task" not in prompt # Renamed/Changed
        
        # Check for new section headers/content
        assert "It has been" in prompt
        assert "ALL OF THE PRICE OR SIGNAL DATA" in prompt
        assert "HERE IS YOUR ACCOUNT INFORMATION" in prompt
        assert "TRADING STYLE GUIDELINES" in prompt

    def test_build_header_section(self, builder, mock_agent):
        """Test _build_header creates proper header."""
        header = builder._build_header(minutes_elapsed=10, invocation_count=5)

        assert "10 minutes" in header
        assert "invoked 5 times" in header
        assert "UTC" not in header # UTC is not explicitly in the string format used

    def test_build_portfolio_section_with_positions(
        self,
        builder,
        mock_account,
        mock_positions,
        mock_agent
    ):
        """Test _build_account_section with positions."""
        section = builder._build_account_section(mock_account, mock_positions, mock_agent)

        # Check account balance info
        assert "10000.0" in section
        assert "8000.0" in section
        assert "Max Allowed Leverage: 10x" in section

        # Check positions
        assert "BTC" in section
        assert "ETH" in section
        assert "50000.0" in section  # BTC entry price
        assert "3000.0" in section  # ETH entry price

    def test_build_portfolio_section_no_positions(self, builder, mock_account, mock_agent):
        """Test _build_account_section with no positions."""
        section = builder._build_account_section(mock_account, [], mock_agent)

        assert "10000.0" in section

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

        # Check timeframes are included
        assert "3‑minute intervals" in section
        assert "4‑hour timeframe" in section

        # Check specific values
        assert "51000.0" in section  # BTC price
        assert "2950.0" in section  # ETH price

    def test_build_market_data_section_missing_coin(self, builder):
        """Test _build_market_data_section handles missing coin data."""
        # Create minimal MarketData for BTC
        btc_data = MarketData(
            coin="BTC",
            price=Price(coin="BTC", price=51000.0, timestamp=datetime.utcnow()),
            klines_3m=pd.DataFrame(), klines_4h=pd.DataFrame(),
            indicators_3m={"ema_20": 50500.0},
            indicators_4h={"ema_20": 50000.0},
            open_interest=None, funding_rate=None,
            volume_current_4h=None, volume_average_4h=None,
            mid_prices_list=[]
        )
        
        market_data = {"BTC": btc_data}

        section = builder._build_market_data_section(market_data)

        # Should only include BTC
        assert "BTC" in section
        assert "ETH" not in section

    def test_build_system_instruction(self, builder):
        """Test _build_system_instruction includes instructions."""
        section = builder._build_system_instruction()

        # Check risk management rules
        assert "AVOID OVER-TRADING" in section
        assert "Conviction & Aggression" in section
        
        # Check JSON format instructions
        assert "CHAIN_OF_THOUGHT" in section
        assert "TRADING_DECISIONS" in section
        assert "JSON" in section

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

        assert "Current live positions & performance: \n\n" in prompt
        assert len(prompt) > 5000
