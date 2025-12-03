#!/usr/bin/env python3
"""Debug API request structure."""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from trading_bot.trading.hyperliquid_signer import HyperLiquidSigner

load_dotenv()

private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")

print("=" * 70)
print("API Request Debug")
print("=" * 70)

# Create signer
signer = HyperLiquidSigner(private_key)
print(f"\nWallet Address: {signer.get_address()}")

# Construct order action (exactly as HyperLiquidExecutor does)
action = {
    "type": "order",
    "orders": [{
        "a": 0,  # BTC asset index
        "b": True,  # Buy
        "p": "10000",  # Price
        "s": "0.001",  # Size
        "r": False,  # Not reduce-only
        "t": {"limit": {"tif": "Gtc"}}
    }],
    "grouping": "na"
}

nonce = int(time.time() * 1000)
vault_address = None

# Sign the action
print(f"\nAction to sign:")
print(json.dumps(action, indent=2))

signature = signer.sign_l1_action(action, nonce, vault_address)

print(f"\nSignature:")
print(json.dumps(signature, indent=2))

# Construct full payload
payload = {
    "action": action,
    "nonce": nonce,
    "signature": signature,
    "vaultAddress": vault_address
}

print(f"\nFull payload:")
print(json.dumps(payload, indent=2, default=str))

print("\n" + "=" * 70)
print("This is what will be sent to HyperLiquid API")
print("=" * 70)
