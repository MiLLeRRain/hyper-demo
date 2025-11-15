#!/usr/bin/env python3
"""Direct test of order placement API."""

import os
import sys
from pathlib import Path
from decimal import Decimal

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor

def main():
    load_dotenv()

    private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")

    print("=" * 70)
    print("Direct Order Placement Test")
    print("=" * 70)

    executor = HyperLiquidExecutor(
        base_url="https://api.hyperliquid-testnet.xyz",
        private_key=private_key,
        dry_run=False
    )

    wallet = executor.get_address()
    print(f"\nWallet: {wallet}")
    print(f"Testnet: https://app.hyperliquid-testnet.xyz")
    print("\nAttempting to place a small test order...")

    # Get current mid price from Info API
    from hyperliquid.info import Info
    info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
    all_mids = info.all_mids()
    current_price = float(all_mids.get("BTC", 0))

    # Use a round number price that's clearly divisible by any tick size
    # Round to nearest $10 and subtract $100 to ensure it's below market
    test_price = (int(current_price / 10) * 10) - 100

    print(f"Current BTC mid price: ${current_price:,.2f}")
    print(f"Test order price: ${test_price:,.2f} (rounded to $10 tick)")

    # Try a very small order
    success, order_id, error = executor.place_order(
        coin="BTC",
        is_buy=True,
        size=Decimal("0.001"),
        price=Decimal(str(test_price)),  # Within price limits
        order_type="limit"
    )

    print("\n" + "=" * 70)
    if success:
        print("SUCCESS!")
        print(f"Order ID: {order_id}")
        print("\nTrying to cancel...")
        cancel_success, cancel_error = executor.cancel_order("BTC", order_id)
        if cancel_success:
            print("Order cancelled successfully")
        else:
            print(f"Cancel failed: {cancel_error}")
    else:
        print("FAILED!")
        print(f"Error: {error}")
        print("\nPossible reasons:")
        print("1. Wallet not activated on testnet website")
        print("2. Need to accept terms of service on website")
        print("3. Need to complete first action via UI")
        print("\nPlease:")
        print(f"- Visit: https://app.hyperliquid-testnet.xyz")
        print(f"- Connect wallet: {wallet}")
        print("- View portfolio or set leverage via UI")
        print("- Then try again")
    print("=" * 70)

if __name__ == "__main__":
    main()
