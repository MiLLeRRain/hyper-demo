"""Orchestrate trading execution flow.

This module coordinates the complete trading workflow from AI decision
to order execution, including:
- Risk validation
- Leverage management
- Position opening/closing
- Stop-loss and take-profit order placement
"""

import logging
from decimal import Decimal
from typing import Optional, Tuple, Dict
from uuid import UUID

from sqlalchemy.orm import Session

from ..infrastructure.database import DatabaseManager
from ..models.database import AgentDecision, TradingAgent
from ..risk.risk_manager import RiskManager
from .hyperliquid_executor import HyperLiquidExecutor, OrderType
from .order_manager import OrderManager, OrderSide
from .position_manager import PositionManager

logger = logging.getLogger(__name__)


class TradingOrchestrator:
    """Coordinate trading execution flow.

    The TradingOrchestrator is the central coordinator for trading operations.
    It orchestrates the interaction between:
    - Risk validation (RiskManager)
    - Order execution (OrderManager + HyperLiquidExecutor)
    - Position tracking (PositionManager)

    Attributes:
        executors: Map of account names to HyperLiquid executors
        default_executor: Fallback executor
        order_manager: OrderManager for order lifecycle management
        position_manager: PositionManager for position tracking
        risk_manager: RiskManager for risk validation
        db_manager: DatabaseManager instance
    """

    def __init__(
        self,
        executors: Dict[str, HyperLiquidExecutor],
        default_executor: HyperLiquidExecutor,
        order_manager: OrderManager,
        position_manager: PositionManager,
        risk_manager: RiskManager,
        db_manager: DatabaseManager
    ):
        """Initialize trading orchestrator.

        Args:
            executors: Map of account names to HyperLiquid executors
            default_executor: Fallback executor
            order_manager: Order manager instance
            position_manager: Position manager instance
            risk_manager: Risk manager instance
            db_manager: Database manager instance
        """
        self.executors = executors
        self.default_executor = default_executor
        self.order_manager = order_manager
        self.position_manager = position_manager
        self.risk_manager = risk_manager
        self.db_manager = db_manager
        logger.info(f"TradingOrchestrator initialized with {len(executors)} executors")

    def _get_executor(self, agent: TradingAgent) -> HyperLiquidExecutor:
        """Get the correct executor for an agent."""
        if not agent.exchange_account:
            return self.default_executor
        
        return self.executors.get(agent.exchange_account, self.default_executor)

    def execute_decision(
        self,
        agent_id: UUID,
        decision_id: UUID,
        session: Optional[Session] = None
    ) -> Tuple[bool, Optional[str]]:
        """Execute an AI trading decision.

        Args:
            agent_id: Trading agent ID
            decision_id: AI decision ID to execute
            session: Optional database session
        """
        if session:
            return self._execute_decision_internal(agent_id, decision_id, session)
        
        with self.db_manager.session_scope() as local_session:
            return self._execute_decision_internal(agent_id, decision_id, local_session)

    def _execute_decision_internal(
        self,
        agent_id: UUID,
        decision_id: UUID,
        session: Session
    ) -> Tuple[bool, Optional[str]]:
        # Load decision from database
        decision = session.query(AgentDecision).filter_by(id=decision_id).first()

        if not decision:
            logger.error(f"Decision not found: {decision_id}")
            return False, "Decision not found"

        # Load agent from database
        agent = session.query(TradingAgent).filter_by(id=agent_id).first()

        if not agent:
            logger.error(f"Agent not found: {agent_id}")
            return False, "Agent not found"

        # Get executor for this agent
        executor = self._get_executor(agent)
        logger.info(f"Using executor for account: {agent.exchange_account or 'default'}")

        logger.info(
            f"Executing decision: agent={agent.name}, "
            f"action={decision.action}, coin={decision.coin}"
        )

        # Handle different actions
        if decision.action == "HOLD":
            logger.info("Action is HOLD, no trade executed")
            return True, None

        elif decision.action == "CLOSE_POSITION":
            return self._close_position(agent_id, decision, executor, session)

        elif decision.action in ["OPEN_LONG", "OPEN_SHORT"]:
            return self._open_position(agent_id, agent, decision, executor, session)

        else:
            logger.error(f"Unknown action: {decision.action}")
            return False, f"Unknown action: {decision.action}"

    def _open_position(
        self,
        agent_id: UUID,
        agent: TradingAgent,
        decision: AgentDecision,
        executor: HyperLiquidExecutor,
        session: Session
    ) -> Tuple[bool, Optional[str]]:
        """Open a new position.

        Args:
            agent_id: Trading agent ID
            agent: TradingAgent database object
            decision: AgentDecision to execute
            executor: Executor to use
            session: Database session
        """
        logger.info(
            f"Opening position: {decision.action} {decision.coin} "
            f"${decision.size_usd} @ {decision.leverage}x"
        )

        # Step 1: Validate risk
        is_valid, reason = self.risk_manager.validate_trade(
            agent_id=agent_id,
            coin=decision.coin,
            size_usd=decision.size_usd,
            leverage=decision.leverage,
            executor=executor,
            session=session
        )

        if not is_valid:
            logger.warning(f"Trade rejected by risk manager for {decision.coin}: {reason}")
            return False, f"Risk check failed: {reason}"

        # Step 2: Set leverage on exchange
        success, error = executor.update_leverage(
            coin=decision.coin,
            leverage=decision.leverage,
            is_cross=True
        )

        if not success:
            logger.error(f"Failed to set leverage: {error}")
            return False, f"Failed to set leverage: {error}"

        # Step 3: Calculate position size in base currency
        # Note: calculate_position_size uses info_client, doesn't need executor
        size = self.position_manager.calculate_position_size(
            agent_id=agent_id,
            coin=decision.coin,
            target_value_usd=decision.size_usd,
            leverage=decision.leverage
        )

        logger.info(f"Calculated position size: {size} {decision.coin}")

        # Step 4: Determine order side
        side = OrderSide.LONG if decision.action == "OPEN_LONG" else OrderSide.SHORT

        # Step 5: Execute market order
        success, trade, error = self.order_manager.execute_trade(
            agent_id=agent_id,
            decision_id=decision.id,
            coin=decision.coin,
            side=side,
            size=size,
            price=None,  # Market order
            order_type=OrderType.MARKET,
            reduce_only=False,
            executor=executor,
            session=session
        )

        if not success:
            logger.error(f"Trade execution failed: {error}")
            return False, f"Trade execution failed: {error}"

        logger.info(f"Position opened successfully: trade_id={trade.id}")

        # Step 6: Place stop-loss order if specified
        if decision.stop_loss_price and float(decision.stop_loss_price) > 0:
            sl_success = self._place_stop_loss(agent_id, trade.id, decision, size, executor)
            if sl_success:
                logger.info(f"Stop-loss order placed at ${decision.stop_loss_price}")
            else:
                logger.warning("Failed to place stop-loss order")

        # Step 7: Place take-profit order if specified
        if decision.take_profit_price and float(decision.take_profit_price) > 0:
            tp_success = self._place_take_profit(agent_id, trade.id, decision, size, executor)
            if tp_success:
                logger.info(f"Take-profit order placed at ${decision.take_profit_price}")
            else:
                logger.warning("Failed to place take-profit order")

        return True, None

    def _close_position(
        self,
        agent_id: UUID,
        decision: AgentDecision,
        executor: HyperLiquidExecutor,
        session: Session
    ) -> Tuple[bool, Optional[str]]:
        """Close existing position.

        Args:
            agent_id: Trading agent ID
            decision: AgentDecision with CLOSE_POSITION action
            executor: Executor to use
            session: Database session
        """
        logger.info(f"Closing position: {decision.coin}")

        # Get open positions for the coin
        positions = self.position_manager.get_current_positions(agent_id, executor=executor, session=session)
        target_positions = [p for p in positions if p.coin == decision.coin]

        if not target_positions:
            logger.warning(f"No open position found for {decision.coin}")
            return False, f"No open position for {decision.coin}"

        position = target_positions[0]

        logger.info(
            f"Found position to close: {position.side} {position.size} {position.coin} "
            f"@ ${position.entry_price}"
        )

        # Execute market close (reduce-only)
        # Buy to close short, sell to close long
        is_buy = (position.side == "short")

        success, order_id, error = executor.place_order(
            coin=decision.coin,
            is_buy=is_buy,
            size=Decimal(str(position.size)),
            price=None,  # Market order
            order_type=OrderType.MARKET,
            reduce_only=True
        )

        if success:
            logger.info(
                f"Position closed successfully: {decision.coin} "
                f"(order_id: {order_id})"
            )
            return True, None
        else:
            logger.error(f"Close order failed: {error}")
            return False, f"Close failed: {error}"

    def _place_stop_loss(
        self,
        agent_id: UUID,
        trade_id: UUID,
        decision: AgentDecision,
        size: Decimal,
        executor: HyperLiquidExecutor
    ) -> bool:
        """Place stop-loss order.

        Args:
            agent_id: Trading agent ID
            trade_id: Trade ID to protect
            decision: AgentDecision with stop_loss_price
            size: Position size
            executor: Executor to use
        """
        logger.info(
            f"Placing stop-loss for trade {trade_id} "
            f"at ${decision.stop_loss_price}"
        )

        # Determine side (opposite of opening trade)
        is_buy = (decision.action == "OPEN_SHORT")
        
        success, order_id, error = executor.place_trigger_order(
            coin=decision.coin,
            is_buy=is_buy,
            size=size,
            trigger_price=Decimal(str(decision.stop_loss_price)),
            is_tp=False,
            reduce_only=True
        )

        if success:
            logger.info(f"Stop-loss placed successfully (OID: {order_id})")
            # TODO: Save order_id to database linked to trade
            return True
        else:
            logger.error(f"Failed to place stop-loss: {error}")
            return False

    def _place_take_profit(
        self,
        agent_id: UUID,
        trade_id: UUID,
        decision: AgentDecision,
        size: Decimal,
        executor: HyperLiquidExecutor
    ) -> bool:
        """Place take-profit order.

        Args:
            agent_id: Trading agent ID
            trade_id: Trade ID to close at profit
            decision: AgentDecision with take_profit_price
            size: Position size
            executor: Executor to use
        """
        logger.info(
            f"Placing take-profit for trade {trade_id} "
            f"at ${decision.take_profit_price}"
        )

        # Determine side (opposite of opening trade)
        is_buy = (decision.action == "OPEN_SHORT")

        success, order_id, error = executor.place_trigger_order(
            coin=decision.coin,
            is_buy=is_buy,
            size=size,
            trigger_price=Decimal(str(decision.take_profit_price)),
            is_tp=True,
            reduce_only=True
        )

        if success:
            logger.info(f"Take-profit placed successfully (OID: {order_id})")
            # TODO: Save order_id to database linked to trade
            return True
        else:
            logger.error(f"Failed to place take-profit: {error}")
            return False

    def get_execution_summary(
        self,
        agent_id: UUID,
        session: Optional[Session] = None
    ) -> dict:
        """Get trading execution summary for an agent.

        Args:
            agent_id: Trading agent ID
            session: Optional database session

        Returns:
            Dictionary with execution metrics
        """
        if session:
            return self._get_execution_summary_internal(agent_id, session)
        
        with self.db_manager.session_scope() as local_session:
            return self._get_execution_summary_internal(agent_id, local_session)

    def _get_execution_summary_internal(self, agent_id: UUID, session: Session) -> dict:
        # Get trade statistics
        trade_stats = self.order_manager.get_trade_statistics(agent_id, session=session)

        # Get account value
        try:
            account = self.position_manager.get_account_value(agent_id, session=session)
            account_value = account.account_value
            unrealized_pnl = account.unrealized_pnl
        except Exception as e:
            logger.error(f"Failed to get account value: {e}")
            account_value = 0.0
            unrealized_pnl = 0.0

        # Get position summary
        pos_summary = self.position_manager.get_position_summary(agent_id, session=session)

        return {
            "account_value": account_value,
            "unrealized_pnl": unrealized_pnl,
            "total_trades": trade_stats["total_trades"],
            "open_trades": trade_stats["open_trades"],
            "closed_trades": trade_stats["closed_trades"],
            "total_pnl": float(trade_stats["total_pnl"]),
            "total_fees": float(trade_stats["total_fees"]),
            "num_positions": pos_summary["num_positions"],
            "total_exposure": pos_summary["total_value"]
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<TradingOrchestrator(executors={len(self.executors)})>"
