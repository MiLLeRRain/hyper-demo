"""Integration tests for Phase 2 AI components."""

import pytest
import asyncio
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.trading_bot.models.database import Base, TradingAgent, AgentDecision
from src.trading_bot.models.market_data import AccountInfo, Position
from src.trading_bot.config.models import LLMConfig, ModelConfig, ProviderConfig
from src.trading_bot.ai.agent_manager import AgentManager
from src.trading_bot.ai.prompt_builder import PromptBuilder
from src.trading_bot.ai.decision_parser import DecisionParser
from src.trading_bot.orchestration.multi_agent_orchestrator import MultiAgentOrchestrator


@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def mock_llm_config():
    """Create mock LLM configuration."""
    return LLMConfig(
        models={
            "deepseek-test": ModelConfig(
                provider="official",
                official=ProviderConfig(
                    api_key="test-key",
                    base_url="https://api.test.com/v1",
                    model_name="deepseek-chat",
                    timeout=30
                )
            )
        }
    )


@pytest.fixture
def test_agent(test_db):
    """Create a test trading agent."""
    agent = TradingAgent(
        id=uuid4(),
        name="Test Agent",
        llm_model="deepseek-test",
        exchange_account="test_account",
        initial_balance=Decimal("10000.00"),
        max_position_size=Decimal("20.0"),
        max_leverage=10,
        stop_loss_pct=Decimal("2.0"),
        take_profit_pct=Decimal("5.0"),
        strategy_description="Test strategy",
        status="active"
    )
    test_db.add(agent)
    test_db.commit()
    test_db.refresh(agent)
    return agent


@pytest.fixture
def mock_market_data():
    """Create mock market data for 6 coins."""
    return {
        "BTC": {
            "price": 51000.0,
            "3m": {"ema": 50500.0, "macd": 150.5, "macd_signal": 120.0, "rsi": 65.5, "atr": 500.0},
            "4h": {"ema": 50000.0, "macd": 200.0, "macd_signal": 180.0, "rsi": 60.0, "atr": 800.0}
        },
        "ETH": {
            "price": 2950.0,
            "3m": {"ema": 2980.0, "macd": -20.5, "macd_signal": -15.0, "rsi": 45.0, "atr": 50.0},
            "4h": {"ema": 3000.0, "macd": -50.0, "macd_signal": -40.0, "rsi": 42.0, "atr": 80.0}
        },
        "SOL": {
            "price": 150.0,
            "3m": {"ema": 149.0, "macd": 2.5, "macd_signal": 2.0, "rsi": 55.0, "atr": 5.0},
            "4h": {"ema": 148.0, "macd": 5.0, "macd_signal": 4.0, "rsi": 58.0, "atr": 8.0}
        },
        "BNB": {
            "price": 300.0,
            "3m": {"ema": 298.0, "macd": 1.5, "macd_signal": 1.0, "rsi": 52.0, "atr": 3.0},
            "4h": {"ema": 297.0, "macd": 3.0, "macd_signal": 2.5, "rsi": 54.0, "atr": 5.0}
        },
        "DOGE": {
            "price": 0.08,
            "3m": {"ema": 0.079, "macd": 0.001, "macd_signal": 0.0008, "rsi": 50.0, "atr": 0.002},
            "4h": {"ema": 0.078, "macd": 0.002, "macd_signal": 0.0015, "rsi": 51.0, "atr": 0.003}
        },
        "XRP": {
            "price": 0.55,
            "3m": {"ema": 0.54, "macd": 0.01, "macd_signal": 0.008, "rsi": 58.0, "atr": 0.01},
            "4h": {"ema": 0.53, "macd": 0.02, "macd_signal": 0.015, "rsi": 60.0, "atr": 0.015}
        }
    }


@pytest.fixture
def mock_account():
    """Create mock account info."""
    return AccountInfo(
        account_value=10000.0,
        withdrawable=8000.0,
        margin_used=2000.0,
        unrealized_pnl=500.0
    )


class TestAgentManagerIntegration:
    """Integration tests for AgentManager with database."""

    def test_load_active_agents(self, test_db, test_agent, mock_llm_config):
        """Test loading active agents from database."""
        agent_manager = AgentManager(test_db, mock_llm_config)

        assert agent_manager.get_agent_count() == 1
        assert len(agent_manager.agents) == 1
        assert agent_manager.agents[0].name == "Test Agent"

    def test_agent_manager_creates_providers(self, test_db, test_agent, mock_llm_config):
        """Test that AgentManager creates LLM providers for agents."""
        agent_manager = AgentManager(test_db, mock_llm_config)

        provider = agent_manager.get_llm_provider(test_agent)
        assert provider is not None
        assert provider.model_name == "deepseek-chat"

    def test_agent_manager_reload(self, test_db, test_agent, mock_llm_config):
        """Test hot-reload of agents."""
        agent_manager = AgentManager(test_db, mock_llm_config)
        assert agent_manager.get_agent_count() == 1

        # Add another agent
        new_agent = TradingAgent(
            id=uuid4(),
            name="New Agent",
            llm_model="deepseek-test",
            exchange_account="test_account_2",
            initial_balance=Decimal("5000.00"),
            status="active"
        )
        test_db.add(new_agent)
        test_db.commit()

        # Reload
        agent_manager.reload_agents()
        assert agent_manager.get_agent_count() == 2


class TestPromptBuilderIntegration:
    """Integration tests for PromptBuilder."""

    def test_build_full_prompt(self, test_agent, mock_market_data, mock_account):
        """Test building a complete prompt."""
        builder = PromptBuilder()
        positions = []

        prompt = builder.build(
            market_data=mock_market_data,
            positions=positions,
            account=mock_account,
            agent=test_agent
        )

        # Verify prompt structure
        assert "HyperLiquid AI Trading System" in prompt
        assert "Portfolio Status" in prompt
        assert "Market Data" in prompt
        assert "Risk Management Constraints" in prompt
        assert "Your Task" in prompt

        # Verify agent-specific data
        assert "20.00%" in prompt  # max_position_size
        assert "10x" in prompt  # max_leverage
        assert "Test strategy" in prompt

        # Verify market data
        assert "BTC" in prompt
        assert "51,000.00" in prompt
        assert "ETH" in prompt
        assert "2,950.00" in prompt

    def test_build_prompt_with_positions(self, test_agent, mock_market_data, mock_account):
        """Test building prompt with existing positions."""
        builder = PromptBuilder()
        positions = [
            Position(
                coin="BTC",
                side="long",
                size=0.1,
                entry_price=50000.0,
                mark_price=51000.0,
                position_value=5100.0,
                unrealized_pnl=100.0,
                leverage=5,
                liquidation_price=45000.0
            )
        ]

        prompt = builder.build(
            market_data=mock_market_data,
            positions=positions,
            account=mock_account,
            agent=test_agent
        )

        assert "BTC" in prompt
        assert "long" in prompt.lower()
        assert "50,000.00" in prompt


class TestDecisionParserIntegration:
    """Integration tests for DecisionParser."""

    def test_parse_and_validate_complete_flow(self):
        """Test parsing and validating a complete LLM response."""
        parser = DecisionParser()

        llm_response = """
I've analyzed the market conditions and here's my decision:

```json
{
  "reasoning": "BTC shows strong bullish momentum with RSI at 65 and MACD golden cross on 4h chart",
  "action": "OPEN_LONG",
  "coin": "BTC",
  "size_usd": 1000.0,
  "leverage": 3,
  "stop_loss_price": 49000.0,
  "take_profit_price": 53000.0,
  "confidence": 0.75
}
```

This is a high-probability setup based on technical indicators.
"""

        decision = parser.parse(llm_response)

        assert decision is not None
        assert decision.action == "OPEN_LONG"
        assert decision.coin == "BTC"
        assert decision.size_usd == 1000.0
        assert decision.leverage == 3
        assert decision.confidence == 0.75

        # Test validation
        is_valid, error_msg = parser.validate_decision_logic(
            decision=decision,
            current_positions=[],
            account_value=10000.0
        )

        assert is_valid
        assert error_msg is None


@pytest.mark.asyncio
class TestMultiAgentOrchestratorIntegration:
    """Integration tests for MultiAgentOrchestrator."""

    async def test_run_decision_cycle(self, test_db, test_agent, mock_llm_config, mock_market_data, mock_account):
        """Test running a complete decision cycle."""
        agent_manager = AgentManager(test_db, mock_llm_config)
        orchestrator = MultiAgentOrchestrator(test_db, agent_manager)

        # Mock LLM response
        mock_llm_response = """
```json
{
  "reasoning": "Market conditions are unclear with mixed signals, better to wait for confirmation",
  "action": "HOLD",
  "coin": "BTC",
  "size_usd": 0.0,
  "leverage": 1,
  "stop_loss_price": 0.0,
  "take_profit_price": 0.0,
  "confidence": 0.5
}
```
"""

        # Patch the LLM provider's generate_async method
        with patch.object(agent_manager.llm_providers[str(test_agent.id)], 'generate_async',
                          new_callable=AsyncMock, return_value=mock_llm_response):

            decisions = await orchestrator.run_decision_cycle(
                market_data=mock_market_data,
                positions=[],
                account=mock_account
            )

            # Verify decision was created
            assert len(decisions) == 1
            decision = decisions[0]

            assert decision.agent_id == test_agent.id
            assert decision.status == "success"
            assert decision.action == "HOLD"
            assert decision.coin == "BTC"
            assert decision.confidence == Decimal("0.50")

            # Verify decision was saved to database
            db_decision = test_db.query(AgentDecision).filter(
                AgentDecision.id == decision.id
            ).first()

            assert db_decision is not None
            assert db_decision.action == "HOLD"

    async def test_run_decision_cycle_with_multiple_agents(
        self, test_db, test_agent, mock_llm_config, mock_market_data, mock_account
    ):
        """Test decision cycle with multiple agents running in parallel."""
        # Create second agent
        agent2 = TradingAgent(
            id=uuid4(),
            name="Test Agent 2",
            llm_model="deepseek-test",
            exchange_account="test_account_2",
            initial_balance=Decimal("5000.00"),
            status="active"
        )
        test_db.add(agent2)
        test_db.commit()

        agent_manager = AgentManager(test_db, mock_llm_config)
        orchestrator = MultiAgentOrchestrator(test_db, agent_manager)

        # Mock different responses for each agent
        mock_responses = {
            str(test_agent.id): """
```json
{
  "reasoning": "BTC showing bullish momentum, opening long position",
  "action": "OPEN_LONG",
  "coin": "BTC",
  "size_usd": 1000.0,
  "leverage": 3,
  "stop_loss_price": 49000.0,
  "take_profit_price": 53000.0,
  "confidence": 0.75
}
```
""",
            str(agent2.id): """
```json
{
  "reasoning": "Market too volatile, holding position",
  "action": "HOLD",
  "coin": "ETH",
  "size_usd": 0.0,
  "leverage": 1,
  "stop_loss_price": 0.0,
  "take_profit_price": 0.0,
  "confidence": 0.6
}
```
"""
        }

        # Patch each provider's generate_async
        for agent_id, response in mock_responses.items():
            provider = agent_manager.llm_providers[agent_id]
            provider.generate_async = AsyncMock(return_value=response)

        decisions = await orchestrator.run_decision_cycle(
            market_data=mock_market_data,
            positions=[],
            account=mock_account
        )

        # Verify both decisions were created
        assert len(decisions) == 2

        # Verify different actions
        actions = {d.action for d in decisions}
        assert "OPEN_LONG" in actions
        assert "HOLD" in actions

    async def test_run_decision_cycle_handles_llm_errors(
        self, test_db, test_agent, mock_llm_config, mock_market_data, mock_account
    ):
        """Test that orchestrator handles LLM errors gracefully."""
        agent_manager = AgentManager(test_db, mock_llm_config)
        orchestrator = MultiAgentOrchestrator(test_db, agent_manager)

        # Mock LLM to raise an error
        with patch.object(agent_manager.llm_providers[str(test_agent.id)], 'generate_async',
                          side_effect=Exception("API Error")):

            decisions = await orchestrator.run_decision_cycle(
                market_data=mock_market_data,
                positions=[],
                account=mock_account
            )

            # Verify failed decision was created
            assert len(decisions) == 1
            decision = decisions[0]

            assert decision.status == "failed"
            assert decision.error_message is not None
            assert "API Error" in decision.error_message

    async def test_run_decision_cycle_handles_invalid_json(
        self, test_db, test_agent, mock_llm_config, mock_market_data, mock_account
    ):
        """Test that orchestrator handles invalid JSON responses."""
        agent_manager = AgentManager(test_db, mock_llm_config)
        orchestrator = MultiAgentOrchestrator(test_db, agent_manager)

        # Mock LLM to return invalid JSON
        invalid_response = "This is not JSON at all!"

        with patch.object(agent_manager.llm_providers[str(test_agent.id)], 'generate_async',
                          new_callable=AsyncMock, return_value=invalid_response):

            decisions = await orchestrator.run_decision_cycle(
                market_data=mock_market_data,
                positions=[],
                account=mock_account
            )

            # Verify failed decision was created
            assert len(decisions) == 1
            decision = decisions[0]

            assert decision.status == "failed"
            assert "Failed to parse JSON decision" in decision.error_message


class TestEndToEndDecisionCycle:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_decision_cycle_workflow(
        self, test_db, test_agent, mock_llm_config, mock_market_data, mock_account
    ):
        """Test the complete workflow from agent creation to decision storage."""
        # 1. Setup
        agent_manager = AgentManager(test_db, mock_llm_config)
        orchestrator = MultiAgentOrchestrator(test_db, agent_manager)

        # 2. Mock LLM response
        mock_response = """
```json
{
  "reasoning": "ETH showing bearish divergence on MACD, opening short position with tight stop loss",
  "action": "OPEN_SHORT",
  "coin": "ETH",
  "size_usd": 1500.0,
  "leverage": 5,
  "stop_loss_price": 3100.0,
  "take_profit_price": 2800.0,
  "confidence": 0.80
}
```
"""

        with patch.object(agent_manager.llm_providers[str(test_agent.id)], 'generate_async',
                          new_callable=AsyncMock, return_value=mock_response):

            # 3. Run decision cycle
            decisions = await orchestrator.run_decision_cycle(
                market_data=mock_market_data,
                positions=[],
                account=mock_account
            )

            # 4. Verify decision
            assert len(decisions) == 1
            decision = decisions[0]

            assert decision.action == "OPEN_SHORT"
            assert decision.coin == "ETH"
            assert decision.size_usd == Decimal("1500.00")
            assert decision.leverage == 5

            # 5. Verify database persistence
            db_decision = test_db.query(AgentDecision).filter(
                AgentDecision.agent_id == test_agent.id
            ).first()

            assert db_decision is not None
            assert db_decision.action == "OPEN_SHORT"
            assert db_decision.reasoning.startswith("ETH showing bearish")

            # 6. Verify agent performance tracking
            performance = orchestrator.get_agent_performance(test_agent.id)

            assert performance["total_decisions"] == 1
            assert performance["success_rate"] == 1.0
            assert float(performance["avg_confidence"]) == 0.80
