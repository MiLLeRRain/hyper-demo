"""Unit tests for configuration module."""

import pytest
import os
import tempfile
from src.trading_bot.config.models import (
    TradingBotConfig,
    LLMConfig,
    ModelConfig,
    ProviderConfig,
    load_config,
)


@pytest.mark.unit
class TestConfigModels:
    """Test Pydantic configuration models."""

    def test_provider_config_valid(self):
        """Test valid provider configuration."""
        config = ProviderConfig(
            api_key="test_key",
            base_url="https://api.example.com",
            model_name="test-model",
            timeout=30,
        )

        assert config.api_key == "test_key"
        assert config.base_url == "https://api.example.com"
        assert config.model_name == "test-model"
        assert config.timeout == 30

    def test_model_config_valid_provider(self):
        """Test model config accepts valid provider types."""
        config = ModelConfig(
            provider="official",
            official=ProviderConfig(
                api_key="key",
                base_url="https://api.example.com",
                model_name="model",
            ),
        )

        assert config.provider == "official"

    def test_model_config_invalid_provider(self):
        """Test model config rejects invalid provider types."""
        with pytest.raises(ValueError, match="Provider must be"):
            ModelConfig(
                provider="invalid",
                official=ProviderConfig(
                    api_key="key",
                    base_url="url",
                    model_name="model",
                ),
            )

    def test_llm_config_validates_active_model_exists(self, mock_llm_config):
        """Test LLM config validation for active_model."""
        # Valid config should work
        assert mock_llm_config.active_model == "deepseek-chat"

    def test_llm_config_invalid_active_model(self):
        """Test LLM config rejects non-existent active_model."""
        with pytest.raises(ValueError, match="active_model.*not found"):
            TradingBotConfig(
                llm=LLMConfig(
                    active_model="nonexistent",
                    fallback_model="qwen-plus",
                    models={
                        "qwen-plus": ModelConfig(
                            provider="official",
                            official=ProviderConfig(
                                api_key="key",
                                base_url="url",
                                model_name="model",
                            ),
                        ),
                    },
                ),
                exchange={"testnet": True},
                trading={"coins": ["BTC"]},
                risk={"max_leverage": 10},
            )

    def test_exchange_config_base_url_testnet(self, mock_exchange_config):
        """Test exchange config returns testnet URL."""
        mock_exchange_config.testnet = True
        assert mock_exchange_config.base_url == mock_exchange_config.testnet_url

    def test_exchange_config_base_url_mainnet(self, mock_exchange_config):
        """Test exchange config returns mainnet URL."""
        mock_exchange_config.testnet = False
        assert mock_exchange_config.base_url == mock_exchange_config.mainnet_url


@pytest.mark.unit
class TestLoadConfig:
    """Test configuration loading from YAML."""

    def test_load_config_file_not_found(self):
        """Test load_config raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")

    def test_load_config_success(self):
        """Test successful config loading from YAML."""
        # Create temporary config file
        config_yaml = """
llm:
  active_model: deepseek-chat
  fallback_model: qwen-plus
  models:
    deepseek-chat:
      provider: official
      official:
        api_key: test_key_123
        base_url: https://api.deepseek.com/v1
        model_name: deepseek-chat
        timeout: 30
    qwen-plus:
      provider: official
      official:
        api_key: test_key_456
        base_url: https://api.qwen.com/v1
        model_name: qwen-plus
        timeout: 30
  max_tokens: 4096
  temperature: 0.7

exchange:
  testnet: true
  mainnet_url: https://api.hyperliquid.xyz
  testnet_url: https://api.hyperliquid-testnet.xyz

trading:
  interval_minutes: 3
  coins: [BTC, ETH, SOL]
  kline_limit_3m: 30
  kline_limit_4h: 24

risk:
  max_position_size_usd: 2000.0
  max_leverage: 10
  stop_loss_pct: 0.15
  max_drawdown_pct: 0.30
  max_account_utilization: 0.80
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = load_config(temp_path)

            assert config.llm.active_model == "deepseek-chat"
            assert config.exchange.testnet is True
            assert len(config.trading.coins) == 3
            assert config.risk.max_leverage == 10

        finally:
            os.unlink(temp_path)

    def test_load_config_with_env_vars(self, monkeypatch):
        """Test config loading with environment variable expansion."""
        # Set environment variable
        monkeypatch.setenv("TEST_API_KEY", "secret_key_from_env")

        config_yaml = """
llm:
  active_model: deepseek-chat
  fallback_model: qwen-plus
  models:
    deepseek-chat:
      provider: official
      official:
        api_key: ${TEST_API_KEY}
        base_url: https://api.deepseek.com/v1
        model_name: deepseek-chat
        timeout: 30
    qwen-plus:
      provider: official
      official:
        api_key: test_key
        base_url: https://api.qwen.com/v1
        model_name: qwen-plus
        timeout: 30
  max_tokens: 4096
  temperature: 0.7

exchange:
  testnet: true

trading:
  coins: [BTC]

risk:
  max_leverage: 10
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.llm.models["deepseek-chat"].official.api_key == "secret_key_from_env"

        finally:
            os.unlink(temp_path)

    def test_load_config_missing_env_var(self):
        """Test config loading fails with missing environment variable."""
        config_yaml = """
llm:
  active_model: deepseek-chat
  fallback_model: qwen-plus
  models:
    deepseek-chat:
      provider: official
      official:
        api_key: ${MISSING_ENV_VAR}
        base_url: https://api.deepseek.com/v1
        model_name: deepseek-chat
    qwen-plus:
      provider: official
      official:
        api_key: test
        base_url: https://api.qwen.com/v1
        model_name: qwen-plus

exchange:
  testnet: true

trading:
  coins: [BTC]

risk:
  max_leverage: 10
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Environment variable.*is not set"):
                load_config(temp_path)

        finally:
            os.unlink(temp_path)
