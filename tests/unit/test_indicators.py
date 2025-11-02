"""Unit tests for technical indicators."""

import pytest
import pandas as pd
from src.trading_bot.data.indicators import TechnicalIndicators


@pytest.mark.unit
class TestTechnicalIndicators:
    """Test technical indicators calculation."""

    def test_calculate_ema(self, mock_kline_data):
        """Test EMA calculation."""
        calc = TechnicalIndicators()
        ema_20 = calc.calculate_ema(mock_kline_data, period=20)

        assert isinstance(ema_20, float)
        assert ema_20 > 0
        # EMA should be close to recent prices
        last_close = mock_kline_data["close"].iloc[-1]
        assert 0.9 * last_close < ema_20 < 1.1 * last_close

    def test_calculate_ema_insufficient_data(self):
        """Test EMA with insufficient data."""
        calc = TechnicalIndicators()
        df = pd.DataFrame({
            "close": [100, 101, 102],
        })

        ema = calc.calculate_ema(df, period=20)
        assert ema == 0.0

    def test_calculate_rsi(self, mock_kline_data):
        """Test RSI calculation."""
        calc = TechnicalIndicators()
        rsi = calc.calculate_rsi(mock_kline_data, period=14)

        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100

    def test_calculate_rsi_uptrend(self):
        """Test RSI in uptrend should be > 50."""
        calc = TechnicalIndicators()

        # Create strong uptrend
        df = pd.DataFrame({
            "close": [i * 100 for i in range(1, 51)],
        })

        rsi = calc.calculate_rsi(df, period=14)
        assert rsi > 70  # Should indicate overbought

    def test_calculate_rsi_insufficient_data(self):
        """Test RSI with insufficient data returns neutral value."""
        calc = TechnicalIndicators()
        df = pd.DataFrame({
            "close": [100, 101],
        })

        rsi = calc.calculate_rsi(df, period=14)
        assert rsi == 50.0  # Neutral value

    def test_calculate_macd(self, mock_kline_data):
        """Test MACD calculation."""
        calc = TechnicalIndicators()
        macd = calc.calculate_macd(mock_kline_data)

        assert "macd" in macd
        assert "macd_signal" in macd
        assert "macd_histogram" in macd

        assert isinstance(macd["macd"], float)
        assert isinstance(macd["macd_signal"], float)
        assert isinstance(macd["macd_histogram"], float)

    def test_calculate_macd_histogram_equals_difference(self, mock_kline_data):
        """Test MACD histogram equals macd - signal."""
        calc = TechnicalIndicators()
        macd = calc.calculate_macd(mock_kline_data)

        # Histogram should equal macd - signal (with small floating point tolerance)
        expected_histogram = macd["macd"] - macd["macd_signal"]
        assert abs(macd["macd_histogram"] - expected_histogram) < 0.01

    def test_calculate_atr(self, mock_kline_data):
        """Test ATR calculation."""
        calc = TechnicalIndicators()
        atr = calc.calculate_atr(mock_kline_data, period=14)

        assert isinstance(atr, float)
        assert atr > 0

    def test_calculate_atr_measures_volatility(self):
        """Test ATR increases with volatility."""
        calc = TechnicalIndicators()

        # Low volatility
        df_low = pd.DataFrame({
            "high": [100.5] * 50,
            "low": [99.5] * 50,
            "close": [100] * 50,
        })

        # High volatility
        df_high = pd.DataFrame({
            "high": [110 + (i % 2) * 10 for i in range(50)],
            "low": [90 + (i % 2) * 10 for i in range(50)],
            "close": [100 + (i % 2) * 10 for i in range(50)],
        })

        atr_low = calc.calculate_atr(df_low, period=14)
        atr_high = calc.calculate_atr(df_high, period=14)

        assert atr_high > atr_low

    def test_calculate_all_indicators(self, mock_kline_data):
        """Test calculate_all returns all indicators."""
        calc = TechnicalIndicators()
        indicators = calc.calculate_all(mock_kline_data)

        # Check all expected indicators are present
        expected_keys = [
            "ema_20",
            "ema_50",
            "macd",
            "macd_signal",
            "macd_histogram",
            "rsi_7",
            "rsi_14",
            "atr_3",
            "atr_14",
        ]

        for key in expected_keys:
            assert key in indicators
            assert isinstance(indicators[key], float)

    def test_calculate_all_insufficient_data(self):
        """Test calculate_all with insufficient data returns empty indicators."""
        calc = TechnicalIndicators()
        df = pd.DataFrame({
            "open": [100],
            "high": [101],
            "low": [99],
            "close": [100.5],
            "volume": [1000],
        })

        indicators = calc.calculate_all(df)

        # Should return empty indicators with safe defaults
        assert indicators["ema_20"] == 0.0
        assert indicators["rsi_14"] == 50.0
        assert indicators["atr_14"] == 0.0

    def test_calculate_bollinger_bands(self, mock_kline_data):
        """Test Bollinger Bands calculation."""
        calc = TechnicalIndicators()
        bb = calc.calculate_bollinger_bands(mock_kline_data, period=20, std=2.0)

        assert "bb_upper" in bb
        assert "bb_middle" in bb
        assert "bb_lower" in bb

        # Upper > Middle > Lower
        assert bb["bb_upper"] > bb["bb_middle"]
        assert bb["bb_middle"] > bb["bb_lower"]

        # Middle should be close to current price
        last_close = mock_kline_data["close"].iloc[-1]
        assert 0.9 * last_close < bb["bb_middle"] < 1.1 * last_close
