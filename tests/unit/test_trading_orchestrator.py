"""Unit tests for TradingOrchestrator."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from src.trading_bot.trading.trading_orchestrator import TradingOrchestrator
from src.trading_bot.trading.order_manager import OrderSide
from src.trading_bot.trading.hyperliquid_executor import OrderType
from src.trading_bot.models.database import AgentDecision, TradingAgent, AgentTrade
from src.trading_bot.models.market_data import Position, AccountInfo


class TestTradingOrchestrator:
    """Test TradingOrchestrator functionality."""

    @pytest.fixture
    def mock_executor(self):
        """Create mock HyperLiquid executor."""
        executor = Mock()
        executor.get_address.return_value = "0x1234567890123456789012345678901234567890"
        executor.update_leverage.return_value = (True, None)
        executor.place_order.return_value = (True, 12345, None)
        executor.place_trigger_order.return_value = (True, 67890, None)
        return executor

    @pytest.fixture
    def mock_order_manager(self):
        """Create mock order manager."""
        manager = Mock()
        mock_trade = Mock(spec=AgentTrade)
        mock_trade.id = uuid4()
        manager.execute_trade.return_value = (True, mock_trade, None)
        manager.get_trade_statistics.return_value = {
            "total_trades": 10,
            "open_trades": 2,
            "closed_trades": 8,
            "total_pnl": Decimal("500"),
            "total_fees": Decimal("50")
        }
        return manager

    @pytest.fixture
    def mock_position_manager(self):
        """Create mock position manager."""
        manager = Mock()
        manager.calculate_position_size.return_value = Decimal("0.1")
        manager.get_current_positions.return_value = []
        manager.get_account_value.return_value = AccountInfo(
            account_value=10000.0,
            withdrawable=8000.0,
            margin_used=2000.0,
            unrealized_pnl=0.0
        )
        manager.get_position_summary.return_value = {
            "num_positions": 0,
            "total_value": 0.0,
            "total_unrealized_pnl": 0.0,
            "positions_by_coin": {}
        }
        return manager

    @pytest.fixture
    def mock_risk_manager(self):
        """Create mock risk manager."""
        manager = Mock()
        manager.validate_trade.return_value = (True, None)
        return manager

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        return db

    @pytest.fixture
    def orchestrator(
        self, mock_executor, mock_order_manager, mock_position_manager,
        mock_risk_manager, mock_db
    ):
        """Create TradingOrchestrator instance."""
        return TradingOrchestrator(
            executor=mock_executor,
            order_manager=mock_order_manager,
            position_manager=mock_position_manager,
            risk_manager=mock_risk_manager,
            db_session=mock_db
        )

    @pytest.fixture
    def mock_agent(self):
        """Create mock trading agent."""
        agent = Mock(spec=TradingAgent)
        agent.id = uuid4()
        agent.name = "TestAgent"
        agent.max_leverage = 10
        agent.max_position_size = Decimal("20")
        return agent

    @pytest.fixture
    def mock_decision_open_long(self):
        """Create mock OPEN_LONG decision."""
        decision = Mock(spec=AgentDecision)
        decision.id = uuid4()
        decision.action = "OPEN_LONG"
        decision.coin = "BTC"
        decision.size_usd = Decimal("5000")
        decision.leverage = 5
        decision.stop_loss_price = Decimal("48000")
        decision.take_profit_price = Decimal("52000")
        return decision

    @pytest.fixture
    def mock_decision_close(self):
        """Create mock CLOSE_POSITION decision."""
        decision = Mock(spec=AgentDecision)
        decision.id = uuid4()
        decision.action = "CLOSE_POSITION"
        decision.coin = "BTC"
        return decision

    def test_initialize(self, orchestrator, mock_executor):
        """Test TradingOrchestrator initialization."""
        assert orchestrator.executor == mock_executor
        assert orchestrator.order_manager is not None
        assert orchestrator.position_manager is not None
        assert orchestrator.risk_manager is not None
        assert orchestrator.db is not None

    def test_execute_decision_hold(
        self, orchestrator, mock_db, mock_agent
    ):
        """Test executing HOLD decision."""
        decision = Mock(spec=AgentDecision)
        decision.id = uuid4()
        decision.action = "HOLD"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            decision, mock_agent
        ]

        success, error = orchestrator.execute_decision(
            agent_id=mock_agent.id,
            decision_id=decision.id
        )

        assert success is True
        assert error is None

    def test_execute_decision_not_found(self, orchestrator, mock_db):
        """Test executing non-existent decision."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        success, error = orchestrator.execute_decision(
            agent_id=uuid4(),
            decision_id=uuid4()
        )

        assert success is False
        assert error == "Decision not found"

    def test_execute_decision_agent_not_found(
        self, orchestrator, mock_db, mock_decision_open_long
    ):
        """Test executing decision when agent doesn't exist."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_decision_open_long, None
        ]

        success, error = orchestrator.execute_decision(
            agent_id=uuid4(),
            decision_id=mock_decision_open_long.id
        )

        assert success is False
        assert error == "Agent not found"

    def test_execute_decision_open_long_success(
        self, orchestrator, mock_db, mock_agent, mock_decision_open_long,
        mock_risk_manager, mock_executor, mock_position_manager, mock_order_manager
    ):
        """Test successfully opening long position."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_decision_open_long, mock_agent
        ]

        success, error = orchestrator.execute_decision(
            agent_id=mock_agent.id,
            decision_id=mock_decision_open_long.id
        )

        assert success is True
        assert error is None

        # Verify risk validation was called
        mock_risk_manager.validate_trade.assert_called_once()

        # Verify leverage was set
        mock_executor.update_leverage.assert_called_once_with(
            coin="BTC",
            leverage=5,
            is_cross=True
        )

        # Verify position size was calculated
        mock_position_manager.calculate_position_size.assert_called_once()

        # Verify trade was executed
        mock_order_manager.execute_trade.assert_called_once()
        call_args = mock_order_manager.execute_trade.call_args[1]
        assert call_args["coin"] == "BTC"
        assert call_args["side"] == OrderSide.LONG
        assert call_args["order_type"] == OrderType.MARKET

    def test_execute_decision_open_short_success(
        self, orchestrator, mock_db, mock_agent, mock_risk_manager,
        mock_executor, mock_position_manager, mock_order_manager
    ):
        """Test successfully opening short position."""
        decision = Mock(spec=AgentDecision)
        decision.id = uuid4()
        decision.action = "OPEN_SHORT"
        decision.coin = "ETH"
        decision.size_usd = Decimal("3000")
        decision.leverage = 3
        decision.stop_loss_price = None
        decision.take_profit_price = None

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            decision, mock_agent
        ]

        success, error = orchestrator.execute_decision(
            agent_id=mock_agent.id,
            decision_id=decision.id
        )

        assert success is True
        assert error is None

        # Verify trade was executed with SHORT side
        call_args = mock_order_manager.execute_trade.call_args[1]
        assert call_args["side"] == OrderSide.SHORT

    def test_execute_decision_risk_rejection(
        self, orchestrator, mock_db, mock_agent, mock_decision_open_long,
        mock_risk_manager
    ):
        """Test opening position rejected by risk manager."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_decision_open_long, mock_agent
        ]

        # Mock risk rejection
        mock_risk_manager.validate_trade.return_value = (False, "Insufficient margin")

        success, error = orchestrator.execute_decision(
            agent_id=mock_agent.id,
            decision_id=mock_decision_open_long.id
        )

        assert success is False
        assert "Risk check failed" in error
        assert "Insufficient margin" in error

    def test_execute_decision_leverage_failure(
        self, orchestrator, mock_db, mock_agent, mock_decision_open_long,
        mock_executor
    ):
        """Test opening position when leverage update fails."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_decision_open_long, mock_agent
        ]

        # Mock leverage failure
        mock_executor.update_leverage.return_value = (False, "API error")

        success, error = orchestrator.execute_decision(
            agent_id=mock_agent.id,
            decision_id=mock_decision_open_long.id
        )

        assert success is False
        assert "Failed to set leverage" in error

    def test_execute_decision_trade_execution_failure(
        self, orchestrator, mock_db, mock_agent, mock_decision_open_long,
        mock_order_manager
    ):
        """Test opening position when trade execution fails."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_decision_open_long, mock_agent
        ]

        # Mock trade execution failure
        mock_order_manager.execute_trade.return_value = (False, None, "Order rejected")

        success, error = orchestrator.execute_decision(
            agent_id=mock_agent.id,
            decision_id=mock_decision_open_long.id
        )

        assert success is False
        assert "Trade execution failed" in error

    def test_execute_decision_close_position_success(
        self, orchestrator, mock_db, mock_agent, mock_decision_close,
        mock_position_manager, mock_executor
    ):
        """Test successfully closing position."""
        # Mock open position
        position = Position(
            coin="BTC",
            side="long",
            size=0.1,
            entry_price=50000.0,
            mark_price=51000.0,
            position_value=5100.0,
            unrealized_pnl=100.0,
            leverage=5,
            liquidation_price=45000.0
        )

        mock_position_manager.get_current_positions.return_value = [position]

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_decision_close, mock_agent
        ]

        success, error = orchestrator.execute_decision(
            agent_id=mock_agent.id,
            decision_id=mock_decision_close.id
        )

        assert success is True
        assert error is None

        # Verify close order was placed
        mock_executor.place_order.assert_called_once()
        call_args = mock_executor.place_order.call_args[1]
        assert call_args["coin"] == "BTC"
        assert call_args["is_buy"] is False  # Sell to close long
        assert call_args["reduce_only"] is True

    def test_execute_decision_close_short_position(
        self, orchestrator, mock_db, mock_agent, mock_decision_close,
        mock_position_manager, mock_executor
    ):
        """Test closing short position."""
        # Mock open short position
        position = Position(
            coin="BTC",
            side="short",
            size=0.1,
            entry_price=50000.0,
            mark_price=49000.0,
            position_value=4900.0,
            unrealized_pnl=100.0,
            leverage=5,
            liquidation_price=55000.0
        )

        mock_position_manager.get_current_positions.return_value = [position]

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_decision_close, mock_agent
        ]

        success, error = orchestrator.execute_decision(
            agent_id=mock_agent.id,
            decision_id=mock_decision_close.id
        )

        assert success is True

        # Verify buy order to close short
        call_args = mock_executor.place_order.call_args[1]
        assert call_args["is_buy"] is True  # Buy to close short

    def test_execute_decision_close_no_position(
        self, orchestrator, mock_db, mock_agent, mock_decision_close,
        mock_position_manager
    ):
        """Test closing position when none exists."""
        mock_position_manager.get_current_positions.return_value = []

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_decision_close, mock_agent
        ]

        success, error = orchestrator.execute_decision(
            agent_id=mock_agent.id,
            decision_id=mock_decision_close.id
        )

        assert success is False
        assert "No open position" in error

    def test_execute_decision_close_order_failure(
        self, orchestrator, mock_db, mock_agent, mock_decision_close,
        mock_position_manager, mock_executor
    ):
        """Test closing position when order fails."""
        position = Position(
            coin="BTC",
            side="long",
            size=0.1,
            entry_price=50000.0,
            mark_price=51000.0,
            position_value=5100.0,
            unrealized_pnl=100.0,
            leverage=5,
            liquidation_price=45000.0
        )

        mock_position_manager.get_current_positions.return_value = [position]
        mock_executor.place_order.return_value = (False, None, "Insufficient margin")

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_decision_close, mock_agent
        ]

        success, error = orchestrator.execute_decision(
            agent_id=mock_agent.id,
            decision_id=mock_decision_close.id
        )

        assert success is False
        assert "Close failed" in error

    def test_execute_decision_unknown_action(
        self, orchestrator, mock_db, mock_agent
    ):
        """Test executing decision with unknown action."""
        decision = Mock(spec=AgentDecision)
        decision.id = uuid4()
        decision.action = "INVALID_ACTION"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            decision, mock_agent
        ]

        success, error = orchestrator.execute_decision(
            agent_id=mock_agent.id,
            decision_id=decision.id
        )

        assert success is False
        assert "Unknown action" in error

    def test_get_execution_summary(
        self, orchestrator, mock_order_manager, mock_position_manager
    ):
        """Test getting execution summary."""
        summary = orchestrator.get_execution_summary(uuid4())

        assert "account_value" in summary
        assert "unrealized_pnl" in summary
        assert "total_trades" in summary
        assert "open_trades" in summary
        assert "closed_trades" in summary
        assert "total_pnl" in summary
        assert "total_fees" in summary
        assert "num_positions" in summary
        assert "total_exposure" in summary

        assert summary["total_trades"] == 10
        assert summary["account_value"] == 10000.0

    def test_repr(self, orchestrator):
        """Test string representation."""
        repr_str = repr(orchestrator)
        assert "TradingOrchestrator" in repr_str
        assert "0x" in repr_str
