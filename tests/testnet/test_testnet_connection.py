#!/usr/bin/env python3
"""Test HyperLiquid Testnet connection and account access.

This script verifies:
1. Testnet API connectivity
2. Market data retrieval
3. Account authentication
4. Supported assets

Usage:
    python test_testnet_connection.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
from trading_bot.data.hyperliquid_client import HyperliquidClient
from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_market_data():
    """Test testnet market data retrieval."""
    print_header("Testing Testnet Market Data")

    try:
        client = HyperliquidClient(
            base_url="https://api.hyperliquid-testnet.xyz"
        )

        # Get all prices
        print("\nFetching coin prices...")
        prices = client.get_all_prices()
        print(f"[OK] Fetched {len(prices)} coin prices")

        # Show sample prices
        sample_coins = ["BTC", "ETH", "SOL"]
        for coin in sample_coins:
            if coin in prices:
                print(f"   {coin}: ${prices[coin].price:,.2f}")

        # Get metadata
        print("\nFetching exchange metadata...")
        meta = client.get_meta()
        universe = meta.get("universe", [])
        print(f"[OK] Exchange supports {len(universe)} assets")

        return True

    except Exception as e:
        print(f"[FAIL] Market data test failed: {e}")
        return False


def test_account_access():
    """Test testnet account access."""
    print_header("Testing Testnet Account Access")

    private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
    if not private_key:
        print("\n[FAIL] HYPERLIQUID_PRIVATE_KEY not found in environment")
        print("       Please set it in your .env file")
        return False

    try:
        # Create executor (testnet, non dry-run)
        executor = HyperLiquidExecutor(
            base_url="https://api.hyperliquid-testnet.xyz",
            private_key=private_key,
            dry_run=False  # Real testnet mode
        )

        print(f"\n[OK] Connected to HyperLiquid Testnet")
        print(f"     Wallet Address: {executor.get_address()}")

        # Get supported assets
        print("\nFetching supported assets...")
        assets = executor.get_supported_assets()
        print(f"[OK] {len(assets)} trading pairs available")
        print(f"     Sample: {', '.join(assets[:15])}...")

        return True

    except Exception as e:
        print(f"\n[FAIL] Account access test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_kline_data():
    """Test K-line data retrieval."""
    print_header("Testing K-line Data Retrieval")

    try:
        client = HyperliquidClient(
            base_url="https://api.hyperliquid-testnet.xyz"
        )

        print("\nFetching BTC 3-minute candles...")
        klines = client.get_klines("BTC", "3m", limit=10)

        if not klines.empty:
            print(f"[OK] Retrieved {len(klines)} candles")
            print(f"\n     Latest candle:")
            latest = klines.iloc[-1]
            print(f"     Time:  {latest['timestamp']}")
            print(f"     Open:  ${latest['open']:,.2f}")
            print(f"     High:  ${latest['high']:,.2f}")
            print(f"     Low:   ${latest['low']:,.2f}")
            print(f"     Close: ${latest['close']:,.2f}")
            return True
        else:
            print("[WARN] No K-line data returned")
            return False

    except Exception as e:
        print(f"[FAIL] K-line test failed: {e}")
        return False


def main():
    """Run all testnet connection tests."""
    print("\n" + "=" * 70)
    print("  HyperLiquid Testnet Connection Test")
    print("=" * 70)
    print("\n  This script will:")
    print("  1. Test market data retrieval")
    print("  2. Test account authentication")
    print("  3. Test historical data access")
    print("\n  [!] Make sure you have:")
    print("      - Created .env file with HYPERLIQUID_PRIVATE_KEY")
    print("      - Testnet wallet with faucet tokens")
    print("=" * 70)

    # Load environment variables from project root
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"\n[OK] Loaded environment from {env_file}")
    else:
        print(f"\n[WARN] No .env file found at {env_file}")
        print("       Copy .env.example to .env and configure it")

    # Run tests
    results = []

    results.append(("Market Data", test_market_data()))
    results.append(("Account Access", test_account_access()))
    results.append(("K-line Data", test_kline_data()))

    # Summary
    print_header("Test Summary")
    print()
    for test_name, passed in results:
        status = "[OK]  " if passed else "[FAIL]"
        print(f"  {status} {test_name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n" + "=" * 70)
        print("  [SUCCESS] All tests passed!")
        print("  You are ready to use HyperLiquid Testnet")
        print("=" * 70)
        print("\n  Next steps:")
        print("  1. Review docs/TESTNET_SETUP_GUIDE.md for trading tests")
        print("  2. Run test_testnet_trading.py for order placement test")
        print("  3. Modify config.yaml to set environment: 'testnet'")
        print()
        return 0
    else:
        print("\n" + "=" * 70)
        print("  [FAILED] Some tests failed")
        print("  Please check the errors above and:")
        print("  - Verify .env configuration")
        print("  - Check testnet wallet has tokens")
        print("  - Verify network connectivity")
        print("=" * 70)
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
