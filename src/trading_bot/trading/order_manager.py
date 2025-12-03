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
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from sqlalchemy.orm import Session

from ..infrastructure.database import DatabaseManager
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
        db_manager: DatabaseManager instance
    """

    def __init__(
        self,
        executor: HyperLiquidExecutor,
        db_manager: DatabaseManager
    ):
        """Initialize order manager.

        Args:
            executor: HyperLiquid executor instance
            db_manager: Database manager instance

        Example:
            >>> executor = HyperLiquidExecutor(...)
            >>> db_manager = DatabaseManager(...)
            >>> manager = OrderManager(executor, db_manager)
        """
        self.executor = executor
        self.db_manager = db_manager
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
        client_order_id: Optional[str] = None,
        executor: Optional[HyperLiquidExecutor] = None,
        session: Optional[Session] = None
    ) -> Tuple[bool, Optional[AgentTrade], Optional[str]]:
        """Execute a trade based on AI decision.

        Args:
            executor: Specific executor to use (overrides default)
            session: Optional database session
            ...
        """
        # pylint: disable=too-many-positional-arguments
        # Use specific executor if provided, else default
        active_executor = executor or self.executor

        is_buy = side == OrderSide.LONG

        logger.info(
            "Executing trade: %s %s %s @ %s (Executor: %s)",
            coin, side.value.upper(), size, price or 'MARKET',
            active_executor.get_address()
        )

        # Execute order on exchange
        success, order_id, error = active_executor.place_order(
            coin=coin,
            is_buy=is_buy,
            size=size,
            price=price,
            order_type=order_type,
            reduce_only=reduce_only,
            client_order_id=client_order_id
        )

        if not success:
            logger.error("Order execution failed: %s", error)
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
            if session:
                session.add(trade)
                session.flush()
            else:
                with self.db_manager.session_scope() as local_session:
                    local_session.add(trade)
                    # session_scope commits on exit
                    # We need to refresh/expunge to use it outside
                    local_session.flush()
                    local_session.refresh(trade)
                    local_session.expunge(trade)

            logger.info(
                "Trade recorded: %s (HyperLiquid OID: %s)",
                trade.id, order_id
            )
            return True, trade, None

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to record trade in database: %s", e)

            # Try to cancel the order since we couldn't record it
            try:
                active_executor.cancel_order(coin, order_id)
                logger.warning("Cancelled orphaned order %s", order_id)
            except Exception as cancel_error:  # pylint: disable=broad-exception-caught
                logger.error("Failed to cancel orphaned order: %s", cancel_error)

            return False, None, str(e)

    def cancel_trade(
        self,
        trade_id: UUID,
        executor: Optional[HyperLiquidExecutor] = None,
        session: Optional[Session] = None
    ) -> Tuple[bool, Optional[str]]:
        """Cancel an open trade.

        Args:
            trade_id: Trade ID to cancel
            executor: Specific executor to use
            session: Optional database session
        """
        if session:
            return self._cancel_trade_internal(trade_id, executor, session)

        try:
            with self.db_manager.session_scope() as local_session:
                return self._cancel_trade_internal(trade_id, executor, local_session)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to cancel trade: %s", e)
            return False, str(e)

    def _cancel_trade_internal(
        self,
        trade_id: UUID,
        executor: Optional[HyperLiquidExecutor],
        session: Session
    ) -> Tuple[bool, Optional[str]]:
        """Internal implementation of cancel_trade."""
        trade = session.query(AgentTrade).filter_by(id=trade_id).first()

        if not trade:
            return False, "Trade not found"

        if trade.status != "open":
            return False, f"Cannot cancel trade with status: {trade.status}"

        # Use specific executor if provided, else default
        active_executor = executor or self.executor

        # Cancel order on exchange
        order_id = int(trade.hyperliquid_order_id)
        success, error = active_executor.cancel_order(trade.coin, order_id)

        if not success:
            logger.error("Failed to cancel order %s: %s", order_id, error)
            return False, error

        # Update trade status
        trade.status = "cancelled"
        trade.exit_time = datetime.utcnow()

        logger.info("Trade cancelled: %s", trade_id)
        return True, None

    def close_trade(
        self,
        trade_id: UUID,
        exit_price: Optional[Decimal] = None,
        realized_pnl: Optional[Decimal] = None,
        fees: Optional[Decimal] = None,
        session: Optional[Session] = None
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
            session: Optional database session

        Returns:
            Tuple of (success, error_message)
        """
        # pylint: disable=too-many-positional-arguments
        if session:
            return self._close_trade_internal(
                trade_id, exit_price, realized_pnl, fees, session
            )

        try:
            with self.db_manager.session_scope() as local_session:
                return self._close_trade_internal(
                    trade_id, exit_price, realized_pnl, fees, local_session
                )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to close trade: %s", e)
            return False, str(e)

    def _close_trade_internal(
        self,
        trade_id: UUID,
        exit_price: Optional[Decimal],
        realized_pnl: Optional[Decimal],
        fees: Optional[Decimal],
        session: Session
    ) -> Tuple[bool, Optional[str]]:
        """Internal implementation of close_trade."""
        # pylint: disable=too-many-positional-arguments
        trade = session.query(AgentTrade).filter_by(id=trade_id).first()

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

        logger.info(
            "Trade closed: %s (PnL: %s, Fees: %s)",
            trade_id, realized_pnl, fees
        )
        return True, None

    def get_trade(
        self,
        trade_id: UUID,
        session: Optional[Session] = None
    ) -> Optional[AgentTrade]:
        """Get a trade record by ID.

        Args:
            trade_id: Trade ID
            session: Optional database session

        Returns:
            AgentTrade object or None if not found
        """
        if session:
            return session.query(AgentTrade).filter_by(id=trade_id).first()

        with self.db_manager.session_scope() as local_session:
            trade = local_session.query(AgentTrade).filter_by(id=trade_id).first()
            if trade:
                local_session.expunge(trade)
            return trade

    def get_agent_trades(
        self,
        agent_id: UUID,
        status: Optional[str] = None,
        limit: int = 100,
        session: Optional[Session] = None
    ) -> List[AgentTrade]:
        """Get trades for a specific agent.

        Args:
            agent_id: Trading agent ID
            status: Filter by status ("open", "closed", "cancelled")
            limit: Maximum number of trades to return
            session: Optional database session

        Returns:
            List of AgentTrade objects
        """
        if session:
            return self._get_agent_trades_internal(agent_id, status, limit, session)

        with self.db_manager.session_scope() as local_session:
            trades = self._get_agent_trades_internal(
                agent_id, status, limit, local_session
            )
            for trade in trades:
                local_session.expunge(trade)
            return trades

    def _get_agent_trades_internal(
        self,
        agent_id: UUID,
        status: Optional[str],
        limit: int,
        session: Session
    ) -> List[AgentTrade]:
        query = session.query(AgentTrade).filter_by(agent_id=agent_id)

        if status:
            query = query.filter_by(status=status)

        trades = query.order_by(AgentTrade.entry_time.desc()).limit(limit).all()
        return trades

    def get_open_trades(
        self,
        agent_id: UUID,
        session: Optional[Session] = None
    ) -> List[AgentTrade]:
        """Get all open trades for an agent.

        Args:
            agent_id: Trading agent ID
            session: Optional database session

        Returns:
            List of open AgentTrade objects
        """
        return self.get_agent_trades(agent_id, status="open", session=session)

    def get_trade_by_order_id(
        self,
        hyperliquid_order_id: str,
        session: Optional[Session] = None
    ) -> Optional[AgentTrade]:
        """Get trade by HyperLiquid order ID.

        Args:
            hyperliquid_order_id: HyperLiquid exchange order ID
            session: Optional database session

        Returns:
            AgentTrade object or None
        """
        if session:
            return session.query(AgentTrade).filter_by(
                hyperliquid_order_id=hyperliquid_order_id
            ).first()

        with self.db_manager.session_scope() as local_session:
            trade = local_session.query(AgentTrade).filter_by(
                hyperliquid_order_id=hyperliquid_order_id
            ).first()
            if trade:
                local_session.expunge(trade)
            return trade

    def batch_cancel_trades(
        self,
        trade_ids: List[UUID],
        session: Optional[Session] = None
    ) -> Dict[UUID, Tuple[bool, Optional[str]]]:
        """Cancel multiple trades at once.

        Args:
            trade_ids: List of trade IDs to cancel
            session: Optional database session

        Returns:
            Dictionary mapping trade_id to (success, error_message)
        """
        results = {}

        for trade_id in trade_ids:
            success, error = self.cancel_trade(trade_id, session=session)
            results[trade_id] = (success, error)

        return results

    def get_trade_statistics(
        self,
        agent_id: UUID,
        session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Get trading statistics for an agent.

        Args:
            agent_id: Trading agent ID
            session: Optional database session

        Returns:
            Dictionary with statistics
        """
        if session:
            return self._get_trade_statistics_internal(agent_id, session)

        with self.db_manager.session_scope() as local_session:
            return self._get_trade_statistics_internal(agent_id, local_session)

    def _get_trade_statistics_internal(
        self,
        agent_id: UUID,
        session: Session
    ) -> Dict[str, Any]:
        all_trades = session.query(AgentTrade).filter_by(agent_id=agent_id).all()

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
