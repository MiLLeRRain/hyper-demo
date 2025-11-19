"""Unit tests for configuration module."""

import pytest
import os
import tempfile
from src.trading_bot.config.models import (
    Config,
    LLMConfig,
    LLMModelConfig,
    HyperLiquidConfig,
    load_config,
)


@pytest.mark.unit
class TestConfigModels:
    """Test Pydantic configuration models."""

    def test_llm_model_config_valid(self):
        """Test valid LLM model configuration."""
        config = LLMModelConfig(
            provider="official",
            official={
                "api_key": "test_key",
                "base_url": "https://api.example.com",
                "model_name": "test-model",
                "timeout": 30
            }
        )
        assert config.provider == "official"
        assert config.official["api_key"] == "test_key"

    def test_hyperliquid_config_urls(self):
        """Test HyperLiquid config URL properties."""
        config = HyperLiquidConfig(
            mainnet_url="https://api.hyperliquid.xyz",
            testnet_url="https://api.hyperliquid-testnet.xyz",
            active_url="testnet_url"
        )
        assert config.is_testnet is True
        assert config.exchange_url == "https://api.hyperliquid-testnet.xyz"

        config.active_url = "mainnet_url"
        assert config.is_testnet is False
        assert config.exchange_url == "https://api.hyperliquid.xyz"


@pytest.mark.unit
class TestLoadConfig:
    """Test configuration loading from YAML."""

    def test_load_config_file_not_found(self):
        """Test load_config raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")

    def test_load_config_success(self):
        """Test successful config loading from YAML."""
        config_yaml = """
environment: test
dry_run:
  enabled: true
  data_source: hyperliquid
  simulate_order_fill: true
  simulate_slippage: 0.001
  simulate_latency_ms: 100
  log_simulated_trades: true
  save_dry_run_results: true

hyperliquid:
  mainnet_url: https://api.hyperliquid.xyz
  testnet_url: https://api.hyperliquid-testnet.xyz
  active_url: testnet_url

llm:
  models:
    deepseek-chat:
      provider: official
      official:
        api_key: test_key
        base_url: https://api.deepseek.com
        model_name: deepseek-chat
  max_tokens: 1000
  temperature: 0.5

trading:
  interval_minutes: 5
  coins: ["BTC", "ETH"]
  kline_limit_3m: 100
  kline_limit_4h: 100
  max_position_per_agent: 1000.0
  stop_loss_percentage: 0.05
  take_profit_percentage: 0.1

agents:
  - name: "TestAgent"
    enabled: true
    provider: "deepseek-chat"
    model: "deepseek-chat"
    temperature: 0.7
    max_tokens: 1000
    description: "Test Agent"

database:
  url: "sqlite:///test.db"

monitoring:
  performance:
    enabled: true
  account:
    enabled: true
  alerts:
    enabled: true

logging:
  level: "INFO"
  log_dir: "logs"
  main_log: "main.log"
  error_log: "error.log"
  rotation: "1 day"
  retention: "7 days"
  compression: "zip"
  json_format: false
  colorize_console: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.environment == "test"
            assert config.hyperliquid.is_testnet is True
            assert len(config.trading.coins) == 2
            assert config.agents[0].name == "TestAgent"
        finally:
            os.unlink(temp_path)

    def test_load_config_with_env_vars(self, monkeypatch):
        """Test config loading with environment variable expansion."""
        monkeypatch.setenv("TEST_API_KEY", "secret_key_from_env")
        
        config_yaml = """
environment: test
dry_run:
  enabled: true
  data_source: hyperliquid
  simulate_order_fill: true
  simulate_slippage: 0.001
  simulate_latency_ms: 100
  log_simulated_trades: true
  save_dry_run_results: true

hyperliquid:
  mainnet_url: https://api.hyperliquid.xyz
  testnet_url: https://api.hyperliquid-testnet.xyz
  active_url: testnet_url

llm:
  models:
    deepseek-chat:
      provider: official
      official:
        api_key: ${TEST_API_KEY}
        base_url: https://api.deepseek.com
        model_name: deepseek-chat
  max_tokens: 1000
  temperature: 0.5

trading:
  interval_minutes: 5
  coins: ["BTC"]
  kline_limit_3m: 100
  kline_limit_4h: 100
  max_position_per_agent: 1000.0
  stop_loss_percentage: 0.05
  take_profit_percentage: 0.1

agents: []
database:
  url: "sqlite:///test.db"
monitoring:
  performance: {}
  account: {}
  alerts: {}
logging:
  level: "INFO"
  log_dir: "logs"
  main_log: "main.log"
  error_log: "error.log"
  rotation: "1 day"
  retention: "7 days"
  compression: "zip"
  json_format: false
  colorize_console: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.llm.models["deepseek-chat"].official["api_key"] == "secret_key_from_env"
        finally:
            os.unlink(temp_path)
