"""Unit tests for PositionManager."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from src.trading_bot.trading.position_manager import PositionManager
from src.trading_bot.models.database import AgentTrade, TradingAgent
from src.trading_bot.models.market_data import Position, AccountInfo


class TestPositionManager:
    """Test PositionManager functionality."""

    @pytest.fixture
    def mock_client(self):
        """Create mock HyperLiquid client."""
        client = Mock()
        # Return an object with a .price attribute
        price_obj = Mock()
        price_obj.price = Decimal("50000")
        client.get_price.return_value = price_obj
        return client

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        return db

    @pytest.fixture
    def position_manager(self, mock_client, mock_db):
        """Create PositionManager instance."""
        return PositionManager(mock_client, mock_db)

    @pytest.fixture
    def mock_agent(self):
        """Create mock trading agent."""
        agent = Mock(spec=TradingAgent)
        agent.id = uuid4()
        agent.initial_balance = Decimal("10000")
        agent.max_leverage = 10
        return agent

    @pytest.fixture
    def mock_open_trades(self):
        """Create mock open trades."""
        trade1 = Mock(spec=AgentTrade)
        trade1.coin = "BTC"
        trade1.side = "long"
        trade1.size = Decimal("0.1")
        trade1.entry_price = Decimal("48000")
        trade1.status = "open"

        trade2 = Mock(spec=AgentTrade)
        trade2.coin = "ETH"
        trade2.side = "short"
        trade2.size = Decimal("1.0")
        trade2.entry_price = Decimal("3100")
        trade2.status = "open"

        return [trade1, trade2]

    def test_initialize(self, position_manager, mock_client):
        """Test PositionManager initialization."""
        assert position_manager.info_client == mock_client
        assert position_manager.db is not None

    def test_get_current_positions_empty(self, position_manager, mock_db):
        """Test getting positions when none exist."""
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        positions = position_manager.get_current_positions(uuid4())

        assert len(positions) == 0

    def test_get_current_positions_long(
        self, position_manager, mock_client, mock_db, mock_agent, mock_open_trades
    ):
        """Test getting long position."""
        agent_id = mock_agent.id

        # Mock database queries
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_open_trades[0]]
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent

        # Mock price (current > entry, so profit)
        price_obj = Mock()
        price_obj.price = Decimal("50000")
        mock_client.get_price.return_value = price_obj

        positions = position_manager.get_current_positions(agent_id)

        assert len(positions) == 1
        pos = positions[0]
        assert pos.coin == "BTC"
        assert pos.side == "long"
        assert pos.size == 0.1
        assert pos.entry_price == 48000.0
        assert pos.mark_price == 50000.0

        # Long position: profit = size * (current - entry)
        assert pos.unrealized_pnl == 200.0  # 0.1 * (50000 - 48000)

    def test_get_current_positions_short(
        self, position_manager, mock_client, mock_db, mock_agent, mock_open_trades
    ):
        """Test getting short position."""
        agent_id = mock_agent.id

        # Mock database queries
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_open_trades[1]]
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent

        # Mock price (current < entry, so profit for short)
        price_obj = Mock()
        price_obj.price = Decimal("3000")
        mock_client.get_price.return_value = price_obj

        positions = position_manager.get_current_positions(agent_id)

        assert len(positions) == 1
        pos = positions[0]
        assert pos.coin == "ETH"
        assert pos.side == "short"

        # Short position: profit = size * (entry - current)
        expected_pnl = Decimal("1.0") * (Decimal("3100") - Decimal("3000"))
        assert pos.unrealized_pnl == expected_pnl  # 100

    def test_get_current_positions_multiple(
        self, position_manager, mock_client, mock_db, mock_agent, mock_open_trades
    ):
        """Test getting multiple positions."""
        agent_id = mock_agent.id

        # Mock database queries
        mock_db.query.return_value.filter_by.return_value.all.return_value = mock_open_trades
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent

        # Mock prices
        def get_price_side_effect(coin):
            price_obj = Mock()
            if coin == "BTC":
                price_obj.price = Decimal("50000")
            elif coin == "ETH":
                price_obj.price = Decimal("3000")
            return price_obj

        mock_client.get_price.side_effect = get_price_side_effect

        positions = position_manager.get_current_positions(agent_id)

        assert len(positions) == 2

    def test_get_current_positions_price_error(
        self, position_manager, mock_client, mock_db, mock_agent, mock_open_trades
    ):
        """Test handling price fetch errors."""
        agent_id = mock_agent.id

        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_open_trades[0]]
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent

        # Mock price error
        mock_client.get_price.side_effect = Exception("Price API error")

        positions = position_manager.get_current_positions(agent_id)

        # Should return empty list when price fetch fails
        assert len(positions) == 0

    def test_get_position(self, position_manager, mock_client, mock_db, mock_agent, mock_open_trades):
        """Test getting a specific position by coin."""
        agent_id = mock_agent.id

        mock_db.query.return_value.filter_by.return_value.all.return_value = mock_open_trades
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent

        def get_price_side_effect(coin):
            price_obj = Mock()
            if coin == "BTC":
                price_obj.price = Decimal("50000")
            elif coin == "ETH":
                price_obj.price = Decimal("3000")
            return price_obj

        mock_client.get_price.side_effect = get_price_side_effect

        btc_position = position_manager.get_position(agent_id, "BTC")
        eth_position = position_manager.get_position(agent_id, "ETH")
        sol_position = position_manager.get_position(agent_id, "SOL")

        assert btc_position is not None
        assert btc_position.coin == "BTC"
        assert eth_position is not None
        assert eth_position.coin == "ETH"
        assert sol_position is None

    def test_has_position(self, position_manager, mock_client, mock_db, mock_agent, mock_open_trades):
        """Test checking if position exists."""
        agent_id = mock_agent.id

        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_open_trades[0]]
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent
        
        price_obj = Mock()
        price_obj.price = Decimal("50000")
        mock_client.get_price.return_value = price_obj

        has_btc = position_manager.has_position(agent_id, "BTC")
        has_eth = position_manager.has_position(agent_id, "ETH")

        assert has_btc is True
        assert has_eth is False

    def test_get_account_value(
        self, position_manager, mock_client, mock_db, mock_agent, mock_open_trades
    ):
        """Test calculating account value."""
        agent_id = mock_agent.id

        # Mock open positions
        mock_db.query.return_value.filter_by.return_value.all.return_value = mock_open_trades
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent

        # Mock prices
        def get_price_side_effect(coin):
            price_obj = Mock()
            if coin == "BTC":
                price_obj.price = Decimal("50000")
            elif coin == "ETH":
                price_obj.price = Decimal("3000")
            return price_obj

        mock_client.get_price.side_effect = get_price_side_effect

        # Mock realized PnL query
        mock_db.query.return_value.filter_by.return_value.scalar.return_value = Decimal("500")

        account = position_manager.get_account_value(agent_id)

        # Verify account info
        assert isinstance(account, AccountInfo)
        # Realized PnL not directly in AccountInfo, calculated internally

        # Unrealized PnL = BTC (0.1 * 2000) + ETH (1.0 * 100) = 200 + 100
        assert account.unrealized_pnl == 300.0

        # Account value = initial + realized + unrealized = 10000 + 500 + 300
        assert account.account_value == 10800.0

        # Position value calculated in get_account_value method
        # Withdrawable = account_value - position_value
        # Position value = BTC (0.1 * 50000) + ETH (1.0 * 3000) = 8000
        assert account.withdrawable == 2800.0  # 10800 - 8000

    def test_get_account_value_agent_not_found(self, position_manager, mock_db):
        """Test account value when agent doesn't exist."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Agent not found"):
            position_manager.get_account_value(uuid4())

    def test_get_account_value_no_positions(
        self, position_manager, mock_db, mock_agent
    ):
        """Test account value with no open positions."""
        agent_id = mock_agent.id

        # No open positions
        mock_db.query.return_value.filter_by.return_value.all.return_value = []
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent

        # No realized PnL
        mock_db.query.return_value.filter_by.return_value.scalar.return_value = None

        account = position_manager.get_account_value(agent_id)

        assert account.unrealized_pnl == 0.0
        assert account.account_value == 10000.0  # Just initial balance
        assert account.withdrawable == 10000.0  # No positions, all withdrawable

    def test_calculate_position_size(self, position_manager, mock_client):
        """Test calculating position size."""
        agent_id = uuid4()
        price_obj = Mock()
        price_obj.price = Decimal("50000")
        mock_client.get_price.return_value = price_obj

        # Want $10,000 position
        size = position_manager.calculate_position_size(
            agent_id, "BTC", Decimal("10000")
        )

        # 10000 / 50000 = 0.2 BTC
        assert size == Decimal("0.2")

    def test_calculate_position_size_with_leverage(self, position_manager, mock_client):
        """Test calculating position size with leverage."""
        agent_id = uuid4()
        price_obj = Mock()
        price_obj.price = Decimal("3000")
        mock_client.get_price.return_value = price_obj

        # Want $30,000 position at 10x leverage
        size = position_manager.calculate_position_size(
            agent_id, "ETH", Decimal("30000"), leverage=10
        )

        # Size calculation doesn't change with leverage
        # 30000 / 3000 = 10 ETH
        assert size == Decimal("10")

    def test_get_total_exposure(
        self, position_manager, mock_client, mock_db, mock_agent, mock_open_trades
    ):
        """Test getting total exposure."""
        agent_id = mock_agent.id

        mock_db.query.return_value.filter_by.return_value.all.return_value = mock_open_trades
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent

        def get_price_side_effect(coin):
            price_obj = Mock()
            if coin == "BTC":
                price_obj.price = Decimal("50000")
            elif coin == "ETH":
                price_obj.price = Decimal("3000")
            return price_obj

        mock_client.get_price.side_effect = get_price_side_effect

        mock_db.query.return_value.filter_by.return_value.scalar.return_value = Decimal("0")

        exposure = position_manager.get_total_exposure(agent_id)

        # BTC: 0.1 * 50000 = 5000
        # ETH: 1.0 * 3000 = 3000
        # Total = 8000
        assert exposure == 8000.0

    def test_get_position_summary(
        self, position_manager, mock_client, mock_db, mock_agent, mock_open_trades
    ):
        """Test getting position summary."""
        agent_id = mock_agent.id

        mock_db.query.return_value.filter_by.return_value.all.return_value = mock_open_trades
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_agent

        def get_price_side_effect(coin):
            price_obj = Mock()
            if coin == "BTC":
                price_obj.price = Decimal("50000")
            elif coin == "ETH":
                price_obj.price = Decimal("3000")
            return price_obj

        mock_client.get_price.side_effect = get_price_side_effect

        summary = position_manager.get_position_summary(agent_id)

        assert summary["num_positions"] == 2
        # Note: total_value and unrealized_pnl are floats from Position model
        assert summary["total_value"] == 8000.0
        assert summary["total_unrealized_pnl"] == 300.0

        # Check BTC details
        assert "BTC" in summary["positions_by_coin"]
        btc = summary["positions_by_coin"]["BTC"]
        assert btc["side"] == "long"
        assert btc["size"] == 0.1
        assert btc["unrealized_pnl"] == 200.0

        # Check ETH details
        assert "ETH" in summary["positions_by_coin"]
        eth = summary["positions_by_coin"]["ETH"]
        assert eth["side"] == "short"
        assert eth["unrealized_pnl"] == 100.0

    def test_calculate_required_margin(self, position_manager, mock_client):
        """Test calculating required margin."""
        price_obj = Mock()
        price_obj.price = Decimal("50000")
        mock_client.get_price.return_value = price_obj

        # 0.1 BTC at $50k = $5000 notional
        # At 10x leverage = $500 margin
        margin = position_manager.calculate_required_margin(
            "BTC", Decimal("0.1"), leverage=10
        )

        assert margin == Decimal("500")

    def test_calculate_required_margin_no_leverage(self, position_manager, mock_client):
        """Test calculating margin with 1x leverage."""
        price_obj = Mock()
        price_obj.price = Decimal("3000")
        mock_client.get_price.return_value = price_obj

        # 1 ETH at $3000 = $3000 notional
        # At 1x leverage = $3000 margin
        margin = position_manager.calculate_required_margin(
            "ETH", Decimal("1"), leverage=1
        )

        assert margin == Decimal("3000")

    def test_repr(self, position_manager):
        """Test string representation."""
        repr_str = repr(position_manager)
        assert "PositionManager" in repr_str
