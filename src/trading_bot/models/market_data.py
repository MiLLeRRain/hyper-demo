"""Market data models."""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel
import pandas as pd


class Price(BaseModel):
    """Current price data for a coin."""

    coin: str
    price: float
    timestamp: datetime
    volume_24h: Optional[float] = None
    change_24h_pct: Optional[float] = None


class Kline(BaseModel):
    """K-line (candlestick) data."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    class Config:
        arbitrary_types_allowed = True


class MarketData(BaseModel):
    """Complete market data for a coin."""

    coin: str
    price: Price
    klines_3m: pd.DataFrame  # 3-minute K-lines
    klines_4h: pd.DataFrame  # 4-hour K-lines
    indicators_3m: Dict[str, float]  # Technical indicators for 3m timeframe
    indicators_4h: Dict[str, float]  # Technical indicators for 4h timeframe
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None

    class Config:
        arbitrary_types_allowed = True


class Position(BaseModel):
    """Current position information."""

    coin: str
    side: str  # "long" or "short"
    size: float
    entry_price: float
    mark_price: float
    position_value: float
    unrealized_pnl: float
    leverage: int
    liquidation_price: float


class AccountInfo(BaseModel):
    """Trading account information."""

    account_value: float  # Total account value (equity)
    withdrawable: float  # Available balance
    margin_used: float
    unrealized_pnl: float
