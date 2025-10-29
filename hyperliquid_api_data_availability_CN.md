# HyperLiquid API 数据可用性分析

## 问题：HyperLiquid能免费提供NoF1.ai所需的所有数据吗？

**答案：是的，HyperLiquid完全免费提供NoF1.ai所需的所有市场数据！**

---

## NoF1.ai 所需数据清单

根据我们之前提取的 `nof1_ai_system_prompts_and_outputs.md` 文档，NoF1.ai的AI交易系统需要以下数据：

### 1. 价格数据
- ✅ **实时价格** (current_price)
- ✅ **历史K线数据** (OHLCV)
- ✅ **3分钟间隔的价格序列**

### 2. 技术指标数据
- ✅ **EMA** (20周期, 50周期)
- ✅ **MACD** (标准12,26,9)
- ✅ **RSI** (7周期, 14周期)
- ✅ **ATR** (3周期, 14周期)
- ⚠️ **Volume** (需要从K线数据计算)

### 3. 永续合约特定数据
- ✅ **Open Interest** (持仓量)
- ✅ **Funding Rate** (资金费率)
- ✅ **预测资金费率**

### 4. 账户数据
- ✅ **持仓信息**
- ✅ **账户价值**
- ✅ **未实现盈亏**
- ✅ **清算价格**

---

## HyperLiquid 免费提供的API端点

### REST API 端点 (https://api.hyperliquid.xyz/info)

#### 市场数据端点（无需认证）

| 端点类型 | NoF1需要 | HyperLiquid提供 | 说明 |
|---------|---------|----------------|------|
| **allMids** | ✅ 实时价格 | ✅ 提供 | 所有币种的mid价格 |
| **l2Book** | ✅ 订单簿 | ✅ 提供 | 20档买卖盘快照 |
| **candleSnapshot** | ✅ K线数据 | ✅ 提供 | 支持1m/3m/5m/15m/30m/1h/2h/4h等多个周期 |
| **metaAndAssetCtxs** | ✅ 综合数据 | ✅ 提供 | **包含funding rate, open interest, mark price, oracle price, 成交量** |
| **fundingHistory** | ✅ 历史资金费率 | ✅ 提供 | 可按时间范围查询 |
| **predictedFundings** | ✅ 预测资金费率 | ✅ 提供 | 多个交易所的预期资金费率 |
| **meta** | ✅ 合约信息 | ✅ 提供 | 资产名称、最大杠杆、保证金表 |

#### 账户数据端点（需要地址参数）

| 端点类型 | NoF1需要 | HyperLiquid提供 | 说明 |
|---------|---------|----------------|------|
| **clearinghouseState** | ✅ 账户状态 | ✅ 提供 | 持仓、保证金、清算价格、累计资金费 |
| **userFills** | ✅ 成交记录 | ✅ 提供 | 用户成交历史 |
| **userFunding** | ✅ 资金费用历史 | ✅ 提供 | 历史资金费用明细 |

### WebSocket API (wss://api.hyperliquid.xyz/ws)

#### 实时市场数据频道（无需认证）

| 频道 | NoF1需要 | HyperLiquid提供 | 更新频率 | 说明 |
|------|---------|----------------|----------|------|
| **allMids** | ✅ 实时价格 | ✅ 提供 | 每个区块(≥0.5s) | 所有资产的mid价格 |
| **l2Book** | ✅ 订单簿更新 | ✅ 提供 | 每个区块(≥0.5s) | 订单簿快照 |
| **trades** | ✅ 成交数据 | ✅ 提供 | 实时 | 价格、数量、买卖方、时间戳 |
| **candle** | ✅ K线数据 | ✅ 提供 | 实时 | 1m/3m/5m/15m/30m/1h/2h/4h等 |
| **bbo** | ✅ 最优买卖价 | ✅ 提供 | 变化时推送 | 最优bid/ask |
| **activeAssetCtx** | ✅ 资产上下文 | ✅ 提供 | 实时 | 成交量、价格、资金费率 |

#### 实时账户数据频道（需要地址参数）

| 频道 | NoF1需要 | HyperLiquid提供 | 说明 |
|------|---------|----------------|------|
| **orderUpdates** | ✅ 订单状态 | ✅ 提供 | 订单变化实时推送 |
| **userFills** | ✅ 成交推送 | ✅ 提供 | 用户成交实时通知 |
| **userFundings** | ✅ 资金费用 | ✅ 提供 | 每小时资金费用推送 |
| **webData2** | ✅ 账户汇总 | ✅ 提供 | 账户综合信息 |

---

## 详细数据对比分析

### 1. 价格数据 ✅ 完全满足

**NoF1.ai需要:**
```python
# 3分钟间隔的价格序列（最近10个）
Mid prices: [114528.0, 114512.0, 114509.5, ..., 114490.5]
```

**HyperLiquid提供:**
- **REST**: `candleSnapshot` - 支持3m周期，最多5000根K线
- **WebSocket**: `candle` - 实时3分钟K线推送
- **实现方式**:
  ```json
  POST https://api.hyperliquid.xyz/info
  {
    "type": "candleSnapshot",
    "req": {
      "coin": "BTC",
      "interval": "3m",
      "startTime": 1698480000000,
      "endTime": 1698483600000
    }
  }
  ```

### 2. 技术指标 ✅ 可计算获得

**NoF1.ai需要:**
```
EMA indicators (20‑period): [114389.01, 114400.152, ..., 114440.056]
MACD indicators: [30.47, 35.171, ..., 30.28]
RSI indicators (7‑Period): [71.48, 68.359, ..., 57.996]
ATR: 386.768 (4h, 3-period)
```

**HyperLiquid提供:**
- ❌ **不直接提供技术指标**
- ✅ **但提供原始OHLCV数据**
- ✅ **可通过Python库计算**: `pandas-ta`, `ta-lib`, `tulip`

**计算示例:**
```python
import pandas as pd
import pandas_ta as ta

# 获取K线数据
candles = get_hyperliquid_candles("BTC", "3m", limit=100)
df = pd.DataFrame(candles)

# 计算技术指标
df['ema_20'] = ta.ema(df['close'], length=20)
df['macd'] = ta.macd(df['close'])['MACD_12_26_9']
df['rsi_7'] = ta.rsi(df['close'], length=7)
df['rsi_14'] = ta.rsi(df['close'], length=14)
df['atr_3'] = ta.atr(df['high'], df['low'], df['close'], length=3)
```

### 3. Open Interest (持仓量) ✅ 完全满足

**NoF1.ai需要:**
```
Open Interest: Latest: 29788.56 Average: 29787.36
```

**HyperLiquid提供:**
- **REST**: `metaAndAssetCtxs` 端点
  ```json
  {
    "type": "metaAndAssetCtxs"
  }
  ```
  返回字段包含: `"openInterest": "29788.56"`

- **WebSocket**: `activeAssetCtx` 频道
  - 实时推送持仓量变化

### 4. Funding Rate (资金费率) ✅ 完全满足

**NoF1.ai需要:**
```
Funding Rate: 1.25e-05
```

**HyperLiquid提供:**
- **REST**:
  - `metaAndAssetCtxs` - 当前资金费率
  - `fundingHistory` - 历史资金费率
  - `predictedFundings` - 预测资金费率

  ```json
  {
    "type": "metaAndAssetCtxs"
  }
  ```
  返回: `"funding": "0.0000125"`

- **WebSocket**: `activeAssetCtx` - 实时资金费率更新

### 5. 成交量数据 ✅ 完全满足

**NoF1.ai需要:**
```
Current Volume: 1.278 vs. Average Volume: 4671.815
```

**HyperLiquid提供:**
- **K线数据中的成交量**:
  ```json
  {
    "t": 1698480000000,
    "o": "114500",
    "h": "114600",
    "l": "114400",
    "c": "114528",
    "v": "1234.5",    // ← 成交量
    "n": 156          // 成交笔数
  }
  ```

- **metaAndAssetCtxs** 中的日成交量:
  ```json
  "dayNtlVlm": "1234567890.50"  // 24小时名义成交量
  ```

### 6. 账户数据 ✅ 完全满足

**NoF1.ai需要:**
```python
{
    'symbol': 'ETH',
    'quantity': 1.26,
    'entry_price': 3965.2,
    'current_price': 4114.95,
    'liquidation_price': 3648.03,
    'unrealized_pnl': 188.69,
    'leverage': 10
}
```

**HyperLiquid提供:**
- **REST**: `clearinghouseState` 端点
  ```json
  {
    "type": "clearinghouseState",
    "user": "0x..."
  }
  ```
  返回完整持仓信息:
  ```json
  {
    "assetPositions": [{
      "position": {
        "coin": "ETH",
        "szi": "1.26",           // 持仓数量
        "entryPx": "3965.2",     // 入场价格
        "liquidationPx": "3648.03",  // 清算价格
        "unrealizedPnl": "188.69",   // 未实现盈亏
        "leverage": {
          "type": "cross",
          "value": 10
        }
      }
    }]
  }
  ```

---

## NoF1.ai 数据获取完整方案

### 方案1: REST API 轮询 (NoF1.ai当前使用的方式)

**优点:**
- 简单易实现
- 无需维护长连接
- 适合3分钟更新频率

**缺点:**
- 有轻微延迟
- 需要多次API调用

**实现示例:**
```python
import requests
import time

API_URL = "https://api.hyperliquid.xyz/info"

def get_all_data():
    # 1. 获取所有币种的价格、OI、资金费率
    market_data = requests.post(API_URL, json={
        "type": "metaAndAssetCtxs"
    }).json()

    # 2. 获取每个币种的K线数据（用于计算技术指标）
    candles = {}
    for coin in ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE']:
        candles[coin] = requests.post(API_URL, json={
            "type": "candleSnapshot",
            "req": {
                "coin": coin,
                "interval": "3m",
                "startTime": int((time.time() - 3600) * 1000),  # 最近1小时
                "endTime": int(time.time() * 1000)
            }
        }).json()

    # 3. 获取账户状态
    account = requests.post(API_URL, json={
        "type": "clearinghouseState",
        "user": "0xYourAddress"
    }).json()

    return market_data, candles, account

# 每3分钟调用一次
while True:
    data = get_all_data()
    # 处理数据...
    time.sleep(180)  # 3分钟
```

### 方案2: WebSocket 实时流 (更高效)

**优点:**
- 实时数据推送
- 减少API调用
- 延迟最低

**缺点:**
- 需要维护连接
- 实现稍复杂

**实现示例:**
```python
import websocket
import json

WS_URL = "wss://api.hyperliquid.xyz/ws"

def on_message(ws, message):
    data = json.loads(message)
    # 处理实时数据
    print(data)

def on_open(ws):
    # 订阅所有需要的频道
    subscriptions = [
        {"method": "subscribe", "subscription": {"type": "allMids"}},
        {"method": "subscribe", "subscription": {"type": "activeAssetCtx", "coin": "BTC"}},
        {"method": "subscribe", "subscription": {"type": "candle", "coin": "BTC", "interval": "3m"}},
        # ... 订阅其他币种和频道
    ]

    for sub in subscriptions:
        ws.send(json.dumps(sub))

ws = websocket.WebSocketApp(WS_URL,
                            on_message=on_message,
                            on_open=on_open)
ws.run_forever()
```

---

## 费用和限制

### 完全免费 ✅

| 项目 | HyperLiquid | 说明 |
|-----|-------------|------|
| **市场数据API** | 免费 | 无需认证，无限调用 |
| **WebSocket连接** | 免费 | 无需认证（市场数据频道） |
| **账户数据API** | 免费 | 需要地址参数，无需私钥 |
| **交易手续费** | Maker: 0.0% / Taker: 0.035% | 只有实际交易收费 |
| **API调用限制** | 文档未明确说明 | 建议合理使用 |

### 建议的调用频率

根据NoF1.ai的3分钟更新周期:

```python
# 推荐配置
POLL_INTERVAL = 180  # 3分钟 = 180秒

# 每个周期的API调用:
# 1次 metaAndAssetCtxs (所有币种的OI、资金费率、价格)
# 6次 candleSnapshot (6个币种的K线数据)
# 1次 clearinghouseState (账户状态)
# 总计: 8次 REST API调用 / 3分钟

# 每天总调用量:
# (24小时 * 60分钟 / 3分钟) * 8次 = 3,840次/天
# 完全在合理范围内
```

---

## 总结

### ✅ HyperLiquid 完全满足 NoF1.ai 的所有数据需求

| 数据类型 | NoF1需要 | HyperLiquid提供 | 获取方式 |
|---------|---------|----------------|---------|
| **实时价格** | ✅ | ✅ | allMids / candleSnapshot |
| **历史K线** | ✅ | ✅ | candleSnapshot (最多5000根) |
| **Open Interest** | ✅ | ✅ | metaAndAssetCtxs |
| **Funding Rate** | ✅ | ✅ | metaAndAssetCtxs / fundingHistory |
| **成交量** | ✅ | ✅ | K线数据中的volume字段 |
| **技术指标(EMA/MACD/RSI/ATR)** | ✅ | ⚠️ 需自行计算 | 使用pandas-ta等库计算 |
| **账户状态** | ✅ | ✅ | clearinghouseState |
| **持仓信息** | ✅ | ✅ | clearinghouseState |
| **订单簿** | ❌ (NoF1不需要) | ✅ | l2Book |

### 唯一需要注意的点

1. **技术指标需要自行计算**
   - HyperLiquid只提供原始OHLCV数据
   - 需要使用Python库 (pandas-ta, ta-lib) 计算EMA、MACD、RSI、ATR
   - 这是标准做法，大多数交易所都不直接提供技术指标

2. **K线数据限制**
   - REST API最多返回5000根K线
   - 对于3分钟周期: 5000 * 3分钟 = 15,000分钟 ≈ 10.4天
   - 完全满足NoF1.ai的需求

### 推荐实现方案

```python
# 1. 使用HyperLiquid官方Python SDK
from hyperliquid.info import Info

info = Info()

# 2. 获取市场数据
meta = info.meta_and_asset_ctxs()
candles = info.candle_snapshot("BTC", "3m", 1000)

# 3. 计算技术指标
import pandas as pd
import pandas_ta as ta

df = pd.DataFrame(candles)
df['ema_20'] = ta.ema(df['close'], 20)
df['macd'] = ta.macd(df['close'])['MACD_12_26_9']

# 4. 获取账户数据
account = info.clearinghouse_state("0xYourAddress")
```

---

## 参考资料

- **HyperLiquid API文档**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- **Python SDK**: https://github.com/hyperliquid-dex/hyperliquid-python-sdk
- **技术指标计算库**:
  - pandas-ta: https://github.com/twopirllc/pandas-ta
  - ta-lib: https://github.com/mrjbq7/ta-lib

---

**结论: HyperLiquid的免费API完全能够提供NoF1.ai所需的所有数据，无需任何付费服务。**
