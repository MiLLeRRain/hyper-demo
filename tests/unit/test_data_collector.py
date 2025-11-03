"""Unit tests for data collector."""

import pytest
from unittest.mock import Mock, patch
import pandas as pd

from src.trading_bot.data.collector import DataCollector
from src.trading_bot.models.market_data import Price, MarketData


@pytest.mark.unit
class TestDataCollector:
    """Test data collector orchestration."""

    def test_collector_initialization(self, mock_exchange_config, mock_trading_config):
        """Test collector initializes correctly."""
        collector = DataCollector(mock_exchange_config, mock_trading_config)

        assert collector.trading_config == mock_trading_config
        assert collector.client is not None
        assert collector.indicators_calculator is not None

    def test_collect_coin_data_success(
        self,
        mock_exchange_config,
        mock_trading_config,
        mock_price_data,
        mock_kline_data,
        mocker,
    ):
        """Test successful coin data collection."""
        collector = DataCollector(mock_exchange_config, mock_trading_config)

        # Mock client methods
        mocker.patch.object(
            collector.client,
            "get_price",
            return_value=mock_price_data["BTC"],
        )
        mocker.patch.object(
            collector.client,
            "get_klines",
            return_value=mock_kline_data,
        )
        mocker.patch.object(
            collector.client,
            "get_open_interest",
            return_value=1234567890.0,
        )
        mocker.patch.object(
            collector.client,
            "get_funding_rate",
            return_value=0.0001,
        )

        # Mock indicators calculation
        mock_indicators = {
            "ema_20": 95123.45,
            "ema_50": 94567.89,
            "rsi_14": 65.34,
        }
        mocker.patch.object(
            collector.indicators_calculator,
            "calculate_all",
            return_value=mock_indicators,
        )

        market_data = collector.collect_coin_data("BTC")

        assert isinstance(market_data, MarketData)
        assert market_data.coin == "BTC"
        assert market_data.price.price == 95420.5
        assert isinstance(market_data.klines_3m, pd.DataFrame)
        assert isinstance(market_data.klines_4h, pd.DataFrame)
        assert market_data.indicators_3m == mock_indicators
        assert market_data.open_interest == 1234567890.0
        assert market_data.funding_rate == 0.0001

    def test_collect_coin_data_optional_data_fails(
        self,
        mock_exchange_config,
        mock_trading_config,
        mock_price_data,
        mock_kline_data,
        mocker,
    ):
        """Test coin data collection continues even if optional data fails."""
        collector = DataCollector(mock_exchange_config, mock_trading_config)

        # Mock required methods to succeed
        mocker.patch.object(
            collector.client,
            "get_price",
            return_value=mock_price_data["BTC"],
        )
        mocker.patch.object(
            collector.client,
            "get_klines",
            return_value=mock_kline_data,
        )

        # Mock optional methods to fail
        mocker.patch.object(
            collector.client,
            "get_open_interest",
            side_effect=Exception("OI API error"),
        )
        mocker.patch.object(
            collector.client,
            "get_funding_rate",
            side_effect=Exception("Funding API error"),
        )

        mocker.patch.object(
            collector.indicators_calculator,
            "calculate_all",
            return_value={},
        )

        market_data = collector.collect_coin_data("BTC")

        # Should still succeed with None for optional fields
        assert market_data.coin == "BTC"
        assert market_data.open_interest is None
        assert market_data.funding_rate is None

    def test_collect_all_success(
        self,
        mock_exchange_config,
        mock_trading_config,
        mock_price_data,
        mock_kline_data,
        mocker,
    ):
        """Test collect_all collects data for all configured coins."""
        collector = DataCollector(mock_exchange_config, mock_trading_config)

        # Mock collect_coin_data
        def mock_collect(coin):
            return MarketData(
                coin=coin,
                price=mock_price_data[coin],
                klines_3m=mock_kline_data,
                klines_4h=mock_kline_data,
                indicators_3m={},
                indicators_4h={},
            )

        mocker.patch.object(
            collector,
            "collect_coin_data",
            side_effect=mock_collect,
        )

        all_data = collector.collect_all()

        assert len(all_data) == 3  # BTC, ETH, SOL
        assert "BTC" in all_data
        assert "ETH" in all_data
        assert "SOL" in all_data

    def test_collect_all_partial_failure(
        self,
        mock_exchange_config,
        mock_trading_config,
        mock_price_data,
        mock_kline_data,
        mocker,
    ):
        """Test collect_all continues even if some coins fail."""
        collector = DataCollector(mock_exchange_config, mock_trading_config)

        # Mock: BTC succeeds, ETH fails, SOL succeeds
        def mock_collect(coin):
            if coin == "ETH":
                raise Exception("ETH API error")
            return MarketData(
                coin=coin,
                price=mock_price_data[coin],
                klines_3m=mock_kline_data,
                klines_4h=mock_kline_data,
                indicators_3m={},
                indicators_4h={},
            )

        mocker.patch.object(
            collector,
            "collect_coin_data",
            side_effect=mock_collect,
        )

        all_data = collector.collect_all()

        assert len(all_data) == 2  # Only BTC and SOL
        assert "BTC" in all_data
        assert "SOL" in all_data
        assert "ETH" not in all_data

    def test_collect_all_total_failure(
        self,
        mock_exchange_config,
        mock_trading_config,
        mocker,
    ):
        """Test collect_all raises error if all coins fail."""
        collector = DataCollector(mock_exchange_config, mock_trading_config)

        # Mock all coins to fail
        mocker.patch.object(
            collector,
            "collect_coin_data",
            side_effect=Exception("API error"),
        )

        with pytest.raises(Exception, match="Failed to collect data for any coin"):
            collector.collect_all()

    def test_get_prices_snapshot(
        self,
        mock_exchange_config,
        mock_trading_config,
        mock_price_data,
        mocker,
    ):
        """Test get_prices_snapshot returns prices for configured coins."""
        collector = DataCollector(mock_exchange_config, mock_trading_config)

        # Add extra coin not in config
        all_prices = {
            **mock_price_data,
            "DOGE": Price(coin="DOGE", price=0.1, timestamp=mock_price_data["BTC"].timestamp),
        }

        mocker.patch.object(
            collector.client,
            "get_all_prices",
            return_value=all_prices,
        )

        prices = collector.get_prices_snapshot()

        # Should only return configured coins
        assert len(prices) == 3
        assert "BTC" in prices
        assert "ETH" in prices
        assert "SOL" in prices
        assert "DOGE" not in prices

    def test_get_prices_snapshot_missing_coins(
        self,
        mock_exchange_config,
        mock_trading_config,
        mock_price_data,
        mocker,
    ):
        """Test get_prices_snapshot handles missing coins."""
        collector = DataCollector(mock_exchange_config, mock_trading_config)

        # Only BTC and ETH available, SOL missing
        partial_prices = {
            "BTC": mock_price_data["BTC"],
            "ETH": mock_price_data["ETH"],
        }

        mocker.patch.object(
            collector.client,
            "get_all_prices",
            return_value=partial_prices,
        )

        prices = collector.get_prices_snapshot()

        assert len(prices) == 2
        assert "BTC" in prices
        assert "ETH" in prices
        assert "SOL" not in prices

    def test_close(self, mock_exchange_config, mock_trading_config, mocker):
        """Test close() closes HTTP client."""
        collector = DataCollector(mock_exchange_config, mock_trading_config)

        mock_close = mocker.patch.object(collector.client, "close")

        collector.close()

        mock_close.assert_called_once()
