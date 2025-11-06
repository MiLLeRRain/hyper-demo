"""Position tracking and management.

This module manages position tracking, account value calculation,
and position-related queries for trading agents.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.database import AgentTrade, TradingAgent
from ..models.market_data import Position, AccountInfo
from ..data.hyperliquid_client import HyperliquidClient

logger = logging.getLogger(__name__)


class PositionManager:
    """Track and manage agent positions.

    The PositionManager provides real-time position tracking by combining
    database records with current market prices. It calculates unrealized P&L,
    account values, and other position metrics.

    Attributes:
        info_client: HyperLiquid Info API client for market data
        db: SQLAlchemy database session
    """

    def __init__(
        self,
        info_client: HyperliquidClient,
        db_session: Session
    ):
        """Initialize position manager.

        Args:
            info_client: HyperLiquid Info API client
            db_session: Database session

        Example:
            >>> client = HyperliquidClient("https://api.hyperliquid.xyz")
            >>> db_session = Session()
            >>> manager = PositionManager(client, db_session)
        """
        self.info_client = info_client
        self.db = db_session
        logger.info("PositionManager initialized")

    def get_current_positions(self, agent_id: UUID) -> List[Position]:
        """Get current open positions for an agent.

        This method:
        1. Queries all open trades from database
        2. Fetches current market prices
        3. Calculates unrealized P&L
        4. Returns Position objects with current data

        Args:
            agent_id: Trading agent ID

        Returns:
            List of Position objects with current market data

        Example:
            >>> positions = manager.get_current_positions(agent_id)
            >>> for pos in positions:
            ...     print(f"{pos.coin}: {pos.unrealized_pnl} USD")
        """
        # Query open trades from database
        open_trades = self.db.query(AgentTrade).filter_by(
            agent_id=agent_id,
            status="open"
        ).all()

        positions = []
        for trade in open_trades:
            try:
                # Get current market price
                current_price = self.info_client.get_price(trade.coin)

                # Calculate unrealized PnL
                if trade.side == "long":
                    # Long: profit when price goes up
                    unrealized_pnl = trade.size * (current_price - trade.entry_price)
                else:  # short
                    # Short: profit when price goes down
                    unrealized_pnl = trade.size * (trade.entry_price - current_price)

                # Get leverage from agent config
                agent = self.db.query(TradingAgent).filter_by(id=agent_id).first()
                leverage = agent.max_leverage if agent else 10

                # Calculate position value
                position_value = trade.size * current_price

                # Calculate liquidation price (simplified)
                if trade.side == "long":
                    liquidation_price = float(trade.entry_price) * (1 - 1 / leverage)
                else:
                    liquidation_price = float(trade.entry_price) * (1 + 1 / leverage)

                position = Position(
                    coin=trade.coin,
                    side=trade.side,
                    size=float(trade.size),
                    entry_price=float(trade.entry_price),
                    mark_price=float(current_price),
                    position_value=float(position_value),
                    unrealized_pnl=float(unrealized_pnl),
                    leverage=leverage,
                    liquidation_price=liquidation_price
                )
                positions.append(position)

                logger.debug(
                    f"Position: {trade.coin} {trade.side} "
                    f"{trade.size} @ {trade.entry_price} "
                    f"(Current: {current_price}, PnL: {unrealized_pnl})"
                )

            except Exception as e:
                logger.error(f"Failed to get position for {trade.coin}: {e}")

        logger.info(f"Found {len(positions)} open positions for agent {agent_id}")
        return positions

    def get_position(self, agent_id: UUID, coin: str) -> Optional[Position]:
        """Get a specific position by coin.

        Args:
            agent_id: Trading agent ID
            coin: Trading pair symbol

        Returns:
            Position object or None if no position in this coin

        Example:
            >>> btc_position = manager.get_position(agent_id, "BTC")
            >>> if btc_position:
            ...     print(f"BTC position: {btc_position.size}")
        """
        positions = self.get_current_positions(agent_id)
        for position in positions:
            if position.coin == coin:
                return position
        return None

    def has_position(self, agent_id: UUID, coin: str) -> bool:
        """Check if agent has an open position in a coin.

        Args:
            agent_id: Trading agent ID
            coin: Trading pair symbol

        Returns:
            True if agent has open position, False otherwise
        """
        return self.get_position(agent_id, coin) is not None

    def get_account_value(self, agent_id: UUID) -> AccountInfo:
        """Calculate agent's account value and metrics.

        This provides a comprehensive view of the agent's account including:
        - Total account value (balance + P&L)
        - Cash balance available
        - Total position value
        - Unrealized P&L (current positions)
        - Realized P&L (closed positions)
        - Available margin

        Args:
            agent_id: Trading agent ID

        Returns:
            AccountInfo object with all account metrics

        Raises:
            ValueError: If agent not found

        Example:
            >>> account = manager.get_account_value(agent_id)
            >>> print(f"Total value: ${account.total_value}")
            >>> print(f"Available margin: ${account.available_margin}")
        """
        agent = self.db.query(TradingAgent).filter_by(id=agent_id).first()

        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # Get all open positions
        positions = self.get_current_positions(agent_id)

        # Calculate total position value (notional value)
        position_value = sum(
            pos.size * pos.mark_price for pos in positions
        )

        # Calculate total unrealized PnL
        unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)

        # Calculate total realized PnL from closed trades
        realized_pnl_query = self.db.query(
            func.sum(AgentTrade.realized_pnl)
        ).filter_by(
            agent_id=agent_id,
            status="closed"
        ).scalar()

        realized_pnl = realized_pnl_query or Decimal("0")

        # Calculate total account value
        account_value = float(agent.initial_balance) + float(realized_pnl) + unrealized_pnl

        # Calculate withdrawable (cash not in positions)
        withdrawable = account_value - position_value

        # Calculate margin used (simplified)
        # For cross margin, margin_used = sum(position_value / leverage)
        # Simplified: assume max leverage for all positions
        margin_used = position_value / (agent.max_leverage if agent.max_leverage > 0 else 1)

        account_info = AccountInfo(
            account_value=float(account_value),
            withdrawable=float(withdrawable),
            margin_used=float(margin_used),
            unrealized_pnl=float(unrealized_pnl)
        )

        logger.info(
            f"Account value for {agent_id}: "
            f"Total=${account_value}, Withdrawable=${withdrawable}, "
            f"Positions=${position_value}, uPnL=${unrealized_pnl}"
        )

        return account_info

    def calculate_position_size(
        self,
        agent_id: UUID,
        coin: str,
        target_value_usd: Decimal,
        leverage: int = 1
    ) -> Decimal:
        """Calculate position size based on target value and leverage.

        Args:
            agent_id: Trading agent ID
            coin: Trading pair symbol
            target_value_usd: Target position value in USD
            leverage: Leverage multiplier (default: 1x)

        Returns:
            Position size in base currency (e.g., BTC quantity)

        Example:
            >>> # Want $10,000 position in BTC at 10x leverage
            >>> size = manager.calculate_position_size(
            ...     agent_id, "BTC", Decimal("10000"), leverage=10
            ... )
            >>> print(f"BTC size: {size}")
        """
        # Get current market price
        current_price = self.info_client.get_price(coin)

        # Calculate size in base currency
        # target_value_usd is the notional value desired
        size = target_value_usd / current_price

        logger.debug(
            f"Calculated size for {coin}: "
            f"${target_value_usd} @ ${current_price} "
            f"= {size} {coin} ({leverage}x leverage)"
        )

        return size

    def get_total_exposure(self, agent_id: UUID) -> float:
        """Get total exposure (sum of all position values).

        Args:
            agent_id: Trading agent ID

        Returns:
            Total exposure in USD

        Example:
            >>> exposure = manager.get_total_exposure(agent_id)
            >>> print(f"Total exposure: ${exposure}")
        """
        positions = self.get_current_positions(agent_id)
        total_exposure = sum(pos.size * pos.mark_price for pos in positions)
        return total_exposure

    def get_position_summary(self, agent_id: UUID) -> Dict[str, any]:
        """Get a summary of all positions.

        Args:
            agent_id: Trading agent ID

        Returns:
            Dictionary with position summary:
            - num_positions: Number of open positions
            - total_value: Total notional value
            - total_unrealized_pnl: Total unrealized P&L
            - positions_by_coin: Dict mapping coin to position details

        Example:
            >>> summary = manager.get_position_summary(agent_id)
            >>> print(f"Positions: {summary['num_positions']}")
            >>> for coin, details in summary['positions_by_coin'].items():
            ...     print(f"{coin}: {details['unrealized_pnl']}")
        """
        positions = self.get_current_positions(agent_id)

        positions_by_coin = {}
        total_value = 0.0
        total_unrealized_pnl = 0.0

        for pos in positions:
            notional_value = pos.size * pos.mark_price
            total_value += notional_value
            total_unrealized_pnl += pos.unrealized_pnl

            positions_by_coin[pos.coin] = {
                "side": pos.side,
                "size": pos.size,
                "entry_price": pos.entry_price,
                "current_price": pos.mark_price,
                "notional_value": notional_value,
                "unrealized_pnl": pos.unrealized_pnl,
                "pnl_pct": (pos.unrealized_pnl / notional_value * 100) if notional_value > 0 else 0.0
            }

        return {
            "num_positions": len(positions),
            "total_value": total_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "positions_by_coin": positions_by_coin
        }

    def calculate_required_margin(
        self,
        coin: str,
        size: Decimal,
        leverage: int
    ) -> Decimal:
        """Calculate required margin for a position.

        Args:
            coin: Trading pair symbol
            size: Position size in base currency
            leverage: Leverage multiplier

        Returns:
            Required margin in USD

        Example:
            >>> margin = manager.calculate_required_margin(
            ...     "BTC", Decimal("0.1"), leverage=10
            ... )
            >>> print(f"Required margin: ${margin}")
        """
        current_price = self.info_client.get_price(coin)
        notional_value = size * current_price
        required_margin = notional_value / leverage

        return required_margin

    def __repr__(self) -> str:
        """String representation."""
        return "<PositionManager>"
