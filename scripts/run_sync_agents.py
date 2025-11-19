#!/usr/bin/env python3
"""
Run sync_agents_from_config.py with correct DB environment variables.
This script sets up the database connection and calls the sync script.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the sync agents script with proper environment variables."""

    # Set database environment variables for Docker PostgreSQL
    env = os.environ.copy()
    env.update({
        'DB_USER': 'trading_bot',
        'DB_PASSWORD': 'trading_bot_2025',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_NAME': 'trading_bot_dev'
    })

    print("=" * 40)
    print("Sync Agents from config.yaml")
    print("=" * 40)
    print(f"Database: {env['DB_NAME']}")
    print(f"Host: {env['DB_HOST']}:{env['DB_PORT']}")
    print(f"User: {env['DB_USER']}")
    print("=" * 40)
    print()

    # Get the project root directory
    project_root = Path(__file__).parent.parent
    sync_script = project_root / "scripts" / "sync_agents_from_config.py"

    # Run the sync script with all command line arguments passed through
    try:
        result = subprocess.run(
            [sys.executable, str(sync_script)] + sys.argv[1:],
            env=env,
            check=False
        )
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
