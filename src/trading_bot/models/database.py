"""SQLAlchemy database models for trading agents."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class TradingAgent(Base):
    """Trading agent model - each agent represents one LLM + one HyperLiquid account."""

    __tablename__ = "trading_agents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    llm_model: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    hyperliquid_account_id: Mapped[Optional[str]] = mapped_column(String(100))
    hyperliquid_api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    hyperliquid_api_secret_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    initial_balance: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    decisions: Mapped[list["AgentDecision"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    trades: Mapped[list["AgentTrade"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    performance_snapshots: Mapped[list["AgentPerformance"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'paused', 'stopped')",
            name="check_trading_agents_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<TradingAgent(name='{self.name}', llm_model='{self.llm_model}', status='{self.status}')>"


class AgentDecision(Base):
    """Agent decision model - stores AI decision history."""

    __tablename__ = "agent_decisions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    market_data_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    llm_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    llm_response: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_decision: Mapped[Optional[dict]] = mapped_column(JSONB)
    execution_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    execution_result: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)

    # Relationships
    agent: Mapped["TradingAgent"] = relationship(back_populates="decisions")
    trades: Mapped[list["AgentTrade"]] = relationship(back_populates="decision")

    __table_args__ = (
        CheckConstraint(
            "execution_status IN ('pending', 'executed', 'failed', 'skipped')",
            name="check_agent_decisions_execution_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<AgentDecision(agent_id={self.agent_id}, status='{self.execution_status}')>"


class AgentTrade(Base):
    """Agent trade model - stores actual trades."""

    __tablename__ = "agent_trades"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    decision_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    coin: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    size: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), nullable=False)
    entry_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 2))
    entry_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )
    exit_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 2))
    exit_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    realized_pnl: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 2))
    unrealized_pnl: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 2))
    fees: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 2))
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False, index=True
    )
    hyperliquid_order_id: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    agent: Mapped["TradingAgent"] = relationship(back_populates="trades")
    decision: Mapped[Optional["AgentDecision"]] = relationship(back_populates="trades")

    __table_args__ = (
        CheckConstraint(
            "side IN ('long', 'short')", name="check_agent_trades_side"
        ),
        CheckConstraint(
            "status IN ('open', 'closed', 'liquidated')",
            name="check_agent_trades_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<AgentTrade(agent_id={self.agent_id}, coin='{self.coin}', side='{self.side}', status='{self.status}')>"


class AgentPerformance(Base):
    """Agent performance model - periodic performance snapshots."""

    __tablename__ = "agent_performance"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    total_value: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), nullable=False)
    cash_balance: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), nullable=False)
    position_value: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), nullable=False)
    total_pnl: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), nullable=False)
    roi_percent: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4))
    num_trades: Mapped[int] = mapped_column(Integer, default=0)
    num_winning_trades: Mapped[int] = mapped_column(Integer, default=0)
    num_losing_trades: Mapped[int] = mapped_column(Integer, default=0)
    win_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    avg_win: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 2))
    avg_loss: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(20, 2))
    profit_factor: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4))
    sharpe_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4))
    max_drawdown: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4))
    max_drawdown_percent: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))

    # Relationships
    agent: Mapped["TradingAgent"] = relationship(
        back_populates="performance_snapshots"
    )

    def __repr__(self) -> str:
        return f"<AgentPerformance(agent_id={self.agent_id}, total_value={self.total_value}, roi={self.roi_percent}%)>"
