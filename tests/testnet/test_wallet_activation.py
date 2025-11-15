#!/usr/bin/env python3
"""Test wallet activation and basic connectivity."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor

def main():
    print("\n" + "=" * 70)
    print("  HyperLiquid Testnet Wallet Activation Check")
    print("=" * 70)

    # Load .env
    load_dotenv()

    private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
    if not private_key:
        print("\n[FAIL] HYPERLIQUID_PRIVATE_KEY not found")
        return 1

    print(f"\n[OK] Private key loaded: {private_key[:10]}...")

    # Create executor
    print("\n[CONNECT] Connecting to testnet...")
    try:
        executor = HyperLiquidExecutor(
            base_url="https://api.hyperliquid-testnet.xyz",
            private_key=private_key,
            dry_run=False
        )

        wallet_address = executor.get_address()
        print(f"[OK] Connected successfully!")
        print(f"\n[WALLET] Address: {wallet_address}")

    except Exception as e:
        print(f"\n[FAIL] Connection failed: {e}")
        return 1

    # Try to get supported assets (read-only, should work)
    print("\n[TEST] Testing read-only API access...")
    try:
        assets = executor.get_supported_assets()
        print(f"[OK] API access OK - {len(assets)} assets available")
    except Exception as e:
        print(f"[FAIL] API access failed: {e}")

    # Check if wallet is activated
    print("\n" + "=" * 70)
    print("  Account Activation Status")
    print("=" * 70)
    print("\n[!] To activate your account on HyperLiquid Testnet:")
    print()
    print("1. Visit: https://app.hyperliquid-testnet.xyz")
    print(f"2. Connect wallet: {wallet_address}")
    print("3. Complete one of these actions on the website:")
    print("   - Accept terms of service (if prompted)")
    print("   - View your portfolio")
    print("   - Set leverage for any coin")
    print("   - Try to place an order via UI")
    print()
    print("4. After activation, your wallet will be registered")
    print("5. Then you can use API/code to place orders")
    print()
    print("=" * 70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
