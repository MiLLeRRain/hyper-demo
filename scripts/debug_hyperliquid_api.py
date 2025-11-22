
import requests
import json

url = "https://api.hyperliquid-testnet.xyz/info"
payload = {"type": "metaAndAssetCtxs"}

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    
    print(f"Type of data: {type(data)}")
    if isinstance(data, list):
        print(f"Length of data: {len(data)}")
        if len(data) > 0:
            print(f"Type of data[0] (universe): {type(data[0])}")
            print(f"Sample data[0]: {str(data[0])[:500]}") # Print first 500 chars
            if isinstance(data[0], list) and len(data[0]) > 0:
                print(f"Type of data[0][0]: {type(data[0][0])}")
                print(f"Sample data[0][0]: {data[0][0]}")
        
        if len(data) > 1:
            print(f"Type of data[1] (assetCtxs): {type(data[1])}")
            if isinstance(data[1], list) and len(data[1]) > 0:
                print(f"Type of data[1][0]: {type(data[1][0])}")
                print(f"Sample data[1][0]: {data[1][0]}")

except Exception as e:
    print(f"Error: {e}")
