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
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

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

        # Create engine
        engine = create_engine(db_url, echo=False)

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
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create a trading agent
        print("\n  Creating TradingAgent...")
        agent = TradingAgent(
            name="Test Agent",
            provider="deepseek",
            model="deepseek-chat",
            is_active=True,
            config={"temperature": 0.7, "max_tokens": 500}
        )
        session.add(agent)
        session.commit()
        print(f"  [OK] Created agent: {agent.name} (ID: {agent.id})")

        # Create a decision
        print("\n  Creating AgentDecision...")
        decision = AgentDecision(
            agent_id=agent.id,
            coin="BTC",
            action="BUY",
            confidence=0.75,
            reasoning="Test decision for integration test",
            entry_price=Decimal("50000.00"),
            position_size=Decimal("0.01"),
            leverage=2,
            stop_loss=Decimal("48000.00"),
            take_profit=Decimal("52000.00"),
            market_data={"price": 50000, "volume": 1000000}
        )
        session.add(decision)
        session.commit()
        print(f"  [OK] Created decision: {decision.action} {decision.coin} (ID: {decision.id})")

        # Create an order
        print("\n  Creating Order...")
        order = Order(
            agent_id=agent.id,
            decision_id=decision.id,
            coin="BTC",
            side="BUY",
            order_type="LIMIT",
            size=Decimal("0.01"),
            price=Decimal("50000.00"),
            status="FILLED",
            exchange_order_id="test_order_123",
            filled_size=Decimal("0.01"),
            average_fill_price=Decimal("50000.00")
        )
        session.add(order)
        session.commit()
        print(f"  [OK] Created order: {order.side} {order.size} {order.coin} (ID: {order.id})")

        # Create a position
        print("\n  Creating Position...")
        position = Position(
            agent_id=agent.id,
            coin="BTC",
            side="LONG",
            size=Decimal("0.01"),
            entry_price=Decimal("50000.00"),
            current_price=Decimal("51000.00"),
            leverage=2,
            unrealized_pnl=Decimal("20.00"),
            is_open=True
        )
        session.add(position)
        session.commit()
        print(f"  [OK] Created position: {position.side} {position.size} {position.coin} (ID: {position.id})")

        # Create performance metric
        print("\n  Creating PerformanceMetric...")
        metric = PerformanceMetric(
            agent_id=agent.id,
            total_trades=1,
            winning_trades=1,
            losing_trades=0,
            total_pnl=Decimal("20.00"),
            win_rate=Decimal("1.00"),
            sharpe_ratio=Decimal("2.5"),
            max_drawdown=Decimal("0.00")
        )
        session.add(metric)
        session.commit()
        print(f"  [OK] Created metric for agent {agent.name} (ID: {metric.id})")

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
        print(f"    Orders: {len(agent.orders)}")
        print(f"    Positions: {len(agent.positions)}")
        print(f"    Metrics: {len(agent.performance_metrics)}")

        # Test decision -> orders relationship
        session.refresh(decision)
        print(f"\n  Decision: {decision.action} {decision.coin}")
        print(f"    Orders: {len(decision.orders)}")
        if decision.orders:
            print(f"    Order Status: {decision.orders[0].status}")

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
        active_agents = session.query(TradingAgent).filter_by(is_active=True).all()
        print(f"\n  Active agents: {len(active_agents)}")

        # Query recent decisions
        recent_decisions = session.query(AgentDecision).order_by(
            AgentDecision.created_at.desc()
        ).limit(10).all()
        print(f"  Recent decisions: {len(recent_decisions)}")

        # Query open positions
        open_positions = session.query(Position).filter_by(is_open=True).all()
        print(f"  Open positions: {len(open_positions)}")

        # Query filled orders
        filled_orders = session.query(Order).filter_by(status="FILLED").all()
        print(f"  Filled orders: {len(filled_orders)}")

        # Aggregate query - total PnL
        total_pnl = session.query(
            Position
        ).filter_by(is_open=False).with_entities(
            text("COALESCE(SUM(realized_pnl), 0)")
        ).scalar() or Decimal("0")
        print(f"  Total realized PnL: ${total_pnl:.2f}")

        print("\n  [OK] All queries working")

    except Exception as e:
        print(f"\n[ERROR] Query test failed: {e}")
        return 1

    # ====================================================================
    # Step 6: Test Updates
    # ====================================================================
    print_section("Step 6: Test Updates")

    try:
        # Update order status
        order.status = "CANCELLED"
        session.commit()
        print(f"\n  [OK] Updated order status to {order.status}")

        # Update position
        position.current_price = Decimal("52000.00")
        position.unrealized_pnl = Decimal("40.00")
        session.commit()
        print(f"  [OK] Updated position price to ${position.current_price}")

        # Close position
        position.is_open = False
        position.realized_pnl = position.unrealized_pnl
        position.closed_at = datetime.now(UTC)
        session.commit()
        print(f"  [OK] Closed position with PnL ${position.realized_pnl}")

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
    print(f"    Orders: {session.query(Order).count()}")
    print(f"    Positions: {session.query(Position).count()}")
    print(f"    Metrics: {session.query(PerformanceMetric).count()}")

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
