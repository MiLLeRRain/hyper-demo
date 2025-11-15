#!/usr/bin/env python3
"""Check if the trading bot is ready for long-term running.

This script verifies:
1. Database connectivity
2. HyperLiquid API access (Testnet)
3. LLM API access (DeepSeek/OpenAI)
4. Wallet balance
5. Configuration validity
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import requests

# Colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(title):
    """Print section header."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{BOLD}  {title}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_success(message):
    """Print success message."""
    print(f"  {GREEN}[OK]{RESET} {message}")


def print_warning(message):
    """Print warning message."""
    print(f"  {YELLOW}[WARNING]{RESET} {message}")


def print_error(message):
    """Print error message."""
    print(f"  {RED}[ERROR]{RESET} {message}")


def print_info(message):
    """Print info message."""
    print(f"  {BLUE}[INFO]{RESET} {message}")


def check_env_file():
    """Check if .env file exists and has required variables."""
    print_header("Step 1: Environment Configuration")

    env_file = Path(__file__).parent.parent / ".env"

    if not env_file.exists():
        print_error(".env file not found!")
        print_info("Please create .env file from .env.example")
        return False

    print_success(".env file exists")

    # Load environment
    load_dotenv()

    # Check required variables
    required_vars = {
        "HYPERLIQUID_PRIVATE_KEY": "HyperLiquid wallet private key",
        "DEEPSEEK_API_KEY": "DeepSeek API key (or OPENAI_API_KEY)"
    }

    optional_vars = {
        "DB_USER": "Database username (default: trading_bot)",
        "DB_PASSWORD": "Database password (required for DB)",
        "DB_HOST": "Database host (default: localhost)",
        "DB_PORT": "Database port (default: 5432)",
        "DB_NAME": "Database name (default: trading_bot)"
    }

    all_ok = True

    for var, desc in required_vars.items():
        value = os.getenv(var)
        if not value:
            print_error(f"{var} not set - {desc}")
            all_ok = False
        else:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print_success(f"{var} = {masked}")

    # Check if at least one LLM API key is set
    has_deepseek = bool(os.getenv("DEEPSEEK_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    if not has_deepseek and not has_openai:
        print_error("No LLM API key found (need DEEPSEEK_API_KEY or OPENAI_API_KEY)")
        all_ok = False

    print()
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if not value:
            print_warning(f"{var} not set - {desc}")
        else:
            if "PASSWORD" in var:
                masked = "***"
            else:
                masked = value
            print_success(f"{var} = {masked}")

    return all_ok


def check_database():
    """Check database connectivity."""
    print_header("Step 2: Database Connection")

    db_user = os.getenv("DB_USER", "trading_bot")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "trading_bot")

    if not db_password:
        print_warning("DB_PASSWORD not set - database features disabled")
        print_info("To enable database:")
        print_info("  1. Run: scripts/setup_database.bat (Windows)")
        print_info("  2. Or:  scripts/setup_database.sh (Linux/Mac)")
        print_info("  3. Set DB_PASSWORD in .env")
        return None  # Not a failure, just optional

    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    try:
        print_info(f"Connecting to: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")

        engine = create_engine(db_url, echo=False)

        with engine.connect() as conn:
            # Check version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            version_short = version.split(",")[0] if version else "Unknown"
            print_success(f"Connected to {version_short}")

            # Check tables
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('trading_agents', 'agent_decisions', 'agent_trades', 'agent_performance', 'bot_state')
            """))
            table_count = result.scalar()

            if table_count >= 5:
                print_success(f"Found {table_count} tables - database ready!")
                return True
            elif table_count > 0:
                print_warning(f"Found {table_count} tables - may need migrations")
                print_info("Run: alembic upgrade head")
                return True
            else:
                print_warning("No tables found - need to run migrations")
                print_info("Run: alembic upgrade head")
                return False

    except Exception as e:
        print_error(f"Database connection failed: {e}")
        print_info("To set up database:")
        print_info("  1. Run: scripts/setup_database.bat (Windows)")
        print_info("  2. Or:  scripts/setup_database.sh (Linux/Mac)")
        return False


def check_hyperliquid_api():
    """Check HyperLiquid API connectivity."""
    print_header("Step 3: HyperLiquid API (Testnet)")

    testnet_url = "https://api.hyperliquid-testnet.xyz/info"

    try:
        # Test Info API
        print_info("Testing Info API...")
        response = requests.post(
            testnet_url,
            json={"type": "allMids"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if "BTC" in data:
                btc_price = float(data["BTC"])
                print_success(f"Info API connected - BTC price: ${btc_price:,.2f}")
            else:
                print_success("Info API connected")
        else:
            print_error(f"Info API returned status {response.status_code}")
            return False

        # Test wallet balance
        private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
        if private_key:
            print_info("Checking wallet balance...")

            from trading_bot.trading.hyperliquid_signer import HyperliquidSigner
            from trading_bot.data.hyperliquid_client import HyperliquidClient

            signer = HyperliquidSigner(private_key)
            wallet = signer.get_address()

            client = HyperliquidClient(base_url=testnet_url)

            # Get account state
            account_response = requests.post(
                testnet_url,
                json={
                    "type": "clearinghouseState",
                    "user": wallet
                },
                timeout=10
            )

            if account_response.status_code == 200:
                account_data = account_response.json()
                if account_data and "marginSummary" in account_data:
                    balance = float(account_data["marginSummary"]["accountValue"])
                    print_success(f"Wallet: {wallet}")
                    print_success(f"Balance: ${balance:,.2f} USDC")

                    if balance < 10:
                        print_warning("Low balance! Visit https://app.hyperliquid-testnet.xyz/ to get faucet")
                else:
                    print_warning("Wallet not activated or has no balance")
                    print_info("Visit: https://app.hyperliquid-testnet.xyz/")
                    print_info("1. Connect wallet")
                    print_info("2. Get testnet faucet")
            else:
                print_warning("Could not fetch wallet balance")

        return True

    except Exception as e:
        print_error(f"HyperLiquid API check failed: {e}")
        return False


def check_llm_api():
    """Check LLM API connectivity."""
    print_header("Step 4: LLM API")

    has_deepseek = bool(os.getenv("DEEPSEEK_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    if not has_deepseek and not has_openai:
        print_error("No LLM API key configured")
        return False

    success = False

    # Test DeepSeek
    if has_deepseek:
        print_info("Testing DeepSeek API...")
        try:
            from trading_bot.ai.providers import OfficialAPIProvider

            provider = OfficialAPIProvider(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com/v1",
                model_name="deepseek-chat"
            )

            response = provider.generate(
                prompt="Say 'OK' if you can read this.",
                max_tokens=10,
                temperature=0.1
            )

            if response and len(response) > 0:
                print_success("DeepSeek API connected")
                success = True
            else:
                print_error("DeepSeek API returned empty response")
        except Exception as e:
            print_error(f"DeepSeek API check failed: {e}")

    # Test OpenAI
    if has_openai:
        print_info("Testing OpenAI API...")
        try:
            from trading_bot.ai.providers import OfficialAPIProvider

            provider = OfficialAPIProvider(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url="https://api.openai.com/v1",
                model_name="gpt-3.5-turbo"
            )

            response = provider.generate(
                prompt="Say 'OK' if you can read this.",
                max_tokens=10,
                temperature=0.1
            )

            if response and len(response) > 0:
                print_success("OpenAI API connected")
                success = True
            else:
                print_error("OpenAI API returned empty response")
        except Exception as e:
            print_error(f"OpenAI API check failed: {e}")

    return success


def check_config_file():
    """Check config.yaml exists and is valid."""
    print_header("Step 5: Configuration File")

    config_file = Path(__file__).parent.parent / "config.yaml"

    if not config_file.exists():
        print_error("config.yaml not found!")
        return False

    print_success("config.yaml exists")

    try:
        import yaml

        with open(config_file) as f:
            config = yaml.safe_load(f)

        # Check key sections
        required_sections = ["hyperliquid", "trading", "agents"]

        for section in required_sections:
            if section in config:
                print_success(f"Section '{section}' found")
            else:
                print_error(f"Section '{section}' missing")
                return False

        # Check if at least one agent is configured
        if config.get("agents"):
            agent_count = len(config["agents"])
            enabled_count = sum(1 for a in config["agents"] if a.get("enabled", True))
            print_success(f"Agents configured: {agent_count} (enabled: {enabled_count})")
        else:
            print_warning("No agents configured")

        return True

    except Exception as e:
        print_error(f"Config file validation failed: {e}")
        return False


def main():
    """Run all checks."""
    print(f"\n{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}  HyperLiquid Trading Bot - Readiness Check{RESET}")
    print(f"{BOLD}{'=' * 70}{RESET}")

    results = {
        "Environment": check_env_file(),
        "Database": check_database(),
        "HyperLiquid API": check_hyperliquid_api(),
        "LLM API": check_llm_api(),
        "Configuration": check_config_file()
    }

    # Summary
    print_header("Summary")

    for component, status in results.items():
        if status is True:
            print_success(f"{component}: Ready")
        elif status is False:
            print_error(f"{component}: Not Ready")
        elif status is None:
            print_warning(f"{component}: Optional (not configured)")

    print()

    # Overall readiness
    required_checks = [
        results["Environment"],
        results["HyperLiquid API"],
        results["LLM API"],
        results["Configuration"]
    ]

    all_ready = all(check is True for check in required_checks)
    db_ready = results["Database"] in [True, None]  # DB is optional

    if all_ready and db_ready:
        print(f"{GREEN}{BOLD}{'=' * 70}{RESET}")
        print(f"{GREEN}{BOLD}  [OK] System is ready for long-term running!{RESET}")
        print(f"{GREEN}{BOLD}{'=' * 70}{RESET}")
        print()
        print("Next steps:")
        print("  1. Start the bot: python tradingbot.py start")
        print("  2. Monitor logs:  python tradingbot.py logs -f")
        print("  3. Check status:  python tradingbot.py status")
        print()

        if results["Database"] is None:
            print(f"{YELLOW}Note: Database is not configured.{RESET}")
            print("Without database, you will lose:")
            print("  - Historical decision records")
            print("  - State recovery after restart")
            print("  - Performance analytics")
            print()
            print("To enable database:")
            print("  1. Run: scripts/setup_database.bat")
            print("  2. Set DB_PASSWORD in .env")
            print()

        return 0
    else:
        print(f"{RED}{BOLD}{'=' * 70}{RESET}")
        print(f"{RED}{BOLD}  [ERROR] System is NOT ready{RESET}")
        print(f"{RED}{BOLD}{'=' * 70}{RESET}")
        print()
        print("Please fix the issues above before starting the bot.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
