# 基于策略的多 Agent 配置指南

## 核心原则

### ❌ 错误方式：用 Temperature 控制策略

```yaml
agents:
  - name: 'Aggressive'
    temperature: 0.9    # 期望更激进
  - name: 'Conservative'
    temperature: 0.3    # 期望更保守
```

**为什么错误**:
- `temperature` 只控制输出的**随机性**，不控制**策略逻辑**
- 所有 Agent 看到**相同的系统提示词**
- 无法真正实现不同的交易策略
- Temperature 0.9 可能让保守策略变得"激进"，但不是策略本身变了，只是输出更随机

### ✅ 正确方式：用系统提示词（System Prompt）定义策略

```yaml
agents:
  # Trend Following Agent
  - name: 'Trend Follower'
    temperature: 0.7    # 固定值
    strategy_description: |
      You are a TREND FOLLOWING trader.
      - Only trade with strong trends
      - Entry: SMA crossover + MACD confirmation
      - Exit: Trend reversal signals

  # Mean Reversion Agent
  - name: 'Mean Reverter'
    temperature: 0.7    # 相同的 temperature
    strategy_description: |
      You are a MEAN REVERSION trader.
      - Trade against extremes
      - Entry: RSI < 30 or RSI > 70
      - Exit: Price returns to mean
```

**为什么正确**:
- 每个 Agent 有**明确的交易哲学**和**规则**
- AI 理解并遵循特定策略
- 可以对比不同策略的实际表现
- Temperature 统一，确保输出稳定性

---

## Temperature 的真实作用

### Temperature 参数说明

```python
# Temperature 控制输出的随机性

temperature = 0.0   # 完全确定性（总是选择概率最高的词）
temperature = 0.3   # 低随机性（输出更一致、保守）
temperature = 0.7   # 中等随机性（平衡）
temperature = 1.0   # 高随机性（更多样化、创造性）
temperature = 2.0   # 极高随机性（可能产生不连贯的输出）
```

### 示例对比

**相同的 Prompt + 不同的 Temperature**:

```
Prompt: "分析 BTC，当前价格 $96,000，RSI=65，应该买入还是持有？"

Temperature 0.1:
"基于技术指标，RSI 65 表明轻微超买，建议 HOLD 等待更好入场点。"
（每次运行输出几乎相同）

Temperature 0.9:
可能输出 1: "RSI 65 还未到超买区，可以考虑小仓位 BUY。"
可能输出 2: "当前处于中性区间，HOLD 观望更稳妥。"
可能输出 3: "技术面偏强，建议 BUY，设好止损。"
（每次运行输出不同，更"冒险"）
```

**问题**: 高 temperature 不等于"激进策略"，只是输出更随机。低 temperature 不等于"保守策略"，只是输出更一致。

---

## 正确的策略设计

### 1. 趋势跟踪策略 (Trend Following)

```yaml
- name: 'Trend Following Agent'
  temperature: 0.7
  strategy_description: |
    You are a TREND FOLLOWING trader. Your core principles:

    1. Trading Philosophy:
       - Only trade in the direction of strong trends
       - Wait for clear trend confirmation before entering
       - Ride trends as long as they remain intact

    2. Entry Rules:
       - LONG: Price above SMA(20) AND SMA(50), MACD bullish, RSI > 50
       - SHORT: Price below SMA(20) AND SMA(50), MACD bearish, RSI < 50
       - HOLD: No clear trend or mixed signals

    3. Risk Management:
       - Position size: 30-50% of account
       - Stop loss: Below recent swing low/high
       - Take profit: Trail stop until trend reversal
       - Leverage: 2-3x

    4. Indicator Priority:
       1. SMA crossovers (most important)
       2. MACD confirmation
       3. RSI for momentum
```

**特点**:
- 明确的入场/出场规则
- 基于技术指标的客观判断
- 适合趋势明显的市场

---

### 2. 均值回归策略 (Mean Reversion)

```yaml
- name: 'Mean Reversion Agent'
  temperature: 0.7
  strategy_description: |
    You are a MEAN REVERSION trader. Your core principles:

    1. Trading Philosophy:
       - Trade against short-term extremes
       - Buy oversold, sell overbought
       - Profit from market overreactions

    2. Entry Rules:
       - LONG: RSI < 30, price 5%+ below SMA(20), volume spike
       - SHORT: RSI > 70, price 5%+ above SMA(20), volume spike
       - HOLD: RSI 30-70 (normal range)

    3. Risk Management:
       - Position size: 20-30% of account (conservative)
       - Stop loss: Tight (2-3% from entry)
       - Take profit: Quick exits at SMA(20)
       - Leverage: 1-2x

    4. Indicator Priority:
       1. RSI extremes (most important)
       2. Distance from SMA(20)
       3. Volume confirmation
```

**特点**:
- 反向操作（买跌卖涨）
- 短期交易，快进快出
- 适合震荡市场

---

### 3. 动量突破策略 (Momentum Breakout)

```yaml
- name: 'Momentum Breakout Agent'
  temperature: 0.7
  strategy_description: |
    You are a MOMENTUM BREAKOUT trader. Your core principles:

    1. Trading Philosophy:
       - Trade explosive price movements
       - Enter on confirmed breakouts with volume
       - Capture large moves in short time

    2. Entry Rules:
       - LONG: Break above recent high + volume > 2x avg + RSI > 60
       - SHORT: Break below recent low + volume > 2x avg + RSI < 40
       - HOLD: No breakout or low volume

    3. Risk Management:
       - Position size: 40-60% (aggressive on strong signals)
       - Stop loss: Just below breakout level (2-4%)
       - Take profit: Trail stop until momentum fades
       - Leverage: 3-5x on strong setups

    4. Indicator Priority:
       1. Volume confirmation (critical!)
       2. Breakout level
       3. MACD acceleration
```

**特点**:
- 进攻性强
- 需要成交量确认
- 适合有明确突破的市场

---

## 实际效果对比

### 场景：BTC 价格 $96,000

**市场数据**:
- 当前价格: $96,000
- SMA(20): $95,500
- SMA(50): $94,000
- RSI: 65
- MACD: +150 (bullish)
- 成交量: 正常水平

### Agent 决策对比

#### Trend Following Agent
```
分析：
✅ 价格在 SMA(20) 和 SMA(50) 之上
✅ MACD 为正值且向上
✅ RSI 65 > 50（上升动能）

决策: BUY
理由: "明确的上升趋势，所有趋势指标一致看多"
置信度: 0.75
```

#### Mean Reversion Agent
```
分析：
❌ RSI 65 未达到超买阈值 70
❌ 价格仅略高于 SMA(20)，未达到 5%+ 偏离
⚠️ 无明显超买信号

决策: HOLD
理由: "当前处于正常范围，未出现极端超买，等待更好的回归机会"
置信度: 0.55
```

#### Momentum Breakout Agent
```
分析：
❌ 无突破新高
❌ 成交量未达到 2倍平均值
⚠️ RSI 65 尚可，但无突破确认

决策: HOLD
理由: "缺乏成交量确认的突破信号，不符合入场条件"
置信度: 0.50
```

### 投票结果
- BUY: 1票
- HOLD: 2票
- **最终决策: HOLD**（多数投票）

---

## 策略组合建议

### 初学者配置（单策略）

```yaml
agents:
  # 只用一个稳健的趋势跟踪
  - name: 'Trend Follower'
    enabled: true
    temperature: 0.7
    strategy_description: "... (趋势跟踪策略)"
```

**优点**: 简单、易于理解和调试

---

### 进阶配置（2-3个互补策略）

```yaml
agents:
  # 趋势跟踪（趋势市场）
  - name: 'Trend Follower'
    enabled: true
    temperature: 0.7

  # 均值回归（震荡市场）
  - name: 'Mean Reverter'
    enabled: true
    temperature: 0.7

  # 可选：动量突破（突破行情）
  - name: 'Momentum Breakout'
    enabled: false    # 按需启用
    temperature: 0.7
```

**优点**:
- 适应不同市场环境
- 策略互补，降低风险
- 可以通过投票/加权决策

---

### 生产配置（精选最优）

```yaml
agents:
  # 通过 Testnet 测试找出最优策略
  - name: 'Best Performer'
    enabled: true
    temperature: 0.7
    strategy_description: "... (在测试中表现最好的策略)"
```

**优点**:
- 成本最低
- 性能最优
- 经过验证

---

## 策略设计要点

### 1. 明确的入场规则

```yaml
# ✅ 好的规则（客观、可量化）
Entry Rules:
- LONG: RSI < 30 AND price < SMA(20) - 5%
- SHORT: RSI > 70 AND price > SMA(20) + 5%

# ❌ 坏的规则（主观、模糊）
Entry Rules:
- LONG: "When the market looks oversold"
- SHORT: "When price is too high"
```

### 2. 清晰的风险参数

```yaml
# ✅ 好的参数（具体数值）
Risk Management:
- Position size: 30% of account
- Stop loss: 3% from entry
- Leverage: 2x maximum

# ❌ 坏的参数（模糊）
Risk Management:
- Position size: "Moderate"
- Stop loss: "Reasonable distance"
- Leverage: "Not too high"
```

### 3. 优先级指标

```yaml
# ✅ 好的优先级（明确权重）
Indicator Priority:
1. RSI extremes (primary signal)
2. Volume confirmation (secondary)
3. MACD trend (confirmation)

# ❌ 坏的优先级（无序）
Indicators:
- RSI, MACD, Volume, SMA (all equally important)
```

---

## 性能评估

### 查询每个策略的表现

```sql
SELECT
    a.name,
    a.strategy_description,
    COUNT(d.id) as decisions,
    SUM(CASE WHEN d.action = 'BUY' THEN 1 ELSE 0 END) as buys,
    SUM(CASE WHEN d.action = 'SELL' THEN 1 ELSE 0 END) as sells,
    SUM(CASE WHEN d.action = 'HOLD' THEN 1 ELSE 0 END) as holds,
    AVG(d.confidence) as avg_confidence,
    p.total_pnl,
    p.win_rate
FROM trading_agents a
LEFT JOIN agent_decisions d ON d.agent_id = a.id
LEFT JOIN agent_performance p ON p.agent_id = a.id
GROUP BY a.id
ORDER BY p.total_pnl DESC;
```

### 对比不同市场环境下的表现

```sql
-- 趋势市场 vs 震荡市场
SELECT
    a.name,
    CASE
        WHEN market_condition = 'trending' THEN 'Trending'
        WHEN market_condition = 'ranging' THEN 'Ranging'
    END as market_type,
    AVG(pnl) as avg_pnl,
    COUNT(*) as trade_count
FROM trades t
JOIN trading_agents a ON a.id = t.agent_id
GROUP BY a.name, market_condition
ORDER BY a.name, market_type;
```

---

## 总结

### ✅ 正确做法
1. **统一 temperature**（如 0.7）
2. **用 `strategy_description` 定义策略**
3. **明确的入场/出场规则**
4. **可量化的风险参数**
5. **指标优先级排序**

### ❌ 错误做法
1. ~~用 temperature 控制策略~~
2. ~~模糊的策略描述~~
3. ~~主观的交易规则~~
4. ~~无明确的止损/止盈~~

### 📋 下一步
1. 复制 `config.multi-strategy.yaml` 为 `config.yaml`
2. 根据需要调整策略描述
3. 在 Testnet 测试 2-4 周
4. 分析数据库，找出最优策略
5. 用最优策略在 Mainnet 运行

---

**配置文件**: `config.multi-strategy.yaml`
**示例配置**: 包含 3 个完整策略（趋势跟踪、均值回归、动量突破）
