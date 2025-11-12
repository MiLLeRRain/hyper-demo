# Mainnet Testing Guide (Dry-Run Mode)

本指南说明如何使用 **Mainnet 真实数据** 进行测试，但 **不执行真实交易**。

## 🎯 测试模式说明

### Dry-Run Mode（推荐用于测试）
- ✅ 使用 **真实的 Mainnet 市场数据**
- ✅ 生成 **真实的 AI 交易决策**
- ✅ 模拟订单执行（**不发送真实订单**）
- ✅ 完全安全，**不会使用真实资金**
- ✅ 可以使用真实钱包地址查看账户状态
- ⚠️ 所有交易操作都被拦截和模拟

### 与真实 Mainnet 交易的区别
| 功能 | Dry-Run | 真实 Mainnet |
|------|---------|-------------|
| 市场数据 | ✅ 真实 | ✅ 真实 |
| AI 决策 | ✅ 真实 | ✅ 真实 |
| 订单执行 | 🎭 模拟 | 💰 真实 |
| 资金使用 | ❌ 不使用 | ⚠️ 真实资金 |
| 风险 | ✅ 零风险 | ⚠️ 有风险 |

---

## 📋 配置步骤

### 1. 获取以太坊钱包私钥

HyperLiquid 使用 **EIP-712 签名认证**（不是 API Key）。

#### 方法 A：使用 MetaMask
1. 打开 MetaMask
2. 点击账户详情
3. 导出私钥（Private Key）
4. 复制私钥（64位十六进制字符串）

#### 方法 B：创建新钱包（推荐测试用）
```python
# 使用 Python 生成新钱包
from eth_account import Account

# 创建新账户
account = Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
```

⚠️ **重要提示**：
- 即使是 Dry-Run 模式，也建议使用**测试钱包**
- Dry-Run 模式下私钥仅用于：
  - 生成钱包地址
  - 获取账户信息（余额、持仓等）
  - **不会用于签署真实交易**

---

### 2. 创建 `.env` 文件

在项目根目录创建 `.env` 文件：

```bash
# 复制示例文件
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：

```bash
# HyperLiquid 配置
# ============================================================================
# 你的以太坊钱包私钥（可以带或不带 0x 前缀）
HYPERLIQUID_PRIVATE_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef

# LLM API Keys（可选，测试时可以跳过）
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
QWEN_API_KEY=sk-your-qwen-api-key

# 数据库配置（可选，测试时可以使用 SQLite）
DB_USER=trading_bot
DB_PASSWORD=your_password
```

---

### 3. 配置 `config.yaml`

确保 `config.yaml` 设置为 Dry-Run 模式：

```yaml
# 在 config.yaml 第 7 行
environment: 'dry-run'  # ✅ 设置为 dry-run

dry_run:
  enabled: true          # ✅ 启用 dry-run
  data_source: 'mainnet' # ✅ 使用 mainnet 数据

hyperliquid:
  private_key: '${HYPERLIQUID_PRIVATE_KEY}'  # ✅ 从环境变量读取
```

---

### 4. 验证配置

运行测试脚本验证配置：

```bash
# 测试数据获取（真实 API 调用）
python run_integration_tests.py --file test_data_collection

# 测试交易执行（模拟订单）
python run_integration_tests.py --file test_trading_execution
```

预期输出：
```
[OK] Executor initialized in DRY-RUN mode
   Address: 0x你的钱包地址
[OK] [DRY-RUN] Limit order placed successfully
   Order ID: 10001
   BTC BUY 0.1 @ $50,000
```

---

## 🧪 测试场景

### 场景 1：获取市场数据（真实 API）

```python
from trading_bot.data.hyperliquid_client import HyperliquidClient

# 创建客户端（不需要私钥，只读操作）
client = HyperliquidClient(base_url="https://api.hyperliquid.xyz")

# 获取所有币种价格
prices = client.get_all_prices()
print(f"BTC Price: ${prices['BTC'].price}")

# 获取 K 线数据
klines = client.get_klines("BTC", "3m", limit=30)
print(klines.tail())
```

### 场景 2：查看账户信息（需要私钥）

```python
import os
from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor

# 从环境变量读取私钥
private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")

# 创建执行器（dry-run 模式）
executor = HyperLiquidExecutor(
    base_url="https://api.hyperliquid.xyz",
    private_key=private_key,
    dry_run=True  # ✅ 重要：启用 dry-run
)

print(f"Wallet Address: {executor.get_address()}")

# 这会调用真实 API 获取账户信息
# account_info = executor.get_account_info()  # 如果实现了此方法
```

### 场景 3：模拟下单（不执行真实交易）

```python
from decimal import Decimal

# 模拟下限价单
success, order_id, error = executor.place_order(
    coin="BTC",
    is_buy=True,
    size=Decimal("0.01"),
    price=Decimal("50000.0"),
    order_type="limit"
)

if success:
    print(f"[DRY-RUN] Order placed: {order_id}")
    print("⚠️ This is a SIMULATED order, not real!")
```

---

## 🔒 安全注意事项

### Dry-Run 模式的安全保证

1. **代码级别拦截**：所有交易操作在代码层面被拦截
   ```python
   # hyperliquid_executor.py
   if self.dry_run:
       # 模拟订单，不调用真实 API
       return True, fake_order_id, None
   ```

2. **不会签署交易**：Dry-Run 模式下不会生成 EIP-712 签名

3. **不会发送交易请求**：不会调用 HyperLiquid 的交易端点

### 私钥安全

- ✅ 使用环境变量存储私钥（不要硬编码）
- ✅ `.env` 文件已在 `.gitignore` 中（不会提交到 Git）
- ✅ 建议使用测试钱包（即使是 dry-run）
- ⚠️ **绝不要**在公开代码或日志中暴露私钥

### 从 Dry-Run 切换到真实交易

如果将来想切换到真实交易（⚠️ **非常危险**）：

```yaml
# config.yaml
environment: 'mainnet'  # ⚠️ 切换到真实交易

# 或者直接在代码中
executor = HyperLiquidExecutor(
    base_url="https://api.hyperliquid.xyz",
    private_key=private_key,
    dry_run=False  # ⚠️ 关闭 dry-run = 真实交易
)
```

**⚠️ 警告**：
- 关闭 dry-run 后，所有订单都会是**真实交易**
- 会使用**真实资金**
- 有**真实的盈亏风险**
- 建议先在 Testnet 充分测试

---

## 📊 测试检查清单

使用 Mainnet Dry-Run 测试前，确认：

- [ ] 已创建 `.env` 文件并填入私钥
- [ ] `config.yaml` 中 `environment: 'dry-run'`
- [ ] `config.yaml` 中 `dry_run.enabled: true`
- [ ] 私钥是测试钱包（推荐）
- [ ] 运行集成测试成功
- [ ] 看到 `[DRY-RUN]` 标记在所有交易操作中
- [ ] 理解 Dry-Run 不会执行真实交易

---

## 🆘 常见问题

### Q1: 我需要在钱包里有资金吗？
**A:** Dry-Run 模式下不需要。你的钱包可以是空的。

### Q2: 会产生 Gas 费用吗？
**A:** 不会。Dry-Run 模式不发送任何区块链交易。

### Q3: 可以看到真实的市场数据吗？
**A:** 可以！Dry-Run 模式使用真实的 Mainnet 市场数据。

### Q4: 如何确认是 Dry-Run 模式？
**A:** 检查日志中是否有 `[DRY-RUN]` 标记：
```
INFO: Initialized HyperLiquidExecutor for 0xYourAddress [DRY-RUN MODE]
INFO: [DRY-RUN] Simulated order: BTC BUY 0.1
```

### Q5: 私钥会被用来做什么？
**A:** 在 Dry-Run 模式下，私钥仅用于：
- 生成钱包地址
- （可选）查询账户信息
- **不会用于签署或发送交易**

---

## 📝 总结

**Dry-Run + Mainnet** 是最佳的测试方式：

✅ **优点**：
- 使用真实市场数据
- 完全安全（零风险）
- 测试完整的交易逻辑
- 不需要测试网代币

⚠️ **限制**：
- 无法测试真实的订单撮合
- 无法测试滑点和流动性
- 无法测试实际的延迟

当你对系统充分了解并准备好后，可以考虑切换到 Testnet（一旦 faucet 可用）或 Mainnet（极度谨慎）。
