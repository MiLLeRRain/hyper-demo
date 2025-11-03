"""Pydantic models for configuration."""

import os
from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator
import yaml


class ProviderConfig(BaseModel):
    """Configuration for a specific LLM service provider."""

    api_key: str
    base_url: str
    model_name: str
    timeout: int = 30


class ModelConfig(BaseModel):
    """Configuration for a specific LLM model."""

    provider: str = Field(..., description="Provider to use: official | openrouter")
    official: Optional[ProviderConfig] = None
    openrouter: Optional[ProviderConfig] = None

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v not in ["official", "openrouter"]:
            raise ValueError(f"Provider must be 'official' or 'openrouter', got: {v}")
        return v


class LLMConfig(BaseModel):
    """LLM configuration."""

    active_model: str = Field(..., description="Currently active model name")
    fallback_model: str = Field(..., description="Fallback model name")
    models: Dict[str, ModelConfig] = Field(..., description="Model definitions")
    max_tokens: int = 4096
    temperature: float = 0.7

    @field_validator("models")
    @classmethod
    def validate_models(cls, v: Dict[str, ModelConfig], info) -> Dict[str, ModelConfig]:
        # Ensure active_model and fallback_model exist in models dict
        # Note: We can't access other fields during validation, so this will be checked in __init__
        return v


class ExchangeConfig(BaseModel):
    """HyperLiquid exchange configuration."""

    testnet: bool = True
    mainnet_url: str = "https://api.hyperliquid.xyz"
    testnet_url: str = "https://api.hyperliquid-testnet.xyz"
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

    @property
    def base_url(self) -> str:
        """Get the appropriate base URL based on testnet setting."""
        return self.testnet_url if self.testnet else self.mainnet_url


class TradingConfig(BaseModel):
    """Trading configuration."""

    interval_minutes: int = Field(3, description="AI decision interval in minutes")
    coins: list[str] = Field(
        default_factory=lambda: ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"],
        description="Coins to trade",
    )
    kline_limit_3m: int = Field(30, description="Number of 3m candles to fetch")
    kline_limit_4h: int = Field(24, description="Number of 4h candles to fetch")


class RiskConfig(BaseModel):
    """Risk management configuration."""

    max_position_size_usd: float = Field(2000.0, description="Max position size per coin")
    max_leverage: int = Field(10, description="Maximum leverage allowed")
    stop_loss_pct: float = Field(0.15, description="Stop loss percentage (15%)")
    max_drawdown_pct: float = Field(0.30, description="Max account drawdown (30%)")
    max_account_utilization: float = Field(0.80, description="Max account utilization (80%)")


class TradingBotConfig(BaseModel):
    """Main trading bot configuration."""

    llm: LLMConfig
    exchange: ExchangeConfig
    trading: TradingConfig
    risk: RiskConfig

    def model_post_init(self, __context) -> None:
        """Validate cross-field dependencies after model initialization."""
        # Check that active_model exists in models
        if self.llm.active_model not in self.llm.models:
            raise ValueError(
                f"active_model '{self.llm.active_model}' not found in models configuration"
            )
        # Check that fallback_model exists in models
        if self.llm.fallback_model not in self.llm.models:
            raise ValueError(
                f"fallback_model '{self.llm.fallback_model}' not found in models configuration"
            )


def load_config(config_path: str = "config.yaml") -> TradingBotConfig:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config YAML file

    Returns:
        TradingBotConfig instance

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
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            value = os.getenv(env_var)
            if value is None:
                raise ValueError(f"Environment variable {env_var} is not set")
            return value
        return obj

    config_dict = expand_env_vars(config_dict)

    return TradingBotConfig(**config_dict)
