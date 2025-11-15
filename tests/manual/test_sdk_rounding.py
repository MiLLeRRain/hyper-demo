#!/usr/bin/env python3
"""Test SDK's rounding utilities."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from hyperliquid.info import Info
from hyperliquid.utils import constants

print("=" * 70)
print("SDK Rounding Utilities")
print("=" * 70)

# Check what's in constants
print("\nConstants available:")
print(dir(constants))

# Initialize Info API
info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)

# Get current price
all_mids = info.all_mids()
btc_price = float(all_mids.get("BTC", 0))

print(f"\nBTC Mid Price: ${btc_price:,.2f}")

# Try different rounding strategies
# For BTC at $95k range, typical tick sizes might be:
# $0.1, $1, $10, $50, $100

possible_tick_sizes = [0.1, 0.5, 1, 5, 10, 50, 100]

for tick in possible_tick_sizes:
    rounded = round(btc_price / tick) * tick
    print(f"Tick {tick:>6}: ${rounded:>12,.2f}")

print("\n" + "=" * 70)
