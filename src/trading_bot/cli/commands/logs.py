"""Logs command for viewing trading bot logs."""

import click
import time
from pathlib import Path


@click.command('logs')
@click.option(
    '--tail', '-n',
    type=int,
    default=50,
    help='Number of lines to show (default: 50)'
)
@click.option(
    '--follow', '-f',
    is_flag=True,
    help='Follow log output (like tail -f)'
)
@click.option(
    '--level', '-l',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
    default='INFO',
    help='Minimum log level to display'
)
@click.option(
    '--error-only', '-e',
    is_flag=True,
    help='Show only errors (shortcut for --level ERROR)'
)
def logs_cmd(tail: int, follow: bool, level: str, error_only: bool):
    """
    View trading bot logs.

    Shows recent log entries with optional filtering and follow mode.
    """
    try:
        # Override level if error-only
        if error_only:
            level = 'ERROR'

        # Get log file path
        log_file = _get_log_file_path()

        if not log_file.exists():
            click.echo(f"❌ Log file not found: {log_file}")
            click.echo("   The service may not have been started yet.")
            return

        if follow:
            _follow_logs(log_file, level)
        else:
            _show_logs(log_file, tail, level)

    except KeyboardInterrupt:
        click.echo("\n👋 Stopped following logs")
    except Exception as e:
        click.echo(f"❌ Error reading logs: {e}", err=True)


def _show_logs(log_file: Path, tail: int, level: str) -> None:
    """Show last N lines of logs."""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Filter by level
        filtered_lines = [
            line for line in lines
            if _should_display_line(line, level)
        ]

        # Get last N lines
        display_lines = filtered_lines[-tail:] if tail > 0 else filtered_lines

        # Print lines
        for line in display_lines:
            _print_colored_line(line)

        # Show count
        if len(display_lines) < len(filtered_lines):
            hidden = len(filtered_lines) - len(display_lines)
            click.echo(f"\n... ({hidden} more lines hidden, use --tail {len(filtered_lines)} to see all)")

    except Exception as e:
        click.echo(f"Error reading log file: {e}", err=True)


def _follow_logs(log_file: Path, level: str) -> None:
    """Follow logs in real-time (like tail -f)."""
    click.echo(f"📜 Following logs from: {log_file}")
    click.echo(f"   Level filter: {level}")
    click.echo(f"   Press Ctrl+C to stop\n")

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            # Jump to end of file
            f.seek(0, 2)

            while True:
                line = f.readline()

                if line:
                    if _should_display_line(line, level):
                        _print_colored_line(line.rstrip())
                else:
                    # No new line, wait a bit
                    time.sleep(0.1)

    except KeyboardInterrupt:
        raise
    except Exception as e:
        click.echo(f"\nError following logs: {e}", err=True)


def _should_display_line(line: str, min_level: str) -> bool:
    """Check if line should be displayed based on log level."""
    # Level hierarchy
    levels = {
        'DEBUG': 0,
        'INFO': 1,
        'WARNING': 2,
        'ERROR': 3,
        'CRITICAL': 4
    }

    min_level_value = levels.get(min_level, 0)

    # Check if line contains a level
    for level_name, level_value in levels.items():
        if level_name in line:
            return level_value >= min_level_value

    # If no level found, show it (might be multi-line continuation)
    return True


def _print_colored_line(line: str) -> None:
    """Print log line with color based on level."""
    line = line.rstrip()

    if 'ERROR' in line or 'CRITICAL' in line:
        click.secho(line, fg='red')
    elif 'WARNING' in line:
        click.secho(line, fg='yellow')
    elif 'INFO' in line:
        click.secho(line, fg='green')
    elif 'DEBUG' in line:
        click.secho(line, fg='cyan')
    else:
        click.echo(line)


def _get_log_file_path() -> Path:
    """Get log file path."""
    # Try to get from config
    try:
        from trading_bot.config.models import Config
        import yaml

        with open('config.yaml', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        cfg = Config(**config_data)

        return Path(cfg.logging.file)

    except Exception:
        # Default fallback
        return Path("logs/trading_bot.log")


if __name__ == '__main__':
    logs_cmd()
