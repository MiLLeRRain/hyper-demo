"""Integration test configuration and fixtures.

Provides test fixtures for integration testing using Dry-Run mode:
- Test database
- Mock API clients
- Sample data
- Configuration
"""

import pytest
import os
from decimal import Decimal
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from unittest.mock import Mock

from trading_bot.models.database import Base, TradingAgent, AgentTrade


@pytest.fixture(scope="session")
def test_config():
    """Test configuration with dry-run mode enabled."""
    return {
        "environment": "dry-run",
        "dry_run": {
            "enabled": True,
            "data_source": "mainnet",
            "simulate_order_fill": True,
            "log_simulated_trades": True
        },
        "hyperliquid": {
            "base_url": "https://api.hyperliquid.xyz",
            "private_key": os.getenv("TEST_PRIVATE_KEY", "0x" + "1" * 64),
            "dry_run": True,
            "timeout": 10
        },
        "llm": {
            "models": {
                "deepseek-chat": {
                    "provider": "official",
                    "official": {
                        "base_url": "https://api.deepseek.com/v1",
                        "api_key": os.getenv("DEEPSEEK_API_KEY", "sk-test"),
                        "model_name": "deepseek-chat",
                        "timeout": 30
                    }
                }
            },
            "max_tokens": 4096,
            "temperature": 0.7
        },
        "trading": {
            "interval_minutes": 3,
            "coins": ["BTC", "ETH", "SOL"]
        }
    }


@pytest.fixture(scope="function")
def test_db_engine():
    """Create in-memory SQLite database for testing.

    Each test gets a fresh database that is automatically cleaned up.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create database session for testing."""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture(scope="function")
def sample_agent(test_db_session):
    """Create a sample trading agent for testing."""
    agent = TradingAgent(
        name="Test Agent",
        model="deepseek-chat",
        initial_balance=Decimal("10000.0"),
        max_leverage=5,
        status="active"
    )
    test_db_session.add(agent)
    test_db_session.commit()
    test_db_session.refresh(agent)

    return agent


@pytest.fixture(scope="function")
def sample_market_data():
    """Sample market data for testing."""
    return {
        "BTC": {
            "symbol": "BTC",
            "price": 50000.0,
            "bid": 49995.0,
            "ask": 50005.0,
            "volume_24h": 1000000.0,
            "high_24h": 51000.0,
            "low_24h": 49000.0,
            "change_24h": 2.5,
            "timestamp": datetime.utcnow().isoformat()
        },
        "ETH": {
            "symbol": "ETH",
            "price": 3000.0,
            "bid": 2998.0,
            "ask": 3002.0,
            "volume_24h": 500000.0,
            "high_24h": 3100.0,
            "low_24h": 2900.0,
            "change_24h": 1.5,
            "timestamp": datetime.utcnow().isoformat()
        },
        "SOL": {
            "symbol": "SOL",
            "price": 100.0,
            "bid": 99.8,
            "ask": 100.2,
            "volume_24h": 200000.0,
            "high_24h": 105.0,
            "low_24h": 95.0,
            "change_24h": 3.0,
            "timestamp": datetime.utcnow().isoformat()
        }
    }


@pytest.fixture(scope="function")
def sample_ai_decision():
    """Sample AI decision for testing."""
    return {
        "action": "buy",
        "symbol": "BTC",
        "confidence": 0.85,
        "size": 0.1,
        "reasoning": "Strong bullish signals with high volume and positive momentum",
        "target_price": 51000.0,
        "stop_loss": 48000.0,
        "take_profit": 52000.0,
        "timeframe": "1h",
        "risk_reward_ratio": 2.0
    }


@pytest.fixture(scope="function")
def mock_hyperliquid_client():
    """Create mock HyperLiquid client for testing."""
    client = Mock()

    # Mock get_all_mids
    client.get_all_mids.return_value = {
        "BTC": 50000.0,
        "ETH": 3000.0,
        "SOL": 100.0
    }

    # Mock get_user_state
    client.get_user_state.return_value = {
        "marginSummary": {
            "accountValue": "10000.0",
            "totalMarginUsed": "0.0",
            "totalNtlPos": "0.0"
        },
        "assetPositions": []
    }

    # Mock get_order_book
    client.get_l2_snapshot.return_value = {
        "coin": "BTC",
        "time": 1704931200000,
        "levels": [
            [
                {"px": "49995.0", "sz": "1.5", "n": 1},
                {"px": "49990.0", "sz": "2.0", "n": 2}
            ],
            [
                {"px": "50005.0", "sz": "1.5", "n": 1},
                {"px": "50010.0", "sz": "2.0", "n": 2}
            ]
        ]
    }

    return client


@pytest.fixture(scope="function")
def mock_deepseek_client():
    """Create mock DeepSeek client for testing."""
    client = Mock()

    # Mock generate_decision
    client.generate_decision.return_value = {
        "action": "buy",
        "symbol": "BTC",
        "confidence": 0.85,
        "size": 0.1,
        "reasoning": "Test reasoning from AI",
        "target_price": 51000.0,
        "stop_loss": 48000.0
    }

    # Mock chat completion
    client.chat.completions.create.return_value = Mock(
        choices=[
            Mock(
                message=Mock(
                    content='{"action": "buy", "symbol": "BTC", "confidence": 0.85}'
                )
            )
        ]
    )

    return client


# Note: Position and Order fixtures commented out as these models
# are not yet implemented. Will be added when Phase 3 is complete.
#
# @pytest.fixture(scope="function")
# def sample_position(test_db_session, sample_agent):
#     """Create a sample position for testing."""
#     pass
#
# @pytest.fixture(scope="function")
# def sample_order(test_db_session, sample_agent):
#     """Create a sample order for testing."""
#     pass


# Pytest configuration
def pytest_configure(config):
    """Configure pytest environment."""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "slow" in item.keywords:
            item.add_marker(pytest.mark.slow)
