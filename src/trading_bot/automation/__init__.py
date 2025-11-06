"""Automation module for trading bot lifecycle management."""

from .trading_bot_service import TradingBotService
from .scheduler import TradingScheduler
from .trading_cycle_executor import TradingCycleExecutor
from .error_handler import ErrorHandler, ErrorAction
from .state_manager import StateManager

__all__ = [
    "TradingBotService",
    "TradingScheduler",
    "TradingCycleExecutor",
    "ErrorHandler",
    "ErrorAction",
    "StateManager",
]
