# LLM API 联调测试指南

## 🎯 测试目标

验证从 AI 决策到 Testnet 实际交易的完整流程：

1. ✅ 获取市场数据
2. ✅ 计算技术指标
3. ✅ 构建 AI Prompt
4. ✅ 调用 LLM API (DeepSeek)
5. ✅ 解析 AI 决策
6. ✅ 在 Testnet 执行交易

---

## 📋 前提条件

### 1. API 密钥配置

确保 `.env` 文件包含：

```bash
# HyperLiquid
HYPERLIQUID_PRIVATE_KEY=your_private_key_here

# LLM API (至少一个)
DEEPSEEK_API_KEY=your_deepseek_key
# OPENAI_API_KEY=your_openai_key  # 可选
```

### 2. Config.yaml 配置

确保 `config.yaml` 包含 agents 配置：

```yaml
environment: 'testnet'

agents:
  - name: 'DeepSeek Trader'
    enabled: true
    provider: 'deepseek'
    model: 'deepseek-chat'
    temperature: 0.7
    max_tokens: 500
```

### 3. Testnet 钱包激活

- ✅ 已领取 testnet faucet
- ✅ 钱包已激活：`0xYOUR_WALLET_ADDRESS_HERE`
- ✅ 有足够余额（949 USDC）

---

## 🚀 运行测试

### 快速测试

```bash
python tests/testnet/test_llm_integration.py
```

### 测试流程

测试会按以下步骤执行：

#### Step 1: 初始化组件
```
✓ HyperliquidClient initialized
✓ Executor initialized (Testnet)
✓ AI components initialized
```

#### Step 2: 收集市场数据
```
Collecting data for BTC...
  Current Price: $95,000.00
  K-line Data: 50 candles (15-minute)

  Technical Indicators:
    EMA(20): $94,850.00
    EMA(50): $94,500.00
    RSI: 58.25
    MACD: 125.50
```

#### Step 3: 构建 AI Prompt
```
Prompt built successfully
Prompt length: 2,450 characters

Preview:
You are an expert cryptocurrency trader analyzing BTC...
```

#### Step 4: 调用 LLM API
```
Using agent: DeepSeek Trader
Provider: deepseek
Model: deepseek-chat

Calling LLM API...
✓ LLM response received
Response length: 450 characters
```

#### Step 5: 解析决策
```
Decision parsed successfully:
  Action: BUY / SELL / HOLD
  Confidence: 75%
  Reasoning: Based on RSI < 30 and MACD crossover...
  Entry Price: $95,250.00
  Position Size: $50.00
  Stop Loss: $94,000.00
  Take Profit: $96,500.00
```

#### Step 6: 执行交易（如果不是 HOLD）
```
Executing BUY order...

Order Details:
  Type: BUY
  Size: 0.001 BTC
  Price: $95,250.00
  Market Price: $95,300.00

✓ Order placed successfully!
  Order ID: 43154123456

Cancelling test order...
✓ Order cancelled successfully
```

---

## 📊 测试结果示例

### 成功案例

```bash
======================================================================
  Test Summary
======================================================================

  [OK] LLM Integration Test Completed!

  Verified components:
    ✓ Market data collection
    ✓ AI prompt building
    ✓ LLM API call
    ✓ Decision parsing
    ✓ Testnet order execution

  Next steps:
    1. Review the AI decision quality
    2. Adjust prompt if needed
    3. Test with different market conditions
    4. Run full backtesting
```

### HOLD 决策案例

如果 AI 决定 HOLD（不交易）：

```
Decision parsed successfully:
  Action: HOLD
  Confidence: 60%
  Reasoning: Market is range-bound, waiting for clearer signal...

[INFO] Decision is HOLD - no trade to execute

This is normal - AI decided to wait for better opportunity
```

---

## 🔍 测试验证点

### ✅ 市场数据
- [ ] 获取最新 BTC 价格
- [ ] 获取 50 根 K 线数据
- [ ] 计算技术指标（EMA, RSI, MACD）

### ✅ AI 集成
- [ ] Prompt 构建正确
- [ ] LLM API 调用成功
- [ ] 响应解析成功
- [ ] 决策格式正确

### ✅ 交易执行
- [ ] 订单价格符合 tick size
- [ ] 订单成功提交
- [ ] 返回有效 Order ID
- [ ] 订单成功取消

---

## 🐛 常见问题

### 1. "No LLM API keys found"

**问题**: `.env` 文件中没有 LLM API key

**解决**:
```bash
# 添加到 .env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
```

### 2. "No active agents found"

**问题**: `config.yaml` 中没有配置 agents

**解决**:
确保 `config.yaml` 包含：
```yaml
agents:
  - name: 'DeepSeek Trader'
    enabled: true
    provider: 'deepseek'
    model: 'deepseek-chat'
```

### 3. "LLM API call failed"

**可能原因**:
- API key 无效
- 网络问题
- API 限额用完

**解决**:
1. 检查 API key 是否正确
2. 测试网络连接
3. 检查 API 使用额度

### 4. "Failed to parse decision"

**可能原因**:
- LLM 返回格式不符合预期
- LLM 返回了无效的 JSON

**解决**:
1. 查看原始 LLM 响应
2. 调整 Prompt 使其更明确
3. 增加 decision_parser 的容错性

### 5. "Price must be divisible by tick size"

**原因**: 订单价格没有对齐 tick size

**解决**:
代码已自动处理 tick size 四舍五入，如果仍出错：
- BTC tick size = $10
- ETH tick size = $1
- 确保价格是 tick size 的整数倍

---

## 📈 下一步

### 测试通过后

1. **调整 AI Prompt**
   - 优化 prompt 提高决策质量
   - 添加更多市场上下文
   - 测试不同的 temperature 值

2. **多市场测试**
   - 测试 ETH、SOL 等其他币种
   - 验证不同市场条件下的决策

3. **回测验证**
   - 使用历史数据验证策略
   - 计算胜率和收益率
   - 优化止损止盈参数

4. **风险管理**
   - 设置合理的仓位大小
   - 配置止损止盈
   - 限制单日交易次数

### 准备生产环境

1. **充分测试**
   - 在 Testnet 运行至少 1 周
   - 测试各种市场条件
   - 验证风险控制机制

2. **监控系统**
   - 设置告警
   - 记录所有决策和交易
   - 实时监控 P&L

3. **小额开始**
   - Mainnet 从小额开始
   - 逐步增加仓位
   - 持续监控和优化

---

## 💡 最佳实践

### Prompt 优化

1. **明确输出格式**
   - 要求 LLM 返回 JSON
   - 定义清晰的字段

2. **提供充分上下文**
   - 当前市场数据
   - 技术指标
   - 历史趋势

3. **设置合理约束**
   - 最大仓位限制
   - 止损止盈范围
   - 可用余额

### 测试策略

1. **多场景测试**
   - 上涨市场
   - 下跌市场
   - 横盘市场

2. **边界条件**
   - 极端价格
   - 高波动性
   - 低流动性

3. **错误处理**
   - API 超时
   - 无效响应
   - 网络错误

---

## 🔗 相关文档

- [Testnet 快速开始](TESTNET_QUICK_START.md)
- [命令参考](COMMANDS.md)
- [测试结果报告](TEST_RESULTS.md)
- [项目结构](PROJECT_STRUCTURE.md)

---

**准备好了吗？运行测试：**

```bash
python tests/testnet/test_llm_integration.py
```

🚀 开始 LLM API 联调！
