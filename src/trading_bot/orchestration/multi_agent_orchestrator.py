"""Multi-Agent Orchestrator - Coordinates parallel decision-making across all agents."""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from src.trading_bot.models.database import TradingAgent, AgentDecision
from src.trading_bot.models.market_data import AccountInfo, Position
from src.trading_bot.ai.agent_manager import AgentManager
from src.trading_bot.ai.prompt_builder import PromptBuilder
from src.trading_bot.ai.decision_parser import DecisionParser, TradingDecision
from src.trading_bot.ai.security import PromptAuditor
from src.trading_bot.config.models import load_config
from src.trading_bot.infrastructure.database import DatabaseManager

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Orchestrates multi-agent trading decisions.

    Responsibilities:
    - Fetch market data and portfolio state
    - Build prompts for each agent
    - Call LLM providers in parallel (async)
    - Parse and validate decisions
    - Save decisions to database
    - Execute trades (delegated to execution engine)

    This is the core component that implements the multi-agent competition pattern.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        agent_manager: AgentManager,
    ):
        """Initialize the Multi-Agent Orchestrator.

        Args:
            db_manager: Database manager
            agent_manager: AgentManager instance
        """
        self.db_manager = db_manager
        self.agent_manager = agent_manager
        self.prompt_builder = PromptBuilder()
        self.decision_parser = DecisionParser()
        
        # Initialize Security Layer
        # We need to load config here or pass it in. For now, loading it is safer.
        try:
            config = load_config()
            security_config = config.security.prompt_audit if config.security else {}
            # Pass db_manager to PromptAuditor
            self.prompt_auditor = PromptAuditor(security_config, db_manager=self.db_manager)
            logger.info(f"Security layer initialized (enabled={self.prompt_auditor.enabled})")
        except Exception as e:
            logger.warning(f"Failed to load security config, using defaults: {e}")
            self.prompt_auditor = PromptAuditor({})

        self.start_time = datetime.utcnow()
        self.invocation_count = 0

        logger.info(
            f"Initialized MultiAgentOrchestrator with {agent_manager.get_agent_count()} agents"
        )

    def generate_all_decisions(
        self,
        market_data: Dict[str, Any],
        trading_orchestrator: Any
    ) -> List[AgentDecision]:
        """Synchronous wrapper to generate decisions for all agents.
        
        Args:
            market_data: Market data for all coins
            trading_orchestrator: TradingOrchestrator instance
            
        Returns:
            List of AgentDecision objects
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(
            self.run_decision_cycle(market_data, trading_orchestrator)
        )

    async def run_decision_cycle(
        self,
        market_data: Dict[str, Dict[str, Any]],
        trading_orchestrator: Any
    ) -> List[AgentDecision]:
        """Run one decision cycle across all agents.

        This is the main entry point for multi-agent decision-making.

        Args:
            market_data: Market data for all coins
            trading_orchestrator: TradingOrchestrator instance

        Returns:
            List of AgentDecision objects (saved to database)
        """
        cycle_start = datetime.utcnow()
        self.invocation_count += 1

        # Get all active agents
        agents = self.agent_manager.agents
        position_manager = trading_orchestrator.position_manager

        logger.info(
            f"Starting decision cycle #{self.invocation_count} | "
            f"Agents: {len(agents)}"
        )

        if not agents:
            logger.warning("No active agents! Skipping decision cycle.")
            return []

        # Run all agents in parallel
        agent_tasks = []
        for agent in agents:
            # Fetch agent-specific state
            try:
                # Get correct executor for this agent
                executor = trading_orchestrator._get_executor(agent)
                
                positions = position_manager.get_current_positions(agent.id, executor=executor)
                account = position_manager.get_account_value(agent.id, executor=executor)
                
                agent_tasks.append(
                    self._run_agent_decision(agent, market_data, positions, account)
                )
            except Exception as e:
                logger.error(f"Failed to fetch state for agent {agent.name}: {e}")
                # Create failed decision immediately
                agent_tasks.append(
                    asyncio.create_task(
                        self._create_failed_decision_async(agent, f"State fetch failed: {e}")
                    )
                )

        # Wait for all agents to complete
        results = await asyncio.gather(*agent_tasks, return_exceptions=True)

        # Process results and save to database
        all_decisions = []
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                logger.error(
                    f"Agent '{agent.name}' failed with error: {result}"
                )
                # Create failed decision record
                decision = self._create_failed_decision(agent, str(result))
                all_decisions.append(decision)
            elif isinstance(result, list):
                all_decisions.extend(result)
            elif result is not None:
                all_decisions.append(result)

        # Log cycle summary
        cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
        successful_decisions = [d for d in all_decisions if d.status == "success"]

        logger.info(
            f"Decision cycle complete | "
            f"Duration: {cycle_duration:.2f}s | "
            f"Success: {len(successful_decisions)}/{len(all_decisions)} | "
            f"Actions: {self._summarize_actions(successful_decisions)}"
        )

        return all_decisions

    async def _create_failed_decision_async(self, agent, error_msg):
        """Async wrapper for creating failed decision."""
        return [self._create_failed_decision(agent, error_msg)]

    async def _run_agent_decision(
        self,
        agent: TradingAgent,
        market_data: Dict[str, Dict[str, Any]],
        positions: List[Position],
        account: AccountInfo
    ) -> List[AgentDecision]:
        """Run decision-making for a single agent.

        Args:
            agent: Trading agent
            market_data: Market data for all coins
            positions: Current positions
            account: Account information

        Returns:
            List of AgentDecision objects
        """
        agent_start = datetime.utcnow()

        logger.info(f"[{agent.name}] Starting decision...")

        try:
            # Fetch recent decisions for context (Memory)
            recent_decisions = self.get_recent_decisions(agent_id=agent.id, limit=5)

            # Build prompt
            prompt = self.prompt_builder.build(
                market_data=market_data,
                positions=positions,
                account=account,
                agent=agent,
                recent_decisions=recent_decisions,
                start_time=self.start_time,
                invocation_count=self.invocation_count
            )

            # Audit and sanitize prompt (Security Layer)
            prompt = self.prompt_auditor.audit(prompt, agent_id=str(agent.id))

            # Get LLM provider
            provider = self.agent_manager.get_llm_provider(agent)

            # Call LLM (async)
            # Use agent's configured max_tokens, defaulting to 2000 if not set or too low
            max_tokens = getattr(agent, 'max_tokens', 2000)
            if max_tokens < 1000:
                max_tokens = 2000

            # Use agent's configured temperature, defaulting to 0.3 if not set
            temperature = getattr(agent, 'temperature', 0.3)

            llm_response = await provider.generate_async(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Parse decisions (returns a list)
            trading_decisions = self.decision_parser.parse(llm_response)

            if not trading_decisions:
                logger.error(f"[{agent.name}] Failed to parse decisions")
                return [self._create_failed_decision(
                    agent,
                    "Failed to parse JSON decisions from LLM response"
                )]

            agent_decisions = []
            for decision in trading_decisions:
                # Validate decision logic
                is_valid, error_msg = self.decision_parser.validate_decision_logic(
                    decision=decision,
                    current_positions=positions,
                    account_value=account.account_value
                )

                if not is_valid:
                    logger.warning(f"[{agent.name}] Invalid decision for {decision.coin}: {error_msg}")
                    agent_decisions.append(self._create_failed_decision(agent, error_msg))
                    continue

                # Create successful decision record
                agent_decision = self._create_successful_decision(
                    agent=agent,
                    decision=decision,
                    llm_response=llm_response,
                    prompt_content=prompt,
                    duration_ms=int((datetime.utcnow() - agent_start).total_seconds() * 1000)
                )
                agent_decisions.append(agent_decision)

                logger.info(
                    f"[{agent.name}] Decision: {decision.action} {decision.coin} | "
                    f"Confidence: {decision.confidence:.2f}"
                )

            return agent_decisions

        except Exception as e:
            logger.error(f"[{agent.name}] Unexpected error: {e}", exc_info=True)
            return [self._create_failed_decision(
                agent, 
                str(e),
                prompt_content=prompt if 'prompt' in locals() else None
            )]

    def _create_successful_decision(
        self,
        agent: TradingAgent,
        decision: TradingDecision,
        llm_response: str,
        prompt_content: str,
        duration_ms: int
    ) -> AgentDecision:
        """Create a successful AgentDecision record.

        Args:
            agent: Trading agent
            decision: Parsed trading decision
            llm_response: Raw LLM response
            prompt_content: Full prompt sent to LLM
            duration_ms: Decision duration in milliseconds

        Returns:
            AgentDecision object (saved to database)
        """
        agent_decision = AgentDecision(
            agent_id=agent.id,
            timestamp=datetime.utcnow(),
            status="success",
            action=decision.action,
            coin=decision.coin,
            size_usd=decision.size_usd,
            leverage=decision.leverage,
            stop_loss_price=decision.stop_loss_price,
            take_profit_price=decision.take_profit_price,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
            chain_of_thought=decision.chain_of_thought,
            llm_response=llm_response,
            prompt_content=prompt_content,
            execution_time_ms=duration_ms,
            error_message=None
        )

        with self.db_manager.session_scope() as session:
            session.add(agent_decision)
            # Commit handled by session_scope
            session.flush()
            session.refresh(agent_decision)
            session.expunge(agent_decision)

        return agent_decision

    def _create_failed_decision(
        self,
        agent: TradingAgent,
        error_message: str,
        prompt_content: Optional[str] = None
    ) -> AgentDecision:
        """Create a failed AgentDecision record.

        Args:
            agent: Trading agent
            error_message: Error description
            prompt_content: Full prompt sent to LLM (optional)

        Returns:
            AgentDecision object (saved to database)
        """
        agent_decision = AgentDecision(
            agent_id=agent.id,
            timestamp=datetime.utcnow(),
            status="failed",
            action="HOLD",  # Default to HOLD on failure
            coin="BTC",  # Default coin
            size_usd=0.0,
            leverage=1,
            stop_loss_price=0.0,
            take_profit_price=0.0,
            confidence=0.0,
            reasoning="Decision failed",
            llm_response=None,
            prompt_content=prompt_content,
            execution_time_ms=0,
            error_message=error_message
        )

        with self.db_manager.session_scope() as session:
            session.add(agent_decision)
            # Commit handled by session_scope
            session.flush()
            session.refresh(agent_decision)
            session.expunge(agent_decision)

        return agent_decision

    def _summarize_actions(self, decisions: List[AgentDecision]) -> str:
        """Summarize actions from decisions.

        Args:
            decisions: List of successful decisions

        Returns:
            Summary string like "3 HOLD, 1 OPEN_LONG"
        """
        if not decisions:
            return "none"

        action_counts = {}
        for decision in decisions:
            action = decision.action
            action_counts[action] = action_counts.get(action, 0) + 1

        summary_parts = [
            f"{count} {action}" for action, count in action_counts.items()
        ]

        return ", ".join(summary_parts)

    def get_recent_decisions(
        self,
        agent_id: Optional[int] = None,
        limit: int = 10
    ) -> List[AgentDecision]:
        """Get recent decisions from database.

        Args:
            agent_id: Optional agent ID filter
            limit: Maximum number of decisions to return

        Returns:
            List of AgentDecision objects
        """
        with self.db_manager.session_scope() as session:
            query = session.query(AgentDecision)

            if agent_id is not None:
                query = query.filter(AgentDecision.agent_id == agent_id)

            decisions = (
                query
                .order_by(AgentDecision.timestamp.desc())
                .limit(limit)
                .all()
            )
            session.expunge_all()
            return decisions

    def get_agent_performance(self, agent_id: int) -> Dict[str, Any]:
        """Get performance statistics for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Dictionary with performance stats
        """
        with self.db_manager.session_scope() as session:
            decisions = (
                session.query(AgentDecision)
                .filter(AgentDecision.agent_id == agent_id)
                .all()
            )
            session.expunge_all()

        if not decisions:
            return {
                "total_decisions": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0,
                "avg_execution_time_ms": 0.0,
                "action_distribution": {}
            }

        total = len(decisions)
        successful = sum(1 for d in decisions if d.status == "success")
        confidences = [d.confidence for d in decisions if d.status == "success"]
        execution_times = [d.execution_time_ms for d in decisions if d.execution_time_ms]

        # Action distribution
        action_dist = {}
        for decision in decisions:
            action = decision.action
            action_dist[action] = action_dist.get(action, 0) + 1

        return {
            "total_decisions": total,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
            "avg_execution_time_ms": sum(execution_times) / len(execution_times) if execution_times else 0.0,
            "action_distribution": action_dist
        }
