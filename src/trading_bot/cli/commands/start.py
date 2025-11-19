"""Start command for trading bot."""

import click
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from trading_bot.config.models import Config, load_config
from trading_bot.automation.trading_bot_service import TradingBotService
import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


@click.command('start')
@click.option(
    '--config', '-c',
    default='config.yaml',
    type=click.Path(exists=True),
    help='Path to configuration file'
)
@click.option(
    '--daemon', '-d',
    is_flag=True,
    help='Run as background daemon (not implemented yet)'
)
def start_cmd(config: str, daemon: bool):
    """
    Start the trading bot service.

    This will initialize all components and start the 3-minute trading cycle.
    The service will run until stopped with 'tradingbot stop' or Ctrl+C.
    """
    try:
        # Load environment variables
        load_dotenv()

        click.echo("=" * 60)
        click.echo("🚀 Starting HyperLiquid AI Trading Bot")
        click.echo("=" * 60)

        # Load configuration
        click.echo(f"📋 Loading configuration from: {config}")
        
        cfg = load_config(config)
        click.echo("✅ Configuration loaded")

        # Check if already running (simple check)
        if _is_service_running():
            click.echo("❌ Error: Service is already running")
            click.echo("   Use 'tradingbot stop' to stop it first")
            return

        if daemon:
            click.echo("⚠️  Daemon mode not implemented yet, running in foreground")

        # Create and start service
        click.echo("\n🔧 Initializing service...")
        service = TradingBotService(cfg)

        click.echo("▶️  Starting service (Press Ctrl+C to stop)...\n")

        # Start service (blocking)
        success = service.start()

        if success:
            click.echo("\n" + "=" * 60)
            click.echo("✅ Trading bot stopped successfully")
            click.echo("=" * 60)
        else:
            click.echo("\n" + "=" * 60)
            click.echo("❌ Trading bot failed to start")
            click.echo("=" * 60)
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Received interrupt signal")
        click.echo("🛑 Shutting down gracefully...")
    except Exception as e:
        click.echo(f"\n❌ Error starting trading bot: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _is_service_running() -> bool:
    """Check if service is already running (simple implementation)."""
    # TODO: Implement proper PID file checking
    # For now, just check for lock file
    lock_file = Path("/tmp/tradingbot.lock")
    return lock_file.exists()


if __name__ == '__main__':
    start_cmd()
