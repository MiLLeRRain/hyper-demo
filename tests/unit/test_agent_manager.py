import pytest
from unittest.mock import Mock, MagicMock, patch
from src.trading_bot.ai.agent_manager import AgentManager
from src.trading_bot.models.database import TradingAgent
from src.trading_bot.config.models import LLMConfig, LLMModelConfig

class TestAgentManager:
    @pytest.fixture
    def mock_db_session(self):
        return MagicMock()

    @pytest.fixture
    def mock_llm_config(self):
        config = MagicMock(spec=LLMConfig)
        config.models = {
            "gpt-4": MagicMock(
                provider="official",
                official={"api_key": "key", "base_url": "url", "model_name": "gpt-4"}
            ),
            "claude-3": MagicMock(
                provider="openrouter",
                openrouter={"api_key": "key", "base_url": "url", "model_name": "claude-3"}
            )
        }
        return config

    @pytest.fixture
    def mock_agents(self):
        agent1 = MagicMock(spec=TradingAgent)
        agent1.id = 1
        agent1.name = "Agent 1"
        agent1.status = "active"
        agent1.llm_model = "gpt-4"

        agent2 = MagicMock(spec=TradingAgent)
        agent2.id = 2
        agent2.name = "Agent 2"
        agent2.status = "active"
        agent2.llm_model = "claude-3"
        
        return [agent1, agent2]

    @patch("src.trading_bot.ai.agent_manager.OfficialAPIProvider")
    @patch("src.trading_bot.ai.agent_manager.OpenRouterProvider")
    def test_init_loads_agents(self, mock_openrouter, mock_official, mock_db_session, mock_llm_config, mock_agents):
        # Setup DB query result
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_agents
        
        manager = AgentManager(mock_db_session, mock_llm_config)
        
        assert len(manager.agents) == 2
        assert len(manager.llm_providers) == 2
        assert "1" in manager.llm_providers
        assert "2" in manager.llm_providers
        
        mock_official.assert_called_once()
        mock_openrouter.assert_called_once()

    def test_create_llm_provider_unknown_model(self, mock_db_session, mock_llm_config):
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        manager = AgentManager(mock_db_session, mock_llm_config)
        
        agent = MagicMock(spec=TradingAgent)
        agent.llm_model = "unknown-model"
        
        with pytest.raises(ValueError, match="Model 'unknown-model' not found"):
            manager._create_llm_provider(agent)

    def test_create_llm_provider_invalid_config(self, mock_db_session, mock_llm_config):
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        # Setup invalid config
        mock_llm_config.models["bad-model"] = MagicMock(provider="official", official=None)
        
        manager = AgentManager(mock_db_session, mock_llm_config)
        
        agent = MagicMock(spec=TradingAgent)
        agent.llm_model = "bad-model"
        
        with pytest.raises(ValueError, match="no official config"):
            manager._create_llm_provider(agent)

    def test_get_llm_provider(self, mock_db_session, mock_llm_config, mock_agents):
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_agents
        
        with patch("src.trading_bot.ai.agent_manager.OfficialAPIProvider"), \
             patch("src.trading_bot.ai.agent_manager.OpenRouterProvider"):
            manager = AgentManager(mock_db_session, mock_llm_config)
            
            provider = manager.get_llm_provider(mock_agents[0])
            assert provider is not None
            
            # Test non-existent agent
            unknown_agent = MagicMock(spec=TradingAgent)
            unknown_agent.id = 999
            unknown_agent.name = "Unknown"
            
            with pytest.raises(KeyError):
                manager.get_llm_provider(unknown_agent)

    def test_reload_agents(self, mock_db_session, mock_llm_config, mock_agents):
        # Initial load empty
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        manager = AgentManager(mock_db_session, mock_llm_config)
        assert len(manager.agents) == 0
        
        # Reload with agents
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_agents
        with patch("src.trading_bot.ai.agent_manager.OfficialAPIProvider"), \
             patch("src.trading_bot.ai.agent_manager.OpenRouterProvider"):
            manager.reload_agents()
            assert len(manager.agents) == 2

    def test_failed_provider_creation_removes_agent(self, mock_db_session, mock_llm_config, mock_agents):
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_agents
        
        # Make provider creation fail for first agent
        with patch("src.trading_bot.ai.agent_manager.OfficialAPIProvider", side_effect=Exception("API Error")), \
             patch("src.trading_bot.ai.agent_manager.OpenRouterProvider"):
            
            manager = AgentManager(mock_db_session, mock_llm_config)
            
            # Should only have 1 agent (the second one)
            assert len(manager.agents) == 1
            assert manager.agents[0].id == 2
