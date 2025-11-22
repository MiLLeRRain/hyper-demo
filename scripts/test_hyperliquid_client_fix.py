
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.trading_bot.data.hyperliquid_client import HyperliquidClient

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_client():
    client = HyperliquidClient(base_url="https://api.hyperliquid-testnet.xyz")
    
    print("Testing get_open_interest('BTC')...")
    oi = client.get_open_interest("BTC")
    print(f"Open Interest for BTC: {oi}")
    
    print("\nTesting get_funding_rate('BTC')...")
    fr = client.get_funding_rate("BTC")
    print(f"Funding Rate for BTC: {fr}")

if __name__ == "__main__":
    test_client()
