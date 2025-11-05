"""Agent Manager - Manages all trading agents and their LLM providers."""

import logging
from typing import Dict, List

from sqlalchemy.orm import Session

from src.trading_bot.models.database import TradingAgent
from src.trading_bot.config.models import LLMConfig
from src.trading_bot.ai.providers import BaseLLMProvider, OfficialAPIProvider, OpenRouterProvider

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages all trading agents.

    Responsibilities:
    - Load active agents from database
    - Create LLM providers for each agent
    - Provide access to agents and their providers
    - Support hot-reload of agents
    """

    def __init__(self, db_session: Session, llm_config: LLMConfig):
        """Initialize the Agent Manager.

        Args:
            db_session: SQLAlchemy database session
            llm_config: LLM configuration from config.yaml
        """
        self.db = db_session
        self.llm_config = llm_config
        self.agents: List[TradingAgent] = []
        self.llm_providers: Dict[str, BaseLLMProvider] = {}  # agent_id -> provider
        self._load_active_agents()

    def _load_active_agents(self):
        """Load active agents from database and create their LLM providers."""
        # Query active agents
        self.agents = (
            self.db.query(TradingAgent)
            .filter(TradingAgent.status == "active")
            .all()
        )

        logger.info(f"Loaded {len(self.agents)} active trading agents from database")

        # Create LLM provider for each agent
        for agent in self.agents:
            try:
                provider = self._create_llm_provider(agent)
                self.llm_providers[str(agent.id)] = provider
                logger.info(
                    f"Created LLM provider for agent '{agent.name}' "
                    f"(model: {agent.llm_model})"
                )
            except Exception as e:
                logger.error(
                    f"Failed to create LLM provider for agent '{agent.name}': {e}"
                )
                # Remove this agent from the list if provider creation fails
                self.agents.remove(agent)

        if not self.agents:
            logger.warning(
                "No active agents with valid LLM providers! "
                "Create agents using: bot agent create"
            )

    def _create_llm_provider(self, agent: TradingAgent) -> BaseLLMProvider:
        """Create LLM provider for an agent.

        Args:
            agent: TradingAgent instance

        Returns:
            BaseLLMProvider instance (OfficialAPIProvider or OpenRouterProvider)

        Raises:
            ValueError: If model not found in config or unknown provider type
        """
        model_name = agent.llm_model

        # Check if model exists in config
        if model_name not in self.llm_config.models:
            raise ValueError(
                f"Model '{model_name}' not found in config.llm.models. "
                f"Available models: {list(self.llm_config.models.keys())}"
            )

        model_config = self.llm_config.models[model_name]
        provider_type = model_config.provider

        # Create provider based on type
        if provider_type == "official":
            if not model_config.official:
                raise ValueError(
                    f"Model '{model_name}' has provider='official' "
                    f"but no official config"
                )
            provider_cfg = model_config.official
            return OfficialAPIProvider(
                api_key=provider_cfg.api_key,
                base_url=provider_cfg.base_url,
                model_name=provider_cfg.model_name,
                timeout=provider_cfg.timeout,
            )

        elif provider_type == "openrouter":
            if not model_config.openrouter:
                raise ValueError(
                    f"Model '{model_name}' has provider='openrouter' "
                    f"but no openrouter config"
                )
            provider_cfg = model_config.openrouter
            return OpenRouterProvider(
                api_key=provider_cfg.api_key,
                base_url=provider_cfg.base_url,
                model_name=provider_cfg.model_name,
                timeout=provider_cfg.timeout,
            )

        else:
            raise ValueError(
                f"Unknown provider type '{provider_type}' for model '{model_name}'. "
                f"Must be 'official' or 'openrouter'"
            )

    def get_llm_provider(self, agent: TradingAgent) -> BaseLLMProvider:
        """Get LLM provider for an agent.

        Args:
            agent: TradingAgent instance

        Returns:
            BaseLLMProvider for this agent

        Raises:
            KeyError: If agent not found in providers dict
        """
        agent_id = str(agent.id)
        if agent_id not in self.llm_providers:
            raise KeyError(f"No LLM provider found for agent {agent.name} ({agent_id})")
        return self.llm_providers[agent_id]

    def reload_agents(self):
        """Reload agents from database (supports hot-reload).

        This allows adding/removing agents without restarting the system.
        """
        logger.info("Reloading agents from database...")
        old_count = len(self.agents)

        # Clear existing agents and providers
        self.agents.clear()
        self.llm_providers.clear()

        # Reload
        self._load_active_agents()

        new_count = len(self.agents)
        logger.info(f"Agent reload complete: {old_count} -> {new_count} agents")

    def get_agent_count(self) -> int:
        """Get count of active agents.

        Returns:
            Number of active agents
        """
        return len(self.agents)

    def get_provider_stats(self) -> Dict[str, dict]:
        """Get statistics for all LLM providers.

        Returns:
            Dictionary mapping agent_id to provider stats
        """
        return {
            agent_id: provider.get_stats()
            for agent_id, provider in self.llm_providers.items()
        }
