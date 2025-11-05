"""Unit tests for RiskManager."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from src.trading_bot.risk.risk_manager import RiskManager
from src.trading_bot.models.database import TradingAgent
from src.trading_bot.models.market_data import Position, AccountInfo


class TestRiskManager:
    """Test RiskManager functionality."""

    @pytest.fixture
    def mock_position_manager(self):
        """Create mock position manager."""
        manager = Mock()
        return manager

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        return db

    @pytest.fixture
    def risk_manager(self, mock_position_manager, mock_db):
        """Create RiskManager instance."""
        return RiskManager(mock_position_manager, mock_db)

    @pytest.fixture
    def mock_agent(self):
        """Create mock trading agent."""
        agent = Mock(spec=TradingAgent)
        agent.id = uuid4()
        agent.max_leverage = 10
        agent.max_position_size = Decimal("20")  # 20% of account
        agent.stop_loss_pct = Decimal("2.0")
        agent.take_profit_pct = Decimal("5.0")
        return agent

    @pytest.fixture
    def mock_account_info(self):
        """Create mock account info."""
        return AccountInfo(
            account_value=10000.0,
            withdrawable=8000.0,
            margin_used=2000.0,
            unrealized_pnl=0.0
        )

    def test_initialize(self, risk_manager, mock_position_manager):
        """Test RiskManager initialization."""
        assert risk_manager.position_manager == mock_position_manager
        assert risk_manager.db is not None

    def test_validate_trade_success(
        self, risk_manager, mock_position_manager, mock_db, mock_agent, mock_account_info
    ):
        """Test successful trade validation."""
        agent_id = mock_agent.id

        # Mock database and position manager
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent
        mock_position_manager.get_account_value.return_value = mock_account_info
        mock_position_manager.get_total_exposure.return_value = 0.0

        # Valid trade: $1000 at 5x leverage
        valid, reason = risk_manager.validate_trade(
            agent_id=agent_id,
            coin="BTC",
            size_usd=Decimal("1000"),
            leverage=5
        )

        assert valid is True
        assert reason is None

    def test_validate_trade_agent_not_found(self, risk_manager, mock_db):
        """Test validation when agent doesn't exist."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        valid, reason = risk_manager.validate_trade(
            agent_id=uuid4(),
            coin="BTC",
            size_usd=Decimal("1000"),
            leverage=5
        )

        assert valid is False
        assert reason == "Agent not found"

    def test_validate_trade_exceeds_max_leverage(
        self, risk_manager, mock_position_manager, mock_db, mock_agent, mock_account_info
    ):
        """Test validation when leverage exceeds maximum."""
        agent_id = mock_agent.id

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent
        mock_position_manager.get_account_value.return_value = mock_account_info

        # Try to use 20x leverage when max is 10x
        valid, reason = risk_manager.validate_trade(
            agent_id=agent_id,
            coin="BTC",
            size_usd=Decimal("1000"),
            leverage=20
        )

        assert valid is False
        assert "exceeds max" in reason
        assert "20x" in reason
        assert "10x" in reason

    def test_validate_trade_exceeds_max_position_size(
        self, risk_manager, mock_position_manager, mock_db, mock_agent, mock_account_info
    ):
        """Test validation when position size exceeds limit."""
        agent_id = mock_agent.id

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent
        mock_position_manager.get_account_value.return_value = mock_account_info
        mock_position_manager.get_total_exposure.return_value = 0.0

        # Account value: $10,000, max position: 20% = $2,000
        # Try to open $3,000 position (exceeds limit)
        valid, reason = risk_manager.validate_trade(
            agent_id=agent_id,
            coin="BTC",
            size_usd=Decimal("3000"),
            leverage=5
        )

        assert valid is False
        assert "exceeds max" in reason

    def test_validate_trade_insufficient_margin(
        self, risk_manager, mock_position_manager, mock_db, mock_agent, mock_account_info
    ):
        """Test validation when insufficient margin."""
        agent_id = mock_agent.id

        # Mock account with only $500 withdrawable
        mock_account_info.withdrawable = 500.0

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent
        mock_position_manager.get_account_value.return_value = mock_account_info
        mock_position_manager.get_total_exposure.return_value = 0.0

        # Need $1000 margin (at 1x leverage), but only have $500
        valid, reason = risk_manager.validate_trade(
            agent_id=agent_id,
            coin="BTC",
            size_usd=Decimal("1000"),
            leverage=1
        )

        assert valid is False
        assert "Insufficient margin" in reason

    def test_validate_trade_exceeds_total_exposure(
        self, risk_manager, mock_position_manager, mock_db, mock_agent, mock_account_info
    ):
        """Test validation when total exposure exceeds limit."""
        agent_id = mock_agent.id

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent
        mock_position_manager.get_account_value.return_value = mock_account_info

        # Already have $7,000 exposure, max is 80% = $8,000
        # Try to add $2,000 more (total $9,000 > $8,000)
        mock_position_manager.get_total_exposure.return_value = 7000.0

        valid, reason = risk_manager.validate_trade(
            agent_id=agent_id,
            coin="ETH",
            size_usd=Decimal("2000"),
            leverage=5
        )

        assert valid is False
        assert "Total exposure" in reason
        assert "exceeds" in reason

    def test_calculate_stop_loss_long(self, risk_manager):
        """Test stop loss calculation for long position."""
        entry_price = Decimal("50000")
        stop_loss_pct = Decimal("2.0")

        sl_price = risk_manager.calculate_stop_loss_price(
            entry_price, stop_loss_pct, is_long=True
        )

        # Long: stop loss 2% below entry
        expected = Decimal("50000") * Decimal("0.98")  # 49000
        assert sl_price == expected

    def test_calculate_stop_loss_short(self, risk_manager):
        """Test stop loss calculation for short position."""
        entry_price = Decimal("50000")
        stop_loss_pct = Decimal("2.0")

        sl_price = risk_manager.calculate_stop_loss_price(
            entry_price, stop_loss_pct, is_long=False
        )

        # Short: stop loss 2% above entry
        expected = Decimal("50000") * Decimal("1.02")  # 51000
        assert sl_price == expected

    def test_calculate_take_profit_long(self, risk_manager):
        """Test take profit calculation for long position."""
        entry_price = Decimal("50000")
        take_profit_pct = Decimal("5.0")

        tp_price = risk_manager.calculate_take_profit_price(
            entry_price, take_profit_pct, is_long=True
        )

        # Long: take profit 5% above entry
        expected = Decimal("50000") * Decimal("1.05")  # 52500
        assert tp_price == expected

    def test_calculate_take_profit_short(self, risk_manager):
        """Test take profit calculation for short position."""
        entry_price = Decimal("50000")
        take_profit_pct = Decimal("5.0")

        tp_price = risk_manager.calculate_take_profit_price(
            entry_price, take_profit_pct, is_long=False
        )

        # Short: take profit 5% below entry
        expected = Decimal("50000") * Decimal("0.95")  # 47500
        assert tp_price == expected

    def test_check_liquidation_risk_no_positions(self, risk_manager, mock_position_manager):
        """Test liquidation check with no open positions."""
        mock_position_manager.get_current_positions.return_value = []

        at_risk, warnings = risk_manager.check_liquidation_risk(uuid4())

        assert at_risk is False
        assert len(warnings) == 0

    def test_check_liquidation_risk_safe_position(self, risk_manager, mock_position_manager):
        """Test liquidation check with safe position."""
        # Position far from liquidation (25% away, which is > 20% threshold)
        position = Position(
            coin="BTC",
            side="long",
            size=0.1,
            entry_price=50000.0,
            mark_price=50000.0,
            position_value=5000.0,
            unrealized_pnl=0.0,
            leverage=10,
            liquidation_price=37500.0  # 25% below current price (safe)
        )

        mock_position_manager.get_current_positions.return_value = [position]

        at_risk, warnings = risk_manager.check_liquidation_risk(
            uuid4(), threshold_pct=Decimal("20")
        )

        assert at_risk is False
        assert len(warnings) == 0

    def test_check_liquidation_risk_at_risk_long(self, risk_manager, mock_position_manager):
        """Test liquidation check with at-risk long position."""
        # Position close to liquidation
        position = Position(
            coin="BTC",
            side="long",
            size=0.1,
            entry_price=50000.0,
            mark_price=46000.0,  # Price dropped
            position_value=4600.0,
            unrealized_pnl=-400.0,
            leverage=10,
            liquidation_price=45500.0  # Only 1.09% below current (risky)
        )

        mock_position_manager.get_current_positions.return_value = [position]

        at_risk, warnings = risk_manager.check_liquidation_risk(
            uuid4(), threshold_pct=Decimal("20")
        )

        assert at_risk is True
        assert len(warnings) == 1
        assert "BTC" in warnings[0]
        assert "long" in warnings[0]

    def test_check_liquidation_risk_at_risk_short(self, risk_manager, mock_position_manager):
        """Test liquidation check with at-risk short position."""
        # Short position close to liquidation
        position = Position(
            coin="ETH",
            side="short",
            size=1.0,
            entry_price=3000.0,
            mark_price=3300.0,  # Price increased
            position_value=3300.0,
            unrealized_pnl=-300.0,
            leverage=10,
            liquidation_price=3350.0  # Only 1.5% above current (risky)
        )

        mock_position_manager.get_current_positions.return_value = [position]

        at_risk, warnings = risk_manager.check_liquidation_risk(
            uuid4(), threshold_pct=Decimal("20")
        )

        assert at_risk is True
        assert len(warnings) == 1
        assert "ETH" in warnings[0]
        assert "short" in warnings[0]

    def test_check_liquidation_risk_multiple_positions(self, risk_manager, mock_position_manager):
        """Test liquidation check with multiple positions."""
        positions = [
            Position(
                coin="BTC",
                side="long",
                size=0.1,
                entry_price=50000.0,
                mark_price=50000.0,
                position_value=5000.0,
                unrealized_pnl=0.0,
                leverage=10,
                liquidation_price=37500.0  # 25% below (safe)
            ),
            Position(
                coin="ETH",
                side="short",
                size=1.0,
                entry_price=3000.0,
                mark_price=3300.0,
                position_value=3300.0,
                unrealized_pnl=-300.0,
                leverage=10,
                liquidation_price=3350.0  # At risk
            )
        ]

        mock_position_manager.get_current_positions.return_value = positions

        at_risk, warnings = risk_manager.check_liquidation_risk(
            uuid4(), threshold_pct=Decimal("20")
        )

        assert at_risk is True
        assert len(warnings) == 1  # Only ETH is at risk
        assert "ETH" in warnings[0]

    def test_get_max_position_size(
        self, risk_manager, mock_position_manager, mock_db, mock_agent, mock_account_info
    ):
        """Test calculating max position size."""
        agent_id = mock_agent.id

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent
        mock_position_manager.get_account_value.return_value = mock_account_info

        # Account value: $10,000, max position: 20%
        max_size = risk_manager.get_max_position_size(agent_id)

        assert max_size == Decimal("2000")  # 20% of $10,000

    def test_get_max_position_size_agent_not_found(self, risk_manager, mock_db):
        """Test max position size when agent doesn't exist."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        max_size = risk_manager.get_max_position_size(uuid4())

        assert max_size == Decimal("0")

    def test_repr(self, risk_manager):
        """Test string representation."""
        repr_str = repr(risk_manager)
        assert "RiskManager" in repr_str
