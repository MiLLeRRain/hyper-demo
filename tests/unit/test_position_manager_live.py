import pytest
from unittest.mock import Mock, MagicMock
from decimal import Decimal
from uuid import uuid4
from src.trading_bot.trading.position_manager import PositionManager
from src.trading_bot.models.database import TradingAgent, AgentTrade
from src.trading_bot.data.hyperliquid_client import HyperliquidClient
from src.trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor

class TestPositionManagerLive:
    @pytest.fixture
    def mock_db_session(self):
        return MagicMock()

    @pytest.fixture
    def mock_info_client(self):
        client = MagicMock(spec=HyperliquidClient)
        client.get_price.return_value = MagicMock(price=50000.0)
        return client

    @pytest.fixture
    def mock_executor(self):
        executor = MagicMock(spec=HyperLiquidExecutor)
        executor.dry_run = False
        executor.wallet_address = "0x123"
        executor.info = MagicMock()
        return executor

    @pytest.fixture
    def agent_id(self):
        return uuid4()

    def test_get_current_positions_live_sync(self, mock_db_session, mock_info_client, mock_executor, agent_id):
        # Setup DB trade
        trade = MagicMock(spec=AgentTrade)
        trade.id = 1
        trade.coin = "BTC"
        trade.size = Decimal("0.1")
        trade.entry_price = Decimal("40000.0")
        trade.side = "long"
        trade.status = "open"
        trade.agent_id = agent_id
        
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = [trade]
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = MagicMock(max_leverage=10)

        # Setup Exchange State
        mock_executor.info.user_state.return_value = {
            "assetPositions": [
                {
                    "position": {
                        "coin": "BTC",
                        "szi": "0.1",
                        "entryPx": "40000.0",
                        "leverage": {"value": 20},
                        "liquidationPx": "38000.0"
                    }
                }
            ]
        }

        manager = PositionManager(mock_info_client, mock_db_session, mock_executor)
        positions = manager.get_current_positions(agent_id)

        assert len(positions) == 1
        pos = positions[0]
        assert pos.coin == "BTC"
        assert pos.leverage == 20  # Should take from exchange
        assert pos.liquidation_price == 38000.0

    def test_get_current_positions_live_sync_mismatch_closed(self, mock_db_session, mock_info_client, mock_executor, agent_id):
        # DB says open, Exchange says 0 size (closed)
        trade = MagicMock(spec=AgentTrade)
        trade.id = 1
        trade.coin = "BTC"
        trade.size = Decimal("0.1")
        trade.status = "open"
        trade.agent_id = agent_id
        trade.notes = ""
        
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = [trade]

        # Exchange has 0 size for BTC (or no position)
        mock_executor.info.user_state.return_value = {
            "assetPositions": [
                {
                    "position": {
                        "coin": "BTC",
                        "szi": "0",
                        "entryPx": "0.0"
                    }
                }
            ]
        }

        manager = PositionManager(mock_info_client, mock_db_session, mock_executor)
        positions = manager.get_current_positions(agent_id)

        assert len(positions) == 0
        assert trade.status == "closed"
        assert "Auto-closed" in trade.notes
        mock_db_session.commit.assert_called()

    def test_get_account_value_live(self, mock_db_session, mock_info_client, mock_executor, agent_id):
        agent = MagicMock(spec=TradingAgent)
        agent.id = agent_id
        agent.name = "Test Agent"
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = agent

        # Setup Exchange State
        mock_executor.info.user_state.return_value = {
            "marginSummary": {
                "accountValue": "10000.0",
                "withdrawable": "5000.0",
                "totalMarginUsed": "2000.0"
            },
            "withdrawable": "5000.0",
            "assetPositions": []
        }

        manager = PositionManager(mock_info_client, mock_db_session, mock_executor)
        account_info = manager.get_account_value(agent_id)

        assert account_info.account_value == 10000.0
        assert account_info.withdrawable == 5000.0
        assert account_info.margin_used == 2000.0

    def test_get_account_value_live_failure_fallback(self, mock_db_session, mock_info_client, mock_executor, agent_id):
        agent = MagicMock(spec=TradingAgent)
        agent.id = agent_id
        agent.initial_balance = Decimal("1000.0")
        agent.max_leverage = 10
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = agent
        
        # Mock realized PnL query
        mock_db_session.query.return_value.filter_by.return_value.scalar.return_value = Decimal("100.0")

        # Make exchange call fail
        mock_executor.info.user_state.side_effect = Exception("API Error")

        manager = PositionManager(mock_info_client, mock_db_session, mock_executor)
        
        # Should fallback to calculation
        account_info = manager.get_account_value(agent_id)
        
        # 1000 + 100 = 1100
        assert account_info.account_value == 1100.0

