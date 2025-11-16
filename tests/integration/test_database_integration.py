"""Comprehensive database integration tests.

Tests all database operations including:
- Schema creation
- CRUD operations for all models
- Relationships and joins
- State persistence
- Performance queries
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session

from src.trading_bot.models.database import (
    Base,
    TradingAgent,
    AgentDecision,
    AgentTrade,
    AgentPerformance,
    BotState
)


@pytest.fixture(scope="module")
def db_engine():
    """Create test database engine."""
    # Use in-memory SQLite for testing (PostgreSQL-compatible subset)
    # For full PostgreSQL testing, use: postgresql://user:pass@localhost/test_db
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for each test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()

    yield session

    # Rollback any uncommitted changes
    session.rollback()
    session.close()


class TestDatabaseSchema:
    """Test database schema creation."""

    def test_all_tables_created(self, db_engine):
        """Verify all tables are created."""
        # Get table names
        inspector = db_engine.dialect.get_table_names(db_engine.connect())

        expected_tables = {
            "trading_agents",
            "agent_decisions",
            "agent_trades",
            "agent_performance",
            "bot_state"
        }

        assert expected_tables.issubset(set(inspector)), \
            f"Missing tables: {expected_tables - set(inspector)}"


class TestTradingAgent:
    """Test TradingAgent CRUD operations."""

    def test_create_agent(self, db_session):
        """Test creating a trading agent."""
        agent = TradingAgent(
            name="Test Trend Follower",
            llm_model="deepseek-chat",
            exchange_account="testnet_account",
            initial_balance=Decimal("10000.00"),
            max_position_size=Decimal("20.00"),
            max_leverage=10,
            stop_loss_pct=Decimal("2.00"),
            take_profit_pct=Decimal("5.00"),
            strategy_description="Follow strong trends with SMA crossover"
        )

        db_session.add(agent)
        db_session.commit()

        # Verify
        assert agent.id is not None
        assert agent.created_at is not None
        assert agent.status == "active"

    def test_unique_agent_name(self, db_session):
        """Test that agent names must be unique."""
        agent1 = TradingAgent(
            name="Duplicate Name",
            llm_model="deepseek-chat",
            exchange_account="account1",
            initial_balance=Decimal("10000.00")
        )
        db_session.add(agent1)
        db_session.commit()

        # Try to create another agent with same name
        agent2 = TradingAgent(
            name="Duplicate Name",
            llm_model="gpt-4",
            exchange_account="account2",
            initial_balance=Decimal("20000.00")
        )
        db_session.add(agent2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_read_agent(self, db_session):
        """Test reading an agent."""
        # Create
        agent = TradingAgent(
            name="Read Test Agent",
            llm_model="deepseek-chat",
            exchange_account="test_account",
            initial_balance=Decimal("5000.00")
        )
        db_session.add(agent)
        db_session.commit()
        agent_id = agent.id

        # Read
        retrieved = db_session.query(TradingAgent).filter_by(id=agent_id).first()

        assert retrieved is not None
        assert retrieved.name == "Read Test Agent"
        assert retrieved.initial_balance == Decimal("5000.00")

    def test_update_agent(self, db_session):
        """Test updating an agent."""
        # Create
        agent = TradingAgent(
            name="Update Test Agent",
            llm_model="deepseek-chat",
            exchange_account="test_account",
            initial_balance=Decimal("10000.00"),
            status="active"
        )
        db_session.add(agent)
        db_session.commit()

        # Update
        agent.status = "paused"
        agent.max_leverage = 5
        db_session.commit()

        # Verify
        db_session.refresh(agent)
        assert agent.status == "paused"
        assert agent.max_leverage == 5

    def test_delete_agent(self, db_session):
        """Test deleting an agent."""
        # Create
        agent = TradingAgent(
            name="Delete Test Agent",
            llm_model="deepseek-chat",
            exchange_account="test_account",
            initial_balance=Decimal("10000.00")
        )
        db_session.add(agent)
        db_session.commit()
        agent_id = agent.id

        # Delete
        db_session.delete(agent)
        db_session.commit()

        # Verify
        retrieved = db_session.query(TradingAgent).filter_by(id=agent_id).first()
        assert retrieved is None


class TestAgentDecision:
    """Test AgentDecision CRUD operations."""

    @pytest.fixture
    def agent(self, db_session):
        """Create a test agent."""
        import uuid
        agent = TradingAgent(
            name=f"Decision Test Agent {uuid.uuid4().hex[:8]}",  # Unique name
            llm_model="deepseek-chat",
            exchange_account="test_account",
            initial_balance=Decimal("10000.00")
        )
        db_session.add(agent)
        db_session.commit()
        return agent

    def test_create_decision(self, db_session, agent):
        """Test creating a decision."""
        decision = AgentDecision(
            agent_id=agent.id,
            status="success",
            action="OPEN_LONG",
            coin="BTC",
            size_usd=Decimal("1000.00"),
            leverage=5,
            stop_loss_price=Decimal("48000.00"),
            take_profit_price=Decimal("52000.00"),
            confidence=Decimal("0.75"),
            reasoning="Strong bullish trend with MACD confirmation",
            llm_response='{"action": "OPEN_LONG", ...}',
            execution_time_ms=1500
        )

        db_session.add(decision)
        db_session.commit()

        # Verify
        assert decision.id is not None
        assert decision.timestamp is not None

    def test_create_hold_decision(self, db_session, agent):
        """Test creating a HOLD decision."""
        decision = AgentDecision(
            agent_id=agent.id,
            status="success",
            action="HOLD",
            coin="ETH",
            size_usd=Decimal("0.00"),
            leverage=1,
            stop_loss_price=Decimal("0.00"),
            take_profit_price=Decimal("0.00"),
            confidence=Decimal("0.60"),
            reasoning="Waiting for clearer signals"
        )

        db_session.add(decision)
        db_session.commit()

        assert decision.action == "HOLD"
        assert decision.size_usd == Decimal("0.00")

    def test_decision_constraints(self, db_session, agent):
        """Test check constraints on decisions."""
        # Invalid action
        with pytest.raises(Exception):
            decision = AgentDecision(
                agent_id=agent.id,
                action="INVALID_ACTION",  # Not in allowed values
                coin="BTC",
                size_usd=Decimal("1000.00"),
                leverage=5,
                stop_loss_price=Decimal("48000.00"),
                take_profit_price=Decimal("52000.00"),
                confidence=Decimal("0.75"),
                reasoning="Test"
            )
            db_session.add(decision)
            db_session.commit()

    def test_query_decisions_by_agent(self, db_session, agent):
        """Test querying decisions for an agent."""
        # Create multiple decisions
        for i in range(5):
            decision = AgentDecision(
                agent_id=agent.id,
                action="HOLD",
                coin="BTC",
                size_usd=Decimal("0.00"),
                leverage=1,
                stop_loss_price=Decimal("0.00"),
                take_profit_price=Decimal("0.00"),
                confidence=Decimal("0.50"),
                reasoning=f"Decision {i}"
            )
            db_session.add(decision)
        db_session.commit()

        # Query
        decisions = db_session.query(AgentDecision).filter_by(
            agent_id=agent.id
        ).all()

        assert len(decisions) == 5


class TestAgentTrade:
    """Test AgentTrade CRUD operations."""

    @pytest.fixture
    def agent(self, db_session):
        """Create a test agent."""
        import uuid
        agent = TradingAgent(
            name=f"Trade Test Agent {uuid.uuid4().hex[:8]}",  # Unique name
            llm_model="deepseek-chat",
            exchange_account="test_account",
            initial_balance=Decimal("10000.00")
        )
        db_session.add(agent)
        db_session.commit()
        return agent

    def test_create_trade(self, db_session, agent):
        """Test creating a trade."""
        trade = AgentTrade(
            agent_id=agent.id,
            coin="BTC",
            side="long",
            size=Decimal("0.1"),
            entry_price=Decimal("50000.00"),
            entry_time=datetime.utcnow(),
            status="open"
        )

        db_session.add(trade)
        db_session.commit()

        assert trade.id is not None
        assert trade.status == "open"

    def test_close_trade(self, db_session, agent):
        """Test closing a trade."""
        # Create trade
        trade = AgentTrade(
            agent_id=agent.id,
            coin="ETH",
            side="long",
            size=Decimal("1.0"),
            entry_price=Decimal("3000.00"),
            entry_time=datetime.utcnow(),
            status="open"
        )
        db_session.add(trade)
        db_session.commit()

        # Close trade
        trade.exit_price = Decimal("3150.00")
        trade.exit_time = datetime.utcnow()
        trade.realized_pnl = Decimal("150.00")
        trade.status = "closed"
        db_session.commit()

        # Verify
        assert trade.status == "closed"
        assert trade.realized_pnl == Decimal("150.00")

    def test_query_open_positions(self, db_session, agent):
        """Test querying open positions."""
        # Create open and closed trades
        open_trade = AgentTrade(
            agent_id=agent.id,
            coin="BTC",
            side="long",
            size=Decimal("0.1"),
            entry_price=Decimal("50000.00"),
            status="open"
        )
        closed_trade = AgentTrade(
            agent_id=agent.id,
            coin="ETH",
            side="short",
            size=Decimal("1.0"),
            entry_price=Decimal("3000.00"),
            status="closed"
        )
        db_session.add_all([open_trade, closed_trade])
        db_session.commit()

        # Query only open positions
        open_positions = db_session.query(AgentTrade).filter_by(
            agent_id=agent.id,
            status="open"
        ).all()

        assert len(open_positions) == 1
        assert open_positions[0].coin == "BTC"


class TestAgentPerformance:
    """Test AgentPerformance CRUD operations."""

    @pytest.fixture
    def agent(self, db_session):
        """Create a test agent."""
        import uuid
        agent = TradingAgent(
            name=f"Performance Test Agent {uuid.uuid4().hex[:8]}",  # Unique name
            llm_model="deepseek-chat",
            exchange_account="test_account",
            initial_balance=Decimal("10000.00")
        )
        db_session.add(agent)
        db_session.commit()
        return agent

    def test_create_performance_snapshot(self, db_session, agent):
        """Test creating a performance snapshot."""
        snapshot = AgentPerformance(
            agent_id=agent.id,
            total_value=Decimal("10500.00"),
            cash_balance=Decimal("8000.00"),
            position_value=Decimal("2500.00"),
            realized_pnl=Decimal("300.00"),
            unrealized_pnl=Decimal("200.00"),
            total_pnl=Decimal("500.00"),
            roi_percent=Decimal("5.00"),
            num_trades=10,
            num_winning_trades=6,
            num_losing_trades=4,
            win_rate=Decimal("60.00"),
            avg_win=Decimal("100.00"),
            avg_loss=Decimal("50.00"),
            profit_factor=Decimal("1.50")
        )

        db_session.add(snapshot)
        db_session.commit()

        assert snapshot.id is not None
        assert snapshot.roi_percent == Decimal("5.00")

    def test_query_performance_history(self, db_session, agent):
        """Test querying performance history."""
        # Create multiple snapshots
        for i in range(3):
            snapshot = AgentPerformance(
                agent_id=agent.id,
                total_value=Decimal(str(10000 + i * 100)),
                cash_balance=Decimal("8000.00"),
                position_value=Decimal("2000.00"),
                realized_pnl=Decimal("0.00"),
                unrealized_pnl=Decimal("0.00"),
                total_pnl=Decimal("0.00")
            )
            db_session.add(snapshot)
        db_session.commit()

        # Query in chronological order
        snapshots = db_session.query(AgentPerformance).filter_by(
            agent_id=agent.id
        ).order_by(AgentPerformance.snapshot_time).all()

        assert len(snapshots) == 3
        assert snapshots[0].total_value == Decimal("10000.00")
        assert snapshots[2].total_value == Decimal("10200.00")


class TestBotState:
    """Test BotState CRUD operations."""

    def test_save_and_load_state(self, db_session):
        """Test saving and loading bot state."""
        # Save state
        state = BotState(
            key="trading_bot_state",
            value='{"cycle_count": 45, "last_cycle_time": "2025-11-15T12:00:00Z"}'
        )
        db_session.add(state)
        db_session.commit()

        # Load state
        loaded = db_session.query(BotState).filter_by(
            key="trading_bot_state"
        ).first()

        assert loaded is not None
        assert "cycle_count" in loaded.value
        assert loaded.updated_at is not None

    def test_upsert_state(self, db_session):
        """Test upserting state (insert or update)."""
        # First save
        state1 = BotState(
            key="test_state",
            value='{"count": 1}'
        )
        db_session.add(state1)
        db_session.commit()

        # Update (simulating upsert)
        state2 = db_session.query(BotState).filter_by(key="test_state").first()
        state2.value = '{"count": 2}'
        db_session.commit()

        # Verify
        final_state = db_session.query(BotState).filter_by(key="test_state").first()
        assert '{"count": 2}' in final_state.value


class TestRelationships:
    """Test relationships between tables."""

    @pytest.fixture
    def agent(self, db_session):
        """Create a test agent."""
        import uuid
        agent = TradingAgent(
            name=f"Relationship Test Agent {uuid.uuid4().hex[:8]}",  # Unique name
            llm_model="deepseek-chat",
            exchange_account="test_account",
            initial_balance=Decimal("10000.00")
        )
        db_session.add(agent)
        db_session.commit()
        return agent

    def test_agent_decisions_relationship(self, db_session, agent):
        """Test agent -> decisions relationship."""
        # Create decisions
        for i in range(3):
            decision = AgentDecision(
                agent_id=agent.id,
                action="HOLD",
                coin="BTC",
                size_usd=Decimal("0.00"),
                leverage=1,
                stop_loss_price=Decimal("0.00"),
                take_profit_price=Decimal("0.00"),
                confidence=Decimal("0.50"),
                reasoning=f"Reason {i}"
            )
            db_session.add(decision)
        db_session.commit()

        # Query through relationship
        db_session.refresh(agent)
        assert len(agent.decisions) == 3

    def test_decision_trade_relationship(self, db_session, agent):
        """Test decision -> trade relationship."""
        # Create decision
        decision = AgentDecision(
            agent_id=agent.id,
            action="OPEN_LONG",
            coin="BTC",
            size_usd=Decimal("1000.00"),
            leverage=5,
            stop_loss_price=Decimal("48000.00"),
            take_profit_price=Decimal("52000.00"),
            confidence=Decimal("0.75"),
            reasoning="Test decision"
        )
        db_session.add(decision)
        db_session.commit()

        # Create trade linked to decision
        trade = AgentTrade(
            agent_id=agent.id,
            decision_id=decision.id,
            coin="BTC",
            side="long",
            size=Decimal("0.02"),
            entry_price=Decimal("50000.00"),
            status="open"
        )
        db_session.add(trade)
        db_session.commit()

        # Query through relationship
        db_session.refresh(decision)
        assert len(decision.trades) == 1
        assert decision.trades[0].coin == "BTC"

    def test_cascade_delete(self, db_session):
        """Test cascade delete of related records."""
        import uuid
        # Create agent with decisions and trades
        agent = TradingAgent(
            name=f"Cascade Test Agent {uuid.uuid4().hex[:8]}",  # Unique name
            llm_model="deepseek-chat",
            exchange_account="test_account",
            initial_balance=Decimal("10000.00")
        )
        db_session.add(agent)
        db_session.flush()

        decision = AgentDecision(
            agent_id=agent.id,
            action="HOLD",
            coin="BTC",
            size_usd=Decimal("0.00"),
            leverage=1,
            stop_loss_price=Decimal("0.00"),
            take_profit_price=Decimal("0.00"),
            confidence=Decimal("0.50"),
            reasoning="Test"
        )
        db_session.add(decision)
        db_session.commit()

        agent_id = agent.id

        # Delete agent
        db_session.delete(agent)
        db_session.commit()

        # Verify decisions are also deleted (cascade)
        decisions = db_session.query(AgentDecision).filter_by(
            agent_id=agent_id
        ).all()
        assert len(decisions) == 0


class TestComplexQueries:
    """Test complex analytical queries."""

    @pytest.fixture
    def setup_data(self, db_session):
        """Setup test data."""
        import uuid
        # Create agent
        agent = TradingAgent(
            name=f"Analytics Test Agent {uuid.uuid4().hex[:8]}",  # Unique name
            llm_model="deepseek-chat",
            exchange_account="test_account",
            initial_balance=Decimal("10000.00")
        )
        db_session.add(agent)
        db_session.flush()

        # Create closed trades
        trades = [
            AgentTrade(
                agent_id=agent.id, coin="BTC", side="long",
                size=Decimal("0.1"), entry_price=Decimal("50000.00"),
                exit_price=Decimal("51000.00"), realized_pnl=Decimal("100.00"),
                status="closed"
            ),
            AgentTrade(
                agent_id=agent.id, coin="ETH", side="long",
                size=Decimal("1.0"), entry_price=Decimal("3000.00"),
                exit_price=Decimal("2900.00"), realized_pnl=Decimal("-100.00"),
                status="closed"
            ),
            AgentTrade(
                agent_id=agent.id, coin="SOL", side="short",
                size=Decimal("10.0"), entry_price=Decimal("100.00"),
                exit_price=Decimal("95.00"), realized_pnl=Decimal("50.00"),
                status="closed"
            ),
        ]
        db_session.add_all(trades)
        db_session.commit()

        return agent

    def test_calculate_total_pnl(self, db_session, setup_data):
        """Test calculating total PnL."""
        agent = setup_data

        total_pnl = db_session.query(
            func.sum(AgentTrade.realized_pnl)
        ).filter_by(
            agent_id=agent.id,
            status="closed"
        ).scalar()

        assert total_pnl == Decimal("50.00")  # 100 - 100 + 50

    def test_calculate_win_rate(self, db_session, setup_data):
        """Test calculating win rate."""
        agent = setup_data

        total_trades = db_session.query(AgentTrade).filter_by(
            agent_id=agent.id,
            status="closed"
        ).count()

        winning_trades = db_session.query(AgentTrade).filter(
            AgentTrade.agent_id == agent.id,
            AgentTrade.status == "closed",
            AgentTrade.realized_pnl > 0
        ).count()

        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

        assert win_rate == pytest.approx(66.67, rel=0.01)  # 2 wins out of 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
