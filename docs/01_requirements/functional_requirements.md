# 功能需求规格

AI交易系统的详细功能需求

---

## 1. 系统概述

### 1.1 系统目标
实现基于LLM的自动加密货币交易系统，在HyperLiquid交易所上交易6个币种（BTC, ETH, SOL, BNB, DOGE, XRP），每3分钟由AI做出交易决策并自动执行。

### 1.2 核心功能
- 实时市场数据采集和技术指标计算
- 基于DeepSeek/Qwen的AI决策生成
- 自动化交易执行（开仓、平仓、止损止盈）
- 严格的风险管理
- CLI管理工具和日志监控

### 1.3 非功能需求
- **可用性**: 7x24小时运行，年可用性 > 99%
- **性能**: 交易循环延迟 < 30秒，AI决策 < 10秒
- **安全性**: API密钥加密存储，严格的风险控制
- **可维护性**: 模块化设计，完整的日志和监控

---

## 2. 功能需求详述

### 2.1 市场数据采集模块

#### 2.1.1 实时价格数据
**需求ID**: FR-101
**优先级**: Must Have

**功能描述**:
- 获取6个币种的实时价格（BTC, ETH, SOL, BNB, DOGE, XRP）
- 支持REST API轮询和WebSocket订阅两种模式
- 数据更新频率: ≤ 5秒

**输入**:
- 币种列表: `["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"]`

**输出**:
```json
{
  "BTC": {
    "price": 95420.50,
    "timestamp": "2025-11-02T12:34:56Z",
    "volume_24h": 1234567890
  },
  ...
}
```

**验收标准**:
- [ ] 能够成功获取所有6个币种的价格
- [ ] 数据延迟 < 5秒
- [ ] API错误时自动重试（最多3次）

---

#### 2.1.2 K线数据采集
**需求ID**: FR-102
**优先级**: Must Have

**功能描述**:
- 获取3分钟和4小时K线数据
- 每个币种至少获取最近100根K线（用于指标计算）

**输入**:
- 币种: `"BTC"`
- 时间周期: `"3m"` 或 `"4h"`
- K线数量: `100`

**输出**:
```python
DataFrame with columns: [timestamp, open, high, low, close, volume]
```

**验收标准**:
- [ ] 支持3分钟和4小时两种时间周期
- [ ] 返回标准OHLCV格式
- [ ] 数据完整性检查（无缺失K线）

---

#### 2.1.3 技术指标计算
**需求ID**: FR-103
**优先级**: Must Have

**功能描述**:
计算以下技术指标（参考NoF1.ai）:
- EMA 20 / EMA 50
- MACD (12, 26, 9)
- RSI 7 / RSI 14
- ATR 3 / ATR 14

**输入**:
- K线数据 (DataFrame)

**输出**:
```python
{
  "ema_20": 95123.45,
  "ema_50": 94567.89,
  "macd": {"macd": 123.45, "signal": 110.23, "histogram": 13.22},
  "rsi_7": 65.34,
  "rsi_14": 58.21,
  "atr_3": 234.56,
  "atr_14": 456.78
}
```

**验收标准**:
- [ ] 所有指标计算准确（与TradingView对比误差 < 0.1%）
- [ ] 使用 `pandas-ta` 库实现
- [ ] 计算时间 < 1秒

---

#### 2.1.4 开放利息和资金费率
**需求ID**: FR-104
**优先级**: Should Have

**功能描述**:
- 获取每个币种的开放利息（Open Interest）
- 获取资金费率（Funding Rate）

**输出**:
```json
{
  "BTC": {
    "open_interest": 1234567890,
    "funding_rate": 0.0001
  }
}
```

---

### 2.2 AI决策生成模块

#### 2.2.1 LLM Provider集成
**需求ID**: FR-201
**优先级**: Must Have

**功能描述**:
- 支持多个trading agents并行运行，每个agent使用独立的LLM模型
- 每个agent = 1个LLM模型 + 1个独立HyperLiquid账户
- Agent配置存储在PostgreSQL数据库
- 支持动态添加/删除agents（通过CLI或API）
- 多个LLM模型可选: DeepSeek Chat, Qwen Plus, Claude等
- 每个模型可通过不同服务提供商访问: Official API, OpenRouter等

**配置示例** (Model Pool):
```yaml
llm:
  # 定义可用模型池（哪些models运行由数据库控制）
  models:
    deepseek-chat:
      # 使用哪个服务提供商: official, openrouter
      provider: official

      official:
        base_url: https://api.deepseek.com/v1
        api_key: ${DEEPSEEK_API_KEY}
        model_name: deepseek-chat
        timeout: 30

      openrouter:
        base_url: https://openrouter.ai/api/v1
        api_key: ${OPENROUTER_API_KEY}
        model_name: deepseek/deepseek-chat
        timeout: 30

    qwen-plus:
      provider: official

      official:
        base_url: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        api_key: ${QWEN_API_KEY}
        model_name: qwen-plus
        timeout: 30

      openrouter:
        base_url: https://openrouter.ai/api/v1
        api_key: ${OPENROUTER_API_KEY}
        model_name: qwen/qwen-2.5-72b-instruct
        timeout: 30

  max_tokens: 4096
  temperature: 0.7

# 数据库配置
database:
  host: localhost
  port: 5432
  database: trading_bot
  user: ${DB_USER}
  password: ${DB_PASSWORD}
```

**Agent管理**:
```bash
# 创建agent（引用config中定义的account）
$ bot agent create \
    --name "DeepSeek Agent 1" \
    --model deepseek-chat \
    --account account_1 \
    --balance 1000.0

# 创建另一个agent使用不同account
$ bot agent create \
    --name "Qwen Agent 1" \
    --model qwen-plus \
    --account account_2 \
    --balance 1000.0

# 列出所有agents
$ bot agent list
ID                                   Name              Model          Account    Status   Balance
abc123...                           DeepSeek Agent 1  deepseek-chat  account_1  active   $10,234.50
def456...                           Qwen Agent 1      qwen-plus      account_2  active   $9,876.30

# 暂停agent
$ bot agent pause abc123

# 查看agent表现
$ bot agent stats abc123
```

**验收标准**:
- [ ] 支持DeepSeek Chat和Qwen Plus（可通过official或OpenRouter）
- [ ] 支持多个agents并行运行（数据库驱动）
- [ ] 每个agent独立决策，互不影响
- [ ] Agent配置存储在PostgreSQL数据库
- [ ] CLI支持完整的agent CRUD操作

---

#### 2.2.2 市场数据格式化
**需求ID**: FR-202
**优先级**: Must Have

**功能描述**:
将市场数据和技术指标格式化为结构化的提示词（约11k字符），参考NoF1.ai的格式。

**提示词结构**:
```markdown
# Market Analysis Request

## Current Time
2025-11-02 12:34:56 UTC

## Portfolio Status
- Account Balance: $10,000
- Current Positions: [...]
- Total PnL: +5.23%

## Market Data (6 coins)

### BTC
- Price: $95,420.50
- 3m Chart: [最近30根K线]
- 4h Chart: [最近24根K线]
- Technical Indicators:
  - EMA 20/50: 95123 / 94567
  - MACD: 123.45 (signal: 110.23)
  - RSI 7/14: 65.34 / 58.21
  - ATR 3/14: 234.56 / 456.78
- Open Interest: 1,234,567,890
- Funding Rate: 0.01%

[... repeat for ETH, SOL, BNB, DOGE, XRP ...]

## Trading Constraints
- Max leverage: 10x
- Max position size: $2,000 per coin
- Stop loss: -15% per position
- Max account drawdown: -30%

## Previous Conversation
[最近3轮对话]

## Task
Based on the above data, provide trading decisions for each coin.
Output format: JSON
```

**验收标准**:
- [ ] 提示词长度 10k-12k 字符
- [ ] 包含所有必要的市场数据和约束条件
- [ ] 保留最近3轮对话上下文

---

#### 2.2.3 AI决策解析
**需求ID**: FR-203
**优先级**: Must Have

**功能描述**:
解析AI返回的JSON格式决策，提取交易指令。

**期望AI输出格式**:
```json
{
  "decisions": [
    {
      "coin": "BTC",
      "action": "OPEN_LONG",
      "position_size_usd": 1000,
      "leverage": 5,
      "entry_price": 95420,
      "stop_loss": 93500,
      "take_profit": 98000,
      "reasoning": "EMA golden cross + RSI oversold + funding rate negative"
    },
    {
      "coin": "ETH",
      "action": "HOLD",
      "reasoning": "Consolidating, wait for breakout"
    },
    {
      "coin": "SOL",
      "action": "CLOSE",
      "reasoning": "Take profit at resistance level"
    }
  ],
  "risk_assessment": "Medium",
  "market_sentiment": "Bullish"
}
```

**支持的action类型**:
- `OPEN_LONG`: 开多仓
- `OPEN_SHORT`: 开空仓
- `CLOSE`: 平仓
- `HOLD`: 保持现状
- `ADJUST_SL`: 调整止损
- `ADJUST_TP`: 调整止盈

**验收标准**:
- [ ] JSON解析成功率 > 95%
- [ ] 解析失败时记录原始输出并告警
- [ ] 验证所有必需字段存在

---

### 2.3 交易执行模块

#### 2.3.1 订单下单
**需求ID**: FR-301
**优先级**: Must Have

**功能描述**:
- 支持市价单（Market Order）和限价单（Limit Order）
- 支持开仓、平仓、调整仓位
- 自动计算杠杆和保证金

**接口设计**:
```python
def place_order(
    coin: str,
    side: Literal["BUY", "SELL"],
    order_type: Literal["MARKET", "LIMIT"],
    size_usd: float,
    leverage: int,
    price: Optional[float] = None,
    reduce_only: bool = False
) -> OrderResult
```

**验收标准**:
- [ ] 订单执行成功率 > 99%
- [ ] 失败时返回明确的错误信息
- [ ] 记录所有订单详情到日志

---

#### 2.3.2 止损止盈设置
**需求ID**: FR-302
**优先级**: Must Have

**功能描述**:
为每个持仓设置止损（Stop Loss）和止盈（Take Profit）。

**接口设计**:
```python
def set_sl_tp(
    coin: str,
    stop_loss_price: float,
    take_profit_price: float
) -> bool
```

**验收标准**:
- [ ] 止损止盈设置成功率 > 99%
- [ ] 支持动态调整SL/TP
- [ ] 止损触发时自动平仓

---

#### 2.3.3 持仓查询
**需求ID**: FR-303
**优先级**: Must Have

**功能描述**:
查询当前所有持仓及其盈亏状态。

**输出**:
```json
{
  "positions": [
    {
      "coin": "BTC",
      "side": "LONG",
      "size": 0.01,
      "entry_price": 95000,
      "current_price": 95420,
      "unrealized_pnl": 4.20,
      "unrealized_pnl_pct": 0.44,
      "leverage": 5,
      "liquidation_price": 91000,
      "stop_loss": 93500,
      "take_profit": 98000
    }
  ],
  "total_unrealized_pnl": 4.20,
  "account_balance": 10004.20
}
```

**验收标准**:
- [ ] 实时更新持仓信息
- [ ] 准确计算未实现盈亏
- [ ] 显示清算价格

---

### 2.4 风险管理模块

#### 2.4.1 预交易风险检查
**需求ID**: FR-401
**优先级**: Must Have

**功能描述**:
在执行交易前验证所有风险规则。

**风险规则**:
1. 单币种最大仓位: $2,000
2. 账户总持仓: < 80% 账户余额
3. 最大杠杆: ≤ 10x
4. 单仓位止损: -15%
5. 账户最大回撤: -30%

**接口设计**:
```python
def validate_trade(
    coin: str,
    size_usd: float,
    leverage: int,
    stop_loss_pct: float
) -> ValidationResult:
    """
    Returns:
        ValidationResult(valid=True/False, reason="...")
    """
```

**验收标准**:
- [ ] 所有风险规则100%执行
- [ ] 违反规则时拒绝交易并记录日志
- [ ] 风险参数可配置

---

#### 2.4.2 运行时风险监控
**需求ID**: FR-402
**优先级**: Must Have

**功能描述**:
实时监控持仓风险，触发风险规则时自动干预。

**监控规则**:
- 单仓位亏损 > 15%: 自动止损
- 账户回撤 > 30%: 停止所有交易，平掉所有仓位
- 清算价格距离 < 5%: 告警

**验收标准**:
- [ ] 每次交易循环检查一次风险
- [ ] 风险触发时自动执行保护措施
- [ ] 发送告警通知（日志/可选Telegram）

---

### 2.5 自动化模块

#### 2.5.1 定时任务调度
**需求ID**: FR-501
**优先级**: Must Have

**功能描述**:
每3分钟执行一次完整的交易循环。

**交易循环步骤**:
1. 采集市场数据和技术指标
2. 查询当前持仓和账户状态
3. 调用LLM生成交易决策
4. 执行风险检查
5. 执行交易决策
6. 更新日志和数据库

**验收标准**:
- [ ] 准时执行（误差 < 5秒）
- [ ] 单次循环总耗时 < 30秒
- [ ] 异常不中断后续循环

---

#### 2.5.2 异常处理和恢复
**需求ID**: FR-502
**优先级**: Must Have

**功能描述**:
优雅地处理各种异常情况，确保系统稳定运行。

**异常场景**:
- API调用失败（网络错误、超时、限流）
- AI决策格式错误
- 订单执行失败
- 数据解析错误

**处理策略**:
- API错误: 重试3次，失败则跳过本次循环
- AI错误: 记录原始输出，告警，跳过交易
- 订单错误: 记录详情，告警，不影响其他币种
- 关键错误: 停止系统，等待人工干预

**验收标准**:
- [ ] 异常不导致系统崩溃
- [ ] 所有异常记录到日志
- [ ] 关键异常触发告警

---

### 2.6 CLI管理工具

#### 2.6.1 基本命令
**需求ID**: FR-601
**优先级**: Should Have

**命令列表**:
```bash
# 启动机器人
$ bot start

# 停止机器人
$ bot stop

# 查看运行状态
$ bot status
Output:
  Status: Running
  Uptime: 2 days 5 hours
  Last cycle: 2025-11-02 12:34:56
  Active agents: 3
  Total trades: 142
  Win rate: 58.45%
  Total PnL: +12.34%

# Agent管理
$ bot agent list                  # 列出所有agents
$ bot agent create [options]      # 创建新agent
$ bot agent pause <agent-id>      # 暂停agent
$ bot agent resume <agent-id>     # 恢复agent
$ bot agent stop <agent-id>       # 停止agent
$ bot agent stats <agent-id>      # 查看agent统计

# 查看当前持仓（所有agents）
$ bot positions
Output:
  Agent: DeepSeek Agent 1
    BTC LONG: +2.34% ($1,000)
  Agent: Qwen Agent 1
    ETH SHORT: -1.23% ($500)

# 查看交易历史
$ bot history --limit 10
$ bot history --agent <agent-id>  # 查看特定agent的历史

# 查看/修改配置
$ bot config get llm.models
$ bot config set risk.max_leverage 8
```

**验收标准**:
- [ ] 所有命令正常工作
- [ ] 输出格式清晰易读
- [ ] 支持 `--help` 查看命令帮助

---

### 2.7 日志和监控

#### 2.7.1 日志系统
**需求ID**: FR-701
**优先级**: Must Have

**日志级别**:
- `DEBUG`: 详细的调试信息
- `INFO`: 正常的业务流程（交易循环开始/结束、订单执行）
- `WARNING`: 非关键错误（API重试、数据缺失）
- `ERROR`: 关键错误（订单失败、风险触发）

**日志格式**:
```
2025-11-02 12:34:56.789 | INFO | trading_bot.main | Starting trading cycle #142
2025-11-02 12:35:01.234 | INFO | trading_bot.ai | AI decision: OPEN_LONG BTC $1000 @95420
2025-11-02 12:35:05.678 | WARNING | trading_bot.exchange | Order partially filled: 80%
2025-11-02 12:35:10.123 | ERROR | trading_bot.risk | Stop loss triggered: BTC -15.2%
```

**日志存储**:
- 文件: `logs/bot_{date}.log`
- 轮转: 每天或每100MB
- 保留: 最近30天

**验收标准**:
- [ ] 所有关键操作都有日志
- [ ] 日志级别正确分类
- [ ] 日志文件自动轮转

---

## 3. 数据模型

### 3.1 配置文件结构

```yaml
# config.yaml

# LLM配置 - 定义可用模型池
llm:
  models:
    deepseek-chat:
      provider: official
      official:
        api_key: ${DEEPSEEK_API_KEY}
        base_url: https://api.deepseek.com/v1
        model_name: deepseek-chat
        timeout: 30
    qwen-plus:
      provider: official
      official:
        api_key: ${QWEN_API_KEY}
        base_url: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        model_name: qwen-plus
        timeout: 30
  max_tokens: 4096
  temperature: 0.7

# 交易所配置
exchange:
  testnet: true  # 测试网模式
  mainnet_url: https://api.hyperliquid.xyz
  testnet_url: https://api.hyperliquid-testnet.xyz

# 数据库配置
database:
  host: localhost
  port: 5432
  database: trading_bot
  user: ${DB_USER}
  password: ${DB_PASSWORD}
  pool_size: 10
  max_overflow: 20

# 交易配置
trading:
  interval_minutes: 3  # AI决策间隔
  coins: ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"]
  kline_limit_3m: 30
  kline_limit_4h: 24

# 风险管理
risk:
  max_position_size_usd: 2000
  max_account_utilization: 0.80
  max_leverage: 10
  stop_loss_pct: 0.15
  max_drawdown_pct: 0.30

# 日志配置
logging:
  level: INFO
  file: logs/bot_{time}.log
  rotation: "100 MB"
  retention: "30 days"

# 注意: 哪些agents运行由数据库管理（trading_agents表）
# 使用CLI创建/管理agents:
#   bot agent create --name "Agent Name" --model deepseek-chat --account account_1 --balance 10000
# account_1 引用上面 exchange.accounts 中定义的账户
```

---

## 4. 接口规范

### 4.1 HyperLiquid API
参考: `docs/05_references/hyperliquid/`

### 4.2 LLM API
参考: `docs/05_references/llm/`

---

## 5. 非功能需求

### 5.1 性能需求
- 交易循环总耗时: < 30秒
- AI决策生成: < 10秒
- 订单执行: < 2秒
- 数据采集: < 5秒

### 5.2 可靠性需求
- 系统可用性: > 99% (允许每月停机 < 7.2小时)
- API调用成功率: > 99%
- 订单执行成功率: > 99%

### 5.3 安全需求
- API密钥加密存储（使用环境变量或加密配置文件）
- 日志中隐藏敏感信息（API key, secret）
- 风险管理规则强制执行

### 5.4 可维护性需求
- 模块化设计（数据采集、AI决策、交易执行、风险管理独立）
- 完整的日志记录
- 代码覆盖率 > 80%
- 符合PEP 8代码规范

---

## 6. 约束和限制

### 6.1 技术约束
- Python 3.8+
- 必须使用官方 HyperLiquid SDK 或 REST API
- LLM Provider必须支持流式输出（可选）

### 6.2 业务约束
- 初期仅支持HyperLiquid交易所
- 仅支持永续合约交易
- 不支持现货交易

### 6.3 成本约束
- AI API费用: < $150/月
- 服务器费用: < $50/月（VPS）

---

## 7. 验收标准

### 7.1 阶段验收

**Phase 1: 数据采集**
- [ ] 能够稳定获取6个币种的市场数据
- [ ] 技术指标计算准确
- [ ] 单元测试覆盖率 > 80%

**Phase 2: AI集成**
- [ ] AI能够生成有效的交易决策
- [ ] 决策解析成功率 > 95%
- [ ] 单元测试覆盖率 > 80%

**Phase 3: 交易执行**
- [ ] 订单执行成功率 > 99%
- [ ] 风险管理规则100%执行
- [ ] 单元测试覆盖率 > 80%

**Phase 4: 自动化**
- [ ] 系统能够7x24小时稳定运行
- [ ] 异常不导致系统崩溃
- [ ] 集成测试通过

**Phase 5: 工具和监控**
- [ ] CLI工具功能完整
- [ ] 日志记录完整
- [ ] 文档完善

### 7.2 最终验收
- [ ] 在测试网运行1周无崩溃
- [ ] 所有Must Have功能实现
- [ ] 代码审查通过
- [ ] 文档完整

---

## 8. 参考文档

- `docs/00_research/nof1_ai_analysis.md`: NoF1.ai功能分析
- `docs/01_requirements/user_stories.md`: 用户故事
- `docs/05_references/hyperliquid/`: HyperLiquid API文档
- `docs/05_references/llm/`: LLM提供商文档
- `.claude/project_rules.md`: 项目规则
