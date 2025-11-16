# HyperLiquid Testnet 配置指南

恭喜！既然 testnet faucet 已经可用，你现在可以在 **真实的 testnet 环境** 进行完整测试。

## 🎯 Testnet vs Dry-Run 对比

| 功能 | Dry-Run | Testnet |
|------|---------|---------|
| 市场数据 | ✅ 真实 Mainnet | ✅ 真实 Testnet |
| AI 决策 | ✅ 生成 | ✅ 生成 |
| 订单执行 | 🎭 模拟 | ✅ **真实订单** |
| 订单撮合 | ❌ 无 | ✅ **真实撮合** |
| 持仓管理 | 🎭 模拟 | ✅ **真实持仓** |
| 资金风险 | ✅ 零风险 | ✅ 零风险（测试币） |
| 测试完整性 | 80% | **95%** |

---

## 📋 配置步骤

### 1️⃣ 准备 Testnet 钱包

你需要一个有 testnet 代币的以太坊钱包：

#### 如果你已经有 testnet 钱包：
- ✅ 导出私钥（从 MetaMask 等钱包）
- ✅ 确认已从 faucet 领取测试代币

#### 如果需要创建新钱包：

```python
# 生成新的 testnet 钱包
from eth_account import Account

account = Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")

# 保存这个私钥，然后：
# 1. 访问 HyperLiquid testnet faucet
# 2. 使用这个地址领取测试代币
```

**Testnet Faucet 地址**：
- 访问 HyperLiquid testnet 网站
- 使用钱包地址申请测试代币

---

### 2️⃣ 配置环境变量

#### 方案 A：使用同一个 `.env` 文件（推荐）

编辑 `.env` 文件，使用你的 testnet 钱包私钥：

```bash
# HyperLiquid Testnet 配置
HYPERLIQUID_PRIVATE_KEY=0x你的testnet钱包私钥

# LLM API Keys（如果要测试 AI 决策）
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
QWEN_API_KEY=sk-your-qwen-api-key

# 数据库配置
DB_USER=trading_bot
DB_PASSWORD=your_password
```

#### 方案 B：创建专门的 testnet 配置

```bash
# 创建 .env.testnet 文件
cp .env.example .env.testnet

# 编辑 .env.testnet
HYPERLIQUID_PRIVATE_KEY=0x你的testnet钱包私钥
```

---

### 3️⃣ 修改 `config.yaml`

将环境切换到 testnet：

```yaml
# config.yaml 第 7 行
environment: 'testnet'  # ✅ 从 'dry-run' 改为 'testnet'
```

**完整的 testnet 配置段：**

```yaml
# ============================================================================
# ENVIRONMENT SELECTION
# ============================================================================
environment: 'testnet'  # ✅ 切换到 testnet

# ============================================================================
# HYPERLIQUID CONFIGURATION
# ============================================================================
hyperliquid:
  # Testnet URL 会自动使用
  mainnet_url: 'https://api.hyperliquid.xyz'
  testnet_url: 'https://api.hyperliquid-testnet.xyz'  # ✅ 会使用这个

  # 从环境变量读取私钥
  private_key: '${HYPERLIQUID_PRIVATE_KEY}'

  # 可选：子账户
  vault_address: null

  # API 设置
  timeout: 10
  max_retries: 3

  # 安全限制（建议保持较低值进行测试）
  max_position_size: 1.0
  max_leverage: 5
  max_daily_trades: 50

# ============================================================================
# TRADING CONFIGURATION
# ============================================================================
trading:
  interval_minutes: 3
  coins: ['BTC', 'ETH', 'SOL']  # Testnet 支持的币种

  # 风险管理（测试阶段建议保守）
  max_position_per_agent: 0.5
  stop_loss_percentage: 5.0
  take_profit_percentage: 10.0
```

**关键配置点**：

```yaml
# environments 段的 testnet 配置
environments:
  testnet:
    dry_run:
      enabled: false  # ✅ 关闭 dry-run，执行真实订单
    hyperliquid:
      active_url: 'testnet_url'  # ✅ 使用 testnet API
    logging:
      level: 'INFO'  # 或 'DEBUG' 查看详细日志
```

---

### 4️⃣ 验证配置

#### 测试 1：检查连接和账户信息

创建测试脚本 `test_testnet_connection.py`：

```python
#!/usr/bin/env python3
"""Test HyperLiquid Testnet connection."""

import os
from dotenv import load_dotenv
from trading_bot.data.hyperliquid_client import HyperliquidClient
from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor

# 加载环境变量
load_dotenv()

def test_connection():
    """Test testnet connection and account access."""

    # 1. 测试市场数据获取
    print("=" * 60)
    print("Testing Testnet Market Data...")
    print("=" * 60)

    client = HyperliquidClient(
        base_url="https://api.hyperliquid-testnet.xyz"
    )

    # 获取价格
    prices = client.get_all_prices()
    print(f"\n✅ Fetched {len(prices)} coin prices")

    if "BTC" in prices:
        print(f"   BTC: ${prices['BTC'].price:,.2f}")
    if "ETH" in prices:
        print(f"   ETH: ${prices['ETH'].price:,.2f}")

    # 2. 测试账户访问
    print("\n" + "=" * 60)
    print("Testing Testnet Account Access...")
    print("=" * 60)

    private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
    if not private_key:
        print("\n❌ Error: HYPERLIQUID_PRIVATE_KEY not found in .env")
        return

    # 创建执行器（testnet, 非 dry-run）
    executor = HyperLiquidExecutor(
        base_url="https://api.hyperliquid-testnet.xyz",
        private_key=private_key,
        dry_run=False  # ✅ 真实 testnet 模式
    )

    print(f"\n✅ Connected to Testnet")
    print(f"   Wallet Address: {executor.get_address()}")

    # 获取支持的资产
    assets = executor.get_supported_assets()
    print(f"\n✅ Supported assets: {len(assets)} coins")
    print(f"   First 10: {', '.join(assets[:10])}")

    print("\n" + "=" * 60)
    print("✅ All tests passed! Testnet connection successful.")
    print("=" * 60)

if __name__ == "__main__":
    test_connection()
```

运行测试：

```bash
python test_testnet_connection.py
```

预期输出：

```
============================================================
Testing Testnet Market Data...
============================================================

✅ Fetched 469 coin prices
   BTC: $106,235.50
   ETH: $3,610.85

============================================================
Testing Testnet Account Access...
============================================================

✅ Connected to Testnet
   Wallet Address: 0xYourTestnetAddress

✅ Supported assets: 220 coins
   First 10: BTC, ETH, SOL, AVAX, MATIC, ...

============================================================
✅ All tests passed! Testnet connection successful.
============================================================
```

---

### 5️⃣ 执行测试交易

#### 小额测试订单

创建 `test_testnet_trading.py`：

```python
#!/usr/bin/env python3
"""Test real trading on HyperLiquid Testnet."""

import os
from decimal import Decimal
from dotenv import load_dotenv
from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor

load_dotenv()

def test_small_trade():
    """Place a small test order on testnet."""

    private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")

    # 创建 testnet 执行器
    executor = HyperLiquidExecutor(
        base_url="https://api.hyperliquid-testnet.xyz",
        private_key=private_key,
        dry_run=False  # ⚠️ 真实交易模式
    )

    print("=" * 60)
    print("⚠️  TESTNET REAL TRADING TEST")
    print("=" * 60)
    print(f"Wallet: {executor.get_address()}")
    print()

    # 下一个小额限价单（价格设置得很低，不会成交）
    print("Placing test limit order (unlikely to fill)...")
    success, order_id, error = executor.place_order(
        coin="BTC",
        is_buy=True,
        size=Decimal("0.001"),  # 非常小的数量
        price=Decimal("10000.0"),  # 远低于市价，不会成交
        order_type="limit"
    )

    if success:
        print(f"✅ Order placed successfully!")
        print(f"   Order ID: {order_id}")
        print(f"   Coin: BTC")
        print(f"   Side: BUY")
        print(f"   Size: 0.001 BTC")
        print(f"   Price: $10,000")
        print()
        print("⚠️ This is a REAL order on testnet!")
        print("   (Price is set low so it won't fill)")

        # 取消订单
        print("\nCancelling order...")
        cancel_success, cancel_error = executor.cancel_order("BTC", order_id)

        if cancel_success:
            print("✅ Order cancelled successfully")
        else:
            print(f"❌ Failed to cancel: {cancel_error}")
    else:
        print(f"❌ Failed to place order: {error}")

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    # 二次确认
    response = input("⚠️  This will place a REAL order on testnet. Continue? (yes/no): ")
    if response.lower() == "yes":
        test_small_trade()
    else:
        print("Test cancelled")
```

运行测试：

```bash
python test_testnet_trading.py
```

---

### 6️⃣ 运行集成测试

运行集成测试套件（使用真实 testnet）：

```bash
# 运行所有集成测试（包括真实交易）
python run_integration_tests.py

# 仅运行数据收集测试（安全）
python run_integration_tests.py --file test_data_collection

# 运行交易执行测试（会执行真实订单！）
python run_integration_tests.py --file test_trading_execution
```

**⚠️ 注意**：在 testnet 模式下，`test_trading_execution.py` 会执行真实订单！

---

## 🔄 从 Testnet 切换回 Dry-Run

如果想切换回 dry-run 模式：

```yaml
# config.yaml
environment: 'dry-run'  # ✅ 切换回 dry-run
```

或者在代码中：

```python
executor = HyperLiquidExecutor(
    base_url="https://api.hyperliquid-testnet.xyz",  # 可以继续用 testnet 数据
    private_key=private_key,
    dry_run=True  # ✅ 启用 dry-run，不执行真实交易
)
```

---

## 🚦 测试流程建议

### 阶段 1：连接测试（5分钟）
- [ ] 配置 `.env` 文件
- [ ] 修改 `config.yaml` 为 testnet
- [ ] 运行 `test_testnet_connection.py`
- [ ] 确认连接成功，看到钱包地址

### 阶段 2：数据获取测试（10分钟）
- [ ] 运行 `test_data_collection` 集成测试
- [ ] 验证能获取市场数据
- [ ] 验证 K 线数据获取
- [ ] 检查数据质量

### 阶段 3：小额交易测试（15分钟）
- [ ] 检查 testnet 账户余额
- [ ] 运行 `test_testnet_trading.py`
- [ ] 下一个小额测试订单
- [ ] 验证订单创建成功
- [ ] 测试订单取消功能

### 阶段 4：完整流程测试（30分钟）
- [ ] 测试市价单
- [ ] 测试限价单
- [ ] 测试杠杆设置
- [ ] 测试持仓管理
- [ ] 测试风险控制

### 阶段 5：AI 决策测试（可选）
- [ ] 配置 LLM API keys
- [ ] 运行完整的 AI 决策周期
- [ ] 验证 AI 生成的交易信号
- [ ] 测试多 agent 协作

---

## ⚠️ 安全注意事项

### Testnet 的优势
- ✅ 使用测试代币（无价值）
- ✅ 完整测试真实交易流程
- ✅ 测试订单撮合和持仓
- ✅ 零财务风险

### Testnet 的限制
- ⚠️ Testnet 市场流动性可能较低
- ⚠️ 价格可能与 mainnet 不同
- ⚠️ 某些币种可能不可用
- ⚠️ 偶尔可能有网络不稳定

### 配置检查清单
- [ ] 确认 `config.yaml` 中 `environment: 'testnet'`
- [ ] 确认 `dry_run.enabled: false`（在 environments.testnet 段）
- [ ] 使用 testnet 钱包私钥（不是 mainnet！）
- [ ] testnet 账户有足够余额
- [ ] 设置了合理的安全限制

---

## 🆘 常见问题

### Q1: 订单为什么没有成交？
**A:** 可能原因：
- 限价单价格设置得太离谱
- Testnet 流动性不足
- 检查订单状态是否为 "pending"

### Q2: 如何检查 testnet 余额？
**A:** 可以通过 HyperLiquid testnet 网站查看，或通过 API：
```python
# 需要实现 get_account_info 方法
account_info = executor.get_account_info()
```

### Q3: 出现签名错误怎么办？
**A:** 检查：
- 私钥格式是否正确（64位十六进制）
- 是否使用了正确的钱包
- 网络连接是否正常

### Q4: 如何从 testnet 切换到 mainnet？
**A:** ⚠️ **非常危险！** 在充分测试前不要切换！
1. 备份当前配置
2. 修改 `config.yaml`: `environment: 'mainnet'`
3. 使用 mainnet 钱包私钥
4. 极度谨慎地进行小额测试

---

## 📊 测试结果记录

建议记录测试结果：

```
测试日期: 2025-XX-XX
Testnet 钱包: 0x...
初始余额: XXX USDC

测试项 | 状态 | 备注
-------|------|------
连接测试 | ✅ | 成功
数据获取 | ✅ | 469 coins
下单测试 | ✅ | Order ID: 12345
取消订单 | ✅ | 成功
市价单 | ⚠️ | 流动性不足
杠杆设置 | ✅ | 5x 成功
持仓管理 | ✅ | 正常
```

---

## 🎉 总结

现在你可以：

1. ✅ **立即开始**：配置 testnet 环境
2. ✅ **安全测试**：使用测试代币进行真实交易
3. ✅ **完整验证**：测试所有交易功能
4. ✅ **零风险**：testnet 代币无价值

**下一步**：
- 配置 `.env` 文件
- 修改 `config.yaml`
- 运行 `test_testnet_connection.py`
- 开始测试！

祝测试顺利！🚀
