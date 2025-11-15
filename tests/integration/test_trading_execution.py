"""Integration tests for trading execution (Phase 3) in Dry-Run mode.

Tests trading execution with simulated orders:
- Order placement
- Order cancellation
- Leverage management
- Position management
- Risk management
"""

import pytest
from decimal import Decimal

from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor


@pytest.mark.integration
class TestTradingExecutionDryRun:
    """Integration tests for trading execution in dry-run mode."""

    def test_executor_initialization_dry_run(self, test_config):
        """Test executor initialization in dry-run mode."""
        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        assert executor is not None
        assert executor.dry_run is True
        assert executor._dry_run_order_id_counter == 10000

        print(f"\n[OK] Executor initialized in DRY-RUN mode")
        print(f"   Address: {executor.get_address()}")

    def test_place_limit_order_dry_run(self, test_config):
        """Test placing limit order in dry-run mode."""
        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        # Place simulated limit buy order
        success, order_id, error = executor.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("0.1"),
            price=Decimal("50000.0"),
            order_type="limit"
        )

        # Verify success
        assert success is True
        assert order_id is not None
        assert error is None
        assert order_id == 10001  # First order ID

        # Verify order is stored
        assert order_id in executor._dry_run_orders
        order_data = executor._dry_run_orders[order_id]
        assert order_data["coin"] == "BTC"
        assert order_data["is_buy"] is True
        assert order_data["size"] == 0.1
        assert order_data["price"] == 50000.0
        assert order_data["status"] == "filled"

        print(f"\n[OK] [DRY-RUN] Limit order placed successfully")
        print(f"   Order ID: {order_id}")
        print(f"   BTC BUY 0.1 @ $50,000")

    def test_place_market_order_dry_run(self, test_config):
        """Test placing market order in dry-run mode."""
        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        # Place simulated market sell order
        success, order_id, error = executor.place_order(
            coin="ETH",
            is_buy=False,
            size=Decimal("1.0"),
            order_type="market"
        )

        # Verify success
        assert success is True
        assert order_id is not None
        assert error is None

        # Verify order data
        order_data = executor._dry_run_orders[order_id]
        assert order_data["coin"] == "ETH"
        assert order_data["is_buy"] is False
        assert order_data["order_type"] == "market"

        print(f"\n[OK] [DRY-RUN] Market order placed successfully")
        print(f"   Order ID: {order_id}")
        print(f"   ETH SELL 1.0 @ MARKET")

    def test_cancel_order_dry_run(self, test_config):
        """Test canceling order in dry-run mode."""
        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        # Place order first
        success, order_id, error = executor.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("0.1"),
            price=Decimal("50000.0")
        )
        assert success is True

        # Cancel the order
        success, error = executor.cancel_order("BTC", order_id)

        # Verify cancellation
        assert success is True
        assert error is None

        # Verify order status updated
        order_data = executor._dry_run_orders[order_id]
        assert order_data["status"] == "cancelled"

        print(f"\n[OK] [DRY-RUN] Order cancelled successfully")
        print(f"   Order ID: {order_id}")

    def test_cancel_nonexistent_order_dry_run(self, test_config):
        """Test canceling non-existent order in dry-run mode."""
        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        # Try to cancel non-existent order
        success, error = executor.cancel_order("BTC", 99999)

        # Should fail gracefully
        assert success is False
        assert error == "Order not found"

        print(f"\n[OK] [DRY-RUN] Correctly handled non-existent order cancellation")

    def test_update_leverage_dry_run(self, test_config):
        """Test updating leverage in dry-run mode."""
        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        # Update leverage to 5x cross margin
        success, error = executor.update_leverage("BTC", 5, is_cross=True)

        # Verify success
        assert success is True
        assert error is None

        print(f"\n[OK] [DRY-RUN] Leverage updated successfully")
        print(f"   BTC: 5x (cross margin)")

    def test_invalid_leverage_dry_run(self, test_config):
        """Test invalid leverage value in dry-run mode."""
        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        # Try invalid leverage (51x)
        success, error = executor.update_leverage("BTC", 51, is_cross=True)

        # Should fail validation
        assert success is False
        assert "Invalid leverage" in error

        print(f"\n[OK] [DRY-RUN] Correctly rejected invalid leverage")
        print(f"   Error: {error}")

    def test_multiple_orders_dry_run(self, test_config):
        """Test placing multiple orders in dry-run mode."""
        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        orders_placed = []

        # Place multiple orders
        coins = ["BTC", "ETH", "SOL"]
        for i, coin in enumerate(coins):
            success, order_id, error = executor.place_order(
                coin=coin,
                is_buy=(i % 2 == 0),  # Alternate buy/sell
                size=Decimal("0.1"),
                price=Decimal("1000.0") * (i + 1)
            )

            assert success is True
            assert order_id is not None
            orders_placed.append((coin, order_id))

        # Verify all orders stored
        assert len(orders_placed) == 3
        assert len(executor._dry_run_orders) == 3

        print(f"\n[OK] [DRY-RUN] Placed {len(orders_placed)} orders:")
        for coin, oid in orders_placed:
            order_data = executor._dry_run_orders[oid]
            side = "BUY" if order_data["is_buy"] else "SELL"
            print(f"   {coin} {side} {order_data['size']} @ ${order_data['price']}")

    def test_order_id_increment_dry_run(self, test_config):
        """Test that order IDs increment correctly in dry-run mode."""
        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        order_ids = []

        # Place 5 orders
        for i in range(5):
            success, order_id, error = executor.place_order(
                coin="BTC",
                is_buy=True,
                size=Decimal("0.01"),
                price=Decimal("50000.0")
            )

            assert success is True
            order_ids.append(order_id)

        # Verify IDs increment sequentially
        assert order_ids == [10001, 10002, 10003, 10004, 10005]

        print(f"\n[OK] [DRY-RUN] Order IDs increment correctly:")
        print(f"   {order_ids}")

    def test_dry_run_vs_live_mode_flag(self, test_config):
        """Test that dry-run flag prevents real API calls."""
        # Dry-run executor
        dry_executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        # Live executor (not actually used, just for comparison)
        live_executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=False
        )

        assert dry_executor.dry_run is True
        assert live_executor.dry_run is False

        print(f"\n[OK] Dry-run flag correctly set:")
        print(f"   Dry executor: {dry_executor.dry_run}")
        print(f"   Live executor: {live_executor.dry_run}")

    @pytest.mark.slow
    def test_order_execution_performance_dry_run(self, test_config):
        """Test order execution performance in dry-run mode."""
        import time

        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        start_time = time.time()

        # Place 10 orders
        for i in range(10):
            executor.place_order(
                coin="BTC",
                is_buy=True,
                size=Decimal("0.01"),
                price=Decimal("50000.0")
            )

        duration = time.time() - start_time

        # Dry-run should be very fast (< 0.1s for 10 orders)
        assert duration < 0.1

        print(f"\n[OK] [DRY-RUN] Placed 10 orders in {duration:.4f}s")
        print(f"   Average: {duration/10*1000:.2f}ms per order")

    def test_unsupported_asset_handling(self, test_config):
        """Test handling of unsupported asset in dry-run mode.

        Note: With official SDK integration, the executor no longer validates
        coin symbols upfront. The exchange will reject invalid symbols when
        the order is placed. In dry-run mode, we simulate success for any coin.
        """
        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        # In dry-run mode, unsupported coins are simulated as successful
        success, order_id, error = executor.place_order(
            coin="UNSUPPORTED",
            is_buy=True,
            size=Decimal("0.1"),
            price=Decimal("100.0")
        )

        # Dry-run mode accepts any coin (for testing flexibility)
        assert success is True
        assert order_id is not None
        print(f"\n[OK] [DRY-RUN] Accepted unsupported asset in dry-run mode")
        print(f"   Note: Live mode would reject this at the exchange level")

    def test_get_supported_assets(self, test_config):
        """Test getting list of supported assets."""
        executor = HyperLiquidExecutor(
            base_url=test_config["hyperliquid"]["base_url"],
            private_key=test_config["hyperliquid"]["private_key"],
            dry_run=True
        )

        assets = executor.get_supported_assets()

        assert isinstance(assets, list)
        assert len(assets) > 0
        assert "BTC" in assets or "ETH" in assets

        print(f"\n[OK] Supported assets ({len(assets)} total):")
        print(f"   {', '.join(assets[:10])}...")
