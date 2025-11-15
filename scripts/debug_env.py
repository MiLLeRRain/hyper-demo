#!/usr/bin/env python3
"""Debug environment variable loading."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor

print("=" * 70)
print("Environment Variable Debug")
print("=" * 70)

# Method 1: Load from current directory
env_file = Path(__file__).parent / ".env"
print(f"\n1. Env file path: {env_file}")
print(f"   Exists: {env_file.exists()}")

if env_file.exists():
    load_dotenv(env_file)
    pk = os.getenv("HYPERLIQUID_PRIVATE_KEY")
    print(f"\n2. Private key from .env:")
    print(f"   First 20 chars: {pk[:20] if pk else 'NOT FOUND'}...")
    print(f"   Has 0x prefix: {pk.startswith('0x') if pk else 'N/A'}")

    if pk:
        # Create executor
        print(f"\n3. Creating executor...")
        executor = HyperLiquidExecutor(
            base_url="https://api.hyperliquid-testnet.xyz",
            private_key=pk,
            dry_run=False
        )
        address = executor.get_address()
        print(f"   Wallet address: {address}")
        print(f"\n4. Expected address: 0xYOUR_WALLET_ADDRESS_HERE")
        print(f"   Match: {address == '0xYOUR_WALLET_ADDRESS_HERE'}")
