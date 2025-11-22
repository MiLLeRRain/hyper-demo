"""Technical indicators calculation using pandas-ta."""

import logging
from typing import Dict, Any, List
import pandas as pd
import pandas_ta as ta

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculate technical indicators for trading analysis."""

    def __init__(self):
        """Initialize indicators calculator."""
        pass

    def calculate_all(self, df: pd.DataFrame, history_len: int = 10) -> Dict[str, Any]:
        """
        Calculate all technical indicators for the given K-line data.

        Args:
            df: DataFrame with columns: timestamp, open, high, low, close, volume
            history_len: Number of historical data points to return in lists

        Returns:
            Dictionary with indicator values (scalars and lists)
        """
        if df.empty or len(df) < 50:
            logger.warning("Insufficient data for indicator calculation")
            return self._empty_indicators()

        try:
            indicators = {}

            # EMA (Exponential Moving Average)
            ema_20 = ta.ema(df["close"], length=20)
            ema_50 = ta.ema(df["close"], length=50)
            
            indicators["ema_20"] = float(ema_20.iloc[-1]) if not ema_20.empty else 0.0
            indicators["ema_50"] = float(ema_50.iloc[-1]) if not ema_50.empty else 0.0
            indicators["ema_20_list"] = self._get_tail(ema_20, history_len)

            # MACD
            macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)
            if macd_df is not None and not macd_df.empty:
                macd_col = "MACD_12_26_9"
                signal_col = "MACDs_12_26_9"
                hist_col = "MACDh_12_26_9"
                
                indicators["macd"] = float(macd_df[macd_col].iloc[-1])
                indicators["macd_signal"] = float(macd_df[signal_col].iloc[-1])
                indicators["macd_histogram"] = float(macd_df[hist_col].iloc[-1])
                indicators["macd_list"] = self._get_tail(macd_df[macd_col], history_len)
            else:
                indicators.update({"macd": 0.0, "macd_signal": 0.0, "macd_histogram": 0.0, "macd_list": []})

            # RSI (Relative Strength Index)
            rsi_7 = ta.rsi(df["close"], length=7)
            rsi_14 = ta.rsi(df["close"], length=14)
            
            indicators["rsi_7"] = float(rsi_7.iloc[-1]) if not rsi_7.empty else 50.0
            indicators["rsi_14"] = float(rsi_14.iloc[-1]) if not rsi_14.empty else 50.0
            indicators["rsi_7_list"] = self._get_tail(rsi_7, history_len)
            indicators["rsi_14_list"] = self._get_tail(rsi_14, history_len)

            # ATR (Average True Range)
            atr_3 = ta.atr(df["high"], df["low"], df["close"], length=3)
            atr_14 = ta.atr(df["high"], df["low"], df["close"], length=14)
            
            indicators["atr_3"] = float(atr_3.iloc[-1]) if not atr_3.empty else 0.0
            indicators["atr_14"] = float(atr_14.iloc[-1]) if not atr_14.empty else 0.0

            # Volume
            indicators["volume_current"] = float(df["volume"].iloc[-1])
            indicators["volume_avg"] = float(df["volume"].rolling(window=20).mean().iloc[-1])

            logger.debug(f"Calculated {len(indicators)} indicators")
            return indicators

        except Exception as e:
            logger.error(f"Failed to calculate indicators: {e}")
            return self._empty_indicators()

    def _get_tail(self, series: pd.Series, length: int) -> List[float]:
        """Get the last N values from a series as a list of floats."""
        if series is None or series.empty:
            return []
        return [float(x) for x in series.tail(length).tolist()]


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
    def _empty_indicators() -> Dict[str, Any]:
        """Return empty indicators dictionary with zero values."""
        return {
            "ema_20": 0.0,
            "ema_50": 0.0,
            "ema_20_list": [],
            "macd": 0.0,
            "macd_signal": 0.0,
            "macd_histogram": 0.0,
            "macd_list": [],
            "rsi_7": 50.0,
            "rsi_14": 50.0,
            "rsi_7_list": [],
            "rsi_14_list": [],
            "atr_3": 0.0,
            "atr_14": 0.0,
            "volume_current": 0.0,
            "volume_avg": 0.0,
        }
