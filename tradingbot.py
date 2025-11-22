#!/usr/bin/env python3
"""
Trading bot CLI entry point.

Usage:
    python tradingbot.py start
    $env:PYTHONIOENCODING="utf-8"; python tradingbot.py start > bot.log 2>&1
    python tradingbot.py stop
    python tradingbot.py status
    python tradingbot.py agent list
    python tradingbot.py logs -f
Logs:
    Get-Content bot.log -Wait -Tail 50
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from trading_bot.cli.main import cli

if __name__ == '__main__':
    cli()
