#!/usr/bin/env python3
"""Quick system check - minimal dependencies."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

print("=" * 70)
print("  Quick System Check")
print("=" * 70)
print()

# Check 1: Private Key
print("1. HyperLiquid Private Key")
private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
if private_key:
    print(f"   [OK] Set ({len(private_key)} chars)")

    # Derive wallet address
    try:
        from eth_account import Account

        # Normalize
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        if len(private_key) < 66:
            private_key = "0x" + private_key[2:].zfill(64)

        account = Account.from_key(private_key)
        print(f"   [OK] Wallet: {account.address}")
    except Exception as e:
        print(f"   [ERROR] Invalid private key: {e}")
else:
    print("   [ERROR] Not set in .env")

print()

# Check 2: LLM API
print("2. LLM API Key")
has_deepseek = bool(os.getenv("DEEPSEEK_API_KEY"))
has_openai = bool(os.getenv("OPENAI_API_KEY"))

if has_deepseek:
    key = os.getenv("DEEPSEEK_API_KEY")
    print(f"   [OK] DeepSeek API: {key[:8]}...")
elif has_openai:
    key = os.getenv("OPENAI_API_KEY")
    print(f"   [OK] OpenAI API: {key[:8]}...")
else:
    print("   [ERROR] No LLM API key found")
    print("          Need DEEPSEEK_API_KEY or OPENAI_API_KEY")

print()

# Check 3: HyperLiquid API
print("3. HyperLiquid API (Testnet)")
try:
    import requests

    response = requests.post(
        "https://api.hyperliquid-testnet.xyz/info",
        json={"type": "allMids"},
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        if "BTC" in data:
            print(f"   [OK] Connected - BTC: ${float(data['BTC']):,.2f}")
        else:
            print("   [OK] Connected")
    else:
        print(f"   [ERROR] HTTP {response.status_code}")

except Exception as e:
    print(f"   [ERROR] {e}")

print()

# Check 4: Database (Optional)
print("4. Database (Optional)")
db_password = os.getenv("DB_PASSWORD")
if db_password:
    try:
        from sqlalchemy import create_engine, text

        db_user = os.getenv("DB_USER", "trading_bot")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "trading_bot")

        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(db_url, echo=False)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   [OK] Connected to PostgreSQL")
    except Exception as e:
        print(f"   [WARNING] Not connected: {e}")
        print("   [INFO] Run: scripts/setup_database.bat")
else:
    print("   [INFO] Not configured (DB_PASSWORD not set)")
    print("   [INFO] Database is optional for testing")

print()
print("=" * 70)

# Summary
issues = []
if not os.getenv("HYPERLIQUID_PRIVATE_KEY"):
    issues.append("HYPERLIQUID_PRIVATE_KEY not set")
if not has_deepseek and not has_openai:
    issues.append("No LLM API key")

if issues:
    print("  [WARNING] Issues found:")
    for issue in issues:
        print(f"    - {issue}")
    print()
    print("  Fix these issues in .env file")
else:
    print("  [OK] Ready for testing!")
    print()
    print("  Next steps:")
    print("    python tests/testnet/test_llm_integration.py")

print("=" * 70)
