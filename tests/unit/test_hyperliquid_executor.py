"""Unit tests for HyperLiquid Executor."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from src.trading_bot.trading.hyperliquid_executor import (
    HyperLiquidExecutor,
    OrderType
)


class TestHyperLiquidExecutor:
    """Test HyperLiquid Executor with official SDK."""

    @pytest.fixture
    def test_private_key(self):
        """Generate a test private key."""
        return "0x" + "1" * 64

    @pytest.fixture
    def executor_dry_run(self, test_private_key):
        """Create executor in dry-run mode (no external dependencies)."""
        with patch('src.trading_bot.trading.hyperliquid_executor.Info') as MockInfo:
            # Mock Info.meta() for get_supported_assets()
            mock_info = MockInfo.return_value
            mock_info.meta.return_value = {
                "universe": [
                    {"name": "BTC"},
                    {"name": "ETH"},
                    {"name": "SOL"}
                ]
            }

            executor = HyperLiquidExecutor(
                base_url="https://api.hyperliquid-testnet.xyz",
                private_key=test_private_key,
                dry_run=True
            )
            return executor

    @pytest.fixture
    def executor_live(self, test_private_key):
        """Create executor in live mode (mocked SDK)."""
        with patch('src.trading_bot.trading.hyperliquid_executor.Exchange') as MockExchange:
            with patch('src.trading_bot.trading.hyperliquid_executor.Info') as MockInfo:
                # Mock Info
                mock_info = MockInfo.return_value
                mock_info.meta.return_value = {
                    "universe": [
                        {"name": "BTC"},
                        {"name": "ETH"},
                        {"name": "SOL"}
                    ]
                }

                # Mock Exchange
                mock_exchange = MockExchange.return_value

                executor = HyperLiquidExecutor(
                    base_url="https://api.hyperliquid-testnet.xyz",
                    private_key=test_private_key,
                    dry_run=False
                )
                executor.exchange = mock_exchange  # Assign mock
                return executor

    def test_initialize_executor_dry_run(self, executor_dry_run):
        """Test executor initialization in dry-run mode."""
        assert executor_dry_run is not None
        assert executor_dry_run.base_url == "https://api.hyperliquid-testnet.xyz"
        assert executor_dry_run.dry_run is True
        assert executor_dry_run.exchange is None  # No exchange in dry-run
        assert executor_dry_run.wallet_address.startswith("0x")
        assert executor_dry_run.vault_address is None

    def test_initialize_with_vault(self, test_private_key):
        """Test initialization with vault address."""
        with patch('src.trading_bot.trading.hyperliquid_executor.Exchange'):
            with patch('src.trading_bot.trading.hyperliquid_executor.Info') as MockInfo:
                mock_info = MockInfo.return_value
                mock_info.meta.return_value = {"universe": [{"name": "BTC"}]}

                vault = "0x" + "2" * 40
                executor = HyperLiquidExecutor(
                    base_url="https://api.hyperliquid-testnet.xyz",
                    private_key=test_private_key,
                    vault_address=vault,
                    dry_run=True
                )
                assert executor.vault_address == vault

    def test_get_address(self, executor_dry_run):
        """Test getting wallet address."""
        address = executor_dry_run.get_address()
        assert address is not None
        assert address.startswith("0x")
        assert len(address) == 42

    def test_get_supported_assets(self, executor_dry_run):
        """Test getting list of supported assets."""
        assets = executor_dry_run.get_supported_assets()
        assert isinstance(assets, list)
        assert "BTC" in assets
        assert "ETH" in assets
        assert len(assets) > 0

    def test_place_order_dry_run(self, executor_dry_run):
        """Test placing order in dry-run mode."""
        success, order_id, error = executor_dry_run.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("0.1"),
            price=Decimal("50000"),
            order_type=OrderType.LIMIT
        )

        assert success is True
        assert order_id is not None
        assert error is None

        # Verify dry-run order was tracked
        assert order_id in executor_dry_run._dry_run_orders
        order = executor_dry_run._dry_run_orders[order_id]
        assert order["coin"] == "BTC"
        assert order["is_buy"] is True
        assert order["size"] == 0.1
        assert order["price"] == 50000.0

    def test_place_market_order_dry_run(self, executor_dry_run):
        """Test placing market order in dry-run mode."""
        success, order_id, error = executor_dry_run.place_order(
            coin="ETH",
            is_buy=False,
            size=Decimal("1.0"),
            order_type=OrderType.MARKET
        )

        assert success is True
        assert order_id is not None
        assert error is None

    def test_place_limit_order_live(self, executor_live):
        """Test placing limit order in live mode (mocked)."""
        # Mock successful order response
        executor_live.exchange.order.return_value = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{
                        "resting": {"oid": 12345}
                    }]
                }
            }
        }

        success, order_id, error = executor_live.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("0.1"),
            price=Decimal("50000"),
            order_type=OrderType.LIMIT
        )

        assert success is True
        assert order_id == 12345
        assert error is None

    def test_place_order_filled_immediately(self, executor_live):
        """Test placing order that fills immediately."""
        executor_live.exchange.order.return_value = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{
                        "filled": {"oid": 67890}
                    }]
                }
            }
        }

        success, order_id, error = executor_live.place_order(
            coin="ETH",
            is_buy=False,
            size=Decimal("1.0"),
            order_type=OrderType.MARKET
        )

        assert success is True
        assert order_id == 67890
        assert error is None

    def test_place_order_rejected(self, executor_live):
        """Test placing order that gets rejected."""
        executor_live.exchange.order.return_value = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{
                        "error": "Insufficient margin"
                    }]
                }
            }
        }

        success, order_id, error = executor_live.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("100.0"),
            price=Decimal("50000")
        )

        assert success is False
        assert order_id is None
        assert "Insufficient margin" in error

    def test_cancel_order_dry_run(self, executor_dry_run):
        """Test canceling order in dry-run mode."""
        # First place an order
        success, order_id, _ = executor_dry_run.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("0.1"),
            price=Decimal("50000")
        )
        assert success is True

        # Then cancel it
        success, error = executor_dry_run.cancel_order("BTC", order_id)
        assert success is True
        assert error is None
        assert executor_dry_run._dry_run_orders[order_id]["status"] == "cancelled"

    def test_cancel_order_not_found_dry_run(self, executor_dry_run):
        """Test canceling non-existent order in dry-run mode."""
        success, error = executor_dry_run.cancel_order("BTC", 99999)
        assert success is False
        assert "not found" in error.lower()

    def test_cancel_order_live(self, executor_live):
        """Test canceling order in live mode (mocked)."""
        executor_live.exchange.cancel.return_value = {
            "status": "ok"
        }

        success, error = executor_live.cancel_order("BTC", 12345)
        assert success is True
        assert error is None

    def test_update_leverage_dry_run(self, executor_dry_run):
        """Test updating leverage in dry-run mode."""
        success, error = executor_dry_run.update_leverage("BTC", 10, True)
        assert success is True
        assert error is None

    def test_update_leverage_invalid_range(self, executor_dry_run):
        """Test leverage validation."""
        success, error = executor_dry_run.update_leverage("BTC", 0, True)
        assert success is False
        assert "Invalid leverage" in error

        success, error = executor_dry_run.update_leverage("BTC", 51, True)
        assert success is False
        assert "Invalid leverage" in error

    def test_update_leverage_live(self, executor_live):
        """Test updating leverage in live mode (mocked)."""
        executor_live.exchange.update_leverage.return_value = {
            "status": "ok"
        }

        success, error = executor_live.update_leverage("BTC", 5, False)
        assert success is True
        assert error is None

    def test_round_price_to_tick_btc(self, executor_dry_run):
        """Test price rounding for BTC."""
        # BTC at high price should use $10 tick
        rounded = executor_dry_run._round_price_to_tick("BTC", 50123.45)
        assert rounded == 50120.0  # Rounded to $10 tick

    def test_round_price_to_tick_altcoin(self, executor_dry_run):
        """Test price rounding for altcoins."""
        # Mid-price altcoin should use $1 tick
        rounded = executor_dry_run._round_price_to_tick("SOL", 123.45)
        assert rounded == 123.0  # Rounded to $1 tick

    def test_repr(self, executor_dry_run):
        """Test string representation."""
        repr_str = repr(executor_dry_run)
        assert "HyperLiquidExecutor" in repr_str
        assert executor_dry_run.wallet_address in repr_str
        assert "DRY-RUN" in repr_str

    def test_repr_live_mode(self, executor_live):
        """Test string representation for live mode."""
        repr_str = repr(executor_live)
        assert "HyperLiquidExecutor" in repr_str
        assert "LIVE" in repr_str

    def test_get_supported_assets_fallback(self, test_private_key):
        """Test fallback to common assets when API fails."""
        with patch('src.trading_bot.trading.hyperliquid_executor.Info') as MockInfo:
            mock_info = MockInfo.return_value
            mock_info.meta.side_effect = Exception("API error")

            executor = HyperLiquidExecutor(
                base_url="https://api.hyperliquid-testnet.xyz",
                private_key=test_private_key,
                dry_run=True
            )

            assets = executor.get_supported_assets()
            # Should return fallback list
            assert isinstance(assets, list)
            assert "BTC" in assets
            assert "ETH" in assets
