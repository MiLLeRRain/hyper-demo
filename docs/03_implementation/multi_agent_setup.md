# 多 LLM 并行工作配置指南

## 概述

系统已内置多 Agent 并行决策能力！你可以配置多个 AI 模型同时分析市场，然后：
- **并行运行**: 所有 AI 同时分析，互不干扰
- **独立决策**: 每个 AI 给出自己的决策
- **性能对比**: 数据库记录每个 AI 的表现
- **最优选择**: 可以选择表现最好的 AI，或者让它们投票

---

## 系统架构

### 并行决策流程

```
每3分钟周期:
├─ 收集市场数据
├─ 构建 Prompt
├─ 并行调用 AI:
│  ├─ DeepSeek Agent    ──→ 决策 A
│  ├─ OpenAI Agent      ──→ 决策 B
│  ├─ Qwen Agent        ──→ 决策 C
│  └─ Claude Agent      ──→ 决策 D
├─ 所有决策保存到数据库
└─ 执行交易（可选择策略）
```

### 代码实现

```python
# src/trading_bot/orchestration/multi_agent_orchestrator.py

async def run_decision_cycle(self, market_data, positions, account):
    """所有 Agent 并行运行"""

    # 获取所有激活的 Agent
    agents = self.agent_manager.agents

    # 并行执行（asyncio.gather）
    agent_tasks = [
        self._run_agent_decision(agent, market_data, positions, account)
        for agent in agents
    ]

    # 等待所有完成
    results = await asyncio.gather(*agent_tasks)

    # 保存所有决策到数据库
    # 每个 Agent 的决策都被记录
```

---

## 快速配置

### 方案 A: 多个相同模型（不同策略）

配置 2-3 个 DeepSeek Agent，使用不同的参数：

```yaml
# config.yaml

agents:
  # 激进型交易者
  - name: 'Aggressive Trader'
    enabled: true
    provider: 'deepseek'
    model: 'deepseek-chat'
    temperature: 0.9        # 高温度 = 更激进
    max_tokens: 500
    description: 'High-risk high-reward strategy'

  # 保守型交易者
  - name: 'Conservative Trader'
    enabled: true
    provider: 'deepseek'
    model: 'deepseek-chat'
    temperature: 0.3        # 低温度 = 更保守
    max_tokens: 500
    description: 'Low-risk conservative strategy'

  # 平衡型交易者
  - name: 'Balanced Trader'
    enabled: true
    provider: 'deepseek'
    model: 'deepseek-chat'
    temperature: 0.6        # 中等温度
    max_tokens: 500
    description: 'Balanced risk-reward strategy'
```

**优点**:
- ✅ 只需一个 API Key（DeepSeek）
- ✅ 成本低（$0.27/1M tokens 输入）
- ✅ 测试不同风险偏好
- ✅ 可以选择最优策略

**成本估算**:
- 每次决策 ~500 tokens
- 3个 Agent = 1500 tokens/周期
- 每天 480 个周期 = 720K tokens
- 成本: ~$0.20/天

---

### 方案 B: 多个不同模型（模型对比）

配置不同的 LLM 模型进行对比：

```yaml
# config.yaml

llm:
  models:
    # DeepSeek (推荐，性价比高)
    deepseek-chat:
      provider: 'official'
      official:
        base_url: 'https://api.deepseek.com/v1'
        api_key: '${DEEPSEEK_API_KEY}'
        model_name: 'deepseek-chat'
        timeout: 30

    # OpenAI GPT-4
    gpt-4-turbo:
      provider: 'official'
      official:
        base_url: 'https://api.openai.com/v1'
        api_key: '${OPENAI_API_KEY}'
        model_name: 'gpt-4-turbo-preview'
        timeout: 30

    # Alibaba Qwen
    qwen-plus:
      provider: 'official'
      official:
        base_url: 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1'
        api_key: '${QWEN_API_KEY}'
        model_name: 'qwen-plus'
        timeout: 30

agents:
  # DeepSeek Agent
  - name: 'DeepSeek Trader'
    enabled: true
    provider: 'deepseek'
    model: 'deepseek-chat'
    temperature: 0.7
    max_tokens: 500

  # OpenAI Agent
  - name: 'GPT-4 Trader'
    enabled: true
    provider: 'openai'
    model: 'gpt-4-turbo'
    temperature: 0.7
    max_tokens: 500

  # Qwen Agent
  - name: 'Qwen Trader'
    enabled: true
    provider: 'qwen'
    model: 'qwen-plus'
    temperature: 0.7
    max_tokens: 500
```

**优点**:
- ✅ 对比不同模型性能
- ✅ 分散风险（模型多样性）
- ✅ 找到最优模型
- ⚠️ 需要多个 API Key
- ⚠️ 成本较高

**成本对比**:

| 模型 | 输入成本 | 输出成本 | 每天成本（480周期） |
|------|---------|---------|-------------------|
| DeepSeek | $0.27/1M | $1.10/1M | ~$0.20 |
| GPT-4 Turbo | $10/1M | $30/1M | ~$7.50 |
| Qwen Plus | $0.50/1M | $2.00/1M | ~$0.40 |

---

### 方案 C: 混合策略（推荐用于测试）

2个便宜模型 + 1个强力模型：

```yaml
agents:
  # 便宜模型：快速决策
  - name: 'DeepSeek Fast'
    enabled: true
    provider: 'deepseek'
    model: 'deepseek-chat'
    temperature: 0.7
    max_tokens: 300         # 更少 tokens = 更快

  - name: 'Qwen Fast'
    enabled: true
    provider: 'qwen'
    model: 'qwen-plus'
    temperature: 0.7
    max_tokens: 300

  # 强力模型：深度分析（仅在关键时刻使用）
  - name: 'GPT-4 Advisor'
    enabled: false           # 默认关闭，需要时启用
    provider: 'openai'
    model: 'gpt-4-turbo'
    temperature: 0.5
    max_tokens: 1000
```

---

## 环境变量配置

### .env 文件

```bash
# HyperLiquid（必需）
HYPERLIQUID_PRIVATE_KEY=your_wallet_private_key

# DeepSeek（推荐，便宜）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxx

# OpenAI（可选，贵但强大）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxx

# Qwen（可选，性价比中等）
QWEN_API_KEY=sk-xxxxxxxxxxxxxx

# Anthropic Claude（可选）
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxx

# 数据库（可选，用于历史记录）
DB_PASSWORD=trading_bot_2025
```

### 获取 API Keys

#### DeepSeek (推荐)
1. 访问: https://platform.deepseek.com/
2. 注册账号
3. 充值（最低 $5）
4. 创建 API Key
5. 成本: $0.27/1M tokens (输入)

#### OpenAI
1. 访问: https://platform.openai.com/
2. 注册账号
3. 充值（最低 $5）
4. 创建 API Key
5. 成本: $10/1M tokens (GPT-4)

#### Qwen (阿里云)
1. 访问: https://help.aliyun.com/zh/dashscope/
2. 注册阿里云账号
3. 开通灵积服务
4. 创建 API Key
5. 成本: $0.50/1M tokens

---

## 决策执行策略

当有多个 Agent 时，如何执行交易？

### 策略 1: 多数投票（Majority Voting）

```python
# 示例：3个 Agent，2个说 BUY，1个说 HOLD
# 结果：执行 BUY

decisions = [
    AgentDecision(action='BUY', confidence=0.8),
    AgentDecision(action='BUY', confidence=0.7),
    AgentDecision(action='HOLD', confidence=0.6),
]

# 计算投票
votes = count_votes(decisions)
# Result: {'BUY': 2, 'HOLD': 1}

final_action = max(votes, key=votes.get)
# final_action = 'BUY'
```

### 策略 2: 置信度加权（Confidence Weighted）

```python
# 每个决策的置信度作为权重

decisions = [
    AgentDecision(action='BUY', confidence=0.8),   # weight=0.8
    AgentDecision(action='BUY', confidence=0.7),   # weight=0.7
    AgentDecision(action='HOLD', confidence=0.9),  # weight=0.9
]

# BUY: 0.8 + 0.7 = 1.5
# HOLD: 0.9

# BUY 总权重更高，执行 BUY
```

### 策略 3: 最优 Agent（Best Performer）

```python
# 查询数据库，找出历史胜率最高的 Agent

best_agent = query("""
    SELECT agent_id, win_rate
    FROM agent_performance
    ORDER BY win_rate DESC
    LIMIT 1
""")

# 只执行最优 Agent 的决策
final_decision = get_decision(best_agent.id)
```

### 策略 4: 保守策略（Conservative）

```python
# 只有所有 Agent 都同意才执行

all_buy = all(d.action == 'BUY' for d in decisions)
all_hold = all(d.action == 'HOLD' for d in decisions)

if all_buy:
    execute('BUY')
elif all_hold:
    execute('HOLD')
else:
    execute('HOLD')  # 默认保守
```

---

## 配置示例

### 示例 1: 初学者配置（1个模型，低成本）

```yaml
agents:
  - name: 'DeepSeek Trader'
    enabled: true
    provider: 'deepseek'
    model: 'deepseek-chat'
    temperature: 0.7
    max_tokens: 500
```

**成本**: ~$0.20/天
**优点**: 简单、便宜
**缺点**: 单点故障

---

### 示例 2: 测试配置（2个模型，性能对比）

```yaml
agents:
  - name: 'DeepSeek Trader'
    enabled: true
    provider: 'deepseek'
    model: 'deepseek-chat'
    temperature: 0.7
    max_tokens: 500

  - name: 'Qwen Trader'
    enabled: true
    provider: 'qwen'
    model: 'qwen-plus'
    temperature: 0.7
    max_tokens: 500
```

**成本**: ~$0.60/天
**优点**: 对比性能、容错
**用途**: 找出更好的模型

---

### 示例 3: 生产配置（3个策略，多样性）

```yaml
agents:
  # 激进型
  - name: 'Aggressive DeepSeek'
    enabled: true
    provider: 'deepseek'
    model: 'deepseek-chat'
    temperature: 0.9
    max_tokens: 500

  # 保守型
  - name: 'Conservative DeepSeek'
    enabled: true
    provider: 'deepseek'
    model: 'deepseek-chat'
    temperature: 0.3
    max_tokens: 500

  # 平衡型
  - name: 'Balanced Qwen'
    enabled: true
    provider: 'qwen'
    model: 'qwen-plus'
    temperature: 0.6
    max_tokens: 500
```

**成本**: ~$1.00/天
**优点**: 多样化策略、投票机制
**用途**: 长期稳定运行

---

## 性能监控

### 数据库查询

#### 查看每个 Agent 的决策统计

```sql
SELECT
    agent_id,
    COUNT(*) as total_decisions,
    SUM(CASE WHEN action = 'BUY' THEN 1 ELSE 0 END) as buy_count,
    SUM(CASE WHEN action = 'SELL' THEN 1 ELSE 0 END) as sell_count,
    SUM(CASE WHEN action = 'HOLD' THEN 1 ELSE 0 END) as hold_count,
    AVG(confidence) as avg_confidence
FROM agent_decisions
GROUP BY agent_id;
```

#### 查看每个 Agent 的盈亏

```sql
SELECT
    a.name,
    p.total_trades,
    p.winning_trades,
    p.win_rate,
    p.total_pnl,
    p.sharpe_ratio
FROM agent_performance p
JOIN trading_agents a ON a.id = p.agent_id
ORDER BY p.total_pnl DESC;
```

#### 对比不同 Agent 的表现

```sql
SELECT
    a.name,
    a.model,
    COUNT(d.id) as decisions,
    COUNT(t.id) as trades,
    SUM(t.realized_pnl) as total_pnl,
    AVG(t.realized_pnl) as avg_pnl_per_trade
FROM trading_agents a
LEFT JOIN agent_decisions d ON d.agent_id = a.id
LEFT JOIN agent_trades t ON t.agent_id = a.id
WHERE t.status = 'CLOSED'
GROUP BY a.id, a.name, a.model
ORDER BY total_pnl DESC;
```

---

## 启用/禁用 Agent

### 方法 1: 修改 config.yaml

```yaml
agents:
  - name: 'DeepSeek Trader'
    enabled: true          # 启用

  - name: 'GPT-4 Trader'
    enabled: false         # 禁用
```

### 方法 2: 运行时控制（TODO）

```bash
# 查看 Agent 列表
python tradingbot.py agent list

# 启用 Agent
python tradingbot.py agent enable "DeepSeek Trader"

# 禁用 Agent
python tradingbot.py agent disable "GPT-4 Trader"
```

---

## 最佳实践

### 1. 从小开始

```yaml
# 第1周：单个 Agent
agents:
  - name: 'DeepSeek Trader'
    enabled: true
```

### 2. 逐步扩展

```yaml
# 第2周：添加第二个 Agent
agents:
  - name: 'DeepSeek Aggressive'
    enabled: true
    temperature: 0.9

  - name: 'DeepSeek Conservative'
    enabled: true
    temperature: 0.3
```

### 3. 性能对比

```bash
# 运行2周后，查看数据库
python scripts/analyze_agent_performance.py
```

### 4. 选择最优

```yaml
# 第4周：只保留表现最好的
agents:
  - name: 'Best Performer'
    enabled: true
    # 使用上周表现最好的参数
```

---

## 常见问题

### Q1: 多个 Agent 会增加成本吗？

**是的**，成本与 Agent 数量成正比：
- 1个 Agent: $0.20/天
- 3个 Agent: $0.60/天
- 5个 Agent: $1.00/天

但可以通过测试找到最优模型，长期节省成本。

### Q2: 多个 Agent 如何避免冲突？

每个 Agent 的决策都保存到数据库，但不会自动全部执行。需要实现执行策略（投票、加权等）。

### Q3: 可以动态调整 Agent 数量吗？

可以！修改 `config.yaml` 后重启服务即可：
```bash
# 修改 config.yaml
vim config.yaml

# 重启
python tradingbot.py stop
python tradingbot.py start
```

### Q4: 推荐的最佳配置？

**Testnet 测试**:
- 2-3 个 DeepSeek Agent（不同参数）
- 成本低、易于对比

**Mainnet 生产**:
- 先用 Testnet 找到最优配置
- 然后只用1-2个最好的 Agent
- 成本可控、性能最优

---

## 总结

### ✅ 系统已支持

- 多个 LLM 并行运行
- 异步执行（asyncio.gather）
- 数据库记录所有决策
- 性能对比和分析

### 📋 配置步骤

1. 编辑 `config.yaml` 添加多个 Agent
2. 在 `.env` 设置对应的 API Keys
3. 启动系统: `python tradingbot.py start`
4. 监控性能: 查询数据库

### 🎯 推荐配置

**初学者**: 1个 DeepSeek Agent
**测试**: 2-3个 DeepSeek Agent（不同温度）
**生产**: 根据 Testnet 结果选择最优配置

---

需要帮助配置具体的多 Agent 设置吗？
