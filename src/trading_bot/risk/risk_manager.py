"""Risk management and validation.

This module provides risk management functionality including:
- Pre-trade risk validation
- Position size limits
- Leverage checks
- Margin sufficiency checks
- Stop-loss and take-profit calculations
- Liquidation risk monitoring
"""

import logging
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from ..infrastructure.database import DatabaseManager
from ..models.database import TradingAgent
from ..trading.position_manager import PositionManager
from ..trading.hyperliquid_executor import HyperLiquidExecutor

logger = logging.getLogger(__name__)


class RiskManager:
    """Enforce risk management rules.

    The RiskManager validates trades against configured risk parameters
    before execution. It ensures trades comply with:
    - Maximum leverage limits
    - Position size constraints
    - Margin requirements
    - Total exposure limits

    Attributes:
        position_manager: PositionManager instance for account queries
        db_manager: DatabaseManager instance
    """

    def __init__(
        self,
        position_manager: PositionManager,
        db_manager: DatabaseManager
    ):
        """Initialize risk manager.

        Args:
            position_manager: Position manager instance
            db_manager: Database manager instance

        Example:
            >>> pos_manager = PositionManager(client, db_manager)
            >>> risk_manager = RiskManager(pos_manager, db_manager)
        """
        self.position_manager = position_manager
        self.db_manager = db_manager
        logger.info("RiskManager initialized")

    def validate_trade(
        self,
        agent_id: UUID,
        coin: str,
        size_usd: Decimal,
        leverage: int,
        executor: Optional[HyperLiquidExecutor] = None,
        session: Optional[Session] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate trade against risk rules.

        Args:
            agent_id: Trading agent ID
            coin: Trading pair symbol
            size_usd: Position size in USD
            leverage: Leverage to use
            executor: Specific executor to use
            session: Optional database session
        """
        # pylint: disable=too-many-positional-arguments
        if session:
            return self._validate_trade_internal(
                agent_id, coin, size_usd, leverage, executor, session
            )

        with self.db_manager.session_scope() as local_session:
            return self._validate_trade_internal(
                agent_id, coin, size_usd, leverage, executor, local_session
            )

    def _validate_trade_internal(
        self,
        agent_id: UUID,
        coin: str,
        size_usd: Decimal,
        leverage: int,
        executor: Optional[HyperLiquidExecutor],
        session: Session
    ) -> Tuple[bool, Optional[str]]:
        # pylint: disable=too-many-positional-arguments
        # Get agent configuration
        agent = session.query(TradingAgent).filter_by(id=agent_id).first()

        if not agent:
            logger.error("Agent not found: %s", agent_id)
            return False, "Agent not found"

        # Get account info
        try:
            account = self.position_manager.get_account_value(
                agent_id, executor=executor, session=session
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to get account value: %s", e)
            return False, f"Failed to get account info: {str(e)}"

        # Rule 1: Check max leverage
        if leverage > agent.max_leverage:
            logger.warning(
                "Leverage %sx exceeds max %sx for agent %s",
                leverage, agent.max_leverage, agent_id
            )
            return False, f"Leverage {leverage}x exceeds max {agent.max_leverage}x"

        # Rule 2: Check max position size (% of account)
        max_position_value = float(account.account_value) * (float(agent.max_position_size) / 100)
        if float(size_usd) > max_position_value:
            logger.warning(
                "Position $%s exceeds max $%.2f (%s%% of account)",
                size_usd, max_position_value, agent.max_position_size
            )
            return False, (
                f"Position ${size_usd} exceeds max ${max_position_value:.2f} "
                f"({agent.max_position_size}% of account)"
            )

        # Rule 3: Check available margin
        required_margin = float(size_usd) / leverage
        available_margin = account.withdrawable

        if required_margin > available_margin:
            logger.warning(
                "Insufficient margin: need $%.2f, have $%.2f",
                required_margin, available_margin
            )
            return False, (
                f"Insufficient margin: need ${required_margin:.2f}, "
                f"have ${available_margin:.2f}"
            )

        logger.info(
            "Trade validation passed: %s $%s @ %sx (margin: $%.2f)",
            coin, size_usd, leverage, required_margin
        )
        return True, None

    def calculate_stop_loss_price(
        self,
        entry_price: Decimal,
        stop_loss_pct: Decimal,
        is_long: bool
    ) -> Decimal:
        """Calculate stop loss price.

        Args:
            entry_price: Entry price
            stop_loss_pct: Stop loss percentage (e.g., 2.0 for 2%)
            is_long: True for long position, False for short

        Returns:
            Stop loss price
        """
        if is_long:
            # Long: stop loss below entry (price decreases)
            stop_loss = entry_price * (1 - stop_loss_pct / 100)
        else:
            # Short: stop loss above entry (price increases)
            stop_loss = entry_price * (1 + stop_loss_pct / 100)

        logger.debug(
            "Calculated stop loss: entry=$%s, sl_pct=%s%%, is_long=%s -> $%s",
            entry_price, stop_loss_pct, is_long, stop_loss
        )
        return stop_loss

    def calculate_take_profit_price(
        self,
        entry_price: Decimal,
        take_profit_pct: Decimal,
        is_long: bool
    ) -> Decimal:
        """Calculate take profit price.

        Args:
            entry_price: Entry price
            take_profit_pct: Take profit percentage (e.g., 5.0 for 5%)
            is_long: True for long position, False for short

        Returns:
            Take profit price
        """
        if is_long:
            # Long: take profit above entry (price increases)
            take_profit = entry_price * (1 + take_profit_pct / 100)
        else:
            # Short: take profit below entry (price decreases)
            take_profit = entry_price * (1 - take_profit_pct / 100)

        logger.debug(
            "Calculated take profit: entry=$%s, tp_pct=%s%%, is_long=%s -> $%s",
            entry_price, take_profit_pct, is_long, take_profit
        )
        return take_profit

    def check_liquidation_risk(
        self,
        agent_id: UUID,
        threshold_pct: Decimal = Decimal("20"),
        executor: Optional[HyperLiquidExecutor] = None,
        session: Optional[Session] = None
    ) -> Tuple[bool, List[str]]:
        """Check if any positions are close to liquidation.

        Args:
            agent_id: Trading agent ID
            threshold_pct: Warning threshold (% distance from liquidation)
            executor: Specific executor to use
            session: Optional database session
        """
        try:
            positions = self.position_manager.get_current_positions(
                agent_id, executor=executor, session=session
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to get positions for liquidation check: %s", e)
            return False, []

        warnings = []
        at_risk = False

        for pos in positions:
            # Calculate distance to liquidation
            if pos.side == "long":
                # Long: liquidation when price drops to liquidation_price
                liq_distance_pct = (
                    (pos.mark_price - pos.liquidation_price) / pos.mark_price
                ) * 100
            else:
                # Short: liquidation when price rises to liquidation_price
                liq_distance_pct = (
                    (pos.liquidation_price - pos.mark_price) / pos.mark_price
                ) * 100

            if liq_distance_pct < float(threshold_pct):
                at_risk = True
                warning_msg = (
                    f"{pos.coin} {pos.side}: {liq_distance_pct:.2f}% from liquidation "
                    f"(current: ${pos.mark_price:.2f}, liq: ${pos.liquidation_price:.2f})"
                )
                warnings.append(warning_msg)
                logger.warning(warning_msg)

        if at_risk:
            logger.warning(
                "Agent %s has %d position(s) at liquidation risk",
                agent_id, len(warnings)
            )
        else:
            logger.debug("No liquidation risk for agent %s", agent_id)

        return at_risk, warnings

    def get_max_position_size(
        self,
        agent_id: UUID,
        leverage: int = 1,
        executor: Optional[HyperLiquidExecutor] = None,
        session: Optional[Session] = None
    ) -> Decimal:
        """Calculate maximum allowed position size.

        Args:
            agent_id: Trading agent ID
            leverage: Leverage to be used
            executor: Specific executor to use
            session: Optional database session
        """
        if session:
            return self._get_max_position_size_internal(
                agent_id, leverage, executor, session
            )

        with self.db_manager.session_scope() as local_session:
            return self._get_max_position_size_internal(
                agent_id, leverage, executor, local_session
            )

    def _get_max_position_size_internal(
        self,
        agent_id: UUID,
        leverage: int,
        executor: Optional[HyperLiquidExecutor],
        session: Session
    ) -> Decimal:
        # pylint: disable=unused-argument
        agent = session.query(TradingAgent).filter_by(id=agent_id).first()
        if not agent:
            logger.error("Agent not found: %s", agent_id)
            return Decimal("0")

        try:
            account = self.position_manager.get_account_value(
                agent_id, executor=executor, session=session
            )
            max_size = Decimal(str(account.account_value)) * agent.max_position_size / 100
            logger.debug(
                "Max position size for agent %s: $%s (%s%% of $%s)",
                agent_id, max_size, agent.max_position_size, account.account_value
            )
            return max_size
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to calculate max position size: %s", e)
            return Decimal("0")

    def __repr__(self) -> str:
        """String representation."""
        return "<RiskManager>"
