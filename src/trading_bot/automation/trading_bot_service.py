"""Trading bot service for lifecycle management."""

import logging
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Event

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from ..config.models import Config
from ..data.hyperliquid_client import HyperliquidClient
from ..data.collector import DataCollector
from ..orchestration.multi_agent_orchestrator import MultiAgentOrchestrator
from ..ai.agent_manager import AgentManager
from ..trading.hyperliquid_executor import HyperLiquidExecutor
from ..trading.order_manager import OrderManager
from ..trading.position_manager import PositionManager
from ..risk.risk_manager import RiskManager
from ..trading.trading_orchestrator import TradingOrchestrator
from .scheduler import TradingScheduler
from .trading_cycle_executor import TradingCycleExecutor
from .state_manager import StateManager

logger = logging.getLogger(__name__)


class TradingBotService:
    """
    Trading bot service for lifecycle management.

    Manages:
    - Configuration loading
    - Component initialization
    - Database connection pool
    - Scheduler lifecycle
    - Graceful shutdown
    """

    def __init__(self, config: Config):
        """
        Initialize trading bot service.

        Args:
            config: Trading bot configuration
        """
        self.config = config
        self.running = False
        self.shutdown_event = Event()

        # Components (initialized in start())
        self.db_engine: Optional[Any] = None
        self.db_session_maker: Optional[sessionmaker] = None
        self.db_session: Optional[Session] = None

        self.info_client: Optional[HyperliquidClient] = None
        self.data_collector: Optional[DataCollector] = None
        self.agent_manager: Optional[AgentManager] = None
        self.multi_agent_orchestrator: Optional[MultiAgentOrchestrator] = None

        self.executor: Optional[HyperLiquidExecutor] = None
        self.order_manager: Optional[OrderManager] = None
        self.position_manager: Optional[PositionManager] = None
        self.risk_manager: Optional[RiskManager] = None
        self.trading_orchestrator: Optional[TradingOrchestrator] = None

        self.cycle_executor: Optional[TradingCycleExecutor] = None
        self.scheduler: Optional[TradingScheduler] = None
        self.state_manager: Optional[StateManager] = None

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("TradingBotService initialized")

    def start(self) -> bool:
        """
        Start the trading bot service.

        Returns:
            True if started successfully, False otherwise
        """
        try:
            logger.info("Starting TradingBotService...")

            # 1. Initialize database
            if not self._init_database():
                return False

            # 2. Health checks
            if not self._health_check():
                return False

            # 3. Initialize Phase 1 components (Data Collection)
            if not self._init_phase1_components():
                return False

            # 4. Initialize Phase 2 components (AI Integration)
            if not self._init_phase2_components():
                return False

            # 5. Initialize Phase 3 components (Trading Execution)
            if not self._init_phase3_components():
                return False

            # 6. Initialize Phase 4 components (Automation)
            if not self._init_phase4_components():
                return False

            # 7. Start scheduler
            self.scheduler.start()

            self.running = True
            logger.info("✅ TradingBotService started successfully")

            # 8. Main loop (wait for shutdown signal)
            self._run_loop()

            return True

        except Exception as e:
            logger.error(f"Failed to start TradingBotService: {e}", exc_info=True)
            self.stop()
            return False

    def stop(self) -> bool:
        """
        Stop the trading bot gracefully.

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping TradingBotService...")

            # Signal shutdown
            self.shutdown_event.set()
            self.running = False

            # Stop scheduler (will wait for current cycle to complete)
            if self.scheduler:
                logger.info("Stopping scheduler...")
                self.scheduler.stop()

            # Close database connections
            if self.db_session:
                logger.info("Closing database session...")
                self.db_session.close()

            if self.db_engine:
                logger.info("Disposing database engine...")
                self.db_engine.dispose()

            logger.info("✅ TradingBotService stopped successfully")
            return True

        except Exception as e:
            logger.error(f"Error stopping TradingBotService: {e}", exc_info=True)
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get current service status.

        Returns:
            Status dictionary
        """
        status = {
            "running": self.running,
            "components_initialized": {
                "database": self.db_engine is not None,
                "data_collector": self.data_collector is not None,
                "multi_agent_orchestrator": self.multi_agent_orchestrator is not None,
                "trading_orchestrator": self.trading_orchestrator is not None,
                "scheduler": self.scheduler is not None
            }
        }

        # Add state information if available
        if self.state_manager:
            try:
                state = self.state_manager.load_state()
                if state:
                    status.update({
                        "uptime_seconds": (time.time() - state.get("service_start_time", time.time())),
                        "cycle_count": state.get("cycle_count", 0),
                        "last_cycle_time": state.get("last_cycle_time"),
                        "last_error": state.get("last_error")
                    })
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")

        # Add scheduler status
        if self.scheduler:
            try:
                status["next_run_time"] = self.scheduler.get_next_run_time()
            except Exception as e:
                logger.warning(f"Failed to get next run time: {e}")

        return status

    def _init_database(self) -> bool:
        """Initialize database connection."""
        try:
            logger.info("Initializing database...")

            db_url = self.config.database.url

            # Create engine with connection pool
            self.db_engine = create_engine(
                db_url,
                pool_size=self.config.database.pool_size,
                max_overflow=self.config.database.max_overflow,
                pool_timeout=self.config.database.pool_timeout,
                pool_recycle=3600,  # Recycle connections after 1 hour
                echo=False
            )

            # Create session maker
            self.db_session_maker = sessionmaker(bind=self.db_engine)

            # Create session
            self.db_session = self.db_session_maker()

            logger.info("✅ Database initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            return False

    def _health_check(self) -> bool:
        """Perform health checks."""
        try:
            logger.info("Performing health checks...")

            # Check database connection
            try:
                self.db_session.execute(text("SELECT 1"))
                logger.info("✅ Database connection OK")
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                return False

            # Check HyperLiquid API (Info API)
            try:
                test_client = HyperliquidClient(
                    base_url=self.config.hyperliquid.info_url,
                    timeout=10
                )
                # Try to get a price
                price = test_client.get_price("BTC")
                if price:
                    logger.info(f"✅ HyperLiquid API connection OK (BTC price: ${price.price:.2f})")
                else:
                    logger.error("HyperLiquid API returned no data")
                    return False
            except Exception as e:
                logger.error(f"HyperLiquid API health check failed: {e}")
                return False

            logger.info("✅ All health checks passed")
            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return False

    def _init_phase1_components(self) -> bool:
        """Initialize Phase 1 components (Data Collection)."""
        try:
            logger.info("Initializing Phase 1 components...")

            # Info API client
            self.info_client = HyperliquidClient(
                base_url=self.config.hyperliquid.info_url,
                timeout=self.config.hyperliquid.timeout
            )

            # Data collector
            self.data_collector = DataCollector(
                exchange_config=self.config.hyperliquid,
                trading_config=self.config.trading
            )

            logger.info("✅ Phase 1 components initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Phase 1 components: {e}", exc_info=True)
            return False

    def _init_phase2_components(self) -> bool:
        """Initialize Phase 2 components (AI Integration)."""
        try:
            logger.info("Initializing Phase 2 components...")

            # Agent manager
            self.agent_manager = AgentManager(
                db_session=self.db_session,
                llm_config=self.config.llm
            )

            # Multi-agent orchestrator
            self.multi_agent_orchestrator = MultiAgentOrchestrator(
                db_session=self.db_session,
                agent_manager=self.agent_manager
            )

            logger.info("✅ Phase 2 components initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Phase 2 components: {e}", exc_info=True)
            return False

    def _init_phase3_components(self) -> bool:
        """Initialize Phase 3 components (Trading Execution)."""
        try:
            logger.info("Initializing Phase 3 components...")

            # Initialize executors for all configured accounts
            self.executors = {}
            
            # Identify accounts used by enabled agents
            enabled_accounts = {
                agent.account 
                for agent in self.config.agents 
                if agent.enabled and agent.account
            }
            
            # 1. Load from new 'accounts' list
            if self.config.hyperliquid.accounts:
                for account in self.config.hyperliquid.accounts:
                    # Skip initialization if account is not used by any enabled agent
                    if account.name not in enabled_accounts:
                        logger.info(f"Skipping initialization for unused account: {account.name}")
                        continue

                    try:
                        executor = HyperLiquidExecutor(
                            base_url=self.config.hyperliquid.exchange_url,
                            private_key=account.private_key,
                            vault_address=account.vault_address,
                            dry_run=self.config.dry_run.enabled,
                            timeout=self.config.hyperliquid.timeout
                        )
                        self.executors[account.name] = executor
                        logger.info(f"Initialized executor for account: {account.name}")
                    except Exception as e:
                        logger.error(f"Failed to initialize executor for {account.name}: {e}")

            # 2. Fallback to legacy 'private_key' if no accounts or specific legacy config
            if not self.executors and self.config.hyperliquid.private_key:
                logger.info("Using legacy single-account configuration")
                self.executors['default'] = HyperLiquidExecutor(
                    base_url=self.config.hyperliquid.exchange_url,
                    private_key=self.config.hyperliquid.private_key,
                    vault_address=self.config.hyperliquid.vault_address,
                    dry_run=self.config.dry_run.enabled,
                    timeout=self.config.hyperliquid.timeout
                )

            if not self.executors:
                raise ValueError("No valid trading accounts configured! Check config.yaml")

            # Set primary executor (for backward compatibility)
            self.executor = next(iter(self.executors.values()))

            # Order manager (needs to be aware of multiple executors, or we pass orchestrator)
            # For now, OrderManager might need refactoring, but let's see.
            # Actually, OrderManager takes 'executor'. We might need to update it too.
            # Or better, TradingOrchestrator handles the routing, and OrderManager just executes?
            # No, OrderManager executes. So OrderManager needs the map or Orchestrator passes the right executor.
            
            # Let's pass the map to TradingOrchestrator, and let it handle the routing.
            # But OrderManager is initialized here.
            
            # Temporary fix: OrderManager still takes one executor (the default one).
            # We will update TradingOrchestrator to use the map and pass the right executor to OrderManager methods?
            # Or create multiple OrderManagers?
            
            # Let's update TradingOrchestrator to take the map.
            
            self.order_manager = OrderManager(
                executor=self.executor, # Default one
                db_session=self.db_session
            )

            # Position manager
            self.position_manager = PositionManager(
                info_client=self.info_client,
                db_session=self.db_session,
                executor=self.executor # Default one
            )

            # Risk manager
            self.risk_manager = RiskManager(
                position_manager=self.position_manager,
                db_session=self.db_session
            )

            # Trading orchestrator
            self.trading_orchestrator = TradingOrchestrator(
                executors=self.executors, # Pass the map!
                default_executor=self.executor,
                order_manager=self.order_manager,
                position_manager=self.position_manager,
                risk_manager=self.risk_manager,
                db_session=self.db_session
            )

            logger.info("✅ Phase 3 components initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Phase 3 components: {e}", exc_info=True)
            return False

    def _init_phase4_components(self) -> bool:
        """Initialize Phase 4 components (Automation)."""
        try:
            logger.info("Initializing Phase 4 components...")

            # State manager
            self.state_manager = StateManager(db_session=self.db_session)

            # Trading cycle executor
            self.cycle_executor = TradingCycleExecutor(
                data_collector=self.data_collector,
                multi_agent_orchestrator=self.multi_agent_orchestrator,
                trading_orchestrator=self.trading_orchestrator,
                state_manager=self.state_manager,
                db_session=self.db_session
            )

            # Scheduler
            self.scheduler = TradingScheduler(
                executor=self.cycle_executor,
                interval_minutes=self.config.trading.cycle_interval_minutes
            )

            logger.info("✅ Phase 4 components initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Phase 4 components: {e}", exc_info=True)
            return False

    def _run_loop(self) -> None:
        """Main service loop (wait for shutdown signal)."""
        try:
            logger.info("TradingBotService is running. Press Ctrl+C to stop.")

            # Wait for shutdown signal
            while not self.shutdown_event.is_set():
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
        sys.exit(0)

    def __repr__(self) -> str:
        """String representation."""
        return f"TradingBotService(running={self.running})"
