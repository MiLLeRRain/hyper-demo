"""SQLAlchemy database models for trading agents."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
    DateTime,
    ForeignKey,
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
    llm_model: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="References model name in config.llm.models"
    )
    exchange_account: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="References account name in config.exchange.accounts"
    )
    initial_balance: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), nullable=False)

    # Risk management parameters
    max_position_size: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2),
        default=20.0,
        nullable=False,
        comment="Max position size as % of account value"
    )
    max_leverage: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
        comment="Maximum allowed leverage (1-50x)"
    )
    stop_loss_pct: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2),
        default=2.0,
        nullable=False,
        comment="Stop loss percentage"
    )
    take_profit_pct: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2),
        default=5.0,
        nullable=False,
        comment="Take profit percentage"
    )
    strategy_description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Description of trading strategy for this agent"
    )

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
    """Agent decision model - stores AI decision history.

    This model stores decisions from the multi-agent trading system.
    Each decision represents one LLM's analysis and recommended action.
    """

    __tablename__ = "agent_decisions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("trading_agents.id"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Decision parsing status
    status: Mapped[str] = mapped_column(
        String(20), default="success", nullable=False, index=True,
        comment="success, failed, or parsing_error"
    )

    # Parsed decision fields (from TradingDecision model)
    action: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True,
        comment="OPEN_LONG, OPEN_SHORT, CLOSE_POSITION, or HOLD"
    )
    coin: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True,
        comment="BTC, ETH, SOL, BNB, DOGE, or XRP"
    )
    size_usd: Mapped[Decimal] = mapped_column(
        DECIMAL(20, 2), nullable=False,
        comment="Position size in USD (0 for HOLD/CLOSE)"
    )
    leverage: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Leverage 1-50x (1 for HOLD/CLOSE)"
    )
    stop_loss_price: Mapped[Decimal] = mapped_column(
        DECIMAL(20, 2), nullable=False,
        comment="Stop loss price (0 for HOLD/CLOSE)"
    )
    take_profit_price: Mapped[Decimal] = mapped_column(
        DECIMAL(20, 2), nullable=False,
        comment="Take profit price (0 for HOLD/CLOSE)"
    )
    confidence: Mapped[Decimal] = mapped_column(
        DECIMAL(3, 2), nullable=False,
        comment="Confidence score 0.00-1.00"
    )
    reasoning: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="LLM's reasoning for the decision"
    )

    # LLM interaction data
    llm_response: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Raw response from LLM"
    )
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Time taken for LLM call in milliseconds"
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Error message if status=failed"
    )

    # Relationships
    agent: Mapped["TradingAgent"] = relationship(back_populates="decisions")
    trades: Mapped[list["AgentTrade"]] = relationship(back_populates="decision")

    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed', 'parsing_error')",
            name="check_agent_decisions_status",
        ),
        CheckConstraint(
            "action IN ('OPEN_LONG', 'OPEN_SHORT', 'CLOSE_POSITION', 'HOLD')",
            name="check_agent_decisions_action",
        ),
        CheckConstraint(
            "coin IN ('BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP')",
            name="check_agent_decisions_coin",
        ),
        CheckConstraint(
            "leverage >= 1 AND leverage <= 50",
            name="check_agent_decisions_leverage",
        ),
        CheckConstraint(
            "confidence >= 0.00 AND confidence <= 1.00",
            name="check_agent_decisions_confidence",
        ),
    )

    def __repr__(self) -> str:
        return f"<AgentDecision(agent_id={self.agent_id}, action='{self.action}', coin='{self.coin}', status='{self.status}')>"


class AgentTrade(Base):
    """Agent trade model - stores actual trades."""

    __tablename__ = "agent_trades"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("trading_agents.id"), nullable=False, index=True
    )
    decision_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("agent_decisions.id"))
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
        PG_UUID(as_uuid=True), ForeignKey("trading_agents.id"), nullable=False, index=True
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
