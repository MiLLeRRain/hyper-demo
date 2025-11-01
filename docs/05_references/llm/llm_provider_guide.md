# LLM Provider 配置指南

## API兼容性说明

**重要发现**: DeepSeek官方、Qwen官方、OpenRouter **使用完全相同的API格式**！

所有提供商都使用OpenAI兼容接口，只有以下区别：
- `base_url` (API端点地址)
- `api_key` (API密钥)
- `model` (模型名称)

**这意味着切换提供商只需修改配置文件，代码完全不变！**

## 快速开始

### 1. 配置API密钥

```bash
# 复制示例配置
cp config.example.yaml config.yaml

# 编辑配置文件，填写你的API密钥
# 只需填写你想使用的提供商的密钥
```

### 2. 选择提供商

在 `config.yaml` 中设置 `active_provider`:

```yaml
# 选择以下之一:
active_provider: 'deepseek_official'  # DeepSeek官方
# active_provider: 'qwen_official'    # Qwen官方
# active_provider: 'openrouter'        # OpenRouter
```

### 3. 使用LLM客户端

```python
from src.llm_client import LLMClient

# 初始化 (自动使用config.yaml中的active_provider)
client = LLMClient('config.yaml')

# 生成交易决策
decision = client.generate_decision(nof1_prompt)

# 运行时切换提供商 (可选)
client.switch_provider('qwen_official')
```

## 提供商对比

### DeepSeek 官方
- **API端点**: `https://api.deepseek.com/v1`
- **获取密钥**: https://platform.deepseek.com/
- **定价**: $0.27/1M输入, $1.10/1M输出
- **缓存**: 90%折扣 ($0.027/1M)
- **优点**: 最便宜，有缓存支持
- **缺点**: 数据用于训练，存储在中国

### Qwen 官方 (阿里云DashScope)
- **API端点**: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- **获取密钥**: https://help.aliyun.com/zh/dashscope/
- **定价**:
  - Qwen-Plus: ¥0.0008/1K tokens (~$0.11/1M)
  - Qwen-Max: ¥0.04/1K tokens (~$5.5/1M)
- **优点**: 中国用户访问快，价格适中
- **缺点**: 需要阿里云账户，国际化程度较低

### OpenRouter
- **API端点**: `https://openrouter.ai/api/v1`
- **获取密钥**: https://openrouter.ai/keys
- **定价**:
  - DeepSeek: $0.27/1M输入, $1.10/1M输出
  - Qwen: $0.54/1M输入, $2.24/1M输出
- **优点**: 零数据保留(ZDR)，支持400+模型，一个账户管理所有
- **缺点**: 价格略高于官方

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

### 基础使用

```python
from src.llm_client import LLMClient

# 方法1: 使用配置文件
client = LLMClient('config.yaml')
decision = client.generate_decision(prompt)

# 方法2: 运行时切换
client.switch_provider('qwen_official')
decision = client.generate_decision(prompt)
```

### 多模型对比

```python
# 同时测试多个提供商的决策质量
providers = ['deepseek_official', 'qwen_official', 'openrouter']
decisions = {}

client = LLMClient('config.yaml')

for provider in providers:
    client.switch_provider(provider)
    decisions[provider] = client.generate_decision(prompt)

# 对比不同模型的决策
for provider, decision in decisions.items():
    print(f"\n=== {provider} ===")
    print(decision)
```

### 错误处理

```python
from src.llm_client import LLMClient

try:
    client = LLMClient('config.yaml')
    decision = client.generate_decision(prompt)
except FileNotFoundError:
    print("请先创建 config.yaml 配置文件")
except ValueError as e:
    print(f"配置错误: {e}")
except Exception as e:
    print(f"API调用失败: {e}")
```

## 常见问题

### Q: 三个提供商的响应质量一样吗？
A: 理论上一样（同样的模型），但实际可能因为：
- 模型版本略有差异
- 推理参数调优不同
- 建议实际测试对比

### Q: 可以在运行时切换提供商吗？
A: 可以！使用 `client.switch_provider('new_provider')`

### Q: 需要修改代码才能切换吗？
A: 不需要！所有提供商使用相同的API格式，只需修改 `config.yaml`

### Q: 为什么隐私不是大问题？
A: 因为你的提示词是固定模板，只有市场数据在变化。即使被训练，也不会泄露专有策略。

### Q: 缓存是什么？
A: DeepSeek官方支持prompt缓存，重复部分只收10%费用。由于我们的提示词模板固定，缓存命中率可达90%。

### Q: 推荐哪个？
A:
- **初学者**: OpenRouter (方便，安全)
- **追求性价比**: Qwen-Plus官方 ($4/月)
- **最低成本**: DeepSeek官方+缓存 ($9/月)
