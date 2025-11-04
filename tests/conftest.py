"""Pytest configuration and shared fixtures."""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.trading_bot.config.models import (
    TradingConfig,
    ExchangeConfig,
    RiskConfig,
    LLMConfig,
    ModelConfig,
    ProviderConfig,
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
    )


@pytest.fixture
def mock_exchange_config():
    """Mock exchange configuration."""
    return ExchangeConfig(
        testnet=True,
        mainnet_url="https://api.hyperliquid.xyz",
        testnet_url="https://api.hyperliquid-testnet.xyz",
    )


@pytest.fixture
def mock_risk_config():
    """Mock risk configuration."""
    return RiskConfig(
        max_position_size_usd=2000.0,
        max_leverage=10,
        stop_loss_pct=0.15,
        max_drawdown_pct=0.30,
        max_account_utilization=0.80,
    )


@pytest.fixture
def mock_llm_config():
    """Mock LLM configuration."""
    return LLMConfig(
        mode="single",  # Use single-agent mode for testing
        active_model="deepseek-chat",
        fallback_model="qwen-plus",
        models={
            "deepseek-chat": ModelConfig(
                provider="official",
                official=ProviderConfig(
                    api_key="test_key",
                    base_url="https://api.deepseek.com/v1",
                    model_name="deepseek-chat",
                    timeout=30,
                ),
            ),
            "qwen-plus": ModelConfig(
                provider="official",
                official=ProviderConfig(
                    api_key="test_key",
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    model_name="qwen-plus",
                    timeout=30,
                ),
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
