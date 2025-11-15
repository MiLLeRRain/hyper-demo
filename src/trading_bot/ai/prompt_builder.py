"""Prompt Builder - Builds NoF1.ai-style prompts for trading agents."""

import logging
from datetime import datetime
from typing import Dict, List, Any

from trading_bot.models.database import TradingAgent
from trading_bot.models.market_data import AccountInfo, Position

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds NoF1.ai-style prompts (~11k characters) for trading agents.

    The prompt includes:
    - Header (current time, system role)
    - Portfolio section (account balance, positions, PnL)
    - Market data section (6 coins: BTC, ETH, SOL, BNB, DOGE, XRP)
    - Technical indicators (3m and 4h timeframes: EMA, MACD, RSI, ATR)
    - Risk constraints
    - Task requirements (JSON output format)
    """

    # Coins to include in market data
    COINS = ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"]

    # Timeframes for technical indicators
    TIMEFRAMES = ["3m", "4h"]

    def __init__(self):
        """Initialize the Prompt Builder."""
        pass

    def build(
        self,
        market_data: Dict[str, Dict[str, Any]],
        positions: List[Position],
        account: AccountInfo,
        agent: TradingAgent
    ) -> str:
        """Build a complete prompt for the trading agent.

        Args:
            market_data: Dictionary of market data for each coin
                Format: {
                    "BTC": {
                        "price": 50000.0,
                        "3m": {"ema": ..., "macd": ..., "rsi": ..., "atr": ...},
                        "4h": {"ema": ..., "macd": ..., "rsi": ..., "atr": ...},
                    },
                    ...
                }
            positions: List of current positions
            account: Account information (balance, margin, etc.)
            agent: Trading agent configuration

        Returns:
            Complete prompt string (~11k characters)
        """
        sections = [
            self._build_header(),
            self._build_portfolio_section(account, positions),
            self._build_market_data_section(market_data),
            self._build_constraints_section(agent),
            self._build_task_section(),
        ]

        prompt = "\n\n".join(sections)

        logger.info(
            f"Built prompt for agent '{agent.name}' | "
            f"Length: {len(prompt)} chars | "
            f"Positions: {len(positions)}"
        )

        return prompt

    def _build_header(self) -> str:
        """Build the header section with current time and system role."""
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        return f"""# HyperLiquid AI Trading System
Current Time: {current_time}

You are an advanced AI trading agent operating on HyperLiquid DEX, a high-performance decentralized perpetual futures exchange.

Your goal is to maximize portfolio returns while managing risk through strategic perpetual futures trading decisions.
You have access to real-time market data, technical indicators, and your current portfolio state."""

    def _build_portfolio_section(
        self,
        account: AccountInfo,
        positions: List[Position]
    ) -> str:
        """Build the portfolio section with account balance and positions.

        Args:
            account: Account information
            positions: List of current positions

        Returns:
            Portfolio section string
        """
        section = "## Portfolio Status\n\n"

        # Account balance
        section += f"**Account Balance:**\n"
        section += f"- Total Value: ${account.account_value:,.2f}\n"
        section += f"- Available Balance: ${account.withdrawable:,.2f}\n"
        section += f"- Margin Used: ${account.margin_used:,.2f}\n"
        section += f"- Unrealized PnL: ${account.unrealized_pnl:,.2f}\n\n"

        # Current positions
        if positions:
            section += f"**Current Positions ({len(positions)}):**\n\n"

            for pos in positions:
                pnl_pct = (pos.unrealized_pnl / abs(pos.position_value) * 100) if pos.position_value != 0 else 0
                side_emoji = "🟢" if pos.side == "long" else "🔴"

                section += f"{side_emoji} **{pos.coin}** ({pos.side.upper()})\n"
                section += f"  - Size: {pos.size} contracts @ ${pos.entry_price:,.2f}\n"
                section += f"  - Current Price: ${pos.mark_price:,.2f}\n"
                section += f"  - Position Value: ${pos.position_value:,.2f}\n"
                section += f"  - Unrealized PnL: ${pos.unrealized_pnl:,.2f} ({pnl_pct:+.2f}%)\n"
                section += f"  - Leverage: {pos.leverage}x\n"
                section += f"  - Liquidation Price: ${pos.liquidation_price:,.2f}\n\n"
        else:
            section += "**Current Positions:** None (all cash)\n"

        return section

    def _build_market_data_section(
        self,
        market_data: Dict[str, Dict[str, Any]]
    ) -> str:
        """Build the market data section with prices and technical indicators.

        Args:
            market_data: Market data for each coin

        Returns:
            Market data section string
        """
        section = "## Market Data\n\n"

        for coin in self.COINS:
            if coin not in market_data:
                logger.warning(f"Missing market data for {coin}, skipping...")
                continue

            data = market_data[coin]

            section += f"### {coin}-USD Perpetual\n\n"
            section += f"**Current Price:** ${data['price']:,.2f}\n\n"

            # Technical indicators for each timeframe
            for tf in self.TIMEFRAMES:
                if tf not in data:
                    logger.warning(f"Missing {tf} data for {coin}, skipping...")
                    continue

                indicators = data[tf]

                section += f"**{tf.upper()} Timeframe:**\n"
                section += f"- EMA(20): ${indicators.get('ema', 0):,.2f}\n"
                section += f"- MACD: {indicators.get('macd', 0):.4f} (Signal: {indicators.get('macd_signal', 0):.4f})\n"
                section += f"- RSI(14): {indicators.get('rsi', 0):.2f}\n"
                section += f"- ATR(14): ${indicators.get('atr', 0):.2f}\n\n"

        return section

    def _build_constraints_section(self, agent: TradingAgent) -> str:
        """Build the constraints section with risk management rules.

        Args:
            agent: Trading agent configuration

        Returns:
            Constraints section string
        """
        return f"""## Risk Management Constraints

You MUST follow these risk management rules:

1. **Position Sizing:**
   - Maximum position size per trade: {agent.max_position_size}% of account value
   - Maximum leverage: {agent.max_leverage}x
   - Maximum total exposure: Do not exceed 100% of account value across all positions

2. **Stop Loss:**
   - REQUIRED: Every position must have a stop loss
   - Maximum loss per trade: {agent.stop_loss_pct}% of position value
   - Stop loss must be realistic and account for market volatility (use ATR)

3. **Take Profit:**
   - Target profit per trade: {agent.take_profit_pct}% of position value
   - Consider scaling out at multiple levels

4. **Trading Strategy:**
   - Strategy: {agent.strategy_description or "Follow technical indicators and market trends"}
   - Focus on high-probability setups
   - Avoid overtrading

5. **Market Conditions:**
   - Do not trade during high volatility unless specifically designed for it
   - Consider overall market sentiment
   - Respect trend direction (don't fight the trend)"""

    def _build_task_section(self) -> str:
        """Build the task section with JSON output requirements.

        Returns:
            Task section string
        """
        return """## Your Task

Analyze the market data, technical indicators, and your current portfolio. Then make ONE trading decision.

**You must respond with ONLY a JSON object in this exact format:**

```json
{
  "reasoning": "Detailed explanation of your analysis and decision (2-3 sentences)",
  "action": "OPEN_LONG" | "OPEN_SHORT" | "CLOSE_POSITION" | "HOLD",
  "coin": "BTC" | "ETH" | "SOL" | "BNB" | "DOGE" | "XRP",
  "size_usd": 0.0,
  "leverage": 1,
  "stop_loss_price": 0.0,
  "take_profit_price": 0.0,
  "confidence": 0.0
}
```

**Field Definitions:**

- `reasoning`: Your analysis explaining WHY you made this decision (required, 2-3 sentences)
- `action`: The action to take (required)
  - "OPEN_LONG": Open a new long position
  - "OPEN_SHORT": Open a new short position
  - "CLOSE_POSITION": Close an existing position for the specified coin
  - "HOLD": Do nothing (no good trading opportunity right now)
- `coin`: The cryptocurrency to trade (required)
- `size_usd`: Position size in USD (required for OPEN_LONG/OPEN_SHORT, 0 for CLOSE/HOLD)
- `leverage`: Leverage to use, 1-50x (required for OPEN_LONG/OPEN_SHORT, 1 for CLOSE/HOLD)
- `stop_loss_price`: Stop loss price in USD (required for OPEN_LONG/OPEN_SHORT, 0 for CLOSE/HOLD)
- `take_profit_price`: Take profit price in USD (required for OPEN_LONG/OPEN_SHORT, 0 for CLOSE/HOLD)
- `confidence`: Your confidence in this decision, 0.0-1.0 (required)

**Important Notes:**

1. You MUST output valid JSON only - no other text before or after
2. You can only make ONE decision per cycle
3. Do NOT open a new position if you already have a position in that coin
4. Stop loss and take profit prices must be realistic and follow risk management rules
5. If there's no good trading opportunity, use "HOLD" action
6. Consider transaction costs and slippage in your decision

**Example Valid Responses:**

Opening a long position:
```json
{
  "reasoning": "BTC shows strong bullish momentum with RSI at 45 and price breaking above EMA on 4h chart. MACD golden cross confirms uptrend. Low ATR suggests stable entry.",
  "action": "OPEN_LONG",
  "coin": "BTC",
  "size_usd": 1000.0,
  "leverage": 3,
  "stop_loss_price": 49000.0,
  "take_profit_price": 52000.0,
  "confidence": 0.75
}
```

Holding (no action):
```json
{
  "reasoning": "Market conditions are unclear with mixed signals across timeframes. RSI near neutral and no clear trend direction. Better to wait for confirmation.",
  "action": "HOLD",
  "coin": "BTC",
  "size_usd": 0.0,
  "leverage": 1,
  "stop_loss_price": 0.0,
  "take_profit_price": 0.0,
  "confidence": 0.50
}
```

Closing a position:
```json
{
  "reasoning": "ETH position has reached take profit target of +8%. RSI showing overbought conditions on 3m chart. Good time to take profits.",
  "action": "CLOSE_POSITION",
  "coin": "ETH",
  "size_usd": 0.0,
  "leverage": 1,
  "stop_loss_price": 0.0,
  "take_profit_price": 0.0,
  "confidence": 0.85
}
```

Now, analyze the data and provide your decision as a JSON object."""
