"""Trading cycle executor for orchestrating complete trading workflow."""

import logging
import time
from typing import Dict, Any, List
from datetime import datetime

from sqlalchemy.orm import Session

from ..data.collector import DataCollector
from ..orchestration.multi_agent_orchestrator import MultiAgentOrchestrator
from ..trading.trading_orchestrator import TradingOrchestrator
from .state_manager import StateManager

logger = logging.getLogger(__name__)


class TradingCycleExecutor:
    """
    Execute complete trading cycle.

    Orchestrates the full trading workflow:
    1. Collect market data
    2. Generate AI decisions for all agents
    3. Execute decisions with error isolation
    4. Collect metrics and update state
    """

    def __init__(
        self,
        data_collector: DataCollector,
        multi_agent_orchestrator: MultiAgentOrchestrator,
        trading_orchestrator: TradingOrchestrator,
        state_manager: StateManager,
        db_session: Session
    ):
        """
        Initialize trading cycle executor.

        Args:
            data_collector: Data collection component
            multi_agent_orchestrator: Multi-agent decision component
            trading_orchestrator: Trading execution component
            state_manager: State persistence component
            db_session: Database session
        """
        self.data_collector = data_collector
        self.multi_agent_orchestrator = multi_agent_orchestrator
        self.trading_orchestrator = trading_orchestrator
        self.state_manager = state_manager
        self.db = db_session

    def execute_cycle(self) -> Dict[str, Any]:
        """
        Execute one complete trading cycle.

        Returns:
            Cycle execution summary with metrics
        """
        cycle_start = time.time()
        cycle_id = datetime.utcnow().isoformat()

        logger.info("="  * 60)
        logger.info(f"🚀 Trading Cycle Started: {cycle_id}")
        logger.info("=" * 60)

        try:
            # Step 1: Collect market data
            logger.info("📊 Step 1: Collecting market data...")
            data_start = time.time()

            market_data = self.data_collector.collect_all()

            data_duration = time.time() - data_start
            logger.info(f"✅ Market data collected in {data_duration:.2f}s")
            logger.info(f"   Coins: {list(market_data.keys())}")

            # Step 2: Generate AI decisions (all agents in parallel)
            logger.info("🤖 Step 2: Generating AI decisions...")
            ai_start = time.time()

            decisions = self.multi_agent_orchestrator.generate_all_decisions(
                market_data=market_data
            )

            ai_duration = time.time() - ai_start
            logger.info(f"✅ Decisions generated in {ai_duration:.2f}s")
            logger.info(f"   Agents processed: {len(decisions)}")

            # Log decisions summary
            for decision in decisions:
                logger.info(
                    f"   Agent {decision.agent_id}: {decision.action} "
                    f"({decision.coin if hasattr(decision, 'coin') else 'N/A'})"
                )

            # Step 3: Execute decisions (with error isolation)
            logger.info("💼 Step 3: Executing trading decisions...")
            exec_start = time.time()

            results = self._execute_decisions(decisions)

            exec_duration = time.time() - exec_start
            logger.info(f"✅ Decisions executed in {exec_duration:.2f}s")

            # Step 4: Collect metrics and update state
            cycle_duration = time.time() - cycle_start

            summary = {
                "cycle_id": cycle_id,
                "cycle_start_time": cycle_start,
                "cycle_duration": cycle_duration,
                "data_collection_duration": data_duration,
                "ai_decision_duration": ai_duration,
                "trade_execution_duration": exec_duration,
                "agents_processed": len(decisions),
                "successful_executions": sum(1 for r in results if r["success"]),
                "failed_executions": sum(1 for r in results if not r["success"]),
                "results": results
            }

            # Update state
            self.state_manager.increment_cycle_count()

            # Log summary
            logger.info("=" * 60)
            logger.info(f"✅ Trading Cycle Completed: {cycle_id}")
            logger.info(f"   Duration: {cycle_duration:.2f}s")
            logger.info(f"   Success: {summary['successful_executions']}/{len(decisions)}")
            if summary['failed_executions'] > 0:
                logger.warning(f"   Failed: {summary['failed_executions']}/{len(decisions)}")
            logger.info("=" * 60)

            return summary

        except Exception as e:
            cycle_duration = time.time() - cycle_start
            error_msg = f"Cycle {cycle_id} failed after {cycle_duration:.2f}s: {e}"

            logger.error("=" * 60)
            logger.error(f"❌ Trading Cycle Failed: {cycle_id}")
            logger.error(f"   Error: {e}")
            logger.error("=" * 60, exc_info=True)

            # Record error in state
            self.state_manager.record_error(str(e))

            # Return error summary
            return {
                "cycle_id": cycle_id,
                "cycle_start_time": cycle_start,
                "cycle_duration": cycle_duration,
                "success": False,
                "error": str(e)
            }

    def _execute_decisions(self, decisions: List[Any]) -> List[Dict[str, Any]]:
        """
        Execute trading decisions with error isolation.

        Args:
            decisions: List of agent decisions

        Returns:
            List of execution results
        """
        results = []

        for decision in decisions:
            try:
                # Get agent_id from decision
                agent_id = decision.agent_id if hasattr(decision, 'agent_id') else decision.get("agent_id")
                decision_id = decision.id if hasattr(decision, 'id') else decision.get("id")

                logger.info(f"   Executing decision for agent {agent_id}...")

                # Execute decision
                success, error = self.trading_orchestrator.execute_decision(
                    agent_id=agent_id,
                    decision_id=decision_id
                )

                result = {
                    "agent_id": str(agent_id),
                    "decision_id": str(decision_id),
                    "success": success,
                    "error": error
                }

                results.append(result)

                if success:
                    logger.info(f"   ✅ Agent {agent_id}: Success")
                else:
                    logger.warning(f"   ⚠️ Agent {agent_id}: {error}")

            except Exception as e:
                # Error isolation: one agent failure doesn't stop others
                logger.error(f"   ❌ Agent execution failed: {e}", exc_info=True)

                results.append({
                    "agent_id": str(agent_id) if 'agent_id' in locals() else "unknown",
                    "decision_id": str(decision_id) if 'decision_id' in locals() else "unknown",
                    "success": False,
                    "error": str(e)
                })

                # Continue with other agents
                continue

        return results

    def __repr__(self) -> str:
        """String representation."""
        cycle_count = self.state_manager.get_cycle_count()
        return f"TradingCycleExecutor(cycles_executed={cycle_count})"
