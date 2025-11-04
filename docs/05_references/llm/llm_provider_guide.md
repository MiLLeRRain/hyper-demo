# LLM Provider 配置指南

## 架构设计: Multi-Agent + Model Pool（多Agent + 模型池）

**核心理念**:
- **定义可用模型池**: 在配置文件中定义所有可用的LLM模型
- **数据库驱动agents**: 通过数据库控制哪些models实际运行
- **每个agent = 1个LLM + 1个账户**: 支持多个agents并行竞争
- **模型优先设计**: 每个模型可通过不同服务提供商访问

### 为什么是Multi-Agent架构？

**NoF1.ai启发**: 让不同LLM模型竞争，看谁表现更好！

```yaml
# ✅ 正确: 模型池 + 数据库驱动
llm:
  models:
    deepseek-chat:
      provider: official  # 选择服务提供商
    qwen-plus:
      provider: official
    # ... 更多模型
```

**哪些agents运行？由数据库控制！**
```bash
# CLI创建agents
$ bot agent create --name "DeepSeek Trader" --model deepseek-chat --balance 10000
$ bot agent create --name "Qwen Trader" --model qwen-plus --balance 10000
# 现在有2个agents并行运行，使用不同的LLM模型
```

### Model-Centric设计

虽然是多agent架构，但仍然遵循Model-Centric原则：
- **DeepSeek-Chat、Qwen-Plus是模型**
- **Official API、OpenRouter是服务提供商**

每个模型可通过不同提供商访问：
```yaml
models:
  deepseek-chat:
    provider: official      # 或 openrouter
    official: {...}
    openrouter: {...}
```

---

## API兼容性说明

**重要发现**: DeepSeek官方、Qwen官方、OpenRouter **使用完全相同的API格式**！

所有服务提供商都使用OpenAI兼容接口，只有以下区别：
- `base_url` (API端点地址)
- `api_key` (API密钥)
- `model_name` (模型标识符)

**这意味着切换服务提供商只需修改配置文件，代码完全不变！**

---

## 快速开始

### 1. 配置API密钥

```bash
# 复制示例配置
cp config.example.yaml config.yaml

# 编辑配置文件，填写你的API密钥
```

### 2. 定义可用模型池

在 `config.yaml` 中配置：

```yaml
llm:
  # 定义可用模型池（哪些agents运行由数据库控制）
  models:
    deepseek-chat:
      # 选择服务提供商: official 或 openrouter
      provider: 'official'

      official:
        api_key: 'YOUR_DEEPSEEK_API_KEY'
        base_url: https://api.deepseek.com/v1
        model_name: deepseek-chat
        timeout: 30

      openrouter:
        api_key: 'YOUR_OPENROUTER_API_KEY'
        base_url: https://openrouter.ai/api/v1
        model_name: deepseek/deepseek-chat
        timeout: 30

    qwen-plus:
      provider: 'official'
      official:
        api_key: 'YOUR_QWEN_API_KEY'
        base_url: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        model_name: qwen-plus
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

### 3. 创建和管理Agents

```bash
# 创建使用DeepSeek的agent
$ bot agent create \
    --name "DeepSeek Trader 1" \
    --model deepseek-chat \
    --account 0x1234... \
    --api-key ${HL_KEY_1} \
    --balance 10000.0

# 创建使用Qwen的agent
$ bot agent create \
    --name "Qwen Trader 1" \
    --model qwen-plus \
    --account 0x5678... \
    --api-key ${HL_KEY_2} \
    --balance 10000.0

# 列出所有agents
$ bot agent list

# 查看agent表现
$ bot agent stats <agent-id>
```

### 4. 使用Multi-Agent系统

```python
from src.trading_bot.ai.agent_manager import AgentManager
from src.trading_bot.ai.multi_agent_orch import MultiAgentOrchestrator
from src.trading_bot.config import load_config
from sqlalchemy.orm import Session

# 加载配置
config = load_config('config.yaml')

# 初始化agent管理器
agent_manager = AgentManager(db_session, config.llm)

# 初始化多agent协调器
orchestrator = MultiAgentOrchestrator(
    agent_manager=agent_manager,
    data_collector=data_collector,
    prompt_builder=prompt_builder,
    decision_parser=decision_parser,
    db_session=db_session
)

# 运行一次决策周期（所有agents并行）
decisions = await orchestrator.run_decision_cycle()
```

## 模型 vs 服务提供商对比

### 可用的LLM模型

#### DeepSeek-Chat
- **模型特点**: 推理能力强，适合复杂决策
- **上下文长度**: 64K tokens
- **官方定价**: $0.27/1M输入, $1.10/1M输出
- **OpenRouter定价**: $0.27/1M输入, $1.10/1M输出（相同）
- **推荐场景**: 需要深度推理的交易决策

#### Qwen-Plus
- **模型特点**: 平衡性能和成本，中文能力强
- **上下文长度**: 32K tokens
- **官方定价**: ¥0.0008/1K tokens (~$0.11/1M)
- **OpenRouter定价**: $0.54/1M输入, $2.24/1M输出
- **推荐场景**: 性价比优先

---

### 服务提供商对比

#### Official API（官方API）
**DeepSeek官方**:
- **API端点**: `https://api.deepseek.com/v1`
- **获取密钥**: https://platform.deepseek.com/
- **优点**: 最便宜，有缓存支持（90%折扣）
- **缺点**: 数据用于训练，存储在中国

**Qwen官方**:
- **API端点**: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- **获取密钥**: https://help.aliyun.com/zh/dashscope/
- **优点**: 中国用户访问快，价格适中
- **缺点**: 需要阿里云账户，国际化程度较低

#### OpenRouter
- **API端点**: `https://openrouter.ai/api/v1`
- **获取密钥**: https://openrouter.ai/keys
- **支持模型**: DeepSeek-Chat, Qwen, Claude, GPT-4等400+模型
- **优点**: 零数据保留(ZDR)，一个账户管理所有模型，方便切换
- **缺点**: 部分模型价格略高于官方

---

### 如何选择？

**选择模型**:
1. **需要最强推理能力** → DeepSeek-Chat
2. **注重性价比** → Qwen-Plus
3. **需要其他模型** → 通过OpenRouter访问Claude、GPT-4等

**选择服务提供商**:
1. **成本最优** → 使用Official API
2. **注重隐私** → 使用OpenRouter (零数据保留)
3. **需要多模型切换** → 使用OpenRouter（一个账户管理所有）

## 隐私考虑

### 我们的用例特殊性

**重要结论**: 对于这个交易系统，隐私顾虑很小！

原因：
1. **提示词结构固定**: 每次都是相同的11,053字符模板
2. **只有数据变化**: 只有市场价格、技术指标在变化
3. **无专有策略**: 提示词本身不包含专有交易策略
4. **AI即时推理**: "智能"来自AI的实时推理，不是提示词模板

**被训练也无妨**: 即使提供商用你的提示词训练模型，他们只能学到：
- 如何格式化市场数据
- 基本的技术指标含义
- 通用的交易决策格式

他们**学不到**你的实际交易策略（因为策略由AI实时生成）。

### 隐私对比

| 提供商 | 数据保留 | 训练使用 | 数据位置 | 隐私评级 |
|--------|---------|---------|---------|---------|
| **OpenRouter** | 零保留(ZDR) | 可选退出 | 美国 | ⭐⭐⭐⭐⭐ |
| **DeepSeek** | 保留 | 全部用于训练 | 中国 | ⭐⭐⭐ |
| **Qwen** | 保留部分 | 非个人部分训练 | 中国 | ⭐⭐⭐⭐ |

**推荐**: 如果你的数据真的敏感，选OpenRouter。但对于这个交易系统，任何提供商都可以。

## 成本估算

假设每3分钟调用一次，每天480次调用：

### 输入Token估算
- 提示词长度: 11,053字符 ≈ 3,000 tokens
- 每天输入: 480 × 3,000 = 1,440,000 tokens
- 每月输入: 1.44M × 30 = 43.2M tokens

### 输出Token估算
- 平均响应: ~500 tokens/次
- 每天输出: 480 × 500 = 240,000 tokens
- 每月输出: 0.24M × 30 = 7.2M tokens

### 月度成本对比

| 提供商 | 月度成本 | 备注 |
|--------|---------|------|
| **DeepSeek官方** | $19.60 | 43.2M × $0.27/M + 7.2M × $1.10/M |
| **DeepSeek官方(缓存)** | $9.15 | 90%缓存命中率 |
| **Qwen-Plus官方** | $4.06 | 50.4M × ¥0.0008/K ÷ 1000 × 7.3 |
| **OpenRouter DeepSeek** | $19.60 | 同官方定价 |
| **OpenRouter Qwen** | $39.49 | 43.2M × $0.54/M + 7.2M × $2.24/M |

## 推荐策略

### 开发阶段
使用 **OpenRouter**:
- 一个账户测试所有模型
- 零数据保留，安全
- 快速切换模型对比效果

### 生产阶段
根据预算选择：
- **预算紧张**: DeepSeek官方 ($9-20/月)
- **平衡选择**: Qwen-Plus官方 ($4/月)
- **注重隐私**: OpenRouter ($20-40/月)

## 代码示例

### 基础使用 - Multi-Agent

```python
from src.trading_bot.ai.agent_manager import AgentManager
from src.trading_bot.ai.multi_agent_orch import MultiAgentOrchestrator
from src.trading_bot.config import load_config
import asyncio

# 加载配置
config = load_config('config.yaml')

# 初始化agent管理器（从数据库加载所有active agents）
agent_manager = AgentManager(db_session, config.llm)

# 初始化协调器
orchestrator = MultiAgentOrchestrator(
    agent_manager=agent_manager,
    data_collector=data_collector,
    prompt_builder=prompt_builder,
    decision_parser=decision_parser,
    db_session=db_session
)

# 运行决策周期（所有agents并行）
decisions = asyncio.run(orchestrator.run_decision_cycle())

# decisions = List[AgentDecision]，每个agent一个决策
for decision in decisions:
    print(f"Agent: {decision.agent.name}")
    print(f"Model: {decision.agent.llm_model}")
    print(f"Decision: {decision.parsed_decision}")
```

### 切换服务提供商

如果想让某个模型使用不同的服务提供商，只需修改 `config.yaml`:

```yaml
# 从官方API切换到OpenRouter
llm:
  models:
    deepseek-chat:
      provider: openrouter  # 改为 openrouter
      # provider: official  # 之前用的official
```

重启程序即可生效，代码无需修改。

### 测试不同模型的效果

**Multi-Agent方式**: 同时运行多个agents，实时对比表现！

```bash
# 创建多个agents使用不同模型
$ bot agent create --name "DeepSeek Trader" --model deepseek-chat --balance 10000
$ bot agent create --name "Qwen Trader" --model qwen-plus --balance 10000
$ bot agent create --name "Claude Trader" --model claude-3-5-sonnet --balance 10000

# 运行系统，3个agents并行交易
$ bot start

# 一段时间后，对比表现
$ bot agent stats abc123  # DeepSeek
$ bot agent stats def456  # Qwen
$ bot agent stats ghi789  # Claude
```

**添加更多模型到池**:
```yaml
# 在config.yaml中添加更多模型定义:
llm:
  models:
    claude-3-5-sonnet:
      provider: openrouter
      openrouter:
        api_key: YOUR_KEY
        base_url: https://openrouter.ai/api/v1
        model_name: anthropic/claude-3.5-sonnet
        timeout: 30

    gpt-4o:
      provider: openrouter
      openrouter:
        api_key: YOUR_KEY
        base_url: https://openrouter.ai/api/v1
        model_name: openai/gpt-4o
        timeout: 30
```

### 错误处理

```python
from src.trading_bot.ai.agent_manager import AgentManager
from src.trading_bot.config import load_config
import asyncio

try:
    config = load_config('config.yaml')
    agent_manager = AgentManager(db_session, config.llm)

    if len(agent_manager.agents) == 0:
        print("没有活跃的agents！使用 'bot agent create' 创建agent")
    else:
        decisions = asyncio.run(orchestrator.run_decision_cycle())

except FileNotFoundError:
    print("请先创建 config.yaml 配置文件")
except ValueError as e:
    print(f"配置错误: {e}")
except Exception as e:
    print(f"错误: {e}")
```

## 常见问题

### Q: 同一个模型通过不同服务提供商访问，响应质量一样吗？
A: 理论上一样（同样的模型），但实际可能因为：
- 模型版本略有差异
- 推理参数调优不同
- 建议实际测试对比

### Q: 可以在运行时添加/删除agents吗？
A: 可以！使用CLI命令：
```bash
$ bot agent create ...    # 添加新agent
$ bot agent pause <id>    # 暂停agent
$ bot agent stop <id>     # 停止agent
```
系统会在下一个决策周期自动识别变化。

### Q: Model-Centric和Provider-Centric有什么区别？
A:
- **Provider-Centric（错误）**: 把DeepSeek当成"提供商"
- **Model-Centric（正确）**: DeepSeek-Chat是模型，Official API和OpenRouter是提供商

### Q: 多个agents会互相影响吗？
A: 不会！每个agent使用独立的：
- LLM模型实例
- HyperLiquid账户
- 决策历史
- 交易记录

它们完全独立竞争。

### Q: 如何对比不同模型的表现？
A: 创建多个agents使用不同模型，运行一段时间后使用 `bot agent stats` 对比：
- 总盈亏 (PnL)
- 胜率 (Win Rate)
- 夏普比率 (Sharpe Ratio)
- 最大回撤 (Max Drawdown)

### Q: 为什么隐私不是大问题？
A: 因为你的提示词是固定模板，只有市场数据在变化。即使被训练，也不会泄露专有策略。

### Q: 缓存是什么？
A: DeepSeek官方支持prompt缓存，重复部分只收10%费用。由于我们的提示词模板固定，缓存命中率可达90%。

### Q: 推荐哪个组合？
A:
- **初学者**: DeepSeek-Chat + OpenRouter (方便，安全)
- **性价比**: Qwen-Plus + Official API ($4/月)
- **最低成本**: DeepSeek-Chat + Official API + 缓存 ($9/月)
- **最强性能**: Claude-3.5-Sonnet + OpenRouter (贵但效果可能更好)

### Q: 如何添加新模型？
A: 在 `config.yaml` 的 `models` 部分添加新模型定义即可：
```yaml
models:
  gpt-4o:
    provider: openrouter
    openrouter:
      api_key: YOUR_KEY
      base_url: https://openrouter.ai/api/v1
      model_name: openai/gpt-4o
      timeout: 30
```
