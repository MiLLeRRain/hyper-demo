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
from .hyperliquid_executor import HyperLiquidExecutor

logger = logging.getLogger(__name__)


class PositionManager:
    """Track and manage agent positions.

    The PositionManager provides real-time position tracking by combining
    database records with current market prices. It calculates unrealized P&L,
    account values, and other position metrics.

    Attributes:
        info_client: HyperLiquid Info API client for market data
        db: SQLAlchemy database session
        executor: Optional HyperLiquidExecutor for fetching user state
    """

    def __init__(
        self,
        info_client: HyperliquidClient,
        db_session: Session,
        executor: Optional[HyperLiquidExecutor] = None
    ):
        """Initialize position manager.

        Args:
            info_client: HyperLiquid Info API client
            db_session: Database session
            executor: Optional HyperLiquidExecutor for user state

        Example:
            >>> client = HyperliquidClient("https://api.hyperliquid.xyz")
            >>> db_session = Session()
            >>> manager = PositionManager(client, db_session, executor)
        """
        self.info_client = info_client
        self.db = db_session
        self.executor = executor
        logger.info("PositionManager initialized")

    def get_current_positions(
        self,
        agent_id: UUID,
        executor: Optional[HyperLiquidExecutor] = None
    ) -> List[Position]:
        """Get current open positions for an agent.

        Args:
            agent_id: Trading agent ID
            executor: Specific executor to use for fetching user state
        """
        # Query open trades from database
        open_trades = self.db.query(AgentTrade).filter_by(
            agent_id=agent_id,
            status="open"
        ).all()

        # Use specific executor if provided, else default
        active_executor = executor or self.executor

        # Fetch user state from exchange if executor is available
        exchange_positions = {}
        if active_executor and not active_executor.dry_run:
            try:
                user_state = active_executor.info.user_state(active_executor.wallet_address)
                for asset_pos in user_state.get("assetPositions", []):
                    pos_data = asset_pos.get("position", {})
                    coin = pos_data.get("coin")
                    if coin:
                        exchange_positions[coin] = pos_data
            except Exception as e:
                logger.error(f"Failed to fetch user state: {e}")

        positions = []
        for trade in open_trades:
            try:
                # Get exchange data for this coin
                exch_pos = exchange_positions.get(trade.coin, {})
                
                # SYNC CHECK: If exchange says size is 0, but DB says open, it means it was closed externally
                # (e.g. liquidation, TP/SL, or manual close)
                exch_size = float(exch_pos.get("szi", 0)) if exch_pos else 0.0
                
                if active_executor and not active_executor.dry_run and exch_size == 0:
                    logger.warning(
                        f"Position mismatch for {trade.coin}: DB has {trade.size}, Exchange has 0. "
                        f"Marking trade {trade.id} as closed."
                    )
                    # Auto-close the trade in DB
                    trade.status = "closed"
                    trade.exit_time = datetime.utcnow()
                    trade.notes = (trade.notes or "") + " [Auto-closed by PositionManager sync]"
                    self.db.commit()
                    continue  # Skip adding to positions list

                # Get current market price
                price_obj = self.info_client.get_price(trade.coin)
                current_price = Decimal(str(price_obj.price))

                # Determine entry price: prefer exchange data, fallback to DB, then 0
                if exch_pos and "entryPx" in exch_pos:
                    entry_price = Decimal(str(exch_pos["entryPx"]))
                elif trade.entry_price is not None:
                    entry_price = trade.entry_price
                else:
                    logger.warning(f"Trade {trade.id} for {trade.coin} has no entry price. Using 0.")
                    entry_price = Decimal("0")

                # Calculate unrealized PnL
                # If we have exchange data, we can use it directly if the size matches
                # But since we might have partial positions, we calculate based on trade size
                if trade.side == "long":
                    # Long: profit when price goes up
                    unrealized_pnl = trade.size * (current_price - entry_price)
                else:  # short
                    # Short: profit when price goes down
                    unrealized_pnl = trade.size * (entry_price - current_price)

                # Get leverage from agent config or exchange
                if exch_pos and "leverage" in exch_pos:
                    leverage = int(exch_pos["leverage"].get("value", 10))
                else:
                    agent = self.db.query(TradingAgent).filter_by(id=agent_id).first()
                    leverage = agent.max_leverage if agent else 10

                # Calculate position value
                position_value = trade.size * current_price

                # Calculate liquidation price
                if exch_pos and "liquidationPx" in exch_pos and exch_pos["liquidationPx"]:
                    liquidation_price = float(exch_pos["liquidationPx"])
                else:
                    # Simplified calculation
                    if trade.side == "long":
                        liquidation_price = float(entry_price) * (1 - 1 / leverage)
                    else:
                        liquidation_price = float(entry_price) * (1 + 1 / leverage)

                position = Position(
                    coin=trade.coin,
                    side=trade.side,
                    size=float(trade.size),
                    entry_price=float(entry_price),
                    mark_price=float(current_price),
                    position_value=float(position_value),
                    unrealized_pnl=float(unrealized_pnl),
                    leverage=leverage,
                    liquidation_price=liquidation_price
                )
                positions.append(position)

                logger.debug(
                    f"Position: {trade.coin} {trade.side} "
                    f"{trade.size} @ {entry_price} "
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

    def get_account_value(
        self,
        agent_id: UUID,
        executor: Optional[HyperLiquidExecutor] = None
    ) -> AccountInfo:
        """Calculate agent's account value and metrics.

        Args:
            agent_id: Trading agent ID
            executor: Specific executor to use
        """
        agent = self.db.query(TradingAgent).filter_by(id=agent_id).first()

        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # Try to get live account value from exchange if executor is available
        active_executor = executor or self.executor
        
        if active_executor:
            logger.info(f"Checking account value for agent {agent.name} using wallet {active_executor.wallet_address} (Dry Run: {active_executor.dry_run})")
            
        if active_executor and not active_executor.dry_run:
            try:
                user_state = active_executor.info.user_state(active_executor.wallet_address)
                logger.debug(f"Raw user state for {active_executor.wallet_address}: {user_state}")
                
                margin_summary = user_state.get("marginSummary", {})
                
                account_value = float(margin_summary.get("accountValue", 0.0))
                
                # Withdrawable is usually at top level, but check both
                withdrawable = float(user_state.get("withdrawable", margin_summary.get("withdrawable", 0.0)))
                
                margin_used = float(margin_summary.get("totalMarginUsed", 0.0))
                
                # Calculate unrealized PnL from positions
                positions = self.get_current_positions(agent_id, executor=active_executor)
                unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
                
                account_info = AccountInfo(
                    account_value=account_value,
                    withdrawable=withdrawable,
                    margin_used=margin_used,
                    unrealized_pnl=unrealized_pnl
                )
                
                logger.info(
                    f"Live account value for {agent_id} ({agent.name}): "
                    f"Total=${account_value}, Withdrawable=${withdrawable}, "
                    f"Margin=${margin_used}, uPnL=${unrealized_pnl}"
                )
                return account_info
                
            except Exception as e:
                logger.error(f"Failed to fetch live account value for {agent.name}: {e}", exc_info=True)
                # Fallback to calculated value

        # Get all open positions
        positions = self.get_current_positions(agent_id, executor=executor)

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

        # Calculate margin used (simplified)
        # For cross margin, margin_used = sum(position_value / leverage)
        # Simplified: assume max leverage for all positions
        margin_used = position_value / (agent.max_leverage if agent.max_leverage > 0 else 1)

        # Calculate withdrawable (cash not in positions)
        # Withdrawable is Equity - Margin Used
        withdrawable = account_value - margin_used

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
        price_obj = self.info_client.get_price(coin)
        current_price = Decimal(str(price_obj.price))

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
        price_obj = self.info_client.get_price(coin)
        current_price = Decimal(str(price_obj.price))
        
        notional_value = size * current_price
        required_margin = notional_value / leverage

        return required_margin

    def __repr__(self) -> str:
        """String representation."""
        return "<PositionManager>"
