"""Technical indicators calculation using pandas-ta."""

import logging
from typing import Dict
import pandas as pd
import pandas_ta as ta

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculate technical indicators for trading analysis."""

    def __init__(self):
        """Initialize indicators calculator."""
        pass

    def calculate_all(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate all technical indicators for the given K-line data.

        Args:
            df: DataFrame with columns: timestamp, open, high, low, close, volume

        Returns:
            Dictionary with indicator values:
            {
                "ema_20": float,
                "ema_50": float,
                "macd": float,
                "macd_signal": float,
                "macd_histogram": float,
                "rsi_7": float,
                "rsi_14": float,
                "atr_3": float,
                "atr_14": float,
            }
        """
        if df.empty or len(df) < 50:
            logger.warning("Insufficient data for indicator calculation")
            return self._empty_indicators()

        try:
            indicators = {}

            # EMA (Exponential Moving Average)
            indicators["ema_20"] = self.calculate_ema(df, period=20)
            indicators["ema_50"] = self.calculate_ema(df, period=50)

            # MACD
            macd_dict = self.calculate_macd(df)
            indicators.update(macd_dict)

            # RSI (Relative Strength Index)
            indicators["rsi_7"] = self.calculate_rsi(df, period=7)
            indicators["rsi_14"] = self.calculate_rsi(df, period=14)

            # ATR (Average True Range)
            indicators["atr_3"] = self.calculate_atr(df, period=3)
            indicators["atr_14"] = self.calculate_atr(df, period=14)

            logger.debug(f"Calculated {len(indicators)} indicators")
            return indicators

        except Exception as e:
            logger.error(f"Failed to calculate indicators: {e}")
            return self._empty_indicators()

    def calculate_ema(self, df: pd.DataFrame, period: int) -> float:
        """
        Calculate Exponential Moving Average.

        Args:
            df: DataFrame with 'close' column
            period: EMA period

        Returns:
            Latest EMA value
        """
        if len(df) < period:
            logger.warning(f"Insufficient data for EMA({period})")
            return 0.0

        ema = ta.ema(df["close"], length=period)
        return float(ema.iloc[-1]) if not ema.empty else 0.0

    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> Dict[str, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            df: DataFrame with 'close' column
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line period (default 9)

        Returns:
            Dictionary with macd, macd_signal, macd_histogram
        """
        if len(df) < slow + signal:
            logger.warning("Insufficient data for MACD")
            return {"macd": 0.0, "macd_signal": 0.0, "macd_histogram": 0.0}

        macd_df = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)

        if macd_df is None or macd_df.empty:
            return {"macd": 0.0, "macd_signal": 0.0, "macd_histogram": 0.0}

        # pandas_ta returns DataFrame with columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        macd_col = f"MACD_{fast}_{slow}_{signal}"
        signal_col = f"MACDs_{fast}_{slow}_{signal}"
        hist_col = f"MACDh_{fast}_{slow}_{signal}"

        return {
            "macd": float(macd_df[macd_col].iloc[-1]) if macd_col in macd_df else 0.0,
            "macd_signal": float(macd_df[signal_col].iloc[-1]) if signal_col in macd_df else 0.0,
            "macd_histogram": float(macd_df[hist_col].iloc[-1]) if hist_col in macd_df else 0.0,
        }

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate RSI (Relative Strength Index).

        Args:
            df: DataFrame with 'close' column
            period: RSI period (default 14)

        Returns:
            Latest RSI value (0-100)
        """
        if len(df) < period + 1:
            logger.warning(f"Insufficient data for RSI({period})")
            return 50.0  # Neutral value

        rsi = ta.rsi(df["close"], length=period)
        return float(rsi.iloc[-1]) if not rsi.empty else 50.0

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate ATR (Average True Range).

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ATR period (default 14)

        Returns:
            Latest ATR value
        """
        if len(df) < period + 1:
            logger.warning(f"Insufficient data for ATR({period})")
            return 0.0

        atr = ta.atr(df["high"], df["low"], df["close"], length=period)
        return float(atr.iloc[-1]) if not atr.empty else 0.0

    def calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std: float = 2.0,
    ) -> Dict[str, float]:
        """
        Calculate Bollinger Bands.

        Args:
            df: DataFrame with 'close' column
            period: Moving average period
            std: Standard deviation multiplier

        Returns:
            Dictionary with bb_upper, bb_middle, bb_lower
        """
        if len(df) < period:
            logger.warning("Insufficient data for Bollinger Bands")
            return {"bb_upper": 0.0, "bb_middle": 0.0, "bb_lower": 0.0}

        bb = ta.bbands(df["close"], length=period, std=std)

        if bb is None or bb.empty:
            return {"bb_upper": 0.0, "bb_middle": 0.0, "bb_lower": 0.0}

        # pandas_ta returns DataFrame with columns: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
        lower_col = f"BBL_{period}_{std}"
        middle_col = f"BBM_{period}_{std}"
        upper_col = f"BBU_{period}_{std}"

        return {
            "bb_upper": float(bb[upper_col].iloc[-1]) if upper_col in bb else 0.0,
            "bb_middle": float(bb[middle_col].iloc[-1]) if middle_col in bb else 0.0,
            "bb_lower": float(bb[lower_col].iloc[-1]) if lower_col in bb else 0.0,
        }

    @staticmethod
    def _empty_indicators() -> Dict[str, float]:
        """Return empty indicators dictionary with zero values."""
        return {
            "ema_20": 0.0,
            "ema_50": 0.0,
            "macd": 0.0,
            "macd_signal": 0.0,
            "macd_histogram": 0.0,
            "rsi_7": 50.0,
            "rsi_14": 50.0,
            "atr_3": 0.0,
            "atr_14": 0.0,
        }
