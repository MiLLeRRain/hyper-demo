"""Status command for trading bot."""

import click
import json
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


@click.command('status')
@click.option(
    '--json-output', '-j',
    is_flag=True,
    help='Output as JSON'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Show detailed information'
)
def status_cmd(json_output: bool, verbose: bool):
    """
    Show trading bot status.

    Displays current status, uptime, cycle count, and agent information.
    """
    try:
        # Get status
        status = _get_service_status()

        if json_output:
            click.echo(json.dumps(status, indent=2, default=str))
        else:
            _print_status(status, verbose)

    except Exception as e:
        click.echo(f"❌ Error getting status: {e}", err=True)
        sys.exit(1)


def _get_service_status() -> dict:
    """Get service status from database."""
    # Import here to avoid circular imports
    from trading_bot.config.models import load_config
    from trading_bot.automation.state_manager import StateManager
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    try:
        # Load environment variables
        load_dotenv()

        # Load config
        cfg = load_config('config.yaml')

        # Connect to database
        engine = create_engine(cfg.database.url)
        Session = sessionmaker(bind=engine)
        db = Session()

        # Get state
        state_manager = StateManager(db)
        state = state_manager.load_state()

        # Check if running
        running = _is_service_running()

        status = {
            "running": running,
            "uptime_seconds": None,
            "cycle_count": 0,
            "last_cycle_time": None,
            "last_error": None
        }

        if state:
            status.update({
                "cycle_count": state.get("cycle_count", 0),
                "last_cycle_time": state.get("last_cycle_time"),
                "last_error": state.get("last_error"),
                "service_start_time": state.get("service_start_time")
            })

            # Calculate uptime
            if state.get("service_start_time"):
                start_time = state["service_start_time"]
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                uptime = (datetime.utcnow() - start_time).total_seconds()
                status["uptime_seconds"] = uptime

        db.close()
        engine.dispose()

        return status

    except Exception as e:
        return {
            "running": _is_service_running(),
            "error": str(e)
        }


def _print_status(status: dict, verbose: bool) -> None:
    """Print status in human-readable format."""
    click.echo("=" * 60)
    click.echo("📊 HyperLiquid AI Trading Bot Status")
    click.echo("=" * 60)

    # Running status
    running = status.get("running", False)
    status_icon = "🟢" if running else "🔴"
    status_text = "Running" if running else "Stopped"
    click.echo(f"{status_icon} Status: {status_text}")

    if status.get("error"):
        click.echo(f"⚠️  Error: {status['error']}")
        return

    # Uptime
    uptime = status.get("uptime_seconds")
    if uptime:
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        click.echo(f"⏱️  Uptime: {hours}h {minutes}m")

    # Cycle info
    cycle_count = status.get("cycle_count", 0)
    click.echo(f"🔄 Cycles executed: {cycle_count}")

    last_cycle = status.get("last_cycle_time")
    if last_cycle:
        if isinstance(last_cycle, str):
            last_cycle = datetime.fromisoformat(last_cycle)
        time_ago = (datetime.utcnow() - last_cycle).total_seconds()
        minutes_ago = int(time_ago // 60)
        click.echo(f"🕐 Last cycle: {minutes_ago} minutes ago")

    # Last error
    last_error = status.get("last_error")
    if last_error:
        click.echo(f"⚠️  Last error: {last_error}")

    if verbose:
        click.echo("\n" + "─" * 60)
        click.echo("Detailed Information:")
        click.echo(f"Service start time: {status.get('service_start_time', 'N/A')}")
        click.echo(f"Last cycle time: {status.get('last_cycle_time', 'N/A')}")

    click.echo("=" * 60)


def _is_service_running() -> bool:
    """Check if service is running."""
    lock_file = Path("/tmp/tradingbot.lock")
    return lock_file.exists()


if __name__ == '__main__':
    status_cmd()
