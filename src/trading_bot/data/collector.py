"""Data collector that orchestrates market data gathering."""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..config.models import TradingConfig, HyperLiquidConfig
from ..models.market_data import MarketData, Price
from .hyperliquid_client import HyperliquidClient
from .indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class DataCollector:
    """Orchestrates market data collection for all configured coins."""

    def __init__(
        self,
        exchange_config: HyperLiquidConfig,
        trading_config: TradingConfig,
    ):
        """
        Initialize data collector.

        Args:
            exchange_config: Exchange configuration
            trading_config: Trading configuration
        """
        self.trading_config = trading_config
        self.client = HyperliquidClient(
            base_url=exchange_config.info_url,
            timeout=10,
        )
        self.indicators_calculator = TechnicalIndicators()

        logger.info(
            f"DataCollector initialized for {len(trading_config.coins)} coins: "
            f"{', '.join(trading_config.coins)}"
        )

    def collect_all(self) -> Dict[str, MarketData]:
        """
        Collect market data for all configured coins.

        Returns:
            Dictionary mapping coin symbol to MarketData

        Raises:
            Exception: If data collection fails critically
        """
        logger.info("Starting market data collection...")
        start_time = datetime.utcnow()

        market_data = {}
        errors = []

        # Optimization: Fetch all prices once to avoid repeated API calls
        try:
            all_prices = self.client.get_all_prices()
        except Exception as e:
            logger.warning(f"Failed to fetch all prices batch, falling back to individual fetch: {e}")
            all_prices = {}

        for coin in self.trading_config.coins:
            try:
                # Pass pre-fetched price if available
                price = all_prices.get(coin)
                data = self.collect_coin_data(coin, price=price)
                market_data[coin] = data
                logger.debug(f"✓ Collected data for {coin}")
            except Exception as e:
                logger.error(f"✗ Failed to collect data for {coin}: {e}")
                errors.append((coin, str(e)))

        elapsed = (datetime.utcnow() - start_time).total_seconds()

        if not market_data:
            raise Exception(
                f"Failed to collect data for any coin. Errors: {errors}"
            )

        success_rate = len(market_data) / len(self.trading_config.coins) * 100
        logger.info(
            f"Market data collection complete: {len(market_data)}/{len(self.trading_config.coins)} "
            f"coins ({success_rate:.1f}%) in {elapsed:.2f}s"
        )

        if errors:
            logger.warning(f"Errors encountered: {errors}")

        return market_data

    def collect_coin_data(self, coin: str, price: Optional[Price] = None) -> MarketData:
        """
        Collect comprehensive market data for a single coin.

        Args:
            coin: Coin symbol (e.g., "BTC")
            price: Optional pre-fetched Price object

        Returns:
            MarketData object with price, klines, and indicators

        Raises:
            Exception: If data collection fails
        """
        logger.debug(f"Collecting data for {coin}...")

        # 1. Get current price (use provided or fetch new)
        if price is None:
            price = self.client.get_price(coin)

        # 2. Get K-lines for both timeframes
        klines_3m = self.client.get_klines(
            coin=coin,
            interval="3m",
            limit=self.trading_config.kline_limit_3m,
        )

        klines_4h = self.client.get_klines(
            coin=coin,
            interval="4h",
            limit=self.trading_config.kline_limit_4h,
        )

        # 3. Calculate technical indicators for both timeframes
        indicators_3m = self.indicators_calculator.calculate_all(klines_3m, history_len=10)
        indicators_4h = self.indicators_calculator.calculate_all(klines_4h, history_len=10)

        # 4. Get additional data (optional, may fail)
        open_interest = None
        funding_rate = None

        try:
            # Note: HyperLiquidClient needs to support these methods
            # If not available, we might need to add them or handle the error
            if hasattr(self.client, 'get_open_interest'):
                open_interest = self.client.get_open_interest(coin)
            
            if hasattr(self.client, 'get_funding_rate'):
                funding_rate = self.client.get_funding_rate(coin)
                
        except Exception as e:
            logger.debug(f"Failed to get additional data for {coin}: {e}")

        # 5. Construct MarketData object
        # Extract mid prices list (using close prices as proxy for mid prices if mid not available)
        mid_prices_list = klines_3m["close"].tail(10).tolist() if not klines_3m.empty else []
        mid_prices_list = [float(x) for x in mid_prices_list]

        market_data = MarketData(
            coin=coin,
            price=price,
            klines_3m=klines_3m,
            klines_4h=klines_4h,
            indicators_3m=indicators_3m,
            indicators_4h=indicators_4h,
            open_interest=open_interest,
            funding_rate=funding_rate,
            volume_24h=price.volume_24h,
            volume_current_4h=indicators_4h.get("volume_current"),
            volume_average_4h=indicators_4h.get("volume_avg"),
            mid_prices_list=mid_prices_list
        )

        return market_data

    def get_prices_snapshot(self) -> Dict[str, Price]:
        """
        Get a quick snapshot of current prices for all configured coins.

        Returns:
            Dictionary mapping coin symbol to Price

        Raises:
            Exception: If price fetch fails
        """
        logger.info("Fetching price snapshot...")

        all_prices = self.client.get_all_prices()

        # Filter to only configured coins
        prices = {
            coin: all_prices[coin]
            for coin in self.trading_config.coins
            if coin in all_prices
        }

        if len(prices) < len(self.trading_config.coins):
            missing = set(self.trading_config.coins) - set(prices.keys())
            logger.warning(f"Missing prices for: {missing}")

        logger.info(f"Price snapshot: {len(prices)}/{len(self.trading_config.coins)} coins")

        return prices

    def close(self):
        """Close the HTTP client session."""
        self.client.close()
        logger.info("DataCollector closed")
