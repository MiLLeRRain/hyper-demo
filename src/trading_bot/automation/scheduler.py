"""Trading scheduler for 3-minute interval execution."""

import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from .trading_cycle_executor import TradingCycleExecutor

logger = logging.getLogger(__name__)


class TradingScheduler:
    """
    Schedule trading cycles at fixed intervals.

    Uses APScheduler to trigger trading cycles every N minutes.
    Prevents overlapping execution and handles failures.
    """

    def __init__(
        self,
        executor: TradingCycleExecutor,
        interval_minutes: int = 3
    ):
        """
        Initialize trading scheduler.

        Args:
            executor: Trading cycle executor
            interval_minutes: Interval between cycles (default: 3)
        """
        self.executor = executor
        self.interval_minutes = interval_minutes

        # Create scheduler
        self.scheduler = BackgroundScheduler(
            job_defaults={
                'coalesce': True,  # Merge missed runs
                'max_instances': 1,  # Prevent overlapping
                'misfire_grace_time': 60  # 60 seconds grace time
            }
        )

        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )

        # Job reference
        self.job = None

        logger.info(f"TradingScheduler initialized (interval: {interval_minutes} minutes)")

    def start(self) -> None:
        """Start the scheduler."""
        try:
            logger.info(f"Starting scheduler with {self.interval_minutes}-minute interval...")

            # Add job
            self.job = self.scheduler.add_job(
                func=self.executor.execute_cycle,
                trigger=IntervalTrigger(minutes=self.interval_minutes),
                id='trading_cycle',
                name='Trading Cycle',
                replace_existing=True
            )

            # Start scheduler
            self.scheduler.start()

            next_run = self.get_next_run_time()
            logger.info(f"✅ Scheduler started. Next cycle: {next_run}")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            raise

    def stop(self, wait: bool = True) -> None:
        """
        Stop the scheduler gracefully.

        Args:
            wait: If True, wait for running jobs to complete
        """
        try:
            logger.info("Stopping scheduler...")

            if wait:
                logger.info("Waiting for current cycle to complete...")

            self.scheduler.shutdown(wait=wait)

            logger.info("✅ Scheduler stopped")

        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}", exc_info=True)

    def pause(self) -> None:
        """Pause the scheduler (can be resumed later)."""
        try:
            self.scheduler.pause()
            logger.info("Scheduler paused")
        except Exception as e:
            logger.error(f"Failed to pause scheduler: {e}")

    def resume(self) -> None:
        """Resume the scheduler."""
        try:
            self.scheduler.resume()
            next_run = self.get_next_run_time()
            logger.info(f"Scheduler resumed. Next cycle: {next_run}")
        except Exception as e:
            logger.error(f"Failed to resume scheduler: {e}")

    def get_next_run_time(self) -> Optional[datetime]:
        """
        Get next scheduled run time.

        Returns:
            Next run time or None if scheduler is not running
        """
        try:
            if self.job:
                return self.job.next_run_time
            return None
        except Exception as e:
            logger.error(f"Failed to get next run time: {e}")
            return None

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.scheduler.running

    def trigger_now(self) -> None:
        """Trigger a cycle immediately (for manual testing)."""
        try:
            logger.info("Triggering cycle manually...")
            result = self.executor.execute_cycle()
            logger.info(f"Manual cycle completed: {result.get('cycle_id')}")
        except Exception as e:
            logger.error(f"Manual trigger failed: {e}", exc_info=True)

    def _job_executed_listener(self, event) -> None:
        """Handle job executed event."""
        logger.debug(f"Job executed: {event.job_id}")

    def _job_error_listener(self, event) -> None:
        """Handle job error event."""
        logger.error(
            f"Job {event.job_id} failed: {event.exception}",
            exc_info=True
        )

    def __repr__(self) -> str:
        """String representation."""
        status = "running" if self.is_running() else "stopped"
        return f"TradingScheduler(interval={self.interval_minutes}min, status={status})"
