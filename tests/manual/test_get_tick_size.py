#!/usr/bin/env python3
"""Get exact tick size information."""

from hyperliquid.info import Info

print("=" * 70)
print("Get Tick Size Information")
print("=" * 70)

# Initialize Info API
info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)

# Get metadata
meta = info.meta()

print("\nFull meta response keys:")
print(meta.keys())

# Check for tick size table
if 'assetCtxs' in meta:
    print("\nAsset Contexts:")
    for idx, ctx in enumerate(meta['assetCtxs']):
        if idx == 3:  # asset=3 is BTC based on error
            print(f"\nAsset {idx} (likely BTC):")
            for key, value in ctx.items():
                print(f"  {key}: {value}")

universe = meta.get("universe", [])
print(f"\nFound {len(universe)} assets in universe")

# Find BTC (should be index 3)
for idx, asset in enumerate(universe):
    if asset["name"] == "BTC":
        print(f"\nBTC is at index: {idx}")
        print("BTC asset data:")
        for key, value in asset.items():
            print(f"  {key}: {value}")

# Look for price context
print("\n" + "=" * 70)
