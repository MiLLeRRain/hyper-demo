"""Initialize database schema and verify setup.

This script:
1. Creates all database tables
2. Verifies schema creation
3. Optionally creates sample data for testing
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import argparse
import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from trading_bot.models.database import (
    Base,
    TradingAgent,
    AgentDecision,
    AgentTrade,
    AgentPerformance,
    BotState
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_url_from_env() -> str:
    """Get database URL from environment variables."""
    db_user = os.getenv("DB_USER", "trading_bot")
    db_password = os.getenv("DB_PASSWORD", "trading_bot_2025")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "trading_bot_dev")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def create_tables(engine):
    """Create all database tables."""
    logger.info("Creating database tables...")

    try:
        Base.metadata.create_all(engine)
        logger.info("Successfully created all tables")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


def verify_schema(engine):
    """Verify that all tables were created correctly."""
    logger.info("Verifying database schema...")

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    expected_tables = {
        "trading_agents",
        "agent_decisions",
        "agent_trades",
        "agent_performance",
        "bot_state"
    }

    missing_tables = expected_tables - set(existing_tables)

    if missing_tables:
        logger.error(f"Missing tables: {missing_tables}")
        return False

    logger.info(f"Successfully verified all {len(expected_tables)} tables")

    # Verify indexes on key tables
    for table_name in expected_tables:
        indexes = inspector.get_indexes(table_name)
        logger.info(f"  {table_name}: {len(indexes)} indexes")

    return True


def create_sample_data(engine):
    """Create sample data for testing."""
    logger.info("Creating sample data...")

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create sample agents
        agents = [
            TradingAgent(
                name="Default Agent",
                llm_model="deepseek-chat",
                exchange_account="testnet_main",
                initial_balance=Decimal("10000.00"),
                max_position_size=Decimal("20.00"),
                max_leverage=10,
                stop_loss_pct=Decimal("2.00"),
                take_profit_pct=Decimal("5.00"),
                strategy_description=None  # Default agent with no custom strategy
            ),
            TradingAgent(
                name="Trend Follower",
                llm_model="deepseek-chat",
                exchange_account="testnet_main",
                initial_balance=Decimal("10000.00"),
                max_position_size=Decimal("30.00"),
                max_leverage=5,
                stop_loss_pct=Decimal("3.00"),
                take_profit_pct=Decimal("7.00"),
                strategy_description="""You are a TREND FOLLOWING trader.
Entry Rules:
- LONG: Price above SMA(20) AND SMA(50), MACD bullish, RSI > 50
- SHORT: Price below SMA(20) AND SMA(50), MACD bearish, RSI < 50
Risk Management:
- Position size: 30% of account
- Stop loss: Below recent swing low/high
- Leverage: 3-5x"""
            ),
        ]

        session.add_all(agents)
        session.commit()

        logger.info(f"Created {len(agents)} sample agents")

        # Create sample decisions
        for agent in agents:
            decision = AgentDecision(
                agent_id=agent.id,
                action="HOLD",
                coin="BTC",
                size_usd=Decimal("0.00"),
                leverage=1,
                stop_loss_price=Decimal("0.00"),
                take_profit_price=Decimal("0.00"),
                confidence=Decimal("0.60"),
                reasoning="Waiting for clearer market signals",
                llm_response='{"action": "HOLD", "reasoning": "Waiting for clearer signals"}',
                execution_time_ms=1200
            )
            session.add(decision)

        session.commit()
        logger.info("Created sample decisions")

        # Create initial bot state
        state = BotState(
            key="trading_bot_state",
            value='{"cycle_count": 0, "last_cycle_time": null, "initialized": true}'
        )
        session.add(state)
        session.commit()

        logger.info("Created initial bot state")

        return True

    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        session.rollback()
        return False

    finally:
        session.close()


def test_database_connection(db_url: str):
    """Test database connection."""
    logger.info("Testing database connection...")

    try:
        engine = create_engine(db_url, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

        logger.info("Successfully connected to database")
        return engine

    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.error(f"Connection string: {db_url.split('@')[0]}@***")
        return None


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Initialize trading bot database")
    parser.add_argument(
        "--db-url",
        help="Database URL (default: read from environment)",
        default=None
    )
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Create sample data for testing"
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing tables before creating (WARNING: destructive)"
    )

    args = parser.parse_args()

    # Get database URL
    db_url = args.db_url or get_db_url_from_env()

    print("=" * 70)
    print("DATABASE INITIALIZATION")
    print("=" * 70)
    print(f"Database: {db_url.split('@')[1] if '@' in db_url else 'local'}")
    print(f"Sample data: {'Yes' if args.sample_data else 'No'}")
    print(f"Drop existing: {'Yes' if args.drop_existing else 'No'}")
    print("=" * 70)
    print()

    # Test connection
    engine = test_database_connection(db_url)
    if not engine:
        logger.error("Exiting due to connection failure")
        return 1

    # Drop existing tables if requested
    if args.drop_existing:
        logger.warning("Dropping existing tables...")
        confirmation = input("Are you sure? This will DELETE ALL DATA! (yes/no): ")
        if confirmation.lower() == "yes":
            Base.metadata.drop_all(engine)
            logger.info("Dropped all existing tables")
        else:
            logger.info("Cancelled drop operation")
            return 1

    # Create tables
    if not create_tables(engine):
        logger.error("Failed to create tables")
        return 1

    # Verify schema
    if not verify_schema(engine):
        logger.error("Schema verification failed")
        return 1

    # Create sample data if requested
    if args.sample_data:
        if not create_sample_data(engine):
            logger.error("Failed to create sample data")
            return 1

    print()
    print("=" * 70)
    print("SUCCESS: Database initialized successfully")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Run integration tests: pytest tests/integration/test_database_integration.py -v")
    print("2. Start the trading bot: python tradingbot.py start")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
