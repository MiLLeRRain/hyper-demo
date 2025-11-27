"""Main CLI entry point for trading bot."""

import click
from .commands import start, stop, status, agent, logs


@click.group()
@click.version_option(version='0.2.0', prog_name='tradingbot')
def cli():
    """
    HyperLiquid AI Trading Bot CLI.

    Manage and monitor your AI trading bot with ease.
    """
    pass


# Register commands
cli.add_command(start.start_cmd)
cli.add_command(stop.stop_cmd)
cli.add_command(status.status_cmd)
cli.add_command(agent.agent_group)
cli.add_command(logs.logs_cmd)


if __name__ == '__main__':
    cli()
