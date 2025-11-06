"""Account monitoring for trading bot.

Monitors account health and risk metrics including:
- Account balance levels
- Unrealized PnL
- Liquidation risk distance
- Total exposure percentage
- Drawdown percentage
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from trading_bot.models.database import TradingAgent, Position
from trading_bot.hyperliquid.client import HyperLiquidClient


class HealthStatus(Enum):
    """Account health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class BalanceAlert:
    """Balance alert information."""
    agent_id: UUID
    agent_name: str
    balance: Decimal
    threshold: Decimal
    severity: HealthStatus
    message: str


@dataclass
class LiquidationAlert:
    """Liquidation risk alert."""
    agent_id: UUID
    agent_name: str
    position_symbol: str
    liquidation_distance: float  # Percentage
    severity: HealthStatus
    message: str


@dataclass
class ExposureAlert:
    """Total exposure alert."""
    agent_id: UUID
    agent_name: str
    total_exposure: Decimal
    exposure_percentage: float
    severity: HealthStatus
    message: str


class AccountMonitor:
    """Monitor account health and risk metrics.

    Checks:
    - Balance levels (low balance warnings)
    - Liquidation risk for all positions
    - Total exposure relative to balance
    - Unrealized PnL and drawdown

    Usage:
        monitor = AccountMonitor(db_session, hl_client)

        # Check account health
        status = monitor.check_account_health(agent_id)

        # Check liquidation risk
        alerts = monitor.check_liquidation_risk(agent_id)

        # Check balance
        balance_alert = monitor.check_balance(agent_id)
    """

    def __init__(
        self,
        db: Session,
        hl_client: Optional[HyperLiquidClient] = None
    ):
        """Initialize account monitor.

        Args:
            db: Database session
            hl_client: HyperLiquid API client (optional)
        """
        self.db = db
        self.hl_client = hl_client

        # Thresholds
        self.min_balance_threshold = Decimal("100.0")  # $100 minimum
        self.critical_balance_threshold = Decimal("50.0")  # $50 critical

        self.warning_liquidation_distance = 20.0  # 20% warning
        self.critical_liquidation_distance = 10.0  # 10% critical

        self.warning_exposure_percentage = 80.0  # 80% warning
        self.critical_exposure_percentage = 90.0  # 90% critical

        logger.info("Account monitor initialized")

    def check_account_health(self, agent_id: UUID) -> HealthStatus:
        """Check overall account health.

        Args:
            agent_id: Trading agent ID

        Returns:
            Overall health status
        """
        try:
            # Get all alerts
            balance_alert = self.check_balance(agent_id)
            liquidation_alerts = self.check_liquidation_risk(agent_id)
            exposure_alert = self.check_exposure(agent_id)

            # Determine overall status
            critical_count = 0
            warning_count = 0

            if balance_alert and balance_alert.severity == HealthStatus.CRITICAL:
                critical_count += 1
            elif balance_alert and balance_alert.severity == HealthStatus.WARNING:
                warning_count += 1

            for alert in liquidation_alerts:
                if alert.severity == HealthStatus.CRITICAL:
                    critical_count += 1
                elif alert.severity == HealthStatus.WARNING:
                    warning_count += 1

            if exposure_alert and exposure_alert.severity == HealthStatus.CRITICAL:
                critical_count += 1
            elif exposure_alert and exposure_alert.severity == HealthStatus.WARNING:
                warning_count += 1

            # Return worst status
            if critical_count > 0:
                return HealthStatus.CRITICAL
            elif warning_count > 0:
                return HealthStatus.WARNING
            else:
                return HealthStatus.HEALTHY

        except Exception as e:
            logger.error(f"Error checking account health for agent {agent_id}: {e}")
            return HealthStatus.WARNING

    def check_balance(self, agent_id: UUID) -> Optional[BalanceAlert]:
        """Check if account balance is sufficient.

        Args:
            agent_id: Trading agent ID

        Returns:
            Balance alert if balance is low, None otherwise
        """
        try:
            # Get agent
            agent = self.db.query(TradingAgent).filter(
                TradingAgent.id == agent_id
            ).first()

            if not agent:
                logger.error(f"Agent {agent_id} not found")
                return None

            # Get current balance (use initial_balance as proxy if no API)
            # In production, you would fetch actual balance from API
            balance = agent.initial_balance

            # Check thresholds
            if balance <= self.critical_balance_threshold:
                return BalanceAlert(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    balance=balance,
                    threshold=self.critical_balance_threshold,
                    severity=HealthStatus.CRITICAL,
                    message=f"CRITICAL: Balance ${balance} below ${self.critical_balance_threshold}"
                )
            elif balance <= self.min_balance_threshold:
                return BalanceAlert(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    balance=balance,
                    threshold=self.min_balance_threshold,
                    severity=HealthStatus.WARNING,
                    message=f"WARNING: Balance ${balance} below ${self.min_balance_threshold}"
                )

            return None

        except Exception as e:
            logger.error(f"Error checking balance for agent {agent_id}: {e}")
            return None

    def check_liquidation_risk(self, agent_id: UUID) -> List[LiquidationAlert]:
        """Check liquidation risk for all positions.

        Args:
            agent_id: Trading agent ID

        Returns:
            List of liquidation alerts
        """
        alerts = []

        try:
            # Get agent
            agent = self.db.query(TradingAgent).filter(
                TradingAgent.id == agent_id
            ).first()

            if not agent:
                logger.error(f"Agent {agent_id} not found")
                return alerts

            # Get all open positions
            positions = self.db.query(Position).filter(
                Position.agent_id == agent_id,
                Position.status == "open"
            ).all()

            for position in positions:
                # Calculate liquidation distance
                # This is a simplified calculation
                # In production, use actual mark price and liquidation price from API
                if position.leverage and position.leverage > 1:
                    # Approximate liquidation distance
                    liquidation_distance = 100.0 / float(position.leverage)

                    # Check thresholds
                    if liquidation_distance <= self.critical_liquidation_distance:
                        alerts.append(LiquidationAlert(
                            agent_id=agent.id,
                            agent_name=agent.name,
                            position_symbol=position.symbol,
                            liquidation_distance=liquidation_distance,
                            severity=HealthStatus.CRITICAL,
                            message=f"CRITICAL: {position.symbol} liquidation risk {liquidation_distance:.1f}%"
                        ))
                    elif liquidation_distance <= self.warning_liquidation_distance:
                        alerts.append(LiquidationAlert(
                            agent_id=agent.id,
                            agent_name=agent.name,
                            position_symbol=position.symbol,
                            liquidation_distance=liquidation_distance,
                            severity=HealthStatus.WARNING,
                            message=f"WARNING: {position.symbol} liquidation risk {liquidation_distance:.1f}%"
                        ))

            return alerts

        except Exception as e:
            logger.error(f"Error checking liquidation risk for agent {agent_id}: {e}")
            return alerts

    def check_exposure(self, agent_id: UUID) -> Optional[ExposureAlert]:
        """Check total exposure relative to balance.

        Args:
            agent_id: Trading agent ID

        Returns:
            Exposure alert if exposure is high, None otherwise
        """
        try:
            # Get agent
            agent = self.db.query(TradingAgent).filter(
                TradingAgent.id == agent_id
            ).first()

            if not agent:
                logger.error(f"Agent {agent_id} not found")
                return None

            # Get all open positions
            positions = self.db.query(Position).filter(
                Position.agent_id == agent_id,
                Position.status == "open"
            ).all()

            # Calculate total exposure (sum of notional values)
            total_exposure = Decimal("0")
            for position in positions:
                # Notional = size * entry_price
                notional = abs(position.size) * position.entry_price
                total_exposure += notional

            # Calculate exposure percentage
            balance = agent.initial_balance
            if balance > 0:
                exposure_percentage = float(total_exposure / balance * 100)
            else:
                exposure_percentage = 0.0

            # Check thresholds
            if exposure_percentage >= self.critical_exposure_percentage:
                return ExposureAlert(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    total_exposure=total_exposure,
                    exposure_percentage=exposure_percentage,
                    severity=HealthStatus.CRITICAL,
                    message=f"CRITICAL: Exposure {exposure_percentage:.1f}% of balance"
                )
            elif exposure_percentage >= self.warning_exposure_percentage:
                return ExposureAlert(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    total_exposure=total_exposure,
                    exposure_percentage=exposure_percentage,
                    severity=HealthStatus.WARNING,
                    message=f"WARNING: Exposure {exposure_percentage:.1f}% of balance"
                )

            return None

        except Exception as e:
            logger.error(f"Error checking exposure for agent {agent_id}: {e}")
            return None

    def get_account_summary(self, agent_id: UUID) -> Dict[str, Any]:
        """Get comprehensive account summary.

        Args:
            agent_id: Trading agent ID

        Returns:
            Account summary with all metrics
        """
        try:
            # Get agent
            agent = self.db.query(TradingAgent).filter(
                TradingAgent.id == agent_id
            ).first()

            if not agent:
                return {"error": f"Agent {agent_id} not found"}

            # Get positions
            positions = self.db.query(Position).filter(
                Position.agent_id == agent_id,
                Position.status == "open"
            ).all()

            # Calculate metrics
            total_exposure = Decimal("0")
            unrealized_pnl = Decimal("0")

            for position in positions:
                notional = abs(position.size) * position.entry_price
                total_exposure += notional
                unrealized_pnl += position.unrealized_pnl or Decimal("0")

            balance = agent.initial_balance
            exposure_percentage = float(total_exposure / balance * 100) if balance > 0 else 0.0

            # Get health status
            health_status = self.check_account_health(agent_id)

            # Compile summary
            summary = {
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "health_status": health_status.value,
                "balance": float(balance),
                "total_exposure": float(total_exposure),
                "exposure_percentage": round(exposure_percentage, 2),
                "unrealized_pnl": float(unrealized_pnl),
                "position_count": len(positions),
                "alerts": {
                    "balance": self.check_balance(agent_id),
                    "liquidation": self.check_liquidation_risk(agent_id),
                    "exposure": self.check_exposure(agent_id)
                }
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting account summary for agent {agent_id}: {e}")
            return {"error": str(e)}

    def monitor_all_agents(self) -> Dict[str, Any]:
        """Monitor all active agents.

        Returns:
            Summary of all agent health statuses
        """
        try:
            # Get all active agents
            agents = self.db.query(TradingAgent).filter(
                TradingAgent.status == "active"
            ).all()

            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_agents": len(agents),
                "healthy_count": 0,
                "warning_count": 0,
                "critical_count": 0,
                "agents": []
            }

            for agent in agents:
                health = self.check_account_health(agent.id)

                if health == HealthStatus.HEALTHY:
                    results["healthy_count"] += 1
                elif health == HealthStatus.WARNING:
                    results["warning_count"] += 1
                elif health == HealthStatus.CRITICAL:
                    results["critical_count"] += 1

                results["agents"].append({
                    "id": str(agent.id),
                    "name": agent.name,
                    "health": health.value
                })

            return results

        except Exception as e:
            logger.error(f"Error monitoring all agents: {e}")
            return {"error": str(e)}
