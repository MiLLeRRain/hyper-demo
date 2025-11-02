"""HyperLiquid API client for fetching market data."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.market_data import Price, Kline

logger = logging.getLogger(__name__)


class HyperliquidClient:
    """Client for HyperLiquid Info API."""

    def __init__(self, base_url: str, timeout: int = 10):
        """
        Initialize HyperLiquid client.

        Args:
            base_url: Base URL for API (mainnet or testnet)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _post(self, endpoint: str, payload: dict) -> dict:
        """
        Make POST request to HyperLiquid API with retry logic.

        Args:
            endpoint: API endpoint
            payload: Request payload

        Returns:
            Response JSON

        Raises:
            requests.RequestException: On API error
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def get_all_prices(self) -> Dict[str, Price]:
        """
        Get current prices for all available coins.

        Returns:
            Dictionary mapping coin symbol to Price object

        Example response from API:
        [
            {"coin": "BTC", "price": "95420.5", "volume": "1234567890", ...},
            ...
        ]
        """
        payload = {"type": "allMids"}

        try:
            data = self._post("/info", payload)

            prices = {}
            current_time = datetime.utcnow()

            # Parse response - format may vary, adjust based on actual API
            if isinstance(data, dict):
                for coin, price_str in data.items():
                    try:
                        prices[coin] = Price(
                            coin=coin,
                            price=float(price_str),
                            timestamp=current_time,
                        )
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Failed to parse price for {coin}: {e}")
            elif isinstance(data, list):
                for item in data:
                    try:
                        coin = item.get("coin") or item.get("symbol")
                        price_val = float(item.get("price") or item.get("mid"))
                        prices[coin] = Price(
                            coin=coin,
                            price=price_val,
                            timestamp=current_time,
                            volume_24h=item.get("volume"),
                        )
                    except (ValueError, KeyError, TypeError) as e:
                        logger.warning(f"Failed to parse price item: {e}")

            logger.info(f"Fetched prices for {len(prices)} coins")
            return prices

        except Exception as e:
            logger.error(f"Failed to fetch prices: {e}")
            raise

    def get_price(self, coin: str) -> Price:
        """
        Get current price for a specific coin.

        Args:
            coin: Coin symbol (e.g., "BTC")

        Returns:
            Price object
        """
        all_prices = self.get_all_prices()
        if coin not in all_prices:
            raise ValueError(f"Price not available for {coin}")
        return all_prices[coin]

    def get_klines(
        self,
        coin: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Get K-line (candlestick) data for a coin.

        Args:
            coin: Coin symbol (e.g., "BTC")
            interval: Time interval ("1m", "3m", "5m", "15m", "1h", "4h", "1d")
            limit: Number of candles to fetch
            start_time: Start time (optional)
            end_time: End time (optional)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume

        Example API payload:
        {
            "type": "candleSnapshot",
            "req": {
                "coin": "BTC",
                "interval": "3m",
                "startTime": 1234567890000,
                "endTime": 1234567890000
            }
        }
        """
        # Calculate time range if not provided
        if end_time is None:
            end_time = datetime.utcnow()

        if start_time is None:
            # Calculate start_time based on interval and limit
            interval_minutes = self._parse_interval_to_minutes(interval)
            start_time = end_time - timedelta(minutes=interval_minutes * limit)

        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": coin,
                "interval": interval,
                "startTime": int(start_time.timestamp() * 1000),
                "endTime": int(end_time.timestamp() * 1000),
            },
        }

        try:
            data = self._post("/info", payload)

            # Parse response into DataFrame
            klines_list = []

            # Handle different response formats
            candles = data if isinstance(data, list) else data.get("candles", [])

            for candle in candles:
                try:
                    # Try different field names
                    timestamp = candle.get("t") or candle.get("timestamp")
                    klines_list.append({
                        "timestamp": datetime.fromtimestamp(timestamp / 1000),
                        "open": float(candle.get("o") or candle.get("open")),
                        "high": float(candle.get("h") or candle.get("high")),
                        "low": float(candle.get("l") or candle.get("low")),
                        "close": float(candle.get("c") or candle.get("close")),
                        "volume": float(candle.get("v") or candle.get("volume", 0)),
                    })
                except (ValueError, KeyError, TypeError) as e:
                    logger.warning(f"Failed to parse candle: {e}")

            df = pd.DataFrame(klines_list)

            if df.empty:
                logger.warning(f"No kline data returned for {coin} {interval}")
                # Return empty DataFrame with correct schema
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            # Sort by timestamp and limit
            df = df.sort_values("timestamp").tail(limit).reset_index(drop=True)

            logger.info(f"Fetched {len(df)} klines for {coin} {interval}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch klines for {coin}: {e}")
            raise

    def get_open_interest(self, coin: str) -> float:
        """
        Get open interest for a coin.

        Args:
            coin: Coin symbol

        Returns:
            Open interest value
        """
        payload = {"type": "metaAndAssetCtxs"}

        try:
            data = self._post("/info", payload)

            # Parse response to find open interest for coin
            # Format depends on actual API response
            for asset in data:
                if asset.get("coin") == coin or asset.get("symbol") == coin:
                    return float(asset.get("openInterest", 0))

            logger.warning(f"Open interest not found for {coin}")
            return 0.0

        except Exception as e:
            logger.error(f"Failed to fetch open interest: {e}")
            return 0.0

    def get_funding_rate(self, coin: str) -> float:
        """
        Get current funding rate for a coin.

        Args:
            coin: Coin symbol

        Returns:
            Funding rate (e.g., 0.0001 for 0.01%)
        """
        payload = {"type": "metaAndAssetCtxs"}

        try:
            data = self._post("/info", payload)

            # Parse response to find funding rate for coin
            for asset in data:
                if asset.get("coin") == coin or asset.get("symbol") == coin:
                    return float(asset.get("funding", 0))

            logger.warning(f"Funding rate not found for {coin}")
            return 0.0

        except Exception as e:
            logger.error(f"Failed to fetch funding rate: {e}")
            return 0.0

    @staticmethod
    def _parse_interval_to_minutes(interval: str) -> int:
        """
        Parse interval string to minutes.

        Args:
            interval: Interval string (e.g., "3m", "1h", "4h")

        Returns:
            Number of minutes
        """
        unit = interval[-1]
        value = int(interval[:-1])

        if unit == "m":
            return value
        elif unit == "h":
            return value * 60
        elif unit == "d":
            return value * 1440
        else:
            raise ValueError(f"Invalid interval: {interval}")

    def close(self):
        """Close the session."""
        self.session.close()
