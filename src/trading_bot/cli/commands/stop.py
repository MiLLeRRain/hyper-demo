"""Stop command for trading bot."""

import click
import signal
import os
from pathlib import Path


@click.command('stop')
@click.option(
    '--force', '-f',
    is_flag=True,
    help='Force stop (immediate shutdown)'
)
def stop_cmd(force: bool):
    """
    Stop the trading bot service.

    By default, waits for the current cycle to complete (graceful shutdown).
    Use --force to stop immediately.
    """
    try:
        click.echo("🛑 Stopping trading bot...")

        # Check if service is running
        if not _is_service_running():
            click.echo("❌ Error: Service is not running")
            return

        # Get PID
        pid = _get_service_pid()

        if not pid:
            click.echo("❌ Error: Could not find service process")
            return

        if force:
            click.echo("⚡ Force stopping (immediate)...")
            os.kill(pid, signal.SIGKILL)
            _remove_lock_file()
            click.echo("✅ Service killed")
        else:
            click.echo("⏳ Graceful shutdown (waiting for current cycle to complete)...")
            os.kill(pid, signal.SIGTERM)
            _remove_lock_file()
            click.echo("✅ Shutdown signal sent")
            click.echo("   Service will stop after current cycle completes")

    except ProcessLookupError:
        click.echo("❌ Error: Process not found")
        _remove_lock_file()
    except PermissionError:
        click.echo("❌ Error: Permission denied. Try with sudo.")
    except Exception as e:
        click.echo(f"❌ Error stopping service: {e}", err=True)


def _is_service_running() -> bool:
    """Check if service is running."""
    lock_file = Path("/tmp/tradingbot.lock")
    return lock_file.exists()


def _get_service_pid() -> int:
    """Get service PID from lock file."""
    try:
        lock_file = Path("/tmp/tradingbot.lock")
        if lock_file.exists():
            pid = int(lock_file.read_text().strip())
            return pid
    except Exception:
        pass
    return 0


def _remove_lock_file() -> None:
    """Remove lock file."""
    try:
        lock_file = Path("/tmp/tradingbot.lock")
        if lock_file.exists():
            lock_file.unlink()
    except Exception:
        pass


if __name__ == '__main__':
    stop_cmd()
