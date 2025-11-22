#!/usr/bin/env python3
"""Verify wallet address matches private key."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from eth_account import Account

# Load environment
load_dotenv()

private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY_DEFAULT")

if not private_key:
    print("❌ HYPERLIQUID_PRIVATE_KEY_DEFAULT not found in .env")
    sys.exit(1)

# Ensure 0x prefix
if not private_key.startswith("0x"):
    private_key = "0x" + private_key

try:
    account = Account.from_key(private_key)
    print("=" * 70)
    print("Wallet Verification")
    print("=" * 70)
    print(f"\nPrivate Key (first 10 chars): {private_key[:10]}...")
    print(f"Wallet Address: {account.address}")
    print("\n" + "=" * 70)
    print("\nNext steps:")
    print("1. Visit https://app.hyperliquid-testnet.xyz")
    print(f"2. Connect wallet with address: {account.address}")
    print("3. Complete account activation on the website")
    print("4. Verify you can see your testnet balance")
    print("=" * 70)
except Exception as e:
    print(f"❌ Invalid private key: {e}")
    sys.exit(1)
