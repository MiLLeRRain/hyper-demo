"""Error handling and recovery mechanism."""

import logging
from enum import Enum
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ErrorAction(Enum):
    """Actions to take when handling errors."""
    RETRY = "retry"  # Retry the operation
    SKIP = "skip"  # Skip and continue
    SHUTDOWN = "shutdown"  # Shutdown service


# Error categories
RETRYABLE_ERRORS = [
    "NetworkError",
    "APITimeoutError",
    "RateLimitError",
    "ConnectionError",
    "ReadTimeout",
    "ConnectTimeout"
]

CRITICAL_ERRORS = [
    "DatabaseConnectionError",
    "ConfigurationError",
    "AuthenticationError",
    "InvalidPrivateKey"
]

SKIPPABLE_ERRORS = [
    "InvalidDecisionError",
    "InsufficientBalanceError",
    "OrderRejectedError",
    "RiskCheckFailedError"
]


class ErrorHandler:
    """
    Handle and recover from errors.

    Classifies errors and determines appropriate recovery actions.
    Tracks consecutive failures to prevent infinite retry loops.
    """

    def __init__(
        self,
        max_consecutive_errors: int = 5,
        error_window_minutes: int = 30
    ):
        """
        Initialize error handler.

        Args:
            max_consecutive_errors: Max consecutive errors before shutdown
            error_window_minutes: Time window for error tracking
        """
        self.max_consecutive_errors = max_consecutive_errors
        self.error_window = timedelta(minutes=error_window_minutes)

        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.consecutive_errors = 0
        self.last_error_time: Optional[datetime] = None
        self.error_history = []

    def handle_error(
        self,
        error: Exception,
        context: str
    ) -> ErrorAction:
        """
        Handle error and determine recovery action.

        Args:
            error: The exception that occurred
            context: Context where error occurred

        Returns:
            ErrorAction indicating how to proceed
        """
        error_type = type(error).__name__
        error_msg = str(error)

        logger.error(f"Error in {context}: [{error_type}] {error_msg}")

        # Record error
        self._record_error(error_type, context)

        # Classify error and determine action
        action = self._classify_error(error_type)

        # Check if we've hit consecutive error threshold
        if self.consecutive_errors >= self.max_consecutive_errors:
            logger.critical(
                f"Consecutive error threshold reached ({self.consecutive_errors}). "
                "Initiating shutdown..."
            )
            return ErrorAction.SHUTDOWN

        logger.info(f"Error action: {action.value}")
        return action

    def reset_error_count(self) -> None:
        """Reset consecutive error count (call after successful operation)."""
        if self.consecutive_errors > 0:
            logger.info(
                f"Resetting error count (was {self.consecutive_errors}). "
                "Operation successful."
            )
            self.consecutive_errors = 0

    def get_error_statistics(self) -> Dict[str, any]:
        """
        Get error statistics.

        Returns:
            Dict with error stats
        """
        # Clean old errors from history
        cutoff_time = datetime.utcnow() - self.error_window
        self.error_history = [
            e for e in self.error_history
            if e["timestamp"] > cutoff_time
        ]

        return {
            "consecutive_errors": self.consecutive_errors,
            "total_errors_in_window": len(self.error_history),
            "error_counts_by_type": dict(self.error_counts),
            "last_error_time": self.last_error_time,
            "window_minutes": self.error_window.total_seconds() / 60
        }

    def _record_error(self, error_type: str, context: str) -> None:
        """
        Record error occurrence.

        Args:
            error_type: Type of error
            context: Context where error occurred
        """
        now = datetime.utcnow()

        # Increment consecutive count
        self.consecutive_errors += 1

        # Increment type count
        self.error_counts[error_type] += 1

        # Update last error time
        self.last_error_time = now

        # Add to history
        self.error_history.append({
            "timestamp": now,
            "error_type": error_type,
            "context": context
        })

        logger.debug(
            f"Error recorded: {error_type} (consecutive: {self.consecutive_errors})"
        )

    def _classify_error(self, error_type: str) -> ErrorAction:
        """
        Classify error and determine action.

        Args:
            error_type: Type of error

        Returns:
            ErrorAction to take
        """
        # Check if critical
        if any(crit in error_type for crit in CRITICAL_ERRORS):
            logger.error(f"Critical error detected: {error_type}")
            return ErrorAction.SHUTDOWN

        # Check if retryable
        if any(retry in error_type for retry in RETRYABLE_ERRORS):
            logger.warning(f"Retryable error: {error_type}")
            return ErrorAction.RETRY

        # Check if skippable
        if any(skip in error_type for skip in SKIPPABLE_ERRORS):
            logger.warning(f"Skippable error: {error_type}")
            return ErrorAction.SKIP

        # Default: retry for unknown errors
        logger.warning(f"Unknown error type: {error_type}, defaulting to RETRY")
        return ErrorAction.RETRY

    def should_shutdown(self) -> bool:
        """
        Check if service should shutdown based on error patterns.

        Returns:
            True if should shutdown
        """
        return self.consecutive_errors >= self.max_consecutive_errors

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ErrorHandler(consecutive={self.consecutive_errors}, "
            f"max={self.max_consecutive_errors})"
        )
