"""Performance monitoring for trading bot.

Tracks and analyzes system performance metrics including:
- Trading cycle durations
- API call latencies and success rates
- Component-level timing (data collection, AI decisions, trade execution)
- Agent success rates
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import statistics
from loguru import logger


@dataclass
class MetricStats:
    """Statistical summary of a metric."""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    values: List[float] = field(default_factory=list)

    def add(self, value: float) -> None:
        """Add a new value to the metric."""
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.values.append(value)

        # Keep only last 1000 values to prevent memory growth
        if len(self.values) > 1000:
            self.values.pop(0)

    @property
    def avg(self) -> float:
        """Calculate average."""
        return self.sum / self.count if self.count > 0 else 0.0

    @property
    def p95(self) -> float:
        """Calculate 95th percentile."""
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        index = int(len(sorted_values) * 0.95)
        return sorted_values[index] if index < len(sorted_values) else sorted_values[-1]

    @property
    def p99(self) -> float:
        """Calculate 99th percentile."""
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        index = int(len(sorted_values) * 0.99)
        return sorted_values[index] if index < len(sorted_values) else sorted_values[-1]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "avg": round(self.avg, 2),
            "min": round(self.min, 2) if self.min != float('inf') else 0.0,
            "max": round(self.max, 2) if self.max != float('-inf') else 0.0,
            "p95": round(self.p95, 2),
            "p99": round(self.p99, 2)
        }


class PerformanceMonitor:
    """Monitor system performance metrics.

    Tracks performance across multiple dimensions:
    - Cycle execution time
    - Component timing (data collection, AI, execution)
    - API call performance
    - Success rates

    Usage:
        monitor = PerformanceMonitor()

        # Record cycle duration
        monitor.record_cycle_duration(12.5)

        # Record API call
        monitor.record_api_call("GET /market_data", 0.15, success=True)

        # Get statistics
        stats = monitor.get_statistics()
    """

    def __init__(self):
        """Initialize performance monitor."""
        # Timing metrics
        self.cycle_duration = MetricStats()
        self.data_collection_duration = MetricStats()
        self.ai_decision_duration = MetricStats()
        self.trade_execution_duration = MetricStats()

        # API metrics
        self.api_calls: Dict[str, MetricStats] = defaultdict(MetricStats)
        self.api_success_count = 0
        self.api_failure_count = 0

        # Agent metrics
        self.agent_success_count = 0
        self.agent_failure_count = 0

        # Start time for uptime tracking
        self.start_time = datetime.utcnow()

        logger.info("Performance monitor initialized")

    def record_cycle_duration(self, duration: float) -> None:
        """Record trading cycle duration.

        Args:
            duration: Cycle duration in seconds
        """
        self.cycle_duration.add(duration)

        # Log warning if cycle is slow
        if duration > 60.0:
            logger.warning(f"Slow trading cycle detected: {duration:.2f}s (target: <60s)")

        logger.debug(f"Cycle duration recorded: {duration:.2f}s")

    def record_data_collection(self, duration: float) -> None:
        """Record data collection duration.

        Args:
            duration: Data collection duration in seconds
        """
        self.data_collection_duration.add(duration)

        if duration > 5.0:
            logger.warning(f"Slow data collection: {duration:.2f}s (target: <5s)")

        logger.debug(f"Data collection duration: {duration:.2f}s")

    def record_ai_decision(self, duration: float) -> None:
        """Record AI decision generation duration.

        Args:
            duration: AI decision duration in seconds
        """
        self.ai_decision_duration.add(duration)

        if duration > 15.0:
            logger.warning(f"Slow AI decision: {duration:.2f}s (target: <15s)")

        logger.debug(f"AI decision duration: {duration:.2f}s")

    def record_trade_execution(self, duration: float) -> None:
        """Record trade execution duration.

        Args:
            duration: Trade execution duration in seconds
        """
        self.trade_execution_duration.add(duration)

        if duration > 5.0:
            logger.warning(f"Slow trade execution: {duration:.2f}s (target: <5s)")

        logger.debug(f"Trade execution duration: {duration:.2f}s")

    def record_api_call(
        self,
        endpoint: str,
        duration: float,
        success: bool
    ) -> None:
        """Record API call metrics.

        Args:
            endpoint: API endpoint called
            duration: Call duration in seconds
            success: Whether the call succeeded
        """
        # Record duration for this endpoint
        self.api_calls[endpoint].add(duration)

        # Update success/failure counts
        if success:
            self.api_success_count += 1
        else:
            self.api_failure_count += 1
            logger.warning(f"API call failed: {endpoint}")

        # Check for slow API calls
        if duration > 2.0:
            logger.warning(f"Slow API call to {endpoint}: {duration:.2f}s")

        logger.debug(f"API call to {endpoint}: {duration:.2f}s, success={success}")

    def record_agent_result(self, success: bool) -> None:
        """Record agent execution result.

        Args:
            success: Whether agent execution succeeded
        """
        if success:
            self.agent_success_count += 1
        else:
            self.agent_failure_count += 1

    def get_api_success_rate(self) -> float:
        """Get API success rate.

        Returns:
            Success rate (0.0 to 1.0)
        """
        total = self.api_success_count + self.api_failure_count
        if total == 0:
            return 1.0
        return self.api_success_count / total

    def get_agent_success_rate(self) -> float:
        """Get agent success rate.

        Returns:
            Success rate (0.0 to 1.0)
        """
        total = self.agent_success_count + self.agent_failure_count
        if total == 0:
            return 1.0
        return self.agent_success_count / total

    def get_uptime_seconds(self) -> float:
        """Get system uptime in seconds.

        Returns:
            Uptime in seconds
        """
        return (datetime.utcnow() - self.start_time).total_seconds()

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics.

        Returns:
            Dictionary containing all performance metrics
        """
        stats = {
            "uptime_seconds": self.get_uptime_seconds(),
            "uptime_hours": round(self.get_uptime_seconds() / 3600, 2),

            "cycle": self.cycle_duration.to_dict(),
            "data_collection": self.data_collection_duration.to_dict(),
            "ai_decision": self.ai_decision_duration.to_dict(),
            "trade_execution": self.trade_execution_duration.to_dict(),

            "api": {
                "success_rate": round(self.get_api_success_rate(), 4),
                "success_count": self.api_success_count,
                "failure_count": self.api_failure_count,
                "total_calls": self.api_success_count + self.api_failure_count,
                "endpoints": {
                    endpoint: stats.to_dict()
                    for endpoint, stats in self.api_calls.items()
                }
            },

            "agent": {
                "success_rate": round(self.get_agent_success_rate(), 4),
                "success_count": self.agent_success_count,
                "failure_count": self.agent_failure_count,
                "total_executions": self.agent_success_count + self.agent_failure_count
            }
        }

        return stats

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status based on performance metrics.

        Returns:
            Health status with warnings
        """
        warnings = []

        # Check cycle performance
        if self.cycle_duration.count > 0:
            avg_cycle = self.cycle_duration.avg
            if avg_cycle > 60.0:
                warnings.append(f"Average cycle duration {avg_cycle:.1f}s exceeds 60s target")

            p95_cycle = self.cycle_duration.p95
            if p95_cycle > 90.0:
                warnings.append(f"P95 cycle duration {p95_cycle:.1f}s exceeds 90s threshold")

        # Check API success rate
        api_success_rate = self.get_api_success_rate()
        if api_success_rate < 0.95:
            warnings.append(f"API success rate {api_success_rate:.2%} below 95% threshold")

        # Check agent success rate
        agent_success_rate = self.get_agent_success_rate()
        if agent_success_rate < 0.90:
            warnings.append(f"Agent success rate {agent_success_rate:.2%} below 90% threshold")

        # Determine overall health
        if not warnings:
            health = "healthy"
        elif len(warnings) <= 2:
            health = "degraded"
        else:
            health = "unhealthy"

        return {
            "status": health,
            "warnings": warnings,
            "metrics_summary": {
                "avg_cycle_duration": round(self.cycle_duration.avg, 2),
                "api_success_rate": round(api_success_rate, 4),
                "agent_success_rate": round(agent_success_rate, 4)
            }
        }

    def reset_metrics(self) -> None:
        """Reset all metrics (useful for testing)."""
        self.cycle_duration = MetricStats()
        self.data_collection_duration = MetricStats()
        self.ai_decision_duration = MetricStats()
        self.trade_execution_duration = MetricStats()
        self.api_calls.clear()
        self.api_success_count = 0
        self.api_failure_count = 0
        self.agent_success_count = 0
        self.agent_failure_count = 0
        self.start_time = datetime.utcnow()

        logger.info("Performance metrics reset")
