"""Pydantic models for configuration."""

import os
import re
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
import yaml


class DatabaseConfig(BaseModel):
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


class HyperLiquidConfig(BaseModel):
    mainnet_url: str
    testnet_url: str
    private_key: Optional[str] = None
    vault_address: Optional[str] = None
    timeout: int = 10
    max_retries: int = 3
    retry_delay: int = 2
    max_position_size: float = 1.0
    max_leverage: int = 5
    max_daily_trades: int = 50
    active_url: Optional[str] = None  # From environment override

    @property
    def info_url(self) -> str:
        if self.active_url == 'mainnet_url':
            return self.mainnet_url
        elif self.active_url == 'testnet_url':
            return self.testnet_url
        return self.testnet_url

    @property
    def exchange_url(self) -> str:
        return self.info_url

    @property
    def is_testnet(self) -> bool:
        return self.info_url == self.testnet_url


class LLMModelConfig(BaseModel):
    provider: str
    official: Optional[Dict[str, Any]] = None
    openrouter: Optional[Dict[str, Any]] = None


class LLMConfig(BaseModel):
    models: Dict[str, LLMModelConfig]
    max_tokens: int = 500
    temperature: float = 0.3


class TradingConfig(BaseModel):
    interval_minutes: int
    coins: List[str]
    kline_limit_3m: int
    kline_limit_4h: int
    max_position_per_agent: float
    stop_loss_percentage: float
    take_profit_percentage: float

    @property
    def cycle_interval_minutes(self) -> int:
        return self.interval_minutes


class AgentConfig(BaseModel):
    name: str
    enabled: bool
    provider: str
    model: str
    temperature: float
    max_tokens: int
    description: str
    strategy_description: Optional[str] = None


class MonitoringConfig(BaseModel):
    performance: Dict[str, bool]
    account: Dict[str, Any]
    alerts: Dict[str, Any]


class LoggingConfig(BaseModel):
    level: str
    log_dir: str
    main_log: str
    error_log: str
    rotation: str
    retention: str
    compression: str
    json_format: bool
    colorize_console: bool


class DryRunConfig(BaseModel):
    enabled: bool
    data_source: str
    simulate_order_fill: bool
    simulate_slippage: float
    simulate_latency_ms: int
    log_simulated_trades: bool
    save_dry_run_results: bool


class Config(BaseModel):
    environment: str
    dry_run: DryRunConfig
    hyperliquid: HyperLiquidConfig
    llm: LLMConfig
    trading: TradingConfig
    agents: List[AgentConfig]
    database: DatabaseConfig
    monitoring: MonitoringConfig
    logging: LoggingConfig
    environments: Optional[Dict[str, Any]] = None

    def __init__(self, **data):
        # Handle environment overrides
        env = data.get('environment')
        if env and 'environments' in data and env in data['environments']:
            overrides = data['environments'][env]
            # Deep merge overrides into data
            self._deep_merge(data, overrides)
        
        super().__init__(**data)

    def _deep_merge(self, target, source):
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value


def load_config(config_path: str = "config.yaml") -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config YAML file

    Returns:
        Config instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)

    # Expand environment variables in API keys
    def expand_env_vars(obj):
        if isinstance(obj, dict):
            return {k: expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Replace ${VAR} with environment variable value
            pattern = re.compile(r'\$\{([^}]+)\}')
            
            def replace_match(match):
                env_var = match.group(1)
                value = os.getenv(env_var)
                return value if value is not None else match.group(0)
            
            return pattern.sub(replace_match, obj)
        return obj

    config_dict = expand_env_vars(config_dict)

    return Config(**config_dict)

