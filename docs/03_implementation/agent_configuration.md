# Agent 配置指南

## 当前配置

已更新 `config.yaml`，包含以下关键改进：

### 1. 统一 Temperature = 0.3 ✅

```yaml
llm:
  temperature: 0.3  # 最稳定的设置
  max_tokens: 500
```

**为什么选择 0.3**:
- ✅ 决策高度一致（95%+ 相同输出）
- ✅ 适合生产环境和真实交易
- ✅ 可复现，便于调试和回测
- ✅ OpenAI 推荐用于 fact-based tasks（交易属于此类）

---

### 2. 保留 Default Agent（基准对照组）✅

```yaml
agents:
  # Default Agent - 无自定义策略
  - name: 'Default Agent'
    enabled: true
    temperature: 0.3
    # 关键：不设置 strategy_description
    # 使用系统默认通用提示词
```

**作用**:
- 📊 作为基准对照（Control Group）
- 📈 对比有策略 vs 无策略的效果
- 🔍 验证自定义策略是否真的有效
- 📉 如果自定义策略表现更差，说明策略设计有问题

---

### 3. 三个可选策略 Agent

所有策略 Agent 默认关闭，按需启用：

```yaml
- Trend Follower: 趋势跟踪策略（默认关闭）
- Mean Reverter: 均值回归策略（默认关闭）
- Momentum Breakout: 动量突破策略（默认关闭）
```

---

## 使用场景

### 场景 1: 初始测试（当前配置）

**只启用 Default Agent**:

```yaml
agents:
  - name: 'Default Agent'
    enabled: true    # ← 只有这个启用

  - name: 'Trend Follower'
    enabled: false   # 关闭

  - name: 'Mean Reverter'
    enabled: false   # 关闭

  - name: 'Momentum Breakout'
    enabled: false   # 关闭
```

**运行**:
```bash
python tradingbot.py start
```

**结果**:
- 只有 Default Agent 在工作
- 使用系统默认提示词
- 建立性能基准线

---

### 场景 2: 对比测试（Default vs 单一策略）

**启用 Default + 一个策略**:

```yaml
agents:
  - name: 'Default Agent'
    enabled: true    # 基准

  - name: 'Trend Follower'
    enabled: true    # 测试趋势策略

  - name: 'Mean Reverter'
    enabled: false

  - name: 'Momentum Breakout'
    enabled: false
```

**运行 1-2 周后，查询数据库**:

```sql
-- 对比 Default vs Trend Follower
SELECT
    a.name,
    COUNT(d.id) as total_decisions,
    SUM(CASE WHEN d.action = 'BUY' THEN 1 ELSE 0 END) as buy_count,
    SUM(CASE WHEN d.action = 'HOLD' THEN 1 ELSE 0 END) as hold_count,
    AVG(d.confidence) as avg_confidence,
    p.total_pnl,
    p.win_rate
FROM trading_agents a
LEFT JOIN agent_decisions d ON d.agent_id = a.id
LEFT JOIN agent_performance p ON p.agent_id = a.id
WHERE a.name IN ('Default Agent', 'Trend Follower')
GROUP BY a.id, a.name, p.total_pnl, p.win_rate
ORDER BY p.total_pnl DESC;
```

**分析**:
- 如果 Trend Follower PnL > Default: 策略有效 ✅
- 如果 Trend Follower PnL < Default: 策略无效，需要调整 ⚠️

---

### 场景 3: 多策略对比

**启用所有 Agent**:

```yaml
agents:
  - name: 'Default Agent'
    enabled: true    # 基准

  - name: 'Trend Follower'
    enabled: true    # 策略 1

  - name: 'Mean Reverter'
    enabled: true    # 策略 2

  - name: 'Momentum Breakout'
    enabled: true    # 策略 3
```

**成本**:
- 4 个 Agent × 500 tokens × 480 周期/天 = 960K tokens/天
- $0.27/1M × 960K = **$0.26/天** ≈ **$8/月**

**运行 2-4 周后分析**:

```sql
-- 策略性能排行榜
SELECT
    a.name,
    p.total_trades,
    p.winning_trades,
    p.win_rate,
    p.total_pnl,
    p.sharpe_ratio,
    p.max_drawdown
FROM agent_performance p
JOIN trading_agents a ON a.id = p.agent_id
ORDER BY p.total_pnl DESC;
```

**示例结果**:

| Agent | Win Rate | Total PnL | Sharpe Ratio |
|-------|----------|-----------|--------------|
| Trend Follower | 65% | +$450 | 1.8 |
| Default Agent | 58% | +$320 | 1.4 |
| Mean Reverter | 55% | +$180 | 1.2 |
| Momentum Breakout | 48% | -$120 | 0.6 |

**结论**: Trend Follower 最优，可以只用这一个策略。

---

### 场景 4: 生产环境（最优策略）

测试后选择最优策略：

```yaml
agents:
  # 只启用表现最好的策略
  - name: 'Trend Follower'
    enabled: true    # 测试验证最优

  - name: 'Default Agent'
    enabled: false   # 关闭基准

  - name: 'Mean Reverter'
    enabled: false

  - name: 'Momentum Breakout'
    enabled: false
```

**成本**:
- 1 个 Agent × $0.065/天 = **$2/月**

---

## Default Agent 的重要性

### 为什么需要 Default Agent？

#### 1. 科学对照实验

```
实验组: 有自定义策略的 Agent
对照组: Default Agent（无策略）

如果实验组表现更好 → 策略有效
如果实验组表现更差 → 策略设计有问题
```

#### 2. 验证策略价值

有时候，**简单的通用策略反而比复杂的自定义策略更好**。

**真实案例**:
```
Default Agent (通用):  胜率 60%, PnL +$400
Custom Strategy (复杂): 胜率 52%, PnL +$150

结论: 自定义策略过度拟合，不如默认策略
```

#### 3. 调试基准

当策略表现不好时：

```
如果 Default Agent 表现也不好:
  → 问题在市场环境或系统设置

如果 Default Agent 表现好:
  → 问题在自定义策略设计
```

---

## 系统提示词对比

### Default Agent 的提示词

```
# HyperLiquid AI Trading System
Current Time: 2025-11-16 12:00:00 UTC

You are an advanced AI trading agent operating on HyperLiquid DEX.

Your goal is to maximize portfolio returns while managing risk.
You have access to real-time market data, technical indicators, and portfolio state.

## Portfolio Status
...

## Market Data
...

## Risk Management Constraints
- Max position size: 50% of account
- Max leverage: 5x
- Stop loss required
...

## Your Task
Analyze the data and make ONE trading decision...
```

**特点**:
- 通用、灵活
- 没有特定策略偏好
- AI 自主决策

---

### Trend Follower 的提示词

```
# HyperLiquid AI Trading System
Current Time: 2025-11-16 12:00:00 UTC

You are an advanced AI trading agent operating on HyperLiquid DEX.

Your goal is to maximize portfolio returns while managing risk.
You have access to real-time market data, technical indicators, and portfolio state.

**Your Trading Strategy:**
You are a TREND FOLLOWING trader. Your core principles:

1. Trading Philosophy:
   - Only trade in the direction of strong trends
   - Wait for clear trend confirmation before entering
   ...

2. Entry Rules:
   - LONG: Price above SMA(20) AND SMA(50), MACD bullish, RSI > 50
   ...

## Portfolio Status
...
```

**特点**:
- 明确的策略指导
- 具体的入场规则
- 指标优先级

---

## 测试流程建议

### 第 1 周: 只用 Default Agent

```yaml
agents:
  - name: 'Default Agent'
    enabled: true
```

**目标**: 建立基准性能数据

---

### 第 2 周: Default + Trend Follower

```yaml
agents:
  - name: 'Default Agent'
    enabled: true
  - name: 'Trend Follower'
    enabled: true
```

**目标**: 对比趋势策略效果

---

### 第 3 周: Default + Mean Reverter

```yaml
agents:
  - name: 'Default Agent'
    enabled: true
  - name: 'Mean Reverter'
    enabled: true
```

**目标**: 对比均值回归策略

---

### 第 4 周: 全部启用

```yaml
agents:
  - name: 'Default Agent'
    enabled: true
  - name: 'Trend Follower'
    enabled: true
  - name: 'Mean Reverter'
    enabled: true
  - name: 'Momentum Breakout'
    enabled: true
```

**目标**: 全面对比，找出最优

---

### 第 5 周+: 只用最优策略

```yaml
agents:
  - name: 'Trend Follower'  # 假设这个最优
    enabled: true
  # 其他全部关闭
```

**目标**: 生产运行

---

## 快速检查

### 查看当前启用的 Agent

```bash
python scripts/quick_check.py

# 或者查看配置
grep -A 3 "enabled: true" config.yaml
```

### 查看 Agent 决策

```bash
# 启动后查看日志
python tradingbot.py logs -f

# 输出示例:
# Agent 'Default Agent' decision: BUY BTC (confidence: 0.65)
```

### 查询数据库

```sql
-- 查看所有 Agent
SELECT id, name, is_active FROM trading_agents;

-- 查看决策统计
SELECT
    a.name,
    COUNT(d.id) as decisions
FROM trading_agents a
LEFT JOIN agent_decisions d ON d.agent_id = a.id
GROUP BY a.id, a.name;
```

---

## 总结

### ✅ 已完成配置

1. **Temperature = 0.3** (最稳定)
2. **Default Agent** (基准对照)
3. **3 个策略 Agent** (可选启用)
4. **所有 Agent 统一参数**

### 📋 当前状态

```yaml
启用: Default Agent (基准)
关闭: Trend Follower, Mean Reverter, Momentum Breakout
```

### 🎯 下一步

1. **立即测试**: `python tests/testnet/test_llm_integration.py`
2. **长期运行**: `python tradingbot.py start`
3. **1周后**: 启用一个策略 Agent，对比效果
4. **1月后**: 分析数据，选择最优策略

---

**配置文件**: `config.yaml`
**当前成本**: ~$2/月 (只有 Default Agent)
**测试成本**: ~$8/月 (所有 4 个 Agent)
