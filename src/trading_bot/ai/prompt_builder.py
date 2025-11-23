"""Prompt Builder - Builds NoF1.ai-style prompts for trading agents."""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from trading_bot.models.database import TradingAgent
from trading_bot.models.market_data import AccountInfo, Position, MarketData

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds NoF1.ai-style prompts for trading agents.

    The prompt strictly follows the NoF1.ai specification:
    - Header (time, invocation count)
    - Market Data (Intraday series, 4h context)
    - Account Information
    """

    # Coins to include in market data
    COINS = ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"]

    def __init__(self):
        """Initialize the Prompt Builder."""
        pass

    def build(
        self,
        market_data: Dict[str, MarketData],
        positions: List[Position],
        account: AccountInfo,
        agent: TradingAgent,
        start_time: Optional[datetime] = None,
        invocation_count: int = 0
    ) -> str:
        """Build a complete prompt for the trading agent.

        Args:
            market_data: Dictionary of market data for each coin
            positions: List of current positions
            account: Account information
            agent: Trading agent configuration
            start_time: Time when the bot started trading
            invocation_count: Number of times the agent has been invoked

        Returns:
            Complete prompt string
        """
        # Calculate minutes elapsed
        if start_time:
            minutes_elapsed = int((datetime.utcnow() - start_time).total_seconds() / 60)
        else:
            minutes_elapsed = 0

        sections = [
            self._build_header(minutes_elapsed, invocation_count),
            self._build_market_data_section(market_data),
            self._build_account_section(account, positions, agent),
            self._build_system_instruction()
        ]

        prompt = "\n\n".join(sections)

        logger.info(
            f"Built prompt for agent '{agent.name}' | "
            f"Length: {len(prompt)} chars | "
            f"Positions: {len(positions)}"
        )

        return prompt

    def _build_header(self, minutes_elapsed: int, invocation_count: int) -> str:
        """Build the header section."""
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
        
        return f"""It has been {minutes_elapsed} minutes since you started trading. The current time is {current_time} and you've been invoked {invocation_count} times. Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha. Below that is your current account information, value, performance, positions, etc.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

Timeframes note: Unless stated otherwise in a section title, intraday series are provided at 3‑minute intervals. If a coin uses a different interval, it is explicitly stated in that coin's section."""

    def _build_market_data_section(self, market_data: Dict[str, MarketData]) -> str:
        """Build the market data section."""
        section = ""

        # Use all coins present in market data
        sorted_coins = sorted(list(market_data.keys()))
        
        for coin in sorted_coins:
            data = market_data[coin]
            
            # Extract scalar values
            current_price = data.price.price
            ind_3m = data.indicators_3m
            ind_4h = data.indicators_4h
            
            # Format scalar line
            section += f"\nALL {coin} DATA\n\n"
            section += f"current_price = {current_price}, current_ema20 = {ind_3m.get('ema_20', 0)}, current_macd = {ind_3m.get('macd', 0)}, current_rsi (7 period) = {ind_3m.get('rsi_7', 0)}\n\n"
            
            # Open Interest & Funding
            oi_latest = data.open_interest if data.open_interest else "N/A"
            oi_avg = "N/A" # We don't have historical OI yet to calc avg
            funding = data.funding_rate if data.funding_rate else "N/A"
            
            section += f"In addition, here is the latest {coin} open interest and funding rate for perps (the instrument you are trading):\n\n"
            section += f"Open Interest: Latest: {oi_latest} Average: {oi_avg}\n"
            section += f"Funding Rate: {funding}\n\n"
            
            # Intraday Series (3m)
            section += "Intraday series (3‑minute intervals, oldest → latest):\n\n"
            section += f"Mid prices: {data.mid_prices_list}\n"
            section += f"EMA indicators (20‑period): {ind_3m.get('ema_20_list', [])}\n"
            section += f"MACD indicators: {ind_3m.get('macd_list', [])}\n"
            section += f"RSI indicators (7‑Period): {ind_3m.get('rsi_7_list', [])}\n"
            section += f"RSI indicators (14‑Period): {ind_3m.get('rsi_14_list', [])}\n\n"
            
            # Longer-term context (4h)
            section += "Longer‑term context (4‑hour timeframe):\n\n"
            section += f"20‑Period EMA: {ind_4h.get('ema_20', 0)} vs. 50‑Period EMA: {ind_4h.get('ema_50', 0)}\n"
            section += f"3‑Period ATR: {ind_4h.get('atr_3', 0)} vs. 14‑Period ATR: {ind_4h.get('atr_14', 0)}\n"
            section += f"Current Volume: {data.volume_current_4h} vs. Average Volume: {data.volume_average_4h}\n"
            section += f"MACD indicators: {ind_4h.get('macd_list', [])}\n"
            section += f"RSI indicators (14‑Period): {ind_4h.get('rsi_14_list', [])}\n"

        return section

    def _build_account_section(self, account: AccountInfo, positions: List[Position], agent: TradingAgent) -> str:
        """Build the account information section."""
        # Calculate return pct (simplified)
        # Assuming starting balance was 10000 or we track it elsewhere. 
        # For now, we just show what we have.
        
        section = "HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE\n\n"
        section += f"Current Total Return (percent): N/A%\n" # We need to track starting balance to calc this
        section += f"Available Cash: {account.withdrawable}\n"
        section += f"Current Account Value: {account.account_value}\n"
        section += f"Max Allowed Leverage: {agent.max_leverage}x\n\n"
        
        section += "Current live positions & performance: "
        
        pos_strings = []
        for pos in positions:
            # Format as dictionary-like string as per example
            pos_dict = {
                'symbol': pos.coin,
                'quantity': pos.size,
                'entry_price': pos.entry_price,
                'current_price': pos.mark_price,
                'liquidation_price': pos.liquidation_price,
                'unrealized_pnl': pos.unrealized_pnl,
                'leverage': pos.leverage,
                # We don't have exit plan stored in Position object yet, so we omit or mock
                'exit_plan': {}, 
                'confidence': 0.0, # We don't store confidence in Position
                'risk_usd': 0.0,
                'notional_usd': pos.position_value
            }
            pos_strings.append(str(pos_dict))
            
        section += " ".join(pos_strings) + "\n\n"
        section += "Sharpe Ratio: N/A" # We don't calculate Sharpe yet
        
        return section

    def _build_system_instruction(self) -> str:
        """Build the system instruction for output format."""
        return """
IMPORTANT: You are a sophisticated crypto hedge fund manager. You must actively look for both LONG and SHORT opportunities. Do not hesitate to open SHORT positions if the technicals (e.g. bearish divergence, overbought RSI, downtrend) or market structure suggest a price decline.

TRADING STYLE GUIDELINES:
1. Focus on the 4-Hour Trend: Do not be shaken out by minor fluctuations in the 3-minute data. Use the 3-minute data for entry timing, but use the 4-hour data for trend direction.
2. Avoid Over-Trading: Only CLOSE a position if the market structure has clearly invalidated your thesis or the 4H trend has reversed. Do not close just to "lock in pennies" or because of short-term noise.
3. Let Profits Run: Be patient with winning positions.

You must respond with THREE components:

1. Natural Language Analysis (User-Facing)
2. CHAIN_OF_THOUGHT (JSON) - MUST INCLUDE AN ENTRY FOR EVERY COIN PROVIDED IN THE DATA ABOVE.
3. TRADING_DECISIONS (Structured Format) - MUST INCLUDE A DECISION FOR EVERY COIN.

Example Output Format:

My portfolio is up... [Analysis] ...

CHAIN_OF_THOUGHT
{
  "BTC": {
    "signal": "long/short/hold/close",
    "confidence": 0.85,
    "justification": "Detailed reasoning for the decision...",
    "risk_usd": 100.0,
    "leverage": 3,
    "stop_loss": 45000.0,
    "profit_target": 55000.0
  },
  "ETH": { ... },
  ... (one for each coin)
}

TRADING_DECISIONS
BTC
HOLD
65%

QUANTITY: 0

ETH
OPEN_LONG
70%

QUANTITY: 1.26

SOL
OPEN_SHORT
75%

QUANTITY: 15.5

... (one for each coin)
"""
