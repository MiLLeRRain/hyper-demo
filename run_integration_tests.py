#!/usr/bin/env python3
"""Run integration tests for the trading bot.

This script runs integration tests in dry-run mode, which:
- Fetches REAL market data from HyperLiquid
- Simulates trade execution (no real orders)
- Tests all components in a safe environment

Usage:
    # Run all tests
    python run_integration_tests.py

    # Run specific test file
    python run_integration_tests.py --file test_data_collection

    # Run with verbose output
    python run_integration_tests.py --verbose

    # Run only fast tests (skip slow tests)
    python run_integration_tests.py --fast
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def main():
    parser = argparse.ArgumentParser(
        description="Run integration tests for trading bot"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Specific test file to run (without .py extension)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    parser.add_argument(
        "--markers",
        "-m",
        type=str,
        help="Run tests matching given mark expression (e.g., 'not slow')"
    )

    args = parser.parse_args()

    # Build pytest command
    cmd = ["pytest", "tests/integration/"]

    # Add specific file if provided
    if args.file:
        test_file = f"tests/integration/{args.file}"
        if not test_file.endswith(".py"):
            test_file += ".py"
        cmd = ["pytest", test_file]

    # Add markers
    if args.fast:
        cmd.extend(["-m", "not slow"])
    elif args.markers:
        cmd.extend(["-m", args.markers])

    # Add verbose flag
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-v")  # Always use verbose for better output

    # Add other pytest options
    cmd.extend([
        "--tb=short",  # Shorter traceback format
        "--color=yes",  # Colored output
        "-s",  # Don't capture output (show print statements)
        "--no-cov",  # Disable coverage for integration tests
    ])

    print("=" * 80)
    print("Running Integration Tests (Dry-Run Mode)")
    print("=" * 80)
    print(f"\nCommand: {' '.join(cmd)}\n")
    print("Test Configuration:")
    print("   [+] Mode: DRY-RUN (Safe - No real trades)")
    print("   [+] Market Data: REAL (from HyperLiquid API)")
    print("   [+] Trade Execution: SIMULATED")
    print("   [+] Risk Level: ZERO\n")
    print("=" * 80)

    # Set PYTHONPATH for subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path)

    # Run pytest
    result = subprocess.run(cmd, env=env)

    # Print summary
    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("[SUCCESS] All tests passed!")
    else:
        print("[FAILED] Some tests failed. Please review the output above.")
    print("=" * 80)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
