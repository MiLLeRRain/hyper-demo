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
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

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
        executor: HyperLiquidExecutor for exchange operations
        order_manager: OrderManager for order lifecycle management
        position_manager: PositionManager for position tracking
        risk_manager: RiskManager for risk validation
        db: SQLAlchemy database session
    """

    def __init__(
        self,
        executor: HyperLiquidExecutor,
        order_manager: OrderManager,
        position_manager: PositionManager,
        risk_manager: RiskManager,
        db_session: Session
    ):
        """Initialize trading orchestrator.

        Args:
            executor: HyperLiquid executor instance
            order_manager: Order manager instance
            position_manager: Position manager instance
            risk_manager: Risk manager instance
            db_session: Database session

        Example:
            >>> executor = HyperLiquidExecutor(...)
            >>> order_mgr = OrderManager(executor, db)
            >>> pos_mgr = PositionManager(info_client, db)
            >>> risk_mgr = RiskManager(pos_mgr, db)
            >>> orchestrator = TradingOrchestrator(
            ...     executor, order_mgr, pos_mgr, risk_mgr, db
            ... )
        """
        self.executor = executor
        self.order_manager = order_manager
        self.position_manager = position_manager
        self.risk_manager = risk_manager
        self.db = db_session
        logger.info("TradingOrchestrator initialized")

    def execute_decision(
        self,
        agent_id: UUID,
        decision_id: UUID
    ) -> Tuple[bool, Optional[str]]:
        """Execute an AI trading decision.

        This is the main entry point for executing trading decisions.
        It handles all decision types: HOLD, OPEN_LONG, OPEN_SHORT, CLOSE_POSITION.

        Workflow:
        1. Load decision and agent from database
        2. Route to appropriate handler based on action
        3. Execute trade with risk validation
        4. Place stop-loss and take-profit orders if specified

        Args:
            agent_id: Trading agent ID
            decision_id: AI decision ID to execute

        Returns:
            Tuple of (success, error_message)
            - success: True if decision executed successfully
            - error_message: Error description if failed, None otherwise

        Example:
            >>> success, error = orchestrator.execute_decision(
            ...     agent_id=uuid4(),
            ...     decision_id=uuid4()
            ... )
            >>> if success:
            ...     print("Decision executed successfully")
            ... else:
            ...     print(f"Failed: {error}")
        """
        # Load decision from database
        decision = self.db.query(AgentDecision).filter_by(id=decision_id).first()

        if not decision:
            logger.error(f"Decision not found: {decision_id}")
            return False, "Decision not found"

        # Load agent from database
        agent = self.db.query(TradingAgent).filter_by(id=agent_id).first()

        if not agent:
            logger.error(f"Agent not found: {agent_id}")
            return False, "Agent not found"

        logger.info(
            f"Executing decision: agent={agent.name}, "
            f"action={decision.action}, coin={decision.coin}"
        )

        # Handle different actions
        if decision.action == "HOLD":
            logger.info("Action is HOLD, no trade executed")
            return True, None

        elif decision.action == "CLOSE_POSITION":
            return self._close_position(agent_id, decision)

        elif decision.action in ["OPEN_LONG", "OPEN_SHORT"]:
            return self._open_position(agent_id, agent, decision)

        else:
            logger.error(f"Unknown action: {decision.action}")
            return False, f"Unknown action: {decision.action}"

    def _open_position(
        self,
        agent_id: UUID,
        agent: TradingAgent,
        decision: AgentDecision
    ) -> Tuple[bool, Optional[str]]:
        """Open a new position.

        This method:
        1. Validates trade against risk rules
        2. Sets leverage on exchange
        3. Calculates position size
        4. Executes market order
        5. Places stop-loss and take-profit orders

        Args:
            agent_id: Trading agent ID
            agent: TradingAgent database object
            decision: AgentDecision to execute

        Returns:
            Tuple of (success, error_message)
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
            leverage=decision.leverage
        )

        if not is_valid:
            logger.warning(f"Trade rejected by risk manager: {reason}")
            return False, f"Risk check failed: {reason}"

        # Step 2: Set leverage on exchange
        success, error = self.executor.update_leverage(
            coin=decision.coin,
            leverage=decision.leverage,
            is_cross=True
        )

        if not success:
            logger.error(f"Failed to set leverage: {error}")
            return False, f"Failed to set leverage: {error}"

        # Step 3: Calculate position size in base currency
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
            reduce_only=False
        )

        if not success:
            logger.error(f"Trade execution failed: {error}")
            return False, f"Trade execution failed: {error}"

        logger.info(f"Position opened successfully: trade_id={trade.id}")

        # Step 6: Place stop-loss order if specified
        if decision.stop_loss_price and float(decision.stop_loss_price) > 0:
            sl_success = self._place_stop_loss(agent_id, trade.id, decision, size)
            if sl_success:
                logger.info(f"Stop-loss order placed at ${decision.stop_loss_price}")
            else:
                logger.warning("Failed to place stop-loss order")

        # Step 7: Place take-profit order if specified
        if decision.take_profit_price and float(decision.take_profit_price) > 0:
            tp_success = self._place_take_profit(agent_id, trade.id, decision, size)
            if tp_success:
                logger.info(f"Take-profit order placed at ${decision.take_profit_price}")
            else:
                logger.warning("Failed to place take-profit order")

        return True, None

    def _close_position(
        self,
        agent_id: UUID,
        decision: AgentDecision
    ) -> Tuple[bool, Optional[str]]:
        """Close existing position.

        This method:
        1. Finds the open position for the coin
        2. Executes a reduce-only market order to close
        3. Updates trade record with exit information

        Args:
            agent_id: Trading agent ID
            decision: AgentDecision with CLOSE_POSITION action

        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"Closing position: {decision.coin}")

        # Get open positions for the coin
        positions = self.position_manager.get_current_positions(agent_id)
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

        success, order_id, error = self.executor.place_order(
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
        size: Decimal
    ) -> bool:
        """Place stop-loss order.

        Args:
            agent_id: Trading agent ID
            trade_id: Trade ID to protect
            decision: AgentDecision with stop_loss_price
            size: Position size

        Returns:
            True if stop-loss placed successfully
        """
        logger.info(
            f"Placing stop-loss for trade {trade_id} "
            f"at ${decision.stop_loss_price}"
        )

        # Determine side (opposite of opening trade)
        is_buy = (decision.action == "OPEN_SHORT")
        
        success, order_id, error = self.executor.place_trigger_order(
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
        size: Decimal
    ) -> bool:
        """Place take-profit order.

        Args:
            agent_id: Trading agent ID
            trade_id: Trade ID to close at profit
            decision: AgentDecision with take_profit_price
            size: Position size

        Returns:
            True if take-profit placed successfully
        """
        logger.info(
            f"Placing take-profit for trade {trade_id} "
            f"at ${decision.take_profit_price}"
        )

        # Determine side (opposite of opening trade)
        is_buy = (decision.action == "OPEN_SHORT")

        success, order_id, error = self.executor.place_trigger_order(
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

    def get_execution_summary(self, agent_id: UUID) -> dict:
        """Get trading execution summary for an agent.

        Args:
            agent_id: Trading agent ID

        Returns:
            Dictionary with execution metrics

        Example:
            >>> summary = orchestrator.get_execution_summary(agent_id)
            >>> print(f"Total trades: {summary['total_trades']}")
        """
        # Get trade statistics
        trade_stats = self.order_manager.get_trade_statistics(agent_id)

        # Get account value
        try:
            account = self.position_manager.get_account_value(agent_id)
            account_value = account.account_value
            unrealized_pnl = account.unrealized_pnl
        except Exception as e:
            logger.error(f"Failed to get account value: {e}")
            account_value = 0.0
            unrealized_pnl = 0.0

        # Get position summary
        pos_summary = self.position_manager.get_position_summary(agent_id)

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
        return f"<TradingOrchestrator(executor={self.executor.get_address()})>"
