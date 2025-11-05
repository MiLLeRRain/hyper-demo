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

from ..models.database import TradingAgent
from ..trading.position_manager import PositionManager

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
        db: SQLAlchemy database session
    """

    def __init__(
        self,
        position_manager: PositionManager,
        db_session: Session
    ):
        """Initialize risk manager.

        Args:
            position_manager: Position manager instance
            db_session: Database session

        Example:
            >>> pos_manager = PositionManager(client, db)
            >>> risk_manager = RiskManager(pos_manager, db)
        """
        self.position_manager = position_manager
        self.db = db_session
        logger.info("RiskManager initialized")

    def validate_trade(
        self,
        agent_id: UUID,
        coin: str,
        size_usd: Decimal,
        leverage: int
    ) -> Tuple[bool, Optional[str]]:
        """Validate trade against risk rules.

        This method performs comprehensive risk checks:
        1. Maximum leverage validation
        2. Position size limits (% of account)
        3. Margin sufficiency check
        4. Total exposure limits

        Args:
            agent_id: Trading agent ID
            coin: Trading pair symbol
            size_usd: Position size in USD
            leverage: Leverage to use

        Returns:
            Tuple of (is_valid, rejection_reason)
            - is_valid: True if trade passes all risk checks
            - rejection_reason: Description of why trade was rejected, or None

        Example:
            >>> valid, reason = risk_manager.validate_trade(
            ...     agent_id=uuid4(),
            ...     coin="BTC",
            ...     size_usd=Decimal("5000"),
            ...     leverage=10
            ... )
            >>> if not valid:
            ...     print(f"Trade rejected: {reason}")
        """
        # Get agent configuration
        agent = self.db.query(TradingAgent).filter_by(id=agent_id).first()

        if not agent:
            logger.error(f"Agent not found: {agent_id}")
            return False, "Agent not found"

        # Get account info
        try:
            account = self.position_manager.get_account_value(agent_id)
        except Exception as e:
            logger.error(f"Failed to get account value: {e}")
            return False, f"Failed to get account info: {str(e)}"

        # Rule 1: Check max leverage
        if leverage > agent.max_leverage:
            logger.warning(
                f"Leverage {leverage}x exceeds max {agent.max_leverage}x "
                f"for agent {agent_id}"
            )
            return False, f"Leverage {leverage}x exceeds max {agent.max_leverage}x"

        # Rule 2: Check max position size (% of account)
        max_position_value = float(account.account_value) * (float(agent.max_position_size) / 100)
        if float(size_usd) > max_position_value:
            logger.warning(
                f"Position ${size_usd} exceeds max ${max_position_value:.2f} "
                f"({agent.max_position_size}% of account)"
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
                f"Insufficient margin: need ${required_margin:.2f}, "
                f"have ${available_margin:.2f}"
            )
            return False, (
                f"Insufficient margin: need ${required_margin:.2f}, "
                f"have ${available_margin:.2f}"
            )

        # Rule 4: Check max total exposure (80% of account value)
        # Calculate current total exposure
        current_exposure = self.position_manager.get_total_exposure(agent_id)
        new_total_exposure = current_exposure + float(size_usd)
        max_total_exposure = account.account_value * 0.8  # 80% max

        if new_total_exposure > max_total_exposure:
            logger.warning(
                f"Total exposure ${new_total_exposure:.2f} exceeds "
                f"max ${max_total_exposure:.2f}"
            )
            return False, (
                f"Total exposure ${new_total_exposure:.2f} exceeds "
                f"max ${max_total_exposure:.2f}"
            )

        logger.info(
            f"Trade validation passed: {coin} ${size_usd} @ {leverage}x "
            f"(margin: ${required_margin:.2f}, exposure: ${new_total_exposure:.2f})"
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

        Example:
            >>> # Long position: stop loss below entry
            >>> sl_price = risk_manager.calculate_stop_loss_price(
            ...     Decimal("50000"), Decimal("2.0"), is_long=True
            ... )
            >>> print(sl_price)  # 49000.0 (2% below 50000)

            >>> # Short position: stop loss above entry
            >>> sl_price = risk_manager.calculate_stop_loss_price(
            ...     Decimal("50000"), Decimal("2.0"), is_long=False
            ... )
            >>> print(sl_price)  # 51000.0 (2% above 50000)
        """
        if is_long:
            # Long: stop loss below entry (price decreases)
            stop_loss = entry_price * (1 - stop_loss_pct / 100)
        else:
            # Short: stop loss above entry (price increases)
            stop_loss = entry_price * (1 + stop_loss_pct / 100)

        logger.debug(
            f"Calculated stop loss: entry=${entry_price}, "
            f"sl_pct={stop_loss_pct}%, is_long={is_long} -> ${stop_loss}"
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

        Example:
            >>> # Long position: take profit above entry
            >>> tp_price = risk_manager.calculate_take_profit_price(
            ...     Decimal("50000"), Decimal("5.0"), is_long=True
            ... )
            >>> print(tp_price)  # 52500.0 (5% above 50000)

            >>> # Short position: take profit below entry
            >>> tp_price = risk_manager.calculate_take_profit_price(
            ...     Decimal("50000"), Decimal("5.0"), is_long=False
            ... )
            >>> print(tp_price)  # 47500.0 (5% below 50000)
        """
        if is_long:
            # Long: take profit above entry (price increases)
            take_profit = entry_price * (1 + take_profit_pct / 100)
        else:
            # Short: take profit below entry (price decreases)
            take_profit = entry_price * (1 - take_profit_pct / 100)

        logger.debug(
            f"Calculated take profit: entry=${entry_price}, "
            f"tp_pct={take_profit_pct}%, is_long={is_long} -> ${take_profit}"
        )
        return take_profit

    def check_liquidation_risk(
        self,
        agent_id: UUID,
        threshold_pct: Decimal = Decimal("20")
    ) -> Tuple[bool, List[str]]:
        """Check if any positions are close to liquidation.

        This method monitors all open positions and warns if any are
        within the threshold distance from their liquidation price.

        Args:
            agent_id: Trading agent ID
            threshold_pct: Warning threshold (% distance from liquidation)

        Returns:
            Tuple of (at_risk, warnings)
            - at_risk: True if any position is within threshold of liquidation
            - warnings: List of warning messages for at-risk positions

        Example:
            >>> at_risk, warnings = risk_manager.check_liquidation_risk(
            ...     agent_id, threshold_pct=Decimal("20")
            ... )
            >>> if at_risk:
            ...     for warning in warnings:
            ...         print(warning)
        """
        try:
            positions = self.position_manager.get_current_positions(agent_id)
        except Exception as e:
            logger.error(f"Failed to get positions for liquidation check: {e}")
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
                f"Agent {agent_id} has {len(warnings)} position(s) at liquidation risk"
            )
        else:
            logger.debug(f"No liquidation risk for agent {agent_id}")

        return at_risk, warnings

    def get_max_position_size(
        self,
        agent_id: UUID,
        leverage: int = 1
    ) -> Decimal:
        """Calculate maximum allowed position size.

        This considers the agent's max_position_size parameter and
        current account value.

        Args:
            agent_id: Trading agent ID
            leverage: Leverage to be used

        Returns:
            Maximum position size in USD

        Example:
            >>> max_size = risk_manager.get_max_position_size(agent_id, leverage=10)
            >>> print(f"Max position: ${max_size}")
        """
        agent = self.db.query(TradingAgent).filter_by(id=agent_id).first()
        if not agent:
            logger.error(f"Agent not found: {agent_id}")
            return Decimal("0")

        try:
            account = self.position_manager.get_account_value(agent_id)
            max_size = Decimal(str(account.account_value)) * agent.max_position_size / 100
            logger.debug(
                f"Max position size for agent {agent_id}: ${max_size} "
                f"({agent.max_position_size}% of ${account.account_value})"
            )
            return max_size
        except Exception as e:
            logger.error(f"Failed to calculate max position size: {e}")
            return Decimal("0")

    def __repr__(self) -> str:
        """String representation."""
        return "<RiskManager>"
