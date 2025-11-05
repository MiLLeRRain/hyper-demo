"""Order lifecycle management for HyperLiquid trading.

This module manages the complete lifecycle of trading orders including:
- Order placement and execution
- Order status tracking
- Order cancellation
- Trade record persistence
"""

import logging
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.database import AgentTrade
from .hyperliquid_executor import HyperLiquidExecutor, OrderType

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """Order side enumeration."""
    LONG = "long"
    SHORT = "short"


class OrderManager:
    """Manage order lifecycle and state.

    The OrderManager coordinates between the HyperLiquid executor and
    the database, ensuring that all trades are properly recorded and
    tracked throughout their lifecycle.

    Attributes:
        executor: HyperLiquidExecutor instance for placing orders
        db: SQLAlchemy database session
    """

    def __init__(
        self,
        executor: HyperLiquidExecutor,
        db_session: Session
    ):
        """Initialize order manager.

        Args:
            executor: HyperLiquid executor instance
            db_session: Database session for trade persistence

        Example:
            >>> executor = HyperLiquidExecutor(...)
            >>> db_session = Session()
            >>> manager = OrderManager(executor, db_session)
        """
        self.executor = executor
        self.db = db_session
        logger.info("OrderManager initialized")

    def execute_trade(
        self,
        agent_id: UUID,
        decision_id: UUID,
        coin: str,
        side: OrderSide,
        size: Decimal,
        price: Optional[Decimal] = None,
        order_type: str = OrderType.LIMIT,
        reduce_only: bool = False,
        client_order_id: Optional[str] = None
    ) -> Tuple[bool, Optional[AgentTrade], Optional[str]]:
        """Execute a trade based on AI decision.

        This method:
        1. Places the order on HyperLiquid exchange
        2. Creates a database record if successful
        3. Returns the trade record and status

        Args:
            agent_id: Trading agent ID
            decision_id: AI decision ID that triggered this trade
            coin: Trading pair symbol (BTC, ETH, etc)
            side: Order side (LONG or SHORT)
            size: Order size in base currency
            price: Limit price (None for market orders)
            order_type: "limit" or "market"
            reduce_only: If True, order can only reduce position
            client_order_id: Optional client-side order ID

        Returns:
            Tuple of (success, trade_record, error_message)
            - success: True if order placed and recorded successfully
            - trade_record: AgentTrade object if successful, None otherwise
            - error_message: Error description if failed, None otherwise

        Example:
            >>> success, trade, error = manager.execute_trade(
            ...     agent_id=uuid4(),
            ...     decision_id=uuid4(),
            ...     coin="BTC",
            ...     side=OrderSide.LONG,
            ...     size=Decimal("0.1"),
            ...     price=Decimal("50000")
            ... )
            >>> if success:
            ...     print(f"Trade ID: {trade.id}")
        """
        is_buy = (side == OrderSide.LONG)

        logger.info(
            f"Executing trade: {coin} {side.value.upper()} "
            f"{size} @ {price or 'MARKET'}"
        )

        # Execute order on exchange
        success, order_id, error = self.executor.place_order(
            coin=coin,
            is_buy=is_buy,
            size=size,
            price=price,
            order_type=order_type,
            reduce_only=reduce_only,
            client_order_id=client_order_id
        )

        if not success:
            logger.error(f"Order execution failed: {error}")
            return False, None, error

        # Create trade record in database
        trade = AgentTrade(
            agent_id=agent_id,
            decision_id=decision_id,
            coin=coin,
            side=side.value,
            size=size,
            entry_price=price,
            entry_time=datetime.utcnow(),
            status="open",
            hyperliquid_order_id=str(order_id)
        )

        try:
            self.db.add(trade)
            self.db.commit()
            logger.info(
                f"Trade recorded: {trade.id} (HyperLiquid OID: {order_id})"
            )
            return True, trade, None

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record trade in database: {e}")

            # Try to cancel the order since we couldn't record it
            try:
                self.executor.cancel_order(coin, order_id)
                logger.warning(f"Cancelled orphaned order {order_id}")
            except Exception as cancel_error:
                logger.error(f"Failed to cancel orphaned order: {cancel_error}")

            return False, None, str(e)

    def cancel_trade(
        self,
        trade_id: UUID
    ) -> Tuple[bool, Optional[str]]:
        """Cancel an open trade.

        This method:
        1. Looks up the trade in the database
        2. Cancels the order on the exchange
        3. Updates the trade status to "cancelled"

        Args:
            trade_id: Trade ID to cancel

        Returns:
            Tuple of (success, error_message)

        Example:
            >>> success, error = manager.cancel_trade(trade_id)
            >>> if not success:
            ...     print(f"Cancel failed: {error}")
        """
        trade = self.db.query(AgentTrade).filter_by(id=trade_id).first()

        if not trade:
            return False, "Trade not found"

        if trade.status != "open":
            return False, f"Cannot cancel trade with status: {trade.status}"

        # Cancel order on exchange
        order_id = int(trade.hyperliquid_order_id)
        success, error = self.executor.cancel_order(trade.coin, order_id)

        if not success:
            logger.error(f"Failed to cancel order {order_id}: {error}")
            return False, error

        # Update trade status
        trade.status = "cancelled"
        trade.exit_time = datetime.utcnow()

        try:
            self.db.commit()
            logger.info(f"Trade cancelled: {trade_id}")
            return True, None

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update cancelled trade: {e}")
            return False, str(e)

    def close_trade(
        self,
        trade_id: UUID,
        exit_price: Optional[Decimal] = None,
        realized_pnl: Optional[Decimal] = None,
        fees: Optional[Decimal] = None
    ) -> Tuple[bool, Optional[str]]:
        """Close a trade and update its status.

        This is called after a position has been closed (either manually
        or via stop-loss/take-profit). It updates the trade record with
        exit information.

        Args:
            trade_id: Trade ID to close
            exit_price: Exit price
            realized_pnl: Realized profit/loss
            fees: Trading fees paid

        Returns:
            Tuple of (success, error_message)

        Example:
            >>> success, error = manager.close_trade(
            ...     trade_id=uuid4(),
            ...     exit_price=Decimal("51000"),
            ...     realized_pnl=Decimal("100"),
            ...     fees=Decimal("5")
            ... )
        """
        trade = self.db.query(AgentTrade).filter_by(id=trade_id).first()

        if not trade:
            return False, "Trade not found"

        if trade.status == "closed":
            return False, "Trade already closed"

        # Update trade record
        trade.exit_price = exit_price
        trade.exit_time = datetime.utcnow()
        trade.realized_pnl = realized_pnl
        trade.fees = fees
        trade.status = "closed"

        try:
            self.db.commit()
            logger.info(
                f"Trade closed: {trade_id} "
                f"(PnL: {realized_pnl}, Fees: {fees})"
            )
            return True, None

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to close trade: {e}")
            return False, str(e)

    def get_trade(self, trade_id: UUID) -> Optional[AgentTrade]:
        """Get a trade record by ID.

        Args:
            trade_id: Trade ID

        Returns:
            AgentTrade object or None if not found
        """
        return self.db.query(AgentTrade).filter_by(id=trade_id).first()

    def get_agent_trades(
        self,
        agent_id: UUID,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentTrade]:
        """Get trades for a specific agent.

        Args:
            agent_id: Trading agent ID
            status: Filter by status ("open", "closed", "cancelled")
            limit: Maximum number of trades to return

        Returns:
            List of AgentTrade objects

        Example:
            >>> # Get all open trades
            >>> open_trades = manager.get_agent_trades(agent_id, status="open")
            >>> # Get last 50 trades
            >>> recent_trades = manager.get_agent_trades(agent_id, limit=50)
        """
        query = self.db.query(AgentTrade).filter_by(agent_id=agent_id)

        if status:
            query = query.filter_by(status=status)

        trades = query.order_by(AgentTrade.entry_time.desc()).limit(limit).all()

        return trades

    def get_open_trades(self, agent_id: UUID) -> List[AgentTrade]:
        """Get all open trades for an agent.

        Args:
            agent_id: Trading agent ID

        Returns:
            List of open AgentTrade objects
        """
        return self.get_agent_trades(agent_id, status="open")

    def get_trade_by_order_id(
        self,
        hyperliquid_order_id: str
    ) -> Optional[AgentTrade]:
        """Get trade by HyperLiquid order ID.

        Args:
            hyperliquid_order_id: HyperLiquid exchange order ID

        Returns:
            AgentTrade object or None
        """
        return self.db.query(AgentTrade).filter_by(
            hyperliquid_order_id=hyperliquid_order_id
        ).first()

    def batch_cancel_trades(
        self,
        trade_ids: List[UUID]
    ) -> Dict[UUID, Tuple[bool, Optional[str]]]:
        """Cancel multiple trades at once.

        Args:
            trade_ids: List of trade IDs to cancel

        Returns:
            Dictionary mapping trade_id to (success, error_message)

        Example:
            >>> results = manager.batch_cancel_trades([trade1_id, trade2_id])
            >>> for trade_id, (success, error) in results.items():
            ...     if not success:
            ...         print(f"Failed to cancel {trade_id}: {error}")
        """
        results = {}

        for trade_id in trade_ids:
            success, error = self.cancel_trade(trade_id)
            results[trade_id] = (success, error)

        return results

    def get_trade_statistics(
        self,
        agent_id: UUID
    ) -> Dict[str, any]:
        """Get trading statistics for an agent.

        Args:
            agent_id: Trading agent ID

        Returns:
            Dictionary with statistics:
            - total_trades: Total number of trades
            - open_trades: Number of open trades
            - closed_trades: Number of closed trades
            - cancelled_trades: Number of cancelled trades
            - total_pnl: Total realized PnL
            - total_fees: Total fees paid

        Example:
            >>> stats = manager.get_trade_statistics(agent_id)
            >>> print(f"Win rate: {stats['closed_trades']} / {stats['total_trades']}")
        """
        from sqlalchemy import func

        all_trades = self.db.query(AgentTrade).filter_by(agent_id=agent_id).all()

        total_trades = len(all_trades)
        open_trades = sum(1 for t in all_trades if t.status == "open")
        closed_trades = sum(1 for t in all_trades if t.status == "closed")
        cancelled_trades = sum(1 for t in all_trades if t.status == "cancelled")

        total_pnl = sum(
            (t.realized_pnl or Decimal("0"))
            for t in all_trades
            if t.status == "closed"
        )

        total_fees = sum(
            (t.fees or Decimal("0"))
            for t in all_trades
            if t.status == "closed"
        )

        return {
            "total_trades": total_trades,
            "open_trades": open_trades,
            "closed_trades": closed_trades,
            "cancelled_trades": cancelled_trades,
            "total_pnl": total_pnl,
            "total_fees": total_fees
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<OrderManager(executor={self.executor.get_address()})>"
