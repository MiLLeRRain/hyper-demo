#!/usr/bin/env python3
"""
Trading bot CLI entry point.

Usage:
    python tradingbot.py start
    python tradingbot.py stop
    python tradingbot.py status
    python tradingbot.py agent list
    python tradingbot.py logs -f
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from trading_bot.cli.main import cli

if __name__ == '__main__':
    cli()
