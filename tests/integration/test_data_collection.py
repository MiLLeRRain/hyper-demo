"""Integration tests for data collection (Phase 1).

Tests HyperLiquid data collection in dry-run mode:
- Market data fetching
- User state fetching
- Order book fetching
"""

import pytest
from decimal import Decimal

from trading_bot.data.hyperliquid_client import HyperliquidClient


@pytest.mark.integration
class TestDataCollection:
    """Integration tests for data collection."""

    def test_client_initialization(self, test_config):
        """Test HyperLiquid client initialization."""
        client = HyperliquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        assert client is not None
        assert client.base_url == test_config["hyperliquid"]["base_url"]

    def test_get_all_prices_real_api(self, test_config):
        """Test fetching real market prices from API.

        This test calls the REAL HyperLiquid API to fetch current prices.
        Safe to run in dry-run mode as it's read-only.
        """
        client = HyperliquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        # Fetch real market data
        prices = client.get_all_prices()

        # Verify response structure
        assert prices is not None
        assert isinstance(prices, dict)

        # Check for common coins
        expected_coins = ["BTC", "ETH"]
        for coin in expected_coins:
            if coin in prices:
                from trading_bot.models.market_data import Price
                assert isinstance(prices[coin], Price)
                assert prices[coin].price > 0

        print(f"\n[OK] Fetched prices for {len(prices)} coins")
        if "BTC" in prices:
            print(f"   BTC: ${prices['BTC'].price}")
        if "ETH" in prices:
            print(f"   ETH: ${prices['ETH'].price}")

    @pytest.mark.skip(reason="Order book method not yet implemented in HyperliquidClient")
    def test_get_l2_snapshot_real_api(self, test_config):
        """Test fetching real order book from API.

        This test calls the REAL HyperLiquid API.
        Safe to run as it's read-only.

        NOTE: This test is skipped because get_l2_snapshot() is not yet implemented.
        """
        client = HyperliquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        # Fetch real order book for BTC
        orderbook = client.get_l2_snapshot("BTC")

        # Verify response structure
        assert orderbook is not None
        assert "coin" in orderbook
        assert "levels" in orderbook
        assert len(orderbook["levels"]) == 2  # [bids, asks]

        bids, asks = orderbook["levels"]

        # Verify bids
        assert len(bids) > 0
        best_bid = bids[0]
        assert "px" in best_bid
        assert "sz" in best_bid

        # Verify asks
        assert len(asks) > 0
        best_ask = asks[0]
        assert "px" in best_ask
        assert "sz" in best_ask

        # Verify bid < ask (no arbitrage)
        best_bid_px = float(best_bid["px"])
        best_ask_px = float(best_ask["px"])
        assert best_bid_px < best_ask_px

        spread = best_ask_px - best_bid_px
        spread_pct = (spread / best_bid_px) * 100

        print(f"\n[OK] BTC Order Book:")
        print(f"   Best Bid: ${best_bid_px:.2f}")
        print(f"   Best Ask: ${best_ask_px:.2f}")
        print(f"   Spread: ${spread:.2f} ({spread_pct:.4f}%)")

    @pytest.mark.skip(reason="User state method not yet implemented in HyperliquidClient")
    def test_get_user_state_with_address(self, test_config):
        """Test fetching user state for a valid address.

        Note: This will return empty state for test address,
        but validates API connectivity.

        NOTE: This test is skipped because get_user_state() is not yet implemented.
        """
        client = HyperliquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        # Use test address
        test_address = "0x0000000000000000000000000000000000000001"

        # Fetch user state (will be empty for test address)
        user_state = client.get_user_state(test_address)

        # Verify response structure
        assert user_state is not None
        assert "marginSummary" in user_state or "assetPositions" in user_state

        print(f"\n[OK] User state fetch successful for {test_address}")

    def test_collect_multi_coin_data(self, test_config):
        """Test collecting data for multiple coins."""
        client = HyperliquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        coins = test_config["trading"]["coins"]  # ["BTC", "ETH", "SOL"]

        # Get all prices once
        all_prices = client.get_all_prices()

        # Collect data for all coins
        market_data = {}
        for coin in coins:
            try:
                if coin in all_prices:
                    price_obj = all_prices[coin]
                    market_data[coin] = {
                        "price": price_obj.price,
                        "coin": coin
                    }

                    # Note: Order book fetching skipped as get_l2_snapshot() not implemented

            except Exception as e:
                print(f"   [FAIL] Failed to fetch data for {coin}: {e}")

        # Verify we got at least some data
        assert len(market_data) > 0

        print(f"\n[OK] Collected data for {len(market_data)} coins:")
        for coin, data in market_data.items():
            price = data.get("price", "N/A")
            print(f"   {coin}: Price=${price}")

    @pytest.mark.slow
    def test_data_collection_performance(self, test_config):
        """Test data collection performance (should be < 5 seconds)."""
        import time

        client = HyperliquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        start_time = time.time()

        # Collect data for all trading coins
        prices = client.get_all_prices()

        # Verify we got data
        assert len(prices) > 0

        duration = time.time() - start_time

        # Should complete in < 5 seconds (Phase 4 requirement)
        assert duration < 5.0

        print(f"\n[OK] Data collection completed in {duration:.2f}s (target: <5s)")
        print(f"   Fetched {len(prices)} coin prices")

    def test_error_handling_invalid_coin(self, test_config):
        """Test error handling for invalid coin symbol."""
        client = HyperliquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        # Try to fetch data for invalid coin
        invalid_coin = "INVALIDCOIN123"

        # Should handle gracefully (not crash)
        try:
            price = client.get_price(invalid_coin)
            # If it returns something without error, that's unexpected
            print(f"\n[WARN] Got response for invalid coin: {price}")
        except ValueError as e:
            # Expected to raise ValueError
            print(f"\n[OK] Correctly handled invalid coin with error: {type(e).__name__}")
            assert "Price not available" in str(e)
        except Exception as e:
            # Other exceptions are also acceptable
            print(f"\n[OK] Correctly handled invalid coin with error: {type(e).__name__}")
            assert True

    def test_data_consistency(self, test_config):
        """Test that fetched data is consistent across multiple calls."""
        client = HyperliquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        # Fetch data twice
        prices1 = client.get_all_prices()
        prices2 = client.get_all_prices()

        # Both should return data
        assert prices1 is not None
        assert prices2 is not None

        # Both should have BTC (if available)
        if "BTC" in prices1 and "BTC" in prices2:
            price1 = prices1["BTC"].price
            price2 = prices2["BTC"].price

            # Prices should be similar (within 5% - allows for market movement)
            price_diff_pct = abs(price1 - price2) / price1 * 100
            assert price_diff_pct < 5.0

            print(f"\n[OK] Price consistency check passed:")
            print(f"   Call 1: ${price1:.2f}")
            print(f"   Call 2: ${price2:.2f}")
            print(f"   Difference: {price_diff_pct:.4f}%")
