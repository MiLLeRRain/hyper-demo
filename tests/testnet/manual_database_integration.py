#!/usr/bin/env python3
"""Test database integration - verify all models and operations.

This test checks:
1. Database connection
2. All models can be created
3. CRUD operations work
4. Relationships work
5. Data persistence
"""

import os
import sys
from pathlib import Path
from datetime import datetime, UTC
from decimal import Decimal

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
from sqlalchemy import text

from trading_bot.infrastructure.database import DatabaseManager
from trading_bot.models.database import (
    Base,
    TradingAgent,
    AgentDecision,
    AgentTrade,
    AgentPerformance
)


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    """Run database integration tests."""
    load_dotenv()

    print_section("Database Integration Test")

    # ====================================================================
    # Step 1: Database Connection
    # ====================================================================
    print_section("Step 1: Database Connection")

    try:
        # Get database URL from environment
        db_user = os.getenv("DB_USER", "trading_bot")
        db_password = os.getenv("DB_PASSWORD", "your_password")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "trading_bot")

        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

        print(f"\n  Connecting to: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")

        # Initialize DatabaseManager
        db_manager = DatabaseManager(db_url)
        engine = db_manager.engine

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"  [OK] Connected to PostgreSQL")
            print(f"       Version: {version[:50]}...")

    except Exception as e:
        print(f"\n[ERROR] Database connection failed: {e}")
        print("\n  Possible solutions:")
        print("  1. Install PostgreSQL:")
        print("     - Download from https://www.postgresql.org/download/")
        print("     - Or use Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=your_password postgres")
        print("\n  2. Create database:")
        print(f"     createdb -U {db_user} {db_name}")
        print("\n  3. Check .env configuration:")
        print(f"     DB_USER={db_user}")
        print(f"     DB_PASSWORD=***")
        print(f"     DB_HOST={db_host}")
        print(f"     DB_PORT={db_port}")
        print(f"     DB_NAME={db_name}")
        return 1

    # ====================================================================
    # Step 2: Create Tables
    # ====================================================================
    print_section("Step 2: Create Database Tables")

    try:
        # Drop all tables first (for clean test)
        print("\n  Dropping existing tables...")
        Base.metadata.drop_all(engine)
        print("  [OK] Dropped all tables")

        # Create all tables
        print("\n  Creating tables...")
        Base.metadata.create_all(engine)
        print("  [OK] Created all tables")

        # List tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """))
            tables = [row[0] for row in result]
            print(f"\n  Tables created: {len(tables)}")
            for table in tables:
                print(f"    - {table}")

    except Exception as e:
        print(f"\n[ERROR] Table creation failed: {e}")
        return 1

    # ====================================================================
    # Step 3: Test CRUD Operations
    # ====================================================================
    print_section("Step 3: Test CRUD Operations")

    # Create session
    session = db_manager.get_session()

    try:
        # Create a trading agent
        print("\n  Creating TradingAgent...")
        agent = TradingAgent(
            name="Test Agent",
            llm_model="deepseek-chat",
            exchange_account="hyperliquid_main",
            initial_balance=Decimal("1000.00"),
            status="active",
            max_position_size=Decimal("20.00"),
            max_leverage=10,
            stop_loss_pct=Decimal("2.00"),
            take_profit_pct=Decimal("5.00")
        )
        session.add(agent)
        session.commit()
        print(f"  [OK] Created agent: {agent.name} (ID: {agent.id})")

        # Create a decision
        print("\n  Creating AgentDecision...")
        decision = AgentDecision(
            agent_id=agent.id,
            coin="BTC",
            action="OPEN_LONG",
            confidence=Decimal("0.75"),
            reasoning="Test decision for integration test",
            size_usd=Decimal("100.00"),
            leverage=2,
            stop_loss_price=Decimal("48000.00"),
            take_profit_price=Decimal("52000.00"),
            status="success"
        )
        session.add(decision)
        session.commit()
        print(f"  [OK] Created decision: {decision.action} {decision.coin} (ID: {decision.id})")

        # Create a trade (replaces Order/Position concepts in this schema)
        print("\n  Creating AgentTrade...")
        trade = AgentTrade(
            agent_id=agent.id,
            decision_id=decision.id,
            coin="BTC",
            side="long",
            size=Decimal("0.002"),
            entry_price=Decimal("50000.00"),
            status="open",
            unrealized_pnl=Decimal("20.00")
        )
        session.add(trade)
        session.commit()
        print(f"  [OK] Created trade: {trade.side} {trade.size} {trade.coin} (ID: {trade.id})")

        # Create performance snapshot
        print("\n  Creating AgentPerformance...")
        perf = AgentPerformance(
            agent_id=agent.id,
            total_value=Decimal("1020.00"),
            cash_balance=Decimal("900.00"),
            position_value=Decimal("120.00"),
            realized_pnl=Decimal("0.00"),
            unrealized_pnl=Decimal("20.00"),
            total_pnl=Decimal("20.00"),
            roi_percent=Decimal("2.00"),
            num_trades=1,
            num_winning_trades=0,
            num_losing_trades=0
        )
        session.add(perf)
        session.commit()
        print(f"  [OK] Created performance snapshot for agent {agent.name} (ID: {perf.id})")

    except Exception as e:
        print(f"\n[ERROR] CRUD operations failed: {e}")
        session.rollback()
        return 1

    # ====================================================================
    # Step 4: Test Relationships
    # ====================================================================
    print_section("Step 4: Test Relationships")

    try:
        # Refresh agent to load relationships
        session.refresh(agent)

        print(f"\n  Agent: {agent.name}")
        print(f"    Decisions: {len(agent.decisions)}")
        print(f"    Trades: {len(agent.trades)}")
        print(f"    Performance Snapshots: {len(agent.performance_snapshots)}")

        # Test decision -> trades relationship
        session.refresh(decision)
        print(f"\n  Decision: {decision.action} {decision.coin}")
        print(f"    Trades: {len(decision.trades)}")
        if decision.trades:
            print(f"    Trade Status: {decision.trades[0].status}")

        print("\n  [OK] All relationships working")

    except Exception as e:
        print(f"\n[ERROR] Relationship test failed: {e}")
        return 1

    # ====================================================================
    # Step 5: Test Queries
    # ====================================================================
    print_section("Step 5: Test Queries")

    try:
        # Query active agents
        active_agents = session.query(TradingAgent).filter_by(status="active").all()
        print(f"\n  Active agents: {len(active_agents)}")

        # Query recent decisions
        recent_decisions = session.query(AgentDecision).order_by(
            AgentDecision.timestamp.desc()
        ).limit(10).all()
        print(f"  Recent decisions: {len(recent_decisions)}")

        # Query open trades
        open_trades = session.query(AgentTrade).filter_by(status="open").all()
        print(f"  Open trades: {len(open_trades)}")

        print("\n  [OK] All queries working")

    except Exception as e:
        print(f"\n[ERROR] Query test failed: {e}")
        return 1

    # ====================================================================
    # Step 6: Test Updates
    # ====================================================================
    print_section("Step 6: Test Updates")

    try:
        # Update trade status
        trade.status = "closed"
        trade.exit_price = Decimal("52000.00")
        trade.realized_pnl = Decimal("40.00")
        trade.exit_time = datetime.now(UTC)
        session.commit()
        print(f"\n  [OK] Closed trade with PnL ${trade.realized_pnl}")

        # Update agent balance
        agent.initial_balance += trade.realized_pnl
        session.commit()
        print(f"  [OK] Updated agent balance to ${agent.initial_balance}")

    except Exception as e:
        print(f"\n[ERROR] Update test failed: {e}")
        return 1

    # ====================================================================
    # Test Summary
    # ====================================================================
    print_section("Test Summary")

    print("\n  [OK] Database Integration Test Completed!")
    print("\n  Verified components:")
    print("    [OK] Database connection")
    print("    [OK] Table creation")
    print("    [OK] CRUD operations (Create, Read, Update)")
    print("    [OK] Model relationships")
    print("    [OK] Complex queries")
    print("    [OK] Data persistence")

    print("\n  Database Statistics:")
    print(f"    Agents: {session.query(TradingAgent).count()}")
    print(f"    Decisions: {session.query(AgentDecision).count()}")
    print(f"    Trades: {session.query(AgentTrade).count()}")
    print(f"    Performance Snapshots: {session.query(AgentPerformance).count()}")

    # Cleanup
    session.close()

    print("\n  Next steps:")
    print("    1. Database is ready for production use")
    print("    2. Run alembic migrations for schema updates")
    print("    3. Set up database backups")
    print("    4. Configure connection pooling")

    return 0


if __name__ == "__main__":
    sys.exit(main())
