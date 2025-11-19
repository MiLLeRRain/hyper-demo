#!/usr/bin/env python3
"""
Monitor TestNet Long-Term Testing

This script provides real-time monitoring of the trading bot during long-term testing.

Features:
- Live bot status
- Agent performance metrics
- Recent decisions and trades
- Database statistics
- System health checks
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import Session

# Load environment
load_dotenv()

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_db_connection():
    """Get database connection."""
    db_user = os.getenv("DB_USER", "trading_bot")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "trading_bot_dev")

    if not db_password:
        raise ValueError("DB_PASSWORD not set in .env")

    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(db_url, echo=False)


def print_header(title):
    """Print section header."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{BOLD}  {title}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}")


def print_agents_status(session):
    """Print agents status."""
    print_header("Agent Status")

    # Get all agents
    result = session.execute(text("""
        SELECT
            name,
            status,
            llm_model,
            initial_balance,
            created_at
        FROM trading_agents
        ORDER BY created_at DESC
    """))

    agents = result.fetchall()

    if not agents:
        print(f"  {YELLOW}No agents configured{RESET}")
        return

    print(f"\n  {'Agent Name':<25} {'Status':<12} {'Model':<15} {'Balance':<12}")
    print(f"  {'-' * 70}")

    for agent in agents:
        name, status, model, balance, created = agent

        status_color = GREEN if status == 'active' else YELLOW if status == 'paused' else RED
        status_display = f"{status_color}{status.upper()}{RESET}"

        print(f"  {name:<25} {status_display:<22} {model:<15} ${balance:>10,.2f}")

    print()


def print_recent_decisions(session, limit=5):
    """Print recent decisions."""
    print_header(f"Recent Decisions (Last {limit})")

    result = session.execute(text(f"""
        SELECT
            ta.name,
            ad.timestamp,
            ad.action,
            ad.coin,
            ad.size_usd,
            ad.confidence,
            ad.status
        FROM agent_decisions ad
        JOIN trading_agents ta ON ad.agent_id = ta.id
        ORDER BY ad.timestamp DESC
        LIMIT {limit}
    """))

    decisions = result.fetchall()

    if not decisions:
        print(f"  {YELLOW}No decisions recorded yet{RESET}")
        return

    print(f"\n  {'Time':<12} {'Agent':<20} {'Action':<12} {'Coin':<6} {'Size':<10} {'Conf':<6} {'Status'}")
    print(f"  {'-' * 80}")

    for decision in decisions:
        agent, timestamp, action, coin, size, confidence, status = decision

        time_str = timestamp.strftime("%H:%M:%S") if timestamp else "N/A"

        # Color code actions
        if action == 'OPEN_LONG':
            action_display = f"{GREEN}{action}{RESET}"
        elif action == 'OPEN_SHORT':
            action_display = f"{RED}{action}{RESET}"
        elif action == 'CLOSE_POSITION':
            action_display = f"{YELLOW}{action}{RESET}"
        else:
            action_display = action

        # Color code status
        status_color = GREEN if status == 'success' else RED
        status_display = f"{status_color}{status}{RESET}"

        print(f"  {time_str:<12} {agent:<20} {action_display:<22} {coin:<6} ${size:>8,.2f} {confidence:>5.0%} {status_display}")

    print()


def print_trade_summary(session):
    """Print trade summary."""
    print_header("Trade Summary")

    result = session.execute(text("""
        SELECT
            COUNT(*) as total_trades,
            COUNT(CASE WHEN status = 'open' THEN 1 END) as open_trades,
            COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_trades,
            COALESCE(SUM(CASE WHEN status = 'closed' THEN realized_pnl ELSE 0 END), 0) as total_pnl
        FROM agent_trades
    """))

    summary = result.fetchone()

    if summary:
        total, open_trades, closed, pnl = summary

        pnl_color = GREEN if pnl >= 0 else RED
        pnl_display = f"{pnl_color}${pnl:+,.2f}{RESET}"

        print(f"\n  Total Trades:  {total}")
        print(f"  Open Trades:   {GREEN}{open_trades}{RESET}")
        print(f"  Closed Trades: {closed}")
        print(f"  Total PnL:     {pnl_display}")
    else:
        print(f"  {YELLOW}No trades recorded yet{RESET}")

    print()


def print_database_stats(session):
    """Print database statistics."""
    print_header("Database Statistics")

    # Get counts
    agents_count = session.execute(text("SELECT COUNT(*) FROM trading_agents")).scalar()
    decisions_count = session.execute(text("SELECT COUNT(*) FROM agent_decisions")).scalar()
    trades_count = session.execute(text("SELECT COUNT(*) FROM agent_trades")).scalar()
    performance_count = session.execute(text("SELECT COUNT(*) FROM agent_performance")).scalar()

    # Get oldest and newest decision
    oldest = session.execute(text("SELECT MIN(timestamp) FROM agent_decisions")).scalar()
    newest = session.execute(text("SELECT MAX(timestamp) FROM agent_decisions")).scalar()

    print(f"\n  Agents:        {agents_count}")
    print(f"  Decisions:     {decisions_count}")
    print(f"  Trades:        {trades_count}")
    print(f"  Snapshots:     {performance_count}")

    if oldest and newest:
        duration = newest - oldest
        print(f"\n  Testing since: {oldest.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Last activity: {newest.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Duration:      {duration}")

    print()


def monitor_loop(refresh_seconds=10):
    """Main monitoring loop."""
    engine = get_db_connection()

    print(f"\n{BOLD}Starting TestNet Monitor...{RESET}")
    print(f"Refresh interval: {refresh_seconds} seconds")
    print(f"Press Ctrl+C to exit\n")

    try:
        while True:
            clear_screen()

            print(f"{BOLD}{'=' * 70}{RESET}")
            print(f"{BOLD}  HyperLiquid TestNet - Live Monitor{RESET}")
            print(f"{BOLD}  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
            print(f"{BOLD}{'=' * 70}{RESET}")

            with Session(engine) as session:
                print_agents_status(session)
                print_recent_decisions(session, limit=5)
                print_trade_summary(session)
                print_database_stats(session)

            print(f"\n{BLUE}Refreshing in {refresh_seconds} seconds... (Ctrl+C to exit){RESET}")

            time.sleep(refresh_seconds)

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Monitoring stopped{RESET}\n")
        return 0


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor TestNet long-term testing")
    parser.add_argument(
        '--refresh',
        type=int,
        default=10,
        help='Refresh interval in seconds (default: 10)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Show status once and exit (no loop)'
    )

    args = parser.parse_args()

    try:
        engine = get_db_connection()

        if args.once:
            # Show status once
            print(f"{BOLD}{'=' * 70}{RESET}")
            print(f"{BOLD}  HyperLiquid TestNet - Status Snapshot{RESET}")
            print(f"{BOLD}  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
            print(f"{BOLD}{'=' * 70}{RESET}")

            with Session(engine) as session:
                print_agents_status(session)
                print_recent_decisions(session, limit=10)
                print_trade_summary(session)
                print_database_stats(session)

            return 0
        else:
            # Continuous monitoring
            return monitor_loop(args.refresh)

    except ValueError as e:
        print(f"\n{RED}[ERROR] Configuration error: {e}{RESET}")
        print(f"\nPlease check your .env file and ensure DB_PASSWORD is set.\n")
        return 1
    except Exception as e:
        print(f"\n{RED}[ERROR] {e}{RESET}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
