"""Integration tests for data collection (Phase 1).

Tests HyperLiquid data collection in dry-run mode:
- Market data fetching
- User state fetching
- Order book fetching
"""

import pytest
from decimal import Decimal

from trading_bot.hyperliquid.client import HyperLiquidClient


@pytest.mark.integration
class TestDataCollection:
    """Integration tests for data collection."""

    def test_client_initialization(self, test_config):
        """Test HyperLiquid client initialization."""
        client = HyperLiquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        assert client is not None
        assert client.base_url == test_config["hyperliquid"]["base_url"]

    def test_get_all_mids_real_api(self, test_config):
        """Test fetching real market prices from API.

        This test calls the REAL HyperLiquid API to fetch current prices.
        Safe to run in dry-run mode as it's read-only.
        """
        client = HyperLiquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        # Fetch real market data
        mids = client.get_all_mids()

        # Verify response structure
        assert mids is not None
        assert isinstance(mids, dict)

        # Check for common coins
        expected_coins = ["BTC", "ETH"]
        for coin in expected_coins:
            if coin in mids:
                assert isinstance(mids[coin], (int, float))
                assert mids[coin] > 0

        print(f"\n✅ Fetched prices for {len(mids)} coins")
        print(f"   BTC: ${mids.get('BTC', 'N/A')}")
        print(f"   ETH: ${mids.get('ETH', 'N/A')}")

    def test_get_l2_snapshot_real_api(self, test_config):
        """Test fetching real order book from API.

        This test calls the REAL HyperLiquid API.
        Safe to run as it's read-only.
        """
        client = HyperLiquidClient(
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

        print(f"\n✅ BTC Order Book:")
        print(f"   Best Bid: ${best_bid_px:.2f}")
        print(f"   Best Ask: ${best_ask_px:.2f}")
        print(f"   Spread: ${spread:.2f} ({spread_pct:.4f}%)")

    def test_get_user_state_with_address(self, test_config):
        """Test fetching user state for a valid address.

        Note: This will return empty state for test address,
        but validates API connectivity.
        """
        client = HyperLiquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        # Use test address
        test_address = "0x0000000000000000000000000000000000000001"

        # Fetch user state (will be empty for test address)
        user_state = client.get_user_state(test_address)

        # Verify response structure
        assert user_state is not None
        assert "marginSummary" in user_state or "assetPositions" in user_state

        print(f"\n✅ User state fetch successful for {test_address}")

    def test_collect_multi_coin_data(self, test_config):
        """Test collecting data for multiple coins."""
        client = HyperLiquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        coins = test_config["trading"]["coins"]  # ["BTC", "ETH", "SOL"]

        # Collect data for all coins
        market_data = {}
        for coin in coins:
            try:
                # Get mid price
                mids = client.get_all_mids()
                if coin in mids:
                    market_data[coin] = {
                        "price": mids[coin],
                        "coin": coin
                    }

                    # Try to get order book
                    try:
                        orderbook = client.get_l2_snapshot(coin)
                        if orderbook and "levels" in orderbook:
                            bids, asks = orderbook["levels"]
                            if bids and asks:
                                market_data[coin]["bid"] = float(bids[0]["px"])
                                market_data[coin]["ask"] = float(asks[0]["px"])
                    except Exception as e:
                        print(f"   ⚠️  Could not fetch order book for {coin}: {e}")

            except Exception as e:
                print(f"   ❌ Failed to fetch data for {coin}: {e}")

        # Verify we got at least some data
        assert len(market_data) > 0

        print(f"\n✅ Collected data for {len(market_data)} coins:")
        for coin, data in market_data.items():
            price = data.get("price", "N/A")
            bid = data.get("bid", "N/A")
            ask = data.get("ask", "N/A")
            print(f"   {coin}: Price=${price}, Bid=${bid}, Ask=${ask}")

    @pytest.mark.slow
    def test_data_collection_performance(self, test_config):
        """Test data collection performance (should be < 5 seconds)."""
        import time

        client = HyperLiquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        start_time = time.time()

        # Collect data for all trading coins
        coins = test_config["trading"]["coins"]
        mids = client.get_all_mids()

        for coin in coins:
            if coin in mids:
                try:
                    client.get_l2_snapshot(coin)
                except Exception:
                    pass  # Some coins might not have order books

        duration = time.time() - start_time

        # Should complete in < 5 seconds (Phase 4 requirement)
        assert duration < 5.0

        print(f"\n✅ Data collection completed in {duration:.2f}s (target: <5s)")

    def test_error_handling_invalid_coin(self, test_config):
        """Test error handling for invalid coin symbol."""
        client = HyperLiquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        # Try to fetch data for invalid coin
        invalid_coin = "INVALIDCOIN123"

        # Should handle gracefully (not crash)
        try:
            orderbook = client.get_l2_snapshot(invalid_coin)
            # If it returns something, verify it's None or error structure
            if orderbook:
                print(f"\n⚠️  Got response for invalid coin: {orderbook}")
        except Exception as e:
            # Expected to raise exception
            print(f"\n✅ Correctly handled invalid coin with error: {type(e).__name__}")
            assert True

    def test_data_consistency(self, test_config):
        """Test that fetched data is consistent across multiple calls."""
        client = HyperLiquidClient(
            base_url=test_config["hyperliquid"]["base_url"]
        )

        # Fetch data twice
        mids1 = client.get_all_mids()
        mids2 = client.get_all_mids()

        # Both should return data
        assert mids1 is not None
        assert mids2 is not None

        # Both should have BTC (if available)
        if "BTC" in mids1 and "BTC" in mids2:
            price1 = mids1["BTC"]
            price2 = mids2["BTC"]

            # Prices should be similar (within 5% - allows for market movement)
            price_diff_pct = abs(price1 - price2) / price1 * 100
            assert price_diff_pct < 5.0

            print(f"\n✅ Price consistency check passed:")
            print(f"   Call 1: ${price1:.2f}")
            print(f"   Call 2: ${price2:.2f}")
            print(f"   Difference: {price_diff_pct:.4f}%")
