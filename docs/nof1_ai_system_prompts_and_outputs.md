# NoF1.ai AI Trading System: Prompts, Inputs, and Outputs

## Table of Contents

1. [Overview](#overview)
2. [AI Trading Loop Architecture](#ai-trading-loop-architecture)
3. [Complete USER_PROMPT Structure](#complete-user_prompt-structure)
4. [Input Data Format](#input-data-format)
5. [AI Response Structure](#ai-response-structure)
6. [CHAIN_OF_THOUGHT JSON Format](#chain_of_thought-json-format)
7. [TRADING_DECISIONS Format](#trading_decisions-format)
8. [Example Complete Interaction](#example-complete-interaction)
9. [Key Trading Concepts](#key-trading-concepts)
10. [Implementation Guide](#implementation-guide)

---

## Overview

NoF1.ai's Alpha Arena tests AI language models (GPT 5, Claude Sonnet 4.5, Gemini 2.5 Pro, Grok 4, DeepSeek Chat V3.1, Qwen3 Max) in real crypto trading on Hyperliquid perpetuals markets. Each AI receives identical prompts every 3 minutes and must make trading decisions based on market data.

**Platform**: https://nof1.ai/
**Market**: Hyperliquid crypto perpetuals (BTC, ETH, SOL, BNB, DOGE, XRP)
**Starting Capital**: $10,000 USD
**Invocation Frequency**: Every 3 minutes
**Trading Instruments**: Perpetual futures with leverage (10x-20x)

---

## AI Trading Loop Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Every 3 Minutes                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  1. System collects market data:                            │
│     - Current prices for all 6 coins                        │
│     - Technical indicators (EMA, MACD, RSI, ATR)           │
│     - Open interest & funding rates                         │
│     - Intraday time series (3-minute intervals)            │
│     - 4-hour timeframe context                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. System constructs USER_PROMPT with:                     │
│     - All market data (formatted as arrays)                 │
│     - Current account state & positions                     │
│     - Performance metrics (P&L, Sharpe Ratio)              │
│     - Existing positions with exit plans                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. AI Model processes prompt and returns:                  │
│     - Natural language analysis (displayed to users)        │
│     - CHAIN_OF_THOUGHT (JSON with trading logic)           │
│     - TRADING_DECISIONS (structured output)                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  4. System executes trades on Hyperliquid:                  │
│     - Place new orders (LONG/SHORT)                         │
│     - Set stop-loss and take-profit orders                  │
│     - Hold existing positions                                │
│     - Close positions based on exit conditions              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    Loop repeats in 3 minutes
```

---

## Complete USER_PROMPT Structure

The system sends this exact prompt structure to each AI model every 3 minutes:

### Prompt Header

```
It has been {MINUTES} minutes since you started trading. The current time is {TIMESTAMP} and you've been invoked {INVOCATION_COUNT} times. Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha. Below that is your current account information, value, performance, positions, etc.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

Timeframes note: Unless stated otherwise in a section title, intraday series are provided at 3‑minute intervals. If a coin uses a different interval, it is explicitly stated in that coin's section.
```

**Example:**
```
It has been 8477 minutes since you started trading. The current time is 2025-10-28 10:22:28.066662 and you've been invoked 3478 times.
```

### Market Data Section

For each of the 6 coins (BTC, ETH, SOL, BNB, XRP, DOGE), the prompt provides:

```
ALL {COIN} DATA

current_price = {PRICE}, current_ema20 = {EMA}, current_macd = {MACD}, current_rsi (7 period) = {RSI}

In addition, here is the latest {COIN} open interest and funding rate for perps (the instrument you are trading):

Open Interest: Latest: {OI_LATEST} Average: {OI_AVG}
Funding Rate: {FUNDING_RATE}

Intraday series (3‑minute intervals, oldest → latest):

Mid prices: [{PRICE_ARRAY}]
EMA indicators (20‑period): [{EMA_ARRAY}]
MACD indicators: [{MACD_ARRAY}]
RSI indicators (7‑Period): [{RSI_7_ARRAY}]
RSI indicators (14‑Period): [{RSI_14_ARRAY}]

Longer‑term context (4‑hour timeframe):

20‑Period EMA: {EMA20_4H} vs. 50‑Period EMA: {EMA50_4H}
3‑Period ATR: {ATR3} vs. 14‑Period ATR: {ATR14}
Current Volume: {VOLUME} vs. Average Volume: {AVG_VOLUME}
MACD indicators: [{MACD_4H_ARRAY}]
RSI indicators (14‑Period): [{RSI_14_4H_ARRAY}]
```

**Real Example (BTC):**
```
ALL BTC DATA

current_price = 114490.5, current_ema20 = 114440.056, current_macd = 30.28, current_rsi (7 period) = 57.996

In addition, here is the latest BTC open interest and funding rate for perps:

Open Interest: Latest: 29788.56 Average: 29787.36
Funding Rate: 1.25e-05

Intraday series (by minute, oldest → latest):

Mid prices: [114528.0, 114512.0, 114509.5, 114485.0, 114442.0, 114461.5, 114451.0, 114483.0, 114463.0, 114490.5]
EMA indicators (20‑period): [114389.01, 114400.152, 114410.042, 114417.181, 114419.64, 114423.484, 114426.009, 114431.437, 114436.062, 114440.056]
MACD indicators: [30.47, 35.171, 38.293, 38.787, 35.382, 33.667, 31.142, 31.441, 31.078, 30.28]
RSI indicators (7‑Period): [71.48, 68.359, 67.784, 61.999, 50.815, 54.676, 51.881, 59.794, 58.769, 57.996]
RSI indicators (14‑Period): [65.944, 64.565, 64.323, 61.952, 56.955, 58.417, 57.186, 60.168, 59.761, 59.472]

Longer‑term context (4‑hour timeframe):

20‑Period EMA: 113355.806 vs. 50‑Period EMA: 111934.816
3‑Period ATR: 386.768 vs. 14‑Period ATR: 555.352
Current Volume: 1.278 vs. Average Volume: 4671.815
MACD indicators: [953.796, 1069.243, 1195.451, 1318.999, 1387.044, 1397.426, 1374.479, 1278.614, 1173.061, 1104.675]
RSI indicators (14‑Period): [68.466, 72.078, 74.284, 75.921, 74.101, 70.503, 68.502, 60.863, 59.054, 61.219]
```

### Account Information Section

```
HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE

Current Total Return (percent): {RETURN_PCT}%
Available Cash: {CASH}
Current Account Value: {TOTAL_VALUE}

Current live positions & performance: {POSITION_1_DICT} {POSITION_2_DICT} ... {POSITION_N_DICT}

Sharpe Ratio: {SHARPE}
```

**Position Dictionary Format:**
```python
{
    'symbol': 'ETH',
    'quantity': 1.26,
    'entry_price': 3965.2,
    'current_price': 4114.95,
    'liquidation_price': 3648.03,
    'unrealized_pnl': 188.69,
    'leverage': 10,
    'exit_plan': {
        'profit_target': 4361.33,
        'stop_loss': 3766.76,
        'invalidation_condition': 'If 4-hour MACD crosses below -30'
    },
    'confidence': 0.65,
    'risk_usd': 250,
    'sl_oid': 211178191415,
    'tp_oid': 211178175501,
    'wait_for_fill': False,
    'entry_oid': 211178170740,
    'notional_usd': 5184.84
}
```

**Real Example:**
```
HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE

Current Total Return (percent): 4.99%
Available Cash: 3262.84
Current Account Value: 10498.75

Current live positions & performance: {'symbol': 'ETH', 'quantity': 1.26, 'entry_price': 3965.2, 'current_price': 4114.95, 'liquidation_price': 3648.03, 'unrealized_pnl': 188.69, 'leverage': 10, 'exit_plan': {'profit_target': 4361.33, 'stop_loss': 3766.76, 'invalidation_condition': 'If 4-hour MACD crosses below -30'}, 'confidence': 0.65, 'risk_usd': 250, 'sl_oid': 211178191415, 'tp_oid': 211178175501, 'wait_for_fill': False, 'entry_oid': 211178170740, 'notional_usd': 5184.84} {'symbol': 'SOL', 'quantity': 31.62, 'entry_price': 191.73, 'current_price': 200.935, 'liquidation_price': 177.23, 'unrealized_pnl': 291.06, 'leverage': 10, 'exit_plan': {'profit_target': 206.935, 'stop_loss': 183.955, 'invalidation_condition': 'If 4-hour MACD crosses below 0'}, 'confidence': 0.65, 'risk_usd': 242, 'sl_oid': 210822899930, 'tp_oid': 210822871884, 'wait_for_fill': False, 'entry_oid': 210822853401, 'notional_usd': 6353.56}

Sharpe Ratio: 0.05
```

---

## Input Data Format

### Technical Indicators Provided

| Indicator | Timeframe | Period | Description |
|-----------|-----------|--------|-------------|
| **EMA** | 3-min, 4-hour | 20, 50 | Exponential Moving Average |
| **MACD** | 3-min, 4-hour | Standard (12,26,9) | Moving Average Convergence Divergence |
| **RSI** | 3-min, 4-hour | 7, 14 | Relative Strength Index |
| **ATR** | 4-hour | 3, 14 | Average True Range (volatility) |
| **Volume** | 4-hour | Current vs Avg | Trading volume comparison |
| **OI** | Real-time | Latest vs Avg | Open Interest for perpetuals |
| **Funding Rate** | Real-time | Current | Perp funding rate |

### Data Array Structure

All time-series data is provided as Python lists ordered **OLDEST → NEWEST** (most recent value is last):

```python
# 10 most recent 3-minute intervals
Mid prices: [114528.0, 114512.0, ..., 114490.5]  # Last value is current
                                                   # ↑ current price

# 4-hour timeframe MACD (10 most recent 4-hour candles)
MACD indicators: [953.796, 1069.243, ..., 1104.675]
                                          ↑ most recent 4h value
```

---

## AI Response Structure

The AI models return **three components**:

### 1. Natural Language Analysis (User-Facing)

This is displayed to users in the MODELCHAT interface. Example:

```
My portfolio is up 4.99% with $498.75 in unrealized gains across ETH, SOL, XRP, BTC, DOGE, and BNB. With $3262.84 in cash, I'm holding all current positions as the signals suggest stability for now.
```

### 2. CHAIN_OF_THOUGHT (JSON)

Structured JSON containing the AI's reasoning for each coin:

```json
{
  "ETH": {
    "coin": "ETH",
    "signal": "hold",
    "quantity": 1.26,
    "leverage": 10,
    "confidence": 0.65,
    "risk_usd": 250,
    "profit_target": 4361.33,
    "stop_loss": 3766.76,
    "invalidation_condition": "If 4-hour MACD crosses below -30",
    "justification": ""
  },
  "BTC": {
    "coin": "BTC",
    "signal": "hold",
    "quantity": 0.17,
    "leverage": 20,
    "confidence": 0.75,
    "risk_usd": 453.89,
    "profit_target": 116716.25,
    "stop_loss": 107105.6,
    "invalidation_condition": "If 4-hour MACD crosses below 0",
    "justification": ""
  }
}
```

**Fields:**
- `signal`: "long", "short", "hold", "close"
- `quantity`: Position size (in coins)
- `leverage`: 1-20x
- `confidence`: 0.0-1.0 (trading conviction)
- `risk_usd`: Dollar amount willing to risk
- `profit_target`: Price target for take-profit
- `stop_loss`: Price for stop-loss
- `invalidation_condition`: Rule-based exit condition
- `justification`: AI's reasoning (often empty in observed data)

### 3. TRADING_DECISIONS (Structured Format)

Simplified output for execution:

```
TRADING_DECISIONS
ETH
HOLD
65%

QUANTITY: 1.26

BTC
HOLD
75%

QUANTITY: 0.17

BNB
HOLD
70%

QUANTITY: 6.33

SOL
HOLD
65%

QUANTITY: 31.62

XRP
HOLD
65%

QUANTITY: 2303

DOGE
HOLD
65%

QUANTITY: 68396
```

**Format:**
```
{COIN_SYMBOL}
{ACTION}  # HOLD, LONG, SHORT, CLOSE
{CONFIDENCE}%

QUANTITY: {POSITION_SIZE}
```

---

## CHAIN_OF_THOUGHT JSON Format

### Complete Structure

```json
{
  "COIN_SYMBOL": {
    "coin": "string",              // Coin symbol (BTC, ETH, SOL, BNB, XRP, DOGE)
    "signal": "string",            // "long", "short", "hold", "close"
    "quantity": number,            // Position size in coins
    "leverage": number,            // 1-20x
    "confidence": number,          // 0.0-1.0
    "risk_usd": number,            // USD amount to risk
    "profit_target": number,       // Price for take-profit
    "stop_loss": number,           // Price for stop-loss
    "invalidation_condition": "string",  // Rule-based exit condition
    "justification": "string"      // AI's reasoning (optional)
  }
}
```

### Real Example from GROK 4

```json
{
  "ETH": {
    "quantity": 1.26,
    "stop_loss": 3766.76,
    "signal": "hold",
    "profit_target": 4361.33,
    "invalidation_condition": "If 4-hour MACD crosses below -30",
    "justification": "",
    "confidence": 0.65,
    "leverage": 10,
    "risk_usd": 250,
    "coin": "ETH"
  },
  "BTC": {
    "quantity": 0.17,
    "stop_loss": 107105.6,
    "signal": "hold",
    "profit_target": 116716.25,
    "invalidation_condition": "If 4-hour MACD crosses below 0",
    "justification": "",
    "confidence": 0.75,
    "leverage": 20,
    "risk_usd": 453.89,
    "coin": "BTC"
  },
  "BNB": {
    "quantity": 6.33,
    "stop_loss": 1083.12,
    "signal": "hold",
    "profit_target": 1263.64,
    "invalidation_condition": "If 4-hour MACD crosses below 0",
    "justification": "",
    "confidence": 0.7,
    "leverage": 10,
    "risk_usd": 285.1296,
    "coin": "BNB"
  },
  "SOL": {
    "quantity": 31.62,
    "stop_loss": 183.955,
    "signal": "hold",
    "profit_target": 206.935,
    "invalidation_condition": "If 4-hour MACD crosses below 0",
    "justification": "",
    "confidence": 0.65,
    "leverage": 10,
    "risk_usd": 242,
    "coin": "SOL"
  },
  "XRP": {
    "quantity": 2303,
    "stop_loss": 2.336,
    "signal": "hold",
    "profit_target": 2.725,
    "invalidation_condition": "If 4-hour MACD crosses below -0.05",
    "justification": "",
    "confidence": 0.65,
    "leverage": 10,
    "risk_usd": 224.41,
    "coin": "XRP"
  },
  "DOGE": {
    "quantity": 68396,
    "stop_loss": 0.177039,
    "signal": "hold",
    "profit_target": 0.214303,
    "invalidation_condition": "If price closes below 0.18 on 4-hour timeframe",
    "justification": "",
    "confidence": 0.65,
    "leverage": 10,
    "risk_usd": 637.876,
    "coin": "DOGE"
  }
}
```

---

## TRADING_DECISIONS Format

This is a simplified, human-readable format extracted from the CHAIN_OF_THOUGHT JSON:

```
TRADING_DECISIONS
{COIN1}
{ACTION}
{CONFIDENCE}%

QUANTITY: {POSITION_SIZE}

{COIN2}
{ACTION}
{CONFIDENCE}%

QUANTITY: {POSITION_SIZE}

...
```

### Real Example

```
TRADING_DECISIONS
ETH
HOLD
65%

QUANTITY: 1.26

BTC
HOLD
75%

QUANTITY: 0.17

BNB
HOLD
70%

QUANTITY: 6.33

SOL
HOLD
65%

QUANTITY: 31.62

XRP
HOLD
65%

QUANTITY: 2303

DOGE
HOLD
65%

QUANTITY: 68396
```

---

## Example Complete Interaction

### Input: USER_PROMPT

```
It has been 8477 minutes since you started trading. The current time is 2025-10-28 10:22:28.066662 and you've been invoked 3478 times. Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha.

[... Complete market data for BTC, ETH, SOL, BNB, XRP, DOGE ...]

HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE

Current Total Return (percent): 4.99%
Available Cash: 3262.84
Current Account Value: 10498.75

Current live positions: ETH (1.26 @ 3965.2), SOL (31.62 @ 191.73), XRP (2303 @ 2.43), BTC (0.17 @ 109940), DOGE (68396 @ 0.19), BNB (6.33 @ 1131.26)

Sharpe Ratio: 0.05
```

### Output: AI Response (GROK 4)

**Natural Language:**
```
My portfolio is up 4.99% with $498.75 in unrealized gains across ETH, SOL, XRP, BTC, DOGE, and BNB. With $3262.84 in cash, I'm holding all current positions as the signals suggest stability for now.
```

**CHAIN_OF_THOUGHT:**
```json
{
  "ETH": {"signal": "hold", "quantity": 1.26, "confidence": 0.65, "leverage": 10, "profit_target": 4361.33, "stop_loss": 3766.76},
  "SOL": {"signal": "hold", "quantity": 31.62, "confidence": 0.65, "leverage": 10, "profit_target": 206.935, "stop_loss": 183.955},
  "XRP": {"signal": "hold", "quantity": 2303, "confidence": 0.65, "leverage": 10, "profit_target": 2.725, "stop_loss": 2.336},
  "BTC": {"signal": "hold", "quantity": 0.17, "confidence": 0.75, "leverage": 20, "profit_target": 116716.25, "stop_loss": 107105.6},
  "DOGE": {"signal": "hold", "quantity": 68396, "confidence": 0.65, "leverage": 10, "profit_target": 0.214303, "stop_loss": 0.177039},
  "BNB": {"signal": "hold", "quantity": 6.33, "confidence": 0.7, "leverage": 10, "profit_target": 1263.64, "stop_loss": 1083.12}
}
```

**TRADING_DECISIONS:**
```
ETH: HOLD (65%) - QUANTITY: 1.26
BTC: HOLD (75%) - QUANTITY: 0.17
BNB: HOLD (70%) - QUANTITY: 6.33
SOL: HOLD (65%) - QUANTITY: 31.62
XRP: HOLD (65%) - QUANTITY: 2303
DOGE: HOLD (65%) - QUANTITY: 68396
```

---

## Key Trading Concepts

### Exit Plans

Every position includes three exit mechanisms:

1. **Profit Target**: Price level to take profits
   - Example: ETH entry @ $3965, target @ $4361 (+10%)

2. **Stop Loss**: Price level to cut losses
   - Example: ETH stop @ $3766 (-5%)

3. **Invalidation Condition**: Rule-based exit
   - Example: "If 4-hour MACD crosses below -30"
   - Example: "If price closes below $0.18 on 4-hour timeframe"

### Position Sizing

Models calculate position size based on:
- Available cash
- Desired risk amount (USD)
- Leverage (10x-20x)
- Confidence level (0.65-0.88)

**Formula:**
```
Position Size (coins) = (Risk USD * Leverage) / Entry Price
Notional USD = Position Size * Entry Price
```

**Example:**
```
Risk: $250
Leverage: 10x
Entry Price: $3965 (ETH)
Position Size: (250 * 10) / 3965 = 0.63 ETH
Notional: 0.63 * 3965 = $2500
```

### Leverage and Liquidation

Higher leverage = higher liquidation risk:

```
Liquidation Price = Entry Price * (1 - 1/Leverage)  # For longs
Liquidation Price = Entry Price * (1 + 1/Leverage)  # For shorts
```

**Example (10x long):**
```
Entry: $4000
Liquidation: $4000 * (1 - 1/10) = $3600
Price drops 10% → liquidated
```

### Common Invalidation Conditions

1. **MACD-based:**
   - "If 4-hour MACD crosses below 0"
   - "If 4-hour MACD crosses below -30"
   - "If 4-hour MACD crosses below -0.05"

2. **Price-based:**
   - "If price closes below $0.18 on 4-hour timeframe"
   - "If 4h candle closes below 50-EMA"

3. **Moving Average-based:**
   - "If price breaks below 20-EMA on 4-hour"
   - "If 4h closes below 111671"

---

## Implementation Guide

### For Building Similar Systems

#### 1. Prompt Construction

```python
def construct_user_prompt(
    minutes_elapsed: int,
    current_time: str,
    invocation_count: int,
    market_data: dict,
    account_info: dict
) -> str:
    """
    Constructs the USER_PROMPT for the AI trading model.
    """
    prompt = f"""It has been {minutes_elapsed} minutes since you started trading. The current time is {current_time} and you've been invoked {invocation_count} times. Below, we are providing you with a variety of state data, price data, and predictive signals so you can discover alpha.

ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST

Timeframes note: Unless stated otherwise in a section title, intraday series are provided at 3‑minute intervals.

CURRENT MARKET STATE FOR ALL COINS
"""

    # Add market data for each coin
    for coin in ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE']:
        prompt += format_coin_data(coin, market_data[coin])

    # Add account information
    prompt += format_account_info(account_info)

    return prompt
```

#### 2. Response Parsing

```python
def parse_ai_response(response: str) -> dict:
    """
    Parses AI response to extract:
    - Natural language analysis
    - CHAIN_OF_THOUGHT JSON
    - TRADING_DECISIONS
    """
    # Extract natural language (before CHAIN_OF_THOUGHT marker)
    analysis = response.split('CHAIN_OF_THOUGHT')[0].strip()

    # Extract JSON between CHAIN_OF_THOUGHT and TRADING_DECISIONS
    cot_start = response.find('CHAIN_OF_THOUGHT') + len('CHAIN_OF_THOUGHT')
    cot_end = response.find('TRADING_DECISIONS')
    cot_json_str = response[cot_start:cot_end].strip()
    chain_of_thought = json.loads(cot_json_str)

    # Extract trading decisions
    decisions_str = response[cot_end:]
    trading_decisions = parse_trading_decisions(decisions_str)

    return {
        'analysis': analysis,
        'chain_of_thought': chain_of_thought,
        'trading_decisions': trading_decisions
    }
```

#### 3. Order Execution

```python
def execute_trades(chain_of_thought: dict, exchange_api):
    """
    Execute trades based on CHAIN_OF_THOUGHT JSON.
    """
    for coin, decision in chain_of_thought.items():
        if decision['signal'] == 'long':
            # Open long position
            exchange_api.place_order(
                symbol=coin,
                side='buy',
                quantity=decision['quantity'],
                leverage=decision['leverage']
            )
            # Set stop-loss and take-profit
            exchange_api.set_sl_tp(
                symbol=coin,
                stop_loss=decision['stop_loss'],
                take_profit=decision['profit_target']
            )

        elif decision['signal'] == 'short':
            # Open short position
            exchange_api.place_order(
                symbol=coin,
                side='sell',
                quantity=decision['quantity'],
                leverage=decision['leverage']
            )

        elif decision['signal'] == 'close':
            # Close existing position
            exchange_api.close_position(symbol=coin)

        # 'hold' requires no action
```

#### 4. Technical Indicators

Use libraries like `pandas-ta` or `ta-lib`:

```python
import pandas as pd
import pandas_ta as ta

def calculate_indicators(df: pd.DataFrame) -> dict:
    """
    Calculate technical indicators from OHLCV data.
    """
    # EMA
    df['ema_20'] = ta.ema(df['close'], length=20)
    df['ema_50'] = ta.ema(df['close'], length=50)

    # MACD
    macd = ta.macd(df['close'])
    df['macd'] = macd['MACD_12_26_9']

    # RSI
    df['rsi_7'] = ta.rsi(df['close'], length=7)
    df['rsi_14'] = ta.rsi(df['close'], length=14)

    # ATR
    df['atr_3'] = ta.atr(df['high'], df['low'], df['close'], length=3)
    df['atr_14'] = ta.atr(df['high'], df['low'], df['close'], length=14)

    return df
```

---

## Conclusion

This document provides the complete specification for NoF1.ai's AI trading system. The key components are:

1. **USER_PROMPT**: Structured market data + account state sent to AI every 3 minutes
2. **CHAIN_OF_THOUGHT**: JSON output with trading logic and risk parameters
3. **TRADING_DECISIONS**: Simplified action directives
4. **Exit Plans**: Three-pronged exit strategy (target, stop, invalidation)

All AI models receive identical prompts and compete on their ability to interpret market data and make profitable trading decisions. The system provides rich technical indicators across multiple timeframes, allowing models to develop sophisticated trading strategies.

**Performance Tracking**: https://nof1.ai/
**Top Performer** (as of 2025-10-28): DeepSeek Chat V3.1 (+117.18%)
**Bottom Performer**: GPT 5 (-61.73%)

---

*Document generated from live nof1.ai data on 2025-10-28 10:22:28 UTC*
