#!/usr/bin/env python3
"""
Sync trading agents from config.yaml to database

Reads agent configurations from config.yaml and syncs them to the database.
This replaces hardcoded SQL initialization with dynamic config-based setup.

Usage:
    python scripts/sync_agents_from_config.py           # Add new agents
    python scripts/sync_agents_from_config.py --reset   # Reset all agents
    python scripts/sync_agents_from_config.py --update  # Update existing agents
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
import argparse
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from trading_bot.models.database import TradingAgent


def load_config(config_path: str = "config.yaml") -> dict:
    """Load config.yaml"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_db_url() -> str:
    """Get database URL from environment"""
    user = os.getenv('DB_USER', 'trading_bot')
    password = os.getenv('DB_PASSWORD', 'trading_bot_2025')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    name = os.getenv('DB_NAME', 'trading_bot_dev')
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def sync_agents(reset: bool = False, update: bool = False, db_url: str = None):
    """Sync agents from config.yaml to database"""

    # Load config
    print("[*] Loading config.yaml...")
    config = load_config()
    agents_config = config.get('agents', [])
    trading_config = config.get('trading', {})

    if not agents_config:
        print("[!] No agents found in config.yaml")
        return

    print(f"[+] Found {len(agents_config)} agents in config")

    # Connect to database
    if db_url is None:
        db_url = get_db_url()
    engine = create_engine(db_url, echo=False)

    with Session(engine) as session:
        # Reset if requested
        if reset:
            print("\n[!] Resetting: Deleting all existing agents...")
            session.execute(text("DELETE FROM trading_agents"))
            session.commit()
            print("[+] All agents deleted\n")

        # Sync each agent
        added = 0
        updated = 0
        skipped = 0

        for agent_cfg in agents_config:
            name = agent_cfg['name']
            enabled = agent_cfg.get('enabled', True)

            # Check if exists
            existing = session.query(TradingAgent).filter_by(name=name).first()

            if existing:
                if update:
                    # Update existing agent
                    existing.llm_model = agent_cfg['model']
                    existing.strategy_description = agent_cfg.get('strategy_description')
                    existing.status = 'active' if enabled else 'paused'
                    existing.max_leverage = trading_config.get('max_leverage', 5)
                    existing.stop_loss_pct = Decimal(str(trading_config.get('stop_loss_percentage', 5.0)))
                    existing.take_profit_pct = Decimal(str(trading_config.get('take_profit_percentage', 10.0)))
                    print(f"[U] Updated: {name} ({existing.status})")
                    updated += 1
                else:
                    print(f"[-] Skipped: {name} (already exists, use --update to modify)")
                    skipped += 1
                continue

            # Create new agent
            agent = TradingAgent(
                name=name,
                llm_model=agent_cfg['model'],
                exchange_account='testnet_account',
                initial_balance=Decimal("10000.00"),
                max_position_size=Decimal(str(trading_config.get('max_position_per_agent', 0.5) * 100)),
                max_leverage=trading_config.get('max_leverage', 5),
                stop_loss_pct=Decimal(str(trading_config.get('stop_loss_percentage', 5.0))),
                take_profit_pct=Decimal(str(trading_config.get('take_profit_percentage', 10.0))),
                strategy_description=agent_cfg.get('strategy_description'),
                status='active' if enabled else 'paused'
            )
            session.add(agent)
            status = "[ON]" if enabled else "[OFF]"
            print(f"[+] Added: {name} - {status}")
            added += 1

        # Commit
        session.commit()

        # Summary
        print(f"\n{'='*60}")
        print(f"[SUCCESS] Sync Complete!")
        print(f"{'='*60}")
        print(f"Added:   {added}")
        if updated > 0:
            print(f"Updated: {updated}")
        if skipped > 0:
            print(f"Skipped: {skipped}")
        print(f"{'='*60}\n")

        # Show all agents
        all_agents = session.query(TradingAgent).all()
        print(f"Current agents in database: {len(all_agents)}")
        for agent in all_agents:
            icon = "[ON]" if agent.status == 'active' else "[OFF]"
            print(f"  {icon} {agent.name:20s} ({agent.llm_model:15s}) {agent.status}")


def main():
    parser = argparse.ArgumentParser(
        description="Sync trading agents from config.yaml to database"
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Delete all existing agents before syncing'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update existing agents with new config values'
    )
    parser.add_argument(
        '--db-url',
        help='Database URL (default: from environment)'
    )

    args = parser.parse_args()

    try:
        sync_agents(reset=args.reset, update=args.update, db_url=args.db_url)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
