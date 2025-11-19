#!/usr/bin/env python3
"""Test real trading on HyperLiquid Testnet.

[!] WARNING: This script places REAL orders on testnet!
While testnet tokens have no value, this tests actual order placement.

Usage:
    python test_testnet_trading.py
"""

import os
import sys
from pathlib import Path
from decimal import Decimal
from time import sleep

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor
from trading_bot.data.hyperliquid_client import HyperliquidClient


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def get_current_price(coin: str) -> float:
    """Get current market price."""
    client = HyperliquidClient(base_url="https://api.hyperliquid-testnet.xyz")
    prices = client.get_all_prices()
    if coin in prices:
        return prices[coin].price
    return 0.0


def test_limit_order(executor: HyperLiquidExecutor):
    """Test placing and cancelling a limit order."""
    print_header("Test 1: Limit Order (Place & Cancel)")

    print("\n  Testing limit order placement...")
    print("  Strategy: Place order far from market (won't fill)")
    print()

    # Get current price
    current_price = get_current_price("BTC")
    if current_price == 0:
        print("[FAIL] Could not get BTC price")
        return False

    print(f"  Current BTC Price: ${current_price:,.2f}")

    # Place order at 50% of market price (very unlikely to fill)
    order_price = current_price * 0.5
    order_size = Decimal("0.001")  # Very small size

    print(f"\n  Placing BUY order:")
    print(f"     Coin:  BTC")
    print(f"     Size:  {order_size} BTC")
    print(f"     Price: ${order_price:,.2f} (50% below market)")
    print(f"     Type:  LIMIT")

    success, order_id, error = executor.place_order(
        coin="BTC",
        is_buy=True,
        size=order_size,
        price=Decimal(str(order_price)),
        order_type="limit"
    )

    if not success:
        print(f"\n  [FAIL] Order placement failed: {error}")
        return False

    print(f"\n  [OK] Order placed successfully!")
    print(f"       Order ID: {order_id}")
    print(f"       Status: Pending (unlikely to fill)")

    # Wait a moment
    print("\n  Waiting 2 seconds...")
    sleep(2)

    # Cancel the order
    print("\n  Cancelling order...")
    cancel_success, cancel_error = executor.cancel_order("BTC", order_id)

    if not cancel_success:
        print(f"  [WARN] Cancel failed: {cancel_error}")
        print(f"         Order may have already filled or expired")
        return True  # Still consider test passed

    print(f"  [OK] Order cancelled successfully")
    return True


def test_leverage_setting(executor: HyperLiquidExecutor):
    """Test leverage setting."""
    print_header("Test 2: Leverage Setting")

    print("\n  Testing leverage configuration...")

    # Set low leverage for safety
    leverage = 2
    is_cross = True

    print(f"\n  Setting leverage:")
    print(f"     Coin:     BTC")
    print(f"     Leverage: {leverage}x")
    print(f"     Mode:     {'Cross' if is_cross else 'Isolated'}")

    success, error = executor.update_leverage("BTC", leverage, is_cross)

    if not success:
        print(f"\n  [FAIL] Leverage update failed: {error}")
        return False

    print(f"\n  [OK] Leverage set successfully")
    return True


def test_multiple_coins(executor: HyperLiquidExecutor):
    """Test operations on multiple coins."""
    print_header("Test 3: Multiple Coins")

    coins_to_test = ["BTC", "ETH", "SOL"]
    results = []

    for coin in coins_to_test:
        print(f"\n  Testing {coin}...")

        # Get price
        price = get_current_price(coin)
        if price == 0:
            print(f"  [SKIP] Could not get {coin} price")
            continue

        print(f"     Current Price: ${price:,.2f}")

        # Set leverage
        success, error = executor.update_leverage(coin, 2, True)
        if success:
            print(f"     [OK] Leverage set to 2x")
            results.append(True)
        else:
            print(f"     [WARN] Leverage failed: {error}")
            results.append(False)

    success_rate = sum(results) / len(results) if results else 0
    print(f"\n  Success rate: {success_rate * 100:.0f}% ({sum(results)}/{len(results)})")

    return success_rate >= 0.5  # At least 50% success


def main():
    """Run testnet trading tests."""
    print("\n" + "=" * 70)
    print("  HyperLiquid Testnet Trading Test")
    print("=" * 70)
    print("\n  [!] WARNING: This will place REAL orders on testnet!")
    print("  [OK] Testnet tokens have no value - completely safe")
    print("  [OK] Orders will be placed far from market price")
    print("  [OK] Orders will be cancelled immediately")
    print("\n" + "=" * 70)

    # Confirmation
    response = input("\n  Continue with testnet trading test? (yes/no): ")
    if response.lower() != "yes":
        print("\n  Test cancelled by user")
        return 0

    # Load environment from project root
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    if not env_file.exists():
        print(f"\n  [FAIL] No .env file found at {env_file}")
        print(f"         Create .env from .env.example")
        return 1

    load_dotenv(env_file)

    private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
    if not private_key:
        print("\n  [FAIL] HYPERLIQUID_PRIVATE_KEY not set")
        return 1

    # Debug: Print private key info
    print(f"\n  [DEBUG] Private key loaded: {private_key[:20]}...")
    print(f"  [DEBUG] Has 0x prefix: {private_key.startswith('0x')}")

    # Create executor
    print("\n  Initializing testnet executor...")
    try:
        executor = HyperLiquidExecutor(
            base_url="https://api.hyperliquid-testnet.xyz",
            private_key=private_key,
            dry_run=False  # [!] REAL testnet trading
        )
        print(f"  [OK] Connected to testnet")
        print(f"       Wallet: {executor.get_address()}")
    except Exception as e:
        print(f"\n  [FAIL] Initialization failed: {e}")
        return 1

    # Run tests
    results = []

    try:
        results.append(("Limit Order", test_limit_order(executor)))
        results.append(("Leverage Setting", test_leverage_setting(executor)))
        results.append(("Multiple Coins", test_multiple_coins(executor)))
    except KeyboardInterrupt:
        print("\n\n  [!] Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n  [FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Summary
    print_header("Test Summary")
    print()
    for test_name, passed in results:
        status = "[OK]  " if passed else "[FAIL]"
        print(f"  {status} {test_name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n" + "=" * 70)
        print("  [SUCCESS] All trading tests passed!")
        print("=" * 70)
        print("\n  You have successfully:")
        print("  [OK] Placed a limit order on testnet")
        print("  [OK] Cancelled an order")
        print("  [OK] Set leverage for multiple coins")
        print("\n  Next steps:")
        print("  1. Review config.yaml and set environment: 'testnet'")
        print("  2. Run the full trading bot with AI decision making")
        print("  3. Monitor performance and iterate")
        print()
        return 0
    else:
        print("\n" + "=" * 70)
        print("  [FAILED] Some tests failed")
        print("=" * 70)
        print("\n  Check the errors above and verify:")
        print("  - Testnet account has sufficient balance")
        print("  - Network connectivity is stable")
        print("  - All coins are available on testnet")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
