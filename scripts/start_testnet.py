#!/usr/bin/env python3
"""
Start TestNet Long-Term Testing

This script prepares and starts the trading bot for long-term testing on HyperLiquid TestNet.

Steps:
1. Verify environment configuration
2. Check database connection
3. Sync agents from config.yaml
4. Run connection tests
5. Start the trading bot
"""

import os
import sys
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def print_header(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_step(step, description):
    """Print step info."""
    print(f"[Step {step}] {description}")
    print("-" * 70)


def run_command(cmd, description, check=True):
    """Run a command and return the result."""
    print(f"\n[*] {description}...")
    print(f"    Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}\n")

    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error: Command failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n[!] Error: {e}")
        return False


def main():
    """Main function."""
    project_root = Path(__file__).parent.parent

    print_header("HyperLiquid TestNet - Long-Term Testing Setup")

    # Step 1: Verify configuration
    print_step(1, "Verify Environment Configuration")
    if not run_command(
        [sys.executable, "scripts/check_readiness.py"],
        "Running readiness check",
        check=False
    ):
        print("\n[!] Readiness check failed. Please fix the issues above.")
        response = input("\nDo you want to continue anyway? (yes/no): ").strip().lower()
        if response != 'yes':
            print("\n[*] Setup cancelled.")
            return 1

    print("\n[+] Configuration verified!")

    # Step 2: Sync agents to database
    print_step(2, "Sync Agents from config.yaml to Database")
    print("\n[?] Do you want to reset all agents in the database?")
    print("    - 'yes': Clear all existing agents and add fresh from config.yaml")
    print("    - 'no':  Only add new agents (keep existing)")

    reset = input("\nReset agents? (yes/no): ").strip().lower()

    if reset == 'yes':
        cmd = [sys.executable, "scripts/run_sync_agents.py", "--reset"]
    else:
        cmd = [sys.executable, "scripts/run_sync_agents.py"]

    if not run_command(cmd, "Syncing agents to database"):
        print("\n[!] Failed to sync agents.")
        return 1

    print("\n[+] Agents synced successfully!")

    # Step 3: Run connection test
    print_step(3, "Test TestNet Connection")

    if not run_command(
        [sys.executable, "tests/testnet/test_testnet_connection.py"],
        "Testing HyperLiquid TestNet connection",
        check=False
    ):
        print("\n[!] Connection test failed.")
        response = input("\nDo you want to continue anyway? (yes/no): ").strip().lower()
        if response != 'yes':
            print("\n[*] Setup cancelled.")
            return 1

    print("\n[+] Connection test passed!")

    # Step 4: Run trading test
    print_step(4, "Test Trading Functionality")

    response = input("\nDo you want to run the trading test? (yes/no): ").strip().lower()

    if response == 'yes':
        if not run_command(
            [sys.executable, "tests/testnet/test_testnet_trading.py"],
            "Testing trading functionality",
            check=False
        ):
            print("\n[!] Trading test failed.")
            response = input("\nDo you want to continue anyway? (yes/no): ").strip().lower()
            if response != 'yes':
                print("\n[*] Setup cancelled.")
                return 1

        print("\n[+] Trading test passed!")
    else:
        print("\n[*] Skipping trading test.")

    # Step 5: Show next steps
    print_header("Setup Complete - Ready to Start Long-Term Testing!")

    print("Your TestNet environment is ready!")
    print()
    print("Next steps:")
    print()
    print("1. Start the trading bot:")
    print("   python tradingbot.py start")
    print()
    print("2. Monitor the bot in real-time:")
    print("   python tradingbot.py logs -f")
    print()
    print("3. Check bot status:")
    print("   python tradingbot.py status")
    print()
    print("4. View agent performance:")
    print("   python tradingbot.py agent list")
    print()
    print("5. Stop the bot when needed:")
    print("   python tradingbot.py stop")
    print()
    print("-" * 70)
    print()
    print("Important Notes:")
    print("  - This is TESTNET - no real money at risk")
    print("  - All trades will be recorded in the database")
    print("  - Logs will be saved to trading_bot.log")
    print("  - You can check your wallet at:")
    print("    https://app.hyperliquid-testnet.xyz/")
    print()
    print("=" * 70)
    print()

    # Ask if user wants to start now
    response = input("Do you want to start the bot now? (yes/no): ").strip().lower()

    if response == 'yes':
        print("\n[*] Starting the trading bot...")
        print()

        # Start the bot
        try:
            result = subprocess.run(
                [sys.executable, "tradingbot.py", "start"],
                check=False
            )
            return result.returncode
        except KeyboardInterrupt:
            print("\n\n[!] Interrupted by user")
            return 130
    else:
        print("\n[*] Setup complete. Start the bot when you're ready:")
        print("    python tradingbot.py start")
        print()
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
