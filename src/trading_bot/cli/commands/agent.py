"""Agent management commands."""

import click
import sys
from pathlib import Path
from tabulate import tabulate
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


@click.group('agent')
def agent_group():
    """Manage trading agents."""
    pass


@agent_group.command('list')
@click.option(
    '--status-filter', '-s',
    type=click.Choice(['active', 'inactive', 'all']),
    default='all',
    help='Filter by status'
)
def list_agents(status_filter: str):
    """
    List all trading agents.

    Shows agent name, model, status, balance, and configuration.
    """
    try:
        agents = _get_all_agents(status_filter)

        if not agents:
            click.echo("No agents found.")
            return

        # Prepare table data
        table = []
        for agent in agents:
            table.append([
                str(agent.id)[:8],  # Short ID
                agent.name,
                agent.llm_model_id,
                agent.status,
                f"${agent.initial_balance:,.2f}",
                f"{agent.max_leverage}x"
            ])

        headers = ["ID", "Name", "Model", "Status", "Balance", "Max Leverage"]
        click.echo("\n" + tabulate(table, headers=headers, tablefmt="grid"))
        click.echo(f"\nTotal: {len(agents)} agents\n")

    except Exception as e:
        click.echo(f"❌ Error listing agents: {e}", err=True)
        sys.exit(1)


@agent_group.command('add')
@click.option('--name', '-n', required=True, help='Agent name')
@click.option('--model', '-m', required=True, help='LLM model ID (e.g., deepseek-chat)')
@click.option('--balance', '-b', type=float, default=1000, help='Initial balance (default: 1000)')
@click.option('--leverage', '-l', type=int, default=10, help='Max leverage (default: 10)')
def add_agent(name: str, model: str, balance: float, leverage: int):
    """
    Add a new trading agent.

    Creates a new agent with specified configuration.
    """
    try:
        click.echo(f"➕ Creating agent '{name}'...")

        agent_id = _create_agent(
            name=name,
            model_id=model,
            balance=balance,
            max_leverage=leverage
        )

        click.echo(f"✅ Agent created successfully!")
        click.echo(f"   ID: {agent_id}")
        click.echo(f"   Name: {name}")
        click.echo(f"   Model: {model}")
        click.echo(f"   Balance: ${balance:,.2f}")
        click.echo(f"   Max Leverage: {leverage}x")

    except Exception as e:
        click.echo(f"❌ Error creating agent: {e}", err=True)
        sys.exit(1)


@agent_group.command('disable')
@click.argument('agent_id')
def disable_agent(agent_id: str):
    """
    Disable an agent.

    The agent will no longer participate in trading cycles.
    """
    try:
        click.echo(f"🔒 Disabling agent {agent_id}...")

        success = _set_agent_status(agent_id, "inactive")

        if success:
            click.echo(f"✅ Agent {agent_id} disabled")
        else:
            click.echo(f"❌ Failed to disable agent")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@agent_group.command('enable')
@click.argument('agent_id')
def enable_agent(agent_id: str):
    """
    Enable an agent.

    The agent will participate in trading cycles.
    """
    try:
        click.echo(f"🔓 Enabling agent {agent_id}...")

        success = _set_agent_status(agent_id, "active")

        if success:
            click.echo(f"✅ Agent {agent_id} enabled")
        else:
            click.echo(f"❌ Failed to enable agent")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@agent_group.command('info')
@click.argument('agent_id')
def agent_info(agent_id: str):
    """
    Show detailed agent information.

    Displays configuration, statistics, and recent performance.
    """
    try:
        agent = _get_agent_info(agent_id)

        if not agent:
            click.echo(f"❌ Agent {agent_id} not found")
            sys.exit(1)

        click.echo("\n" + "=" * 60)
        click.echo(f"📋 Agent Information: {agent.name}")
        click.echo("=" * 60)
        click.echo(f"ID: {agent.id}")
        click.echo(f"Name: {agent.name}")
        click.echo(f"Model: {agent.llm_model_id}")
        click.echo(f"Status: {agent.status}")
        click.echo(f"\n💰 Configuration:")
        click.echo(f"   Initial Balance: ${agent.initial_balance:,.2f}")
        click.echo(f"   Max Leverage: {agent.max_leverage}x")
        click.echo(f"   Max Position Size: {agent.max_position_size}%")
        click.echo(f"\n🕐 Timestamps:")
        click.echo(f"   Created: {agent.created_at}")
        click.echo(f"   Updated: {agent.updated_at}")
        click.echo("=" * 60 + "\n")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# Helper functions

def _get_all_agents(status_filter: str):
    """Get all agents from database."""
    from trading_bot.config.models import Config
    from trading_bot.models.database import TradingAgent
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import yaml

    # Load config
    with open('config.yaml', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    cfg = Config(**config_data)

    # Connect to database
    engine = create_engine(cfg.database.url)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Query agents
    query = db.query(TradingAgent)

    if status_filter != 'all':
        query = query.filter(TradingAgent.status == status_filter)

    agents = query.all()

    db.close()
    engine.dispose()

    return agents


def _create_agent(name: str, model_id: str, balance: float, max_leverage: int):
    """Create a new agent."""
    from trading_bot.config.models import Config
    from trading_bot.models.database import TradingAgent
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from decimal import Decimal
    import yaml

    # Load config
    with open('config.yaml', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    cfg = Config(**config_data)

    # Connect to database
    engine = create_engine(cfg.database.url)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Create agent
    agent = TradingAgent(
        id=uuid4(),
        name=name,
        llm_model_id=model_id,
        status="active",
        initial_balance=Decimal(str(balance)),
        max_leverage=max_leverage,
        max_position_size=Decimal("20.0")  # Default 20%
    )

    db.add(agent)
    db.commit()

    agent_id = agent.id

    db.close()
    engine.dispose()

    return agent_id


def _set_agent_status(agent_id: str, status: str) -> bool:
    """Set agent status."""
    from trading_bot.config.models import Config
    from trading_bot.models.database import TradingAgent
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from uuid import UUID
    import yaml

    try:
        # Load config
        with open('config.yaml', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        cfg = Config(**config_data)

        # Connect to database
        engine = create_engine(cfg.database.url)
        Session = sessionmaker(bind=engine)
        db = Session()

        # Update agent
        agent = db.query(TradingAgent).filter(
            TradingAgent.id == UUID(agent_id)
        ).first()

        if agent:
            agent.status = status
            db.commit()
            success = True
        else:
            success = False

        db.close()
        engine.dispose()

        return success

    except Exception:
        return False


def _get_agent_info(agent_id: str):
    """Get agent information."""
    from trading_bot.config.models import Config
    from trading_bot.models.database import TradingAgent
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from uuid import UUID
    import yaml

    # Load config
    with open('config.yaml', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    cfg = Config(**config_data)

    # Connect to database
    engine = create_engine(cfg.database.url)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Query agent
    agent = db.query(TradingAgent).filter(
        TradingAgent.id == UUID(agent_id)
    ).first()

    db.close()
    engine.dispose()

    return agent


if __name__ == '__main__':
    agent_group()
