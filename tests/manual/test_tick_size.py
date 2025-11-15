#!/usr/bin/env python3
"""Check tick size and asset metadata."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from hyperliquid.info import Info

load_dotenv()

print("=" * 70)
print("HyperLiquid Asset Metadata Check")
print("=" * 70)

# Initialize Info API
info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)

# Get metadata
meta = info.meta()
universe = meta.get("universe", [])

# Find BTC
btc_meta = None
for asset in universe:
    if asset["name"] == "BTC":
        btc_meta = asset
        break

if btc_meta:
    print("\nBTC Metadata:")
    print(f"  Name: {btc_meta.get('name')}")
    print(f"  Size Decimals: {btc_meta.get('szDecimals')}")

    # Get current price
    all_mids = info.all_mids()
    btc_price = float(all_mids.get("BTC", 0))
    print(f"\n  Current Mid Price: ${btc_price:,.2f}")

    # Calculate test price with proper rounding
    sz_decimals = btc_meta.get('szDecimals', 5)

    # Try market order style - slightly below mid
    test_price_below = btc_price * 0.999  # 0.1% below

    print(f"\n  Test Price (0.1% below): ${test_price_below:,.2f}")
    print(f"  Rounded to {sz_decimals} decimals: ${test_price_below:.{sz_decimals}f}")

    # Show full metadata
    print("\nFull BTC Metadata:")
    for key, value in btc_meta.items():
        print(f"  {key}: {value}")
else:
    print("BTC not found in universe!")

print("\n" + "=" * 70)
