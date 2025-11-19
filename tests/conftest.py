"""Pytest configuration and shared fixtures."""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.trading_bot.config.models import (
    TradingConfig,
    HyperLiquidConfig,
    LLMConfig,
    LLMModelConfig,
)
from src.trading_bot.models.market_data import Price


@pytest.fixture
def mock_trading_config():
    """Mock trading configuration."""
    return TradingConfig(
        interval_minutes=3,
        coins=["BTC", "ETH", "SOL"],
        kline_limit_3m=30,
        kline_limit_4h=24,
        max_position_per_agent=0.5,
        stop_loss_percentage=5.0,
        take_profit_percentage=10.0,
    )


@pytest.fixture
def mock_exchange_config():
    """Mock exchange configuration."""
    return HyperLiquidConfig(
        mainnet_url="https://api.hyperliquid.xyz",
        testnet_url="https://api.hyperliquid-testnet.xyz",
        active_url="testnet_url",
    )


@pytest.fixture
def mock_llm_config():
    """Mock LLM configuration - defines available model pool."""
    return LLMConfig(
        models={
            "deepseek-chat": LLMModelConfig(
                provider="official",
                official={
                    "api_key": "test_key",
                    "base_url": "https://api.deepseek.com/v1",
                    "model_name": "deepseek-chat",
                    "timeout": 30,
                },
            ),
            "qwen-plus": LLMModelConfig(
                provider="official",
                official={
                    "api_key": "test_key",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model_name": "qwen-plus",
                    "timeout": 30,
                },
            ),
        },
        max_tokens=4096,
        temperature=0.7,
    )


@pytest.fixture
def mock_price_data():
    """Mock price data."""
    return {
        "BTC": Price(
            coin="BTC",
            price=95420.5,
            timestamp=datetime.utcnow(),
            volume_24h=1234567890.0,
        ),
        "ETH": Price(
            coin="ETH",
            price=3520.75,
            timestamp=datetime.utcnow(),
            volume_24h=987654321.0,
        ),
        "SOL": Price(
            coin="SOL",
            price=142.30,
            timestamp=datetime.utcnow(),
            volume_24h=456789012.0,
        ),
    }


@pytest.fixture
def mock_kline_data():
    """Mock K-line data."""
    now = datetime.utcnow()
    data = []

    for i in range(100):
        timestamp = now - timedelta(minutes=3 * (100 - i))
        base_price = 95000.0 + (i * 5)  # Uptrend

        data.append({
            "timestamp": timestamp,
            "open": base_price,
            "high": base_price + 50,
            "low": base_price - 30,
            "close": base_price + 20,
            "volume": 1000000.0 + (i * 10000),
        })

    return pd.DataFrame(data)


@pytest.fixture
def mock_http_session(mocker):
    """Mock HTTP session for API calls."""
    session = mocker.Mock()
    session.post.return_value.status_code = 200
    session.post.return_value.json.return_value = {}
    return session
