"""Unit tests for OrderManager."""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from src.trading_bot.trading.order_manager import OrderManager, OrderSide
from src.trading_bot.models.database import AgentTrade


class TestOrderManager:
    """Test OrderManager functionality."""

    @pytest.fixture
    def mock_executor(self):
        """Create mock executor."""
        executor = Mock()
        executor.get_address.return_value = "0x1234567890123456789012345678901234567890"
        return executor

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        return db

    @pytest.fixture
    def order_manager(self, mock_executor, mock_db):
        """Create OrderManager instance."""
        return OrderManager(mock_executor, mock_db)

    def test_initialize(self, order_manager, mock_executor):
        """Test OrderManager initialization."""
        assert order_manager.executor == mock_executor
        assert order_manager.db is not None

    def test_execute_trade_success(self, order_manager, mock_executor, mock_db):
        """Test successful trade execution."""
        # Mock executor response
        mock_executor.place_order.return_value = (True, 12345, None)

        agent_id = uuid4()
        decision_id = uuid4()

        success, trade, error = order_manager.execute_trade(
            agent_id=agent_id,
            decision_id=decision_id,
            coin="BTC",
            side=OrderSide.LONG,
            size=Decimal("0.1"),
            price=Decimal("50000")
        )

        assert success is True
        assert trade is not None
        assert error is None

        # Verify order was placed
        mock_executor.place_order.assert_called_once()

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_execute_trade_order_failure(self, order_manager, mock_executor, mock_db):
        """Test trade execution when order placement fails."""
        # Mock executor failure
        mock_executor.place_order.return_value = (False, None, "Insufficient margin")

        success, trade, error = order_manager.execute_trade(
            agent_id=uuid4(),
            decision_id=uuid4(),
            coin="BTC",
            side=OrderSide.LONG,
            size=Decimal("0.1"),
            price=Decimal("50000")
        )

        assert success is False
        assert trade is None
        assert error == "Insufficient margin"

        # Should not commit to database
        mock_db.commit.assert_not_called()

    def test_execute_trade_db_failure(self, order_manager, mock_executor, mock_db):
        """Test trade execution when database commit fails."""
        # Mock executor success
        mock_executor.place_order.return_value = (True, 12345, None)
        mock_executor.cancel_order.return_value = (True, None)

        # Mock database failure
        mock_db.commit.side_effect = Exception("Database error")

        success, trade, error = order_manager.execute_trade(
            agent_id=uuid4(),
            decision_id=uuid4(),
            coin="BTC",
            side=OrderSide.LONG,
            size=Decimal("0.1"),
            price=Decimal("50000")
        )

        assert success is False
        assert trade is None
        assert "Database error" in error

        # Should rollback and try to cancel orphaned order
        mock_db.rollback.assert_called_once()
        mock_executor.cancel_order.assert_called_once_with("BTC", 12345)

    def test_execute_short_trade(self, order_manager, mock_executor, mock_db):
        """Test executing a short trade."""
        mock_executor.place_order.return_value = (True, 67890, None)

        success, trade, error = order_manager.execute_trade(
            agent_id=uuid4(),
            decision_id=uuid4(),
            coin="ETH",
            side=OrderSide.SHORT,
            size=Decimal("1.0"),
            price=Decimal("3000")
        )

        assert success is True

        # Verify SHORT converts to is_buy=False
        call_args = mock_executor.place_order.call_args
        assert call_args[1]["is_buy"] is False

    def test_execute_market_order(self, order_manager, mock_executor, mock_db):
        """Test executing market order."""
        from src.trading_bot.trading.hyperliquid_executor import OrderType

        mock_executor.place_order.return_value = (True, 11111, None)

        success, trade, error = order_manager.execute_trade(
            agent_id=uuid4(),
            decision_id=uuid4(),
            coin="SOL",
            side=OrderSide.LONG,
            size=Decimal("10"),
            order_type=OrderType.MARKET
        )

        assert success is True

        # Verify market order type was passed
        call_args = mock_executor.place_order.call_args
        assert call_args[1]["order_type"] == OrderType.MARKET

    def test_cancel_trade_success(self, order_manager, mock_executor, mock_db):
        """Test successful trade cancellation."""
        trade_id = uuid4()

        # Mock existing trade
        mock_trade = Mock(spec=AgentTrade)
        mock_trade.id = trade_id
        mock_trade.status = "open"
        mock_trade.coin = "BTC"
        mock_trade.hyperliquid_order_id = "12345"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_trade
        mock_executor.cancel_order.return_value = (True, None)

        success, error = order_manager.cancel_trade(trade_id)

        assert success is True
        assert error is None

        # Verify order cancelled on exchange
        mock_executor.cancel_order.assert_called_once_with("BTC", 12345)

        # Verify trade status updated
        assert mock_trade.status == "cancelled"
        assert mock_trade.exit_time is not None
        mock_db.commit.assert_called_once()

    def test_cancel_trade_not_found(self, order_manager, mock_db):
        """Test cancelling non-existent trade."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        success, error = order_manager.cancel_trade(uuid4())

        assert success is False
        assert error == "Trade not found"

    def test_cancel_trade_already_closed(self, order_manager, mock_db):
        """Test cancelling already closed trade."""
        mock_trade = Mock(spec=AgentTrade)
        mock_trade.status = "closed"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_trade

        success, error = order_manager.cancel_trade(uuid4())

        assert success is False
        assert "Cannot cancel" in error

    def test_cancel_trade_exchange_failure(self, order_manager, mock_executor, mock_db):
        """Test trade cancellation when exchange cancel fails."""
        mock_trade = Mock(spec=AgentTrade)
        mock_trade.status = "open"
        mock_trade.coin = "BTC"
        mock_trade.hyperliquid_order_id = "12345"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_trade
        mock_executor.cancel_order.return_value = (False, "Order not found")

        success, error = order_manager.cancel_trade(uuid4())

        assert success is False
        assert error == "Order not found"

    def test_close_trade_success(self, order_manager, mock_db):
        """Test closing a trade."""
        trade_id = uuid4()

        mock_trade = Mock(spec=AgentTrade)
        mock_trade.id = trade_id
        mock_trade.status = "open"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_trade

        success, error = order_manager.close_trade(
            trade_id=trade_id,
            exit_price=Decimal("51000"),
            realized_pnl=Decimal("100"),
            fees=Decimal("5")
        )

        assert success is True
        assert error is None

        # Verify trade updated
        assert mock_trade.exit_price == Decimal("51000")
        assert mock_trade.realized_pnl == Decimal("100")
        assert mock_trade.fees == Decimal("5")
        assert mock_trade.status == "closed"
        assert mock_trade.exit_time is not None

        mock_db.commit.assert_called_once()

    def test_close_trade_not_found(self, order_manager, mock_db):
        """Test closing non-existent trade."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        success, error = order_manager.close_trade(uuid4())

        assert success is False
        assert error == "Trade not found"

    def test_close_trade_already_closed(self, order_manager, mock_db):
        """Test closing already closed trade."""
        mock_trade = Mock(spec=AgentTrade)
        mock_trade.status = "closed"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_trade

        success, error = order_manager.close_trade(uuid4())

        assert success is False
        assert error == "Trade already closed"

    def test_get_trade(self, order_manager, mock_db):
        """Test getting a trade by ID."""
        trade_id = uuid4()
        mock_trade = Mock(spec=AgentTrade)

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_trade

        trade = order_manager.get_trade(trade_id)

        assert trade == mock_trade
        mock_db.query.assert_called()

    def test_get_agent_trades(self, order_manager, mock_db):
        """Test getting trades for an agent."""
        agent_id = uuid4()
        mock_trades = [Mock(spec=AgentTrade) for _ in range(3)]

        mock_query = Mock()
        mock_query.filter_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_trades

        mock_db.query.return_value = mock_query

        trades = order_manager.get_agent_trades(agent_id)

        assert len(trades) == 3
        assert trades == mock_trades

    def test_get_agent_trades_with_status_filter(self, order_manager, mock_db):
        """Test getting trades filtered by status."""
        agent_id = uuid4()

        mock_query = Mock()
        mock_query.filter_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        trades = order_manager.get_agent_trades(agent_id, status="open")

        # Verify filter_by was called twice (once for agent_id, once for status)
        assert mock_query.filter_by.call_count == 2

    def test_get_open_trades(self, order_manager, mock_db):
        """Test getting open trades."""
        agent_id = uuid4()

        mock_query = Mock()
        mock_query.filter_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        trades = order_manager.get_open_trades(agent_id)

        # Should filter by status="open"
        assert mock_query.filter_by.call_count == 2

    def test_get_trade_by_order_id(self, order_manager, mock_db):
        """Test getting trade by HyperLiquid order ID."""
        mock_trade = Mock(spec=AgentTrade)

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_trade

        trade = order_manager.get_trade_by_order_id("12345")

        assert trade == mock_trade

    def test_batch_cancel_trades(self, order_manager, mock_executor, mock_db):
        """Test batch cancelling multiple trades."""
        trade_ids = [uuid4(), uuid4(), uuid4()]

        # Mock trades
        mock_trades = [
            Mock(spec=AgentTrade, status="open", coin="BTC", hyperliquid_order_id="1"),
            Mock(spec=AgentTrade, status="open", coin="ETH", hyperliquid_order_id="2"),
            Mock(spec=AgentTrade, status="open", coin="SOL", hyperliquid_order_id="3")
        ]

        mock_db.query.return_value.filter_by.return_value.first.side_effect = mock_trades
        mock_executor.cancel_order.return_value = (True, None)

        results = order_manager.batch_cancel_trades(trade_ids)

        assert len(results) == 3
        for trade_id in trade_ids:
            success, error = results[trade_id]
            assert success is True
            assert error is None

    def test_get_trade_statistics(self, order_manager, mock_db):
        """Test getting trade statistics."""
        agent_id = uuid4()

        # Mock trades
        mock_trades = [
            Mock(spec=AgentTrade, status="open", realized_pnl=None, fees=None),
            Mock(spec=AgentTrade, status="closed", realized_pnl=Decimal("100"), fees=Decimal("5")),
            Mock(spec=AgentTrade, status="closed", realized_pnl=Decimal("-50"), fees=Decimal("3")),
            Mock(spec=AgentTrade, status="cancelled", realized_pnl=None, fees=None),
        ]

        mock_db.query.return_value.filter_by.return_value.all.return_value = mock_trades

        stats = order_manager.get_trade_statistics(agent_id)

        assert stats["total_trades"] == 4
        assert stats["open_trades"] == 1
        assert stats["closed_trades"] == 2
        assert stats["cancelled_trades"] == 1
        assert stats["total_pnl"] == Decimal("50")  # 100 - 50
        assert stats["total_fees"] == Decimal("8")  # 5 + 3

    def test_repr(self, order_manager):
        """Test string representation."""
        repr_str = repr(order_manager)

        assert "OrderManager" in repr_str
        assert "0x" in repr_str
