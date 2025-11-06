"""Alert system for trading bot.

Sends alerts through multiple channels:
- Console output (always enabled)
- Log files (always enabled)
- Telegram (optional)
- Email (optional)

Alert levels: INFO, WARNING, ERROR, CRITICAL
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from loguru import logger
import json


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure."""
    level: AlertLevel
    title: str
    message: str
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "context": self.context or {},
            "timestamp": self.timestamp.isoformat()
        }

    def to_string(self) -> str:
        """Convert to human-readable string."""
        emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }.get(self.level, "")

        lines = [
            f"{emoji} {self.level.value.upper()}: {self.title}",
            f"Message: {self.message}",
            f"Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        ]

        if self.context:
            lines.append(f"Context: {json.dumps(self.context, indent=2)}")

        return "\n".join(lines)


@dataclass
class AlertConfig:
    """Alert system configuration."""
    # Console alerts (always enabled)
    console_enabled: bool = True

    # Telegram alerts
    telegram_enabled: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Email alerts
    email_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: Optional[List[str]] = None

    # Alert level thresholds
    min_console_level: AlertLevel = AlertLevel.INFO
    min_telegram_level: AlertLevel = AlertLevel.WARNING
    min_email_level: AlertLevel = AlertLevel.ERROR


class AlertSystem:
    """Send alerts through configured channels.

    Channels:
    - Console: Always enabled, color-coded output
    - Log file: Always enabled via loguru
    - Telegram: Optional, for mobile notifications
    - Email: Optional, for critical alerts

    Usage:
        config = AlertConfig(
            telegram_enabled=True,
            telegram_bot_token="your_token",
            telegram_chat_id="your_chat_id"
        )
        alert_system = AlertSystem(config)

        # Send alert
        alert_system.send_alert(Alert(
            level=AlertLevel.WARNING,
            title="Low Balance",
            message="Agent ABC balance below $100",
            context={"agent_id": "abc123", "balance": 95.50}
        ))
    """

    def __init__(self, config: AlertConfig):
        """Initialize alert system.

        Args:
            config: Alert configuration
        """
        self.config = config
        self.channels = self._setup_channels()

        logger.info("Alert system initialized with channels: " +
                   ", ".join(self.channels))

    def _setup_channels(self) -> List[str]:
        """Setup alert channels based on configuration.

        Returns:
            List of enabled channel names
        """
        channels = ["console", "log"]

        if self.config.telegram_enabled:
            if self._validate_telegram_config():
                channels.append("telegram")
            else:
                logger.warning("Telegram enabled but configuration invalid")

        if self.config.email_enabled:
            if self._validate_email_config():
                channels.append("email")
            else:
                logger.warning("Email enabled but configuration invalid")

        return channels

    def _validate_telegram_config(self) -> bool:
        """Validate Telegram configuration.

        Returns:
            True if valid
        """
        return bool(
            self.config.telegram_bot_token and
            self.config.telegram_chat_id
        )

    def _validate_email_config(self) -> bool:
        """Validate email configuration.

        Returns:
            True if valid
        """
        return bool(
            self.config.smtp_host and
            self.config.smtp_port and
            self.config.smtp_username and
            self.config.smtp_password and
            self.config.email_from and
            self.config.email_to
        )

    def send_alert(self, alert: Alert) -> None:
        """Send alert through all enabled channels.

        Args:
            alert: Alert to send
        """
        try:
            # Always send to console if enabled
            if self.config.console_enabled:
                if self._should_send_to_channel(alert.level, self.config.min_console_level):
                    self._send_to_console(alert)

            # Always log
            self._send_to_log(alert)

            # Send to Telegram if enabled
            if "telegram" in self.channels:
                if self._should_send_to_channel(alert.level, self.config.min_telegram_level):
                    self._send_to_telegram(alert)

            # Send to Email if enabled
            if "email" in self.channels:
                if self._should_send_to_channel(alert.level, self.config.min_email_level):
                    self._send_to_email(alert)

        except Exception as e:
            logger.error(f"Error sending alert: {e}")

    def _should_send_to_channel(
        self,
        alert_level: AlertLevel,
        min_level: AlertLevel
    ) -> bool:
        """Check if alert should be sent to channel based on level.

        Args:
            alert_level: Alert level
            min_level: Minimum level for channel

        Returns:
            True if should send
        """
        level_order = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.ERROR: 2,
            AlertLevel.CRITICAL: 3
        }

        return level_order[alert_level] >= level_order[min_level]

    def _send_to_console(self, alert: Alert) -> None:
        """Send alert to console with colors.

        Args:
            alert: Alert to send
        """
        # Use click or print with ANSI colors
        colors = {
            AlertLevel.INFO: "\033[94m",  # Blue
            AlertLevel.WARNING: "\033[93m",  # Yellow
            AlertLevel.ERROR: "\033[91m",  # Red
            AlertLevel.CRITICAL: "\033[95m"  # Magenta
        }
        reset = "\033[0m"

        color = colors.get(alert.level, "")
        print(f"{color}{alert.to_string()}{reset}\n")

    def _send_to_log(self, alert: Alert) -> None:
        """Send alert to log file.

        Args:
            alert: Alert to send
        """
        log_message = f"{alert.title}: {alert.message}"

        if alert.context:
            log_message += f" | Context: {json.dumps(alert.context)}"

        if alert.level == AlertLevel.INFO:
            logger.info(log_message)
        elif alert.level == AlertLevel.WARNING:
            logger.warning(log_message)
        elif alert.level == AlertLevel.ERROR:
            logger.error(log_message)
        elif alert.level == AlertLevel.CRITICAL:
            logger.critical(log_message)

    def _send_to_telegram(self, alert: Alert) -> None:
        """Send alert to Telegram.

        Args:
            alert: Alert to send
        """
        try:
            import requests

            url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"

            # Format message
            message = f"*{alert.level.value.upper()}*: {alert.title}\n\n{alert.message}"

            if alert.context:
                message += f"\n\n```json\n{json.dumps(alert.context, indent=2)}\n```"

            payload = {
                "chat_id": self.config.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }

            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()

            logger.debug(f"Alert sent to Telegram: {alert.title}")

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")

    def _send_to_email(self, alert: Alert) -> None:
        """Send alert via email.

        Args:
            alert: Alert to send
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.config.email_from
            msg["To"] = ", ".join(self.config.email_to)
            msg["Subject"] = f"[{alert.level.value.upper()}] {alert.title}"

            # Email body
            body = f"""
Alert Level: {alert.level.value.upper()}
Title: {alert.title}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{alert.message}

Context:
{json.dumps(alert.context, indent=2) if alert.context else 'N/A'}
"""

            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)

            logger.debug(f"Alert sent via email: {alert.title}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    # Convenience methods for common alerts

    def send_service_started(self) -> None:
        """Send service started alert."""
        self.send_alert(Alert(
            level=AlertLevel.INFO,
            title="Trading Bot Started",
            message="Trading bot service has started successfully"
        ))

    def send_service_stopped(self) -> None:
        """Send service stopped alert."""
        self.send_alert(Alert(
            level=AlertLevel.INFO,
            title="Trading Bot Stopped",
            message="Trading bot service has been stopped"
        ))

    def send_low_balance_alert(self, agent_name: str, balance: float) -> None:
        """Send low balance alert.

        Args:
            agent_name: Agent name
            balance: Current balance
        """
        self.send_alert(Alert(
            level=AlertLevel.WARNING,
            title="Low Balance Warning",
            message=f"Agent {agent_name} balance is low: ${balance:.2f}",
            context={"agent_name": agent_name, "balance": balance}
        ))

    def send_liquidation_risk_alert(
        self,
        agent_name: str,
        symbol: str,
        distance: float
    ) -> None:
        """Send liquidation risk alert.

        Args:
            agent_name: Agent name
            symbol: Position symbol
            distance: Liquidation distance percentage
        """
        level = AlertLevel.CRITICAL if distance < 10 else AlertLevel.WARNING

        self.send_alert(Alert(
            level=level,
            title="Liquidation Risk Alert",
            message=f"Agent {agent_name} position {symbol} at {distance:.1f}% from liquidation",
            context={
                "agent_name": agent_name,
                "symbol": symbol,
                "distance": distance
            }
        ))

    def send_error_alert(self, error_type: str, error_message: str) -> None:
        """Send error alert.

        Args:
            error_type: Type of error
            error_message: Error message
        """
        self.send_alert(Alert(
            level=AlertLevel.ERROR,
            title=f"Error: {error_type}",
            message=error_message,
            context={"error_type": error_type}
        ))

    def send_daily_summary(self, summary: Dict[str, Any]) -> None:
        """Send daily trading summary.

        Args:
            summary: Daily summary data
        """
        message = f"""
Daily Trading Summary:
- Total Cycles: {summary.get('total_cycles', 0)}
- Successful Trades: {summary.get('successful_trades', 0)}
- Failed Trades: {summary.get('failed_trades', 0)}
- Total PnL: ${summary.get('total_pnl', 0):.2f}
"""

        self.send_alert(Alert(
            level=AlertLevel.INFO,
            title="Daily Trading Summary",
            message=message.strip(),
            context=summary
        ))
