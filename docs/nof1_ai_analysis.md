# nof1.ai 网站完整分析文档

> 生成时间: 2025-10-28
> 分析工具: Chrome DevTools MCP
> 目标网站: https://nof1.ai/

---

## 1. 项目概览

**nof1.ai (Alpha Arena)** 是一个AI交易竞技平台，用于测试和比较不同AI模型在真实加密货币市场中的投资能力。

### 核心概念
- **真实资金**: 每个AI模型获得$10,000的真实资金
- **真实市场**: 在Hyperliquid平台交易加密货币永续合约
- **相同输入**: 所有模型接收相同的提示词和市场数据
- **公开透明**: 所有交易和模型输出完全公开

### 参赛模型
1. GPT 5 (OpenAI)
2. Claude Sonnet 4.5 (Anthropic)
3. Gemini 2.5 Pro (Google)
4. Grok 4 (xAI)
5. DeepSeek Chat V3.1 (DeepSeek)
6. Qwen 3 Max (Alibaba)
7. BTC Buy&Hold (基准对照)

### 比赛规则
- **起始资金**: 每个模型$10,000
- **交易市场**: Hyperliquid加密货币永续合约
- **交易资产**: BTC, ETH, SOL, BNB, DOGE, XRP
- **目标**: 最大化风险调整后收益
- **持续时间**: Season 1 运行至 2025年11月3日 17:00 EST
- **自主决策**: AI必须自主产生alpha、确定仓位大小、交易时机和风险管理

---

## 2. 网络请求分析

### 2.1 核心API端点

#### 初始加载关键API

| API端点 | 请求方式 | 刷新频率 | 作用 | 缓存策略 |
|---------|---------|---------|------|---------|
| `/api/crypto-prices` | GET | 实时轮询 (~5-10秒) | 获取加密货币实时价格 | HIT/公开缓存 |
| `/api/trades` | GET | 周期性 | 获取所有完成的交易记录 | HIT/公开缓存 |
| `/api/account-totals` | GET | 定期更新 | 获取所有模型的账户总值和持仓 | STALE/公开缓存 |
| `/api/since-inception-values` | GET | 低频 | 获取模型从开始至今的基准数据 | HIT/公开缓存 |
| `/api/leaderboard` | GET | 按需 | 获取排行榜数据 | HIT/公开缓存 |
| `/api/analytics/[model_id]` | GET | 按需 | 获取单个模型的详细分析数据 | HIT/公开缓存 |

#### 辅助API

| API端点 | 作用 |
|---------|------|
| `/_vercel/insights/view` | 页面访问统计 |
| `/_vercel/insights/event` | 用户行为事件跟踪 |
| `/_next/data/[buildId]/blog.json` | 博客内容数据 |

### 2.2 API数据结构详解

#### `/api/crypto-prices` 响应结构

```json
{
  "prices": {
    "BTC": {
      "symbol": "BTC",
      "price": 114349.5,
      "timestamp": 1761644483976
    },
    "ETH": { "symbol": "ETH", "price": 4108.85, "timestamp": 1761644483976 },
    "SOL": { "symbol": "SOL", "price": 201.715, "timestamp": 1761644483976 },
    "BNB": { "symbol": "BNB", "price": 1133.05, "timestamp": 1761644483976 },
    "DOGE": { "symbol": "DOGE", "price": 0.199805, "timestamp": 1761644483976 },
    "XRP": { "symbol": "XRP", "price": 2.65285, "timestamp": 1761644483976 }
  },
  "serverTime": 1761644483976
}
```

**数据字段说明:**
- `symbol`: 加密货币代码
- `price`: 当前价格（美元）
- `timestamp`: Unix时间戳（毫秒）
- `serverTime`: 服务器时间

#### `/api/trades` 响应结构（部分）

```json
{
  "trades": [
    {
      "id": "gpt-5_406a069e-67d4-4375-b134-3cfdc2f29638",
      "model_id": "gpt-5",
      "symbol": "SOL",
      "side": "long",
      "trade_type": "long",
      "quantity": 60.39,
      "leverage": 1,
      "entry_price": 198.7,
      "exit_price": 202.76,
      "entry_time": 1761601311.276,
      "exit_time": 1761635846.821,
      "entry_human_time": "2025-10-27 21:41:51.276000",
      "exit_human_time": "2025-10-28 07:17:26.821000",
      "realized_gross_pnl": 245.1834,
      "realized_net_pnl": 235.485734,
      "total_commission_dollars": 9.697666,
      "entry_commission_dollars": 4.799796,
      "exit_commission_dollars": 4.89787,
      "confidence": 0,
      "entry_crossed": true,
      "exit_crossed": true,
      "entry_liquidation": null,
      "exit_liquidation": null,
      "exit_plan": {}
    }
  ]
}
```

**交易记录字段说明:**
- `id`: 唯一交易ID
- `model_id`: 模型标识符
- `symbol`: 交易品种
- `side`: 方向（long/short）
- `quantity`: 交易数量
- `leverage`: 杠杆倍数
- `entry_price` / `exit_price`: 入场/出场价格
- `realized_net_pnl`: 实现净损益
- `total_commission_dollars`: 总手续费
- `confidence`: AI置信度
- `exit_plan`: 退出计划（止盈止损策略）

#### `/api/account-totals` 响应结构（简化）

```json
{
  "accountTotals": [
    {
      "id": "gpt-5_0",
      "model_id": "gpt-5",
      "timestamp": 1760741958.847073,
      "realized_pnl": -32.90960200000001,
      "total_unrealized_pnl": 337.88502,
      "dollar_equity": 10304.975418,
      "sharpe_ratio": 0.077,
      "cum_pnl_pct": 3.05,
      "since_inception_minute_marker": 59,
      "since_inception_hourly_marker": 0,
      "positions": {
        "XRP": {
          "symbol": "XRP",
          "oid": 204600432746,
          "entry_price": 2.339594,
          "current_price": 2.31705,
          "quantity": -7716,
          "leverage": 12,
          "margin": 1670.575901,
          "unrealized_pnl": 174.3401,
          "closed_pnl": -8.12,
          "commission": 16.243539000000002,
          "liquidation_price": 2.4717151438,
          "confidence": 0.64,
          "risk_usd": 600,
          "entry_time": 1760738675.497112,
          "exit_plan": {
            "profit_target": 2.19783,
            "stop_loss": 2.41611,
            "invalidation_condition": "Close if a 4h candle closes > 2.455 (20EMA + 1xATR14) AND the 4h MACD histogram turns >= 0."
          }
        }
      }
    }
  ]
}
```

**账户总览字段说明:**
- `dollar_equity`: 账户总权益（美元）
- `realized_pnl`: 已实现损益
- `total_unrealized_pnl`: 未实现损益总计
- `sharpe_ratio`: 夏普比率
- `cum_pnl_pct`: 累计损益百分比
- `positions`: 当前持仓详情
  - `quantity`: 持仓数量（负数表示空头）
  - `leverage`: 杠杆倍数
  - `unrealized_pnl`: 未实现损益
  - `liquidation_price`: 强平价格
  - `exit_plan`: 退出计划
    - `profit_target`: 目标止盈价
    - `stop_loss`: 止损价
    - `invalidation_condition`: 策略失效条件

#### `/api/analytics/[model_id]` 响应结构（简化）

```json
{
  "analytics": [
    {
      "id": "deepseek-chat-v3.1",
      "model_id": "deepseek-chat-v3.1",
      "updated_at": 1761644671.990744,
      "fee_pnl_moves_breakdown_table": {
        "overall_pnl_with_fees": 10049.005192,
        "overall_pnl_without_fees": 10338.7373,
        "total_fees_paid": 306.10908100000006,
        "avg_net_pnl": 591.1179524705883,
        "biggest_net_gain": 7378.132678,
        "biggest_net_loss": -749.171398
      },
      "winners_losers_breakdown_table": {
        "win_rate": 41.17647058823529,
        "avg_winners_net_pnl": 1823.341936,
        "avg_losers_net_pnl": -271.438836,
        "avg_winners_holding_period": 4346.006569048336,
        "avg_losers_holding_period": 1977.0885849996407
      },
      "signals_breakdown_table": {
        "num_long_signals": 22,
        "num_short_signals": 1,
        "num_close_signals": 11,
        "num_hold_signals": 31440,
        "avg_confidence": 0.6955359979668087,
        "avg_leverage": 1,
        "long_short_ratio": 22
      },
      "overall_trades_overview_table": {
        "total_trades": 17,
        "avg_holding_period_mins": 2952.525401960868,
        "avg_size_of_trade_notional": 21739.720360000003,
        "avg_convo_leverage": 12.608695652173912
      },
      "last_trade_exit_time": 1761531867.177,
      "last_convo_timestamp": 1761644669.082119
    }
  ]
}
```

**分析数据说明:**
- `fee_pnl_moves_breakdown_table`: 费用和损益明细
- `winners_losers_breakdown_table`: 盈亏交易统计
- `signals_breakdown_table`: 信号统计（做多/做空/持有/平仓）
- `overall_trades_overview_table`: 交易总览

#### `/api/leaderboard` 响应结构

```json
{
  "leaderboard": [
    {
      "id": "qwen3-max",
      "equity": 21193.78,
      "return_pct": 111.94,
      "num_trades": 1,
      "num_wins": 1,
      "num_losses": 0,
      "win_dollars": 1013.71,
      "lose_dollars": 0,
      "sharpe": 0
    }
  ]
}
```

**排行榜字段:**
- `equity`: 当前权益
- `return_pct`: 回报率百分比
- `num_trades`: 交易次数
- `win_dollars` / `lose_dollars`: 盈利/亏损金额

### 2.3 网络请求行为模式

#### 初始加载序列
1. HTML文档加载
2. CSS、JavaScript资源并行加载
3. 字体资源加载（Google Fonts - IBM Plex Mono）
4. Logo和币种图标加载
5. 核心数据API并行请求：
   - `/api/crypto-prices`
   - `/api/trades`
   - `/api/account-totals`
   - `/api/since-inception-values`

#### 实时更新模式
- **价格更新**: `/api/crypto-prices` 每5-10秒轮询一次
- **账户数据**: `/api/account-totals?lastHourlyMarker=251` 定期检查更新
- **交易记录**: `/api/trades` 周期性刷新
- **无WebSocket**: 未发现WebSocket或Server-Sent Events连接

#### 缓存策略
- 所有API响应头包含: `cache-control: public, max-age=0, must-revalidate`
- Vercel CDN缓存: 通过 `x-vercel-cache: HIT/STALE` 标识
- 静态资源（JS/CSS）: 长期缓存，通过构建ID版本化

---

## 3. 页面组件和功能模块

### 3.1 主页面 (https://nof1.ai/)

#### 顶部导航栏
**组件**: Navigation Header
- **LIVE** - 实时图表页面（当前页）
- **LEADERBOARD** - 排行榜页面
- **BLOG** - 博客页面
- **MODELS** - 模型下拉菜单
- **JOIN THE PLATFORM WAITLIST** - 加入候补名单
- **ABOUT NOF1** - 关于NOF1（跳转到 thenof1.com）

#### 实时价格滚动条
**组件**: Crypto Price Ticker
- 显示6种加密货币实时价格
- 数据源: `/api/crypto-prices`
- 更新频率: 5-10秒
- 展示币种: BTC, ETH, SOL, BNB, DOGE, XRP
- 每个币显示: 图标 + 名称 + 价格

#### 表现摘要栏
**组件**: Performance Summary Bar
- **HIGHEST**: 表现最佳模型及其收益
  - 示例: "DEEPSEEK CHAT V3.1 $21,764.89 +117.65%"
- **LOWEST**: 表现最差模型及其损失
  - 示例: "GPT 5 $3,864.90 -61.35%"

#### 主图表区域
**组件**: Total Account Value Chart
- **标题**: TOTAL ACCOUNT VALUE
- **时间范围切换**: ALL / 72H
- **显示模式切换**: $ (美元) / % (百分比)
- **图表类型**: 多线图（每个模型一条线）
- **图表库**: 可能使用 Recharts 或类似库
- **数据源**: `/api/account-totals` + `/api/since-inception-values`
- **特性**:
  - X轴: 时间轴
  - Y轴: 账户价值（美元）
  - 图例: 各模型对应的颜色标识
  - 悬停tooltip: 显示特定时间点的价值

#### 模型卡片列表
**组件**: Model Performance Cards
位于页面底部，展示每个模型的摘要信息：
- 模型图标和名称
- 当前账户价值
- 点击跳转到模型详情页

**示例模型卡片**:
```
┌──────────────────────┐
│ GPT 5                │
│ $3,855.68           │
└──────────────────────┘
```

#### 标签页面板
**组件**: Tabbed Content Panel
位于右侧区域，包含4个标签：

1. **COMPLETED TRADES**
   - 显示最近100笔完成的交易
   - 可按模型筛选（下拉菜单：ALL MODELS）
   - 每笔交易显示:
     - 模型名称和图标
     - 交易方向（long/short）
     - 币种
     - 入场/出场价格
     - 数量
     - 持有时间
     - 名义价值
     - 净损益（彩色标识盈亏）

2. **MODELCHAT**
   - 功能: 查看AI模型的思考过程和决策理由
   - 状态: 当前实现需要进一步交互才能查看内容
   - 预期展示: AI的推理对话和决策日志

3. **POSITIONS**
   - 显示当前所有活跃持仓
   - 按模型分组
   - 每个持仓显示:
     - 币种和方向
     - 入场价格/当前价格
     - 数量和杠杆
     - 未实现损益
     - 清算价格
     - 保证金使用

4. **README.TXT**
   - 项目说明文档
   - 内容:
     - "A Better Benchmark" - 项目理念
     - "The Contestants" - 参赛模型列表
     - "Competition Rules" - 比赛规则
       - 起始资金
       - 交易市场
       - 目标
       - 透明度
       - 自主性
       - 持续时间

### 3.2 模型详情页 (https://nof1.ai/models/[model_id])

#### 示例: DeepSeek Chat V3.1 详情页

**页面布局**:

##### 顶部导航
- **← [LIVE CHART]** - 返回主页面
- **📊 [LEADERBOARD]** - 查看排行榜

##### 模型信息卡
```
┌───────────────────────────────────┐
│ 🐋 DEEPSEEK CHAT V3.1             │
│ Total Account Value: $21,729.70   │
│ Available Cash: $13,654.10        │
│ [LINK TO WALLET] 🔗               │
└───────────────────────────────────┘
```

##### 损益摘要
```
┌─────────────────────────────────────────────────────┐
│ Total P&L:        Total Fees:      Net Realized:    │
│ $11,729.70        $306.11          $10,049.01       │
└─────────────────────────────────────────────────────┘
```

##### 统计指标
**左侧面板**:
- Average Leverage: 12.6
- Average Confidence: 69.6%
- Biggest Win: $7,378
- Biggest Loss: -$749.17

**右侧面板** - HOLD TIMES:
- Long: 96.5%
- Short: 2.5%
- Flat: 1.4%

##### 活跃持仓区域 (ACTIVE POSITIONS)
显示当前所有持仓，每个持仓卡片包含:

```
┌──────────────────────────────────────┐
│ ❌ XRP                               │
│ Entry Time: 23:25:48                 │
│ Entry Price: $2.44                   │
│ Side: long                           │
│ Quantity: 3609                       │
│ Leverage: 10X                        │
│ Liquidation Price: $2.26             │
│ Margin: $1,643                       │
│ Unrealized P&L: $774.31              │
│                                      │
│ Exit Plan:                           │
│ Profit Target: $2.82                 │
│ Stop Loss: $2.33                     │
│ Invalidation: If the price closes    │
│ below 2.30 on a 3-minute candle     │
│                                      │
│ [VIEW]                               │
└──────────────────────────────────────┘
```

**Exit Plan 弹出框示例**:
点击 [VIEW] 按钮后显示完整退出计划：
- Profit Target（止盈目标）
- Stop Loss（止损价格）
- Invalidation Condition（策略失效条件）
  - 详细的技术指标条件
  - K线周期判断
  - 技术指标组合（如：20EMA、ATR、MACD等）

##### 最近25笔交易表格 (LAST 25 TRADES)

表格列:
| SIDE | COIN | ENTRY PRICE | EXIT PRICE | QUANTITY | HOLDING TIME | NOTIONAL ENTRY | NOTIONAL EXIT | TOTAL FEES | NET P&L |
|------|------|-------------|------------|----------|--------------|----------------|---------------|------------|---------|
| LONG | ETH  | $3,929.6    | $4,216     | 26.05    | 68H 32M      | $102,366       | $109,827      | $84.88     | $7,378  |

### 3.3 排行榜页面 (https://nof1.ai/leaderboard)

**功能**: 展示所有模型的实时排名和关键指标

**数据源**: `/api/leaderboard`

**可能包含的指标**:
- 当前排名
- 模型名称
- 账户权益
- 回报率 (%)
- 总交易次数
- 胜率
- 夏普比率
- 最大回撤

### 3.4 博客页面 (https://nof1.ai/blog)

**功能**: 发布项目更新、分析文章和技术博客

**数据源**: `/_next/data/YEkf9XbCOC_cNu0U0LooY/blog.json`

---

## 4. 交互行为模式和用户流程

### 4.1 用户交互流程

#### 主要用户路径

**路径1: 观察实时表现**
```
访问主页 → 查看总账户价值图表 → 观察各模型表现 → 查看实时价格
```

**路径2: 深入研究特定模型**
```
主页 → 点击模型卡片 → 查看模型详情页 →
  → 分析持仓 → 查看Exit Plan → 研究历史交易
```

**路径3: 比较模型表现**
```
主页 → 点击LEADERBOARD → 查看排行榜 → 比较各项指标
```

**路径4: 了解交易细节**
```
主页 → COMPLETED TRADES标签 → 筛选特定模型 →
  → 查看交易详情（价格、时间、损益）
```

### 4.2 按钮和交互元素

#### 主要按钮类型

1. **导航按钮**
   - CSS类: `terminal-header`
   - 样式: 文本链接，悬停时改变颜色
   - 示例: LIVE, LEADERBOARD, BLOG, MODELS

2. **标签切换按钮**
   - CSS类: `terminal-text`
   - 状态: active（黑底白字）/ inactive（白底黑字）
   - 示例: COMPLETED TRADES, MODELCHAT, POSITIONS, README.TXT

3. **小型控制按钮**
   - CSS类: `terminal-button-small`
   - 用途: 时间范围、显示模式切换
   - 示例: ALL/72H, $/%

4. **查看详情按钮**
   - 文本: "VIEW"
   - 功能: 展开Exit Plan详情
   - 交互: 点击后显示模态框或展开区域

5. **下拉菜单**
   - CSS类: `terminal-text hover:border-terminal-green`
   - 示例: "ALL MODELS ▼"
   - 功能: 筛选特定模型的交易

6. **关闭按钮**
   - 符号: "✕"
   - CSS类: 红色背景半透明
   - 功能: 关闭弹出框或提示

#### 交互反馈

- **悬停效果**: 按钮悬停时改变颜色
- **激活状态**: active按钮有不同的背景色
- **加载状态**: 数据加载时可能显示骨架屏或加载动画
- **实时更新**: 价格和账户数值自动更新，无需刷新页面

### 4.3 前端技术栈

基于网络请求和代码特征分析：

- **框架**: Next.js (React)
- **构建ID**: YEkf9XbCOC_cNu0U0LooY
- **部署平台**: Vercel
- **字体**: IBM Plex Mono (Google Fonts)
- **图表库**: 可能是Recharts或类似React图表库
- **样式**: Tailwind CSS (基于CSS类命名模式)
- **监控**: Vercel Analytics

---

## 5. AI交易策略和提示词模式

### 5.1 Exit Plan（退出计划）结构

基于DeepSeek Chat V3.1的实际持仓，Exit Plan包含以下要素：

#### XRP持仓的Exit Plan示例

```json
{
  "profit_target": 2.19783,
  "stop_loss": 2.41611,
  "invalidation_condition": "Close if a 4h candle closes > 2.455 (20EMA + 1xATR14) AND the 4h MACD histogram turns >= 0."
}
```

**解读**:
- **Profit Target（止盈）**: $2.19783 - AI设定的目标出场价
- **Stop Loss（止损）**: $2.41611 - 风险控制的最大损失价格
- **Invalidation Condition（失效条件）**:
  - 技术条件: 4小时K线收盘价 > 2.455（20日EMA + 1倍ATR14）
  - 且MACD柱状图 >= 0
  - 满足条件时平仓退出

#### Exit Plan的技术特征

1. **技术指标组合**:
   - EMA (指数移动平均线)
   - ATR (平均真实波幅)
   - MACD (移动平均收敛发散指标)

2. **K线周期**:
   - 常见: 3分钟、4小时
   - 用于不同时间框架的判断

3. **条件逻辑**:
   - AND条件: 多个条件必须同时满足
   - 价格阈值 + 技术指标状态

### 5.2 AI决策参数

从API数据中提取的关键决策参数：

| 参数 | 说明 | 示例值 |
|------|------|--------|
| `confidence` | AI对该笔交易的置信度 | 0.64 (64%) |
| `risk_usd` | 该笔交易的风险金额 | $600 |
| `leverage` | 使用的杠杆倍数 | 10X, 12X |
| `entry_time` | 入场时间戳 | 1760738675.497112 |

### 5.3 信号类型统计（DeepSeek Chat V3.1 案例）

基于 `signals_breakdown_table` 数据：

```json
{
  "num_long_signals": 22,
  "num_short_signals": 1,
  "num_close_signals": 11,
  "num_hold_signals": 31440,
  "avg_confidence": 0.6955359979668087,
  "avg_leverage": 1,
  "long_short_ratio": 22
}
```

**分析**:
- **交易倾向**: 绝大多数做多 (long_short_ratio: 22:1)
- **持有为主**: 99.89%的信号为"持有"
- **平均置信度**: 69.6%
- **保守策略**: 平均杠杆仅1倍（实际交易时会提高）

### 5.4 推测的AI提示词结构

虽然无法直接访问提示词，但根据Exit Plan和交易行为，推测提示词可能包含：

**可能的提示词模板**:

```
你是一个专业的加密货币交易员，管理着$10,000的账户。

当前市场数据:
- BTC价格: $107,000
- ETH价格: $3,850
- SOL价格: $184
- [其他币种数据...]

技术指标:
- [各币种的EMA、MACD、ATR等指标]

你的任务:
1. 分析当前市场状况
2. 决定是否开新仓位、平仓或持有
3. 如果开仓，需要指定:
   - 交易品种
   - 方向（long/short）
   - 仓位大小
   - 杠杆倍数
   - 置信度（0-1）
   - 风险金额
   - Exit Plan:
     * Profit Target
     * Stop Loss
     * Invalidation Condition（使用技术指标条件）

请以JSON格式返回你的决策。
```

**输出格式推测**:

```json
{
  "action": "open_position",
  "symbol": "XRP",
  "side": "long",
  "quantity": 7716,
  "leverage": 12,
  "confidence": 0.64,
  "risk_usd": 600,
  "exit_plan": {
    "profit_target": 2.19783,
    "stop_loss": 2.41611,
    "invalidation_condition": "Close if a 4h candle closes > 2.455 (20EMA + 1xATR14) AND the 4h MACD histogram turns >= 0."
  },
  "reasoning": "XRP在4小时图上显示看跌趋势..."
}
```

### 5.5 风险管理模式

从数据中观察到的风险管理特征：

1. **单笔风险限制**:
   - 通常在$300-$650之间
   - 占总资金3-6.5%

2. **杠杆使用**:
   - 范围: 1X - 20X
   - 平均: 10-12X
   - 根据置信度和波动性调整

3. **保证金管理**:
   - 每个持仓显示独立的保证金要求
   - 清算价格明确标识

4. **组合多样化**:
   - 同时持有多个币种
   - 主要币种: BTC, ETH, SOL, XRP, BNB, DOGE

---

## 6. 技术实现细节

### 6.1 前端架构

#### Next.js应用结构

**路由**:
- `/` - 主页（实时图表）
- `/leaderboard` - 排行榜
- `/blog` - 博客
- `/models/[id]` - 模型详情页（动态路由）
- `/waitlist` - 候补名单

**静态资源路径**:
- `/_next/static/chunks/` - JavaScript代码块
- `/_next/static/css/` - CSS样式表
- `/logos/` - 模型和项目Logo
- `/coins/` - 币种图标（SVG格式）
- `/logos_white/` - 白色版本Logo

#### 关键JavaScript文件

| 文件 | 作用 |
|------|------|
| `webpack-a339f4a57035852b.js` | Webpack运行时 |
| `framework-a6e0b7e30f98059a.js` | React框架代码 |
| `main-9ac460727c653804.js` | Next.js主入口 |
| `pages/_app-a5ae0a367d6e6067.js` | 应用根组件 |
| `pages/index-90c6605b45c2fbc0.js` | 主页代码 |
| `pages/models/[id]-fdc67f6b2fab2453.js` | 模型详情页代码 |

### 6.2 实时数据更新机制

#### 轮询策略

**实现方式**: HTTP轮询（无WebSocket）

**轮询间隔**:
- `/api/crypto-prices`: ~5-10秒
- `/api/account-totals`: ~10-15秒
- `/api/trades`: ~15-30秒

**客户端逻辑**:
```javascript
// 伪代码示例
setInterval(async () => {
  const prices = await fetch('/api/crypto-prices');
  updatePriceDisplay(prices);
}, 5000);

setInterval(async () => {
  const accountData = await fetch('/api/account-totals?lastHourlyMarker=' + lastMarker);
  if (accountData.hasUpdate) {
    updateChart(accountData);
    lastMarker = accountData.newMarker;
  }
}, 10000);
```

#### 增量更新优化

通过 `lastHourlyMarker` 参数实现增量更新：
- 客户端记录最后一次更新的标记
- 服务器只返回新增数据
- 减少数据传输量

### 6.3 性能优化策略

1. **CDN缓存**: 通过Vercel Edge Network分发
2. **代码分割**: Next.js自动按路由分割代码
3. **图片优化**: Next.js Image组件优化图片加载
4. **字体优化**: 使用Google Fonts CDN + font-display: swap
5. **API缓存**: 公开缓存策略，减少服务器负载

### 6.4 样式系统

**Tailwind CSS类命名模式示例**:
```css
terminal-header
terminal-button-small
mobile-button-gradient-blue
border-terminal-green
text-foreground
hover:text-accent-primary
```

**设计风格**:
- Terminal/命令行风格
- 黑白为主色调
- 鲜艳颜色用于强调（绿色盈利、红色亏损）
- 等宽字体（IBM Plex Mono）
- 复古电脑终端美学

---

## 7. 数据流程图

### 7.1 页面加载流程

```
用户访问nof1.ai
    ↓
加载HTML + CSS + JS
    ↓
并行请求核心API:
    ├─ /api/crypto-prices → 实时价格
    ├─ /api/trades → 交易历史
    ├─ /api/account-totals → 账户数据
    └─ /api/since-inception-values → 基准数据
    ↓
渲染初始页面
    ↓
启动轮询定时器:
    ├─ 每5秒更新价格
    ├─ 每10秒更新账户
    └─ 每30秒更新交易
```

### 7.2 用户交互流程

```
用户点击模型卡片
    ↓
导航到 /models/[id]
    ↓
请求模型特定API:
    ├─ /api/analytics/[id] → 详细分析
    ├─ /api/leaderboard → 排名对比
    ├─ /api/account-totals → 当前持仓
    └─ /api/trades → 历史交易
    ↓
渲染模型详情页
    ↓
用户点击"VIEW"按钮
    ↓
展开Exit Plan详情
```

---

## 8. 关键发现和洞察

### 8.1 技术架构洞察

1. **无实时通信**: 使用HTTP轮询而非WebSocket
   - 优点: 实现简单，兼容性好
   - 缺点: 延迟稍高，服务器负载较大

2. **完全公开数据**: 所有API无需认证即可访问
   - 体现了"透明度"的核心理念
   - 便于第三方开发者构建工具

3. **Vercel优化**: 充分利用Vercel平台特性
   - Edge缓存
   - 自动优化
   - 分析工具

### 8.2 AI交易策略洞察

1. **趋势跟随为主**: 大多数模型采用做多策略（96.5%）
2. **技术指标驱动**: Exit Plan大量使用EMA、MACD、ATR等经典指标
3. **保守风险管理**:
   - 单笔风险控制在3-6%
   - 平均杠杆不高（10-12X）
   - 清晰的止损机制

4. **持有时间**:
   - 平均持仓时间: ~49小时（2952分钟）
   - 盈利交易平均持有更久（72小时）
   - 亏损交易平均持有更短（33小时）

### 8.3 用户体验设计洞察

1. **极简主义**: 界面简洁，信息密度高
2. **信息层次**:
   - 一级: 总览（主页图表）
   - 二级: 分类（标签页面板）
   - 三级: 详情（模型页面）
   - 四级: 深度（Exit Plan弹窗）

3. **实时感**: 虽然是轮询，但通过流畅的动画营造实时感
4. **可操作性有限**: 作为观察平台，用户只能查看不能交互交易

### 8.4 商业模式推测

1. **主要目标**:
   - 展示AI交易能力
   - 吸引AI开发者和投资者关注
   - 构建AI金融工具品牌

2. **潜在收入来源**:
   - API访问费用（未来）
   - AI交易策略订阅
   - 交易信号服务
   - 机构合作

3. **候补名单**: "JOIN THE PLATFORM WAITLIST"
   - 暗示未来会推出可交易平台
   - 用户可能能用自己的资金+AI策略交易

---

## 9. API使用示例（供开发参考）

### 9.1 获取实时价格

```javascript
// 获取所有币种实时价格
const response = await fetch('https://nof1.ai/api/crypto-prices');
const data = await response.json();

console.log(data.prices.BTC.price); // 114349.5
console.log(data.serverTime); // 1761644483976
```

### 9.2 获取排行榜

```javascript
const response = await fetch('https://nof1.ai/api/leaderboard');
const data = await response.json();

// 按权益排序
const sorted = data.leaderboard.sort((a, b) => b.equity - a.equity);
console.log('Top performer:', sorted[0].id, sorted[0].return_pct + '%');
```

### 9.3 获取模型详细分析

```javascript
const modelId = 'deepseek-chat-v3.1';
const response = await fetch(`https://nof1.ai/api/analytics/${modelId}`);
const data = await response.json();

const analytics = data.analytics[0];
console.log('Win rate:', analytics.winners_losers_breakdown_table.win_rate + '%');
console.log('Total trades:', analytics.overall_trades_overview_table.total_trades);
```

### 9.4 获取交易历史

```javascript
const response = await fetch('https://nof1.ai/api/trades');
const data = await response.json();

// 筛选特定模型的交易
const gpt5Trades = data.trades.filter(t => t.model_id === 'gpt-5');

// 计算总盈亏
const totalPnL = gpt5Trades.reduce((sum, t) => sum + t.realized_net_pnl, 0);
console.log('GPT-5 Total P&L:', totalPnL);
```

---

## 10. 文件结构建议（供AI编程使用）

为了方便后续AI编程时读取需求，建议将分析文档组织为以下结构：

```
nof1-ai-analysis/
├── README.md                     # 本文档
├── api-specifications/           # API详细规范
│   ├── crypto-prices.md
│   ├── trades.md
│   ├── account-totals.md
│   ├── analytics.md
│   └── leaderboard.md
├── ui-components/                # UI组件规范
│   ├── navigation.md
│   ├── chart-area.md
│   ├── model-cards.md
│   └── tabbed-panel.md
├── data-structures/              # 数据结构定义
│   ├── trade-object.schema.json
│   ├── position-object.schema.json
│   └── analytics-object.schema.json
├── user-flows/                   # 用户流程图
│   ├── main-interaction.mermaid
│   └── model-detail.mermaid
├── ai-strategy/                  # AI策略分析
│   ├── exit-plan-examples.md
│   ├── risk-management.md
│   └── prompt-engineering.md
└── screenshots/                  # 页面截图
    ├── homepage.png
    ├── model-detail.png
    └── exit-plan-popup.png
```

---

## 11. 总结

### 11.1 核心功能总结

nof1.ai是一个创新的AI交易能力测试平台，通过以下方式实现其目标：

1. **真实市场测试**: 使用真实资金在真实市场交易
2. **公平对比**: 所有AI模型接收相同的数据和提示词
3. **完全透明**: 所有交易、决策和结果公开展示
4. **实时监控**: 用户可实时观察AI的交易表现
5. **深度分析**: 提供详细的统计数据和分析指标

### 11.2 技术栈总结

- **前端**: Next.js + React + Tailwind CSS
- **部署**: Vercel Edge Network
- **数据更新**: HTTP轮询（5-10秒间隔）
- **图表**: React图表库（可能是Recharts）
- **字体**: IBM Plex Mono（等宽字体）
- **风格**: Terminal/命令行美学

### 11.3 API端点总结

| API | 用途 | 更新频率 |
|-----|------|---------|
| `/api/crypto-prices` | 实时价格 | 5-10秒 |
| `/api/trades` | 交易历史 | 15-30秒 |
| `/api/account-totals` | 账户和持仓 | 10-15秒 |
| `/api/since-inception-values` | 基准数据 | 低频 |
| `/api/leaderboard` | 排行榜 | 按需 |
| `/api/analytics/[id]` | 模型分析 | 按需 |

### 11.4 数据特征总结

**实时性**:
- 价格数据: 实时（5-10秒延迟）
- 交易数据: 近实时（30秒内）
- 持仓数据: 近实时（15秒内）

**完整性**:
- 包含入场/出场的完整交易信息
- 详细的费用明细
- 清晰的风险管理参数（止盈、止损、清算价）

**可访问性**:
- 所有API公开，无需认证
- 数据格式规范（JSON）
- 适合第三方开发

---

## 12. 附录

### 12.1 术语表

| 术语 | 解释 |
|------|------|
| **Perpetual Contract** | 永续合约，无到期日的期货合约 |
| **PnL** | Profit and Loss，损益 |
| **Realized PnL** | 已实现损益，已平仓交易的盈亏 |
| **Unrealized PnL** | 未实现损益，持仓的浮动盈亏 |
| **Leverage** | 杠杆，放大交易规模的倍数 |
| **Margin** | 保证金，开仓所需的资金 |
| **Liquidation Price** | 清算价格，触及此价格将被强制平仓 |
| **Long** | 做多，买入看涨 |
| **Short** | 做空，卖出看跌 |
| **Exit Plan** | 退出计划，包含止盈止损策略 |
| **Sharpe Ratio** | 夏普比率，衡量风险调整后收益的指标 |
| **EMA** | Exponential Moving Average，指数移动平均线 |
| **MACD** | Moving Average Convergence Divergence，移动平均收敛发散指标 |
| **ATR** | Average True Range，平均真实波幅 |

### 12.2 相关链接

- 主网站: https://nof1.ai/
- 关于页面: https://thenof1.com/
- 交易平台: Hyperliquid

### 12.3 分析局限性

本文档基于2025年10月28日的单次访问分析，存在以下局限：

1. **对话内容未获取**: MODELCHAT功能需要进一步交互才能访问
2. **提示词未公开**: AI的输入提示词不在公开API中
3. **历史数据有限**: 仅获取了最近的交易和持仓数据
4. **动态变化**: 平台可能随时更新功能和数据结构

### 12.4 建议后续分析

1. **长期监控**: 持续跟踪各模型的表现变化
2. **策略反向工程**: 基于交易记录推测AI的决策逻辑
3. **性能对比**: 与传统量化策略对比
4. **市场条件影响**: 分析不同市场环境下AI的表现
5. **对话日志分析**: 如果能访问MODELCHAT，深入分析AI的推理过程

---

**文档版本**: 1.0
**最后更新**: 2025-10-28
**分析者**: Claude (Sonnet 4.5)
**数据来源**: nof1.ai 官方API

---

## 许可和使用说明

本文档供学习和研究目的使用。数据和信息来源于nof1.ai公开API。如需商业使用，请联系nof1.ai官方。
