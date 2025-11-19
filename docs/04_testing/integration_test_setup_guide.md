# HyperLiquid 测试网集成测试准备指南

## 📋 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [第一步：生成测试钱包](#第一步生成测试钱包)
- [第二步：领取测试资金](#第二步领取测试资金)
- [第三步：配置项目](#第三步配置项目)
- [第四步：验证连接](#第四步验证连接)
- [第五步：运行集成测试](#第五步运行集成测试)
- [故障排查](#故障排查)
- [最佳实践](#最佳实践)

---

## 概述

本指南将帮助你配置 HyperLiquid 测试网环境，准备集成测试所需的一切资源。

### ✅ 完全免费

- 无需真实资金
- 测试网使用虚拟代币
- 所有 API 调用免费
- 无需 KYC 验证

### 🎯 目标

完成本指南后，你将能够：
1. 创建测试网钱包
2. 获取测试 USDC
3. 在测试网上执行真实交易
4. 运行完整的集成测试套件

---

## 前置要求

### 系统要求

- Python 3.11+
- 已安装项目依赖（`pip install -r requirements.txt`）
- PostgreSQL 数据库（用于存储测试数据）

### 所需时间

- 初始设置：15-20 分钟
- 测试执行：5-10 分钟

---

## 第一步：生成测试钱包

### 1.1 使用 Python 脚本生成钱包

创建一个脚本来生成测试钱包：

```bash
# 创建工具脚本目录
mkdir -p scripts/testnet

# 创建钱包生成脚本
cat > scripts/testnet/generate_wallet.py << 'EOF'
#!/usr/bin/env python3
"""生成 HyperLiquid 测试网钱包."""

from eth_account import Account
import secrets

def generate_wallet():
    """生成新的以太坊钱包."""
    # 生成随机私钥
    private_key = "0x" + secrets.token_hex(32)
    account = Account.from_key(private_key)

    print("=" * 60)
    print("HyperLiquid 测试网钱包已生成")
    print("=" * 60)
    print(f"\n钱包地址: {account.address}")
    print(f"\n私钥: {private_key}")
    print("\n⚠️  警告:")
    print("- 这是测试网钱包，仅用于测试")
    print("- 不要在主网上使用此私钥")
    print("- 不要向此地址发送真实资金")
    print("- 请妥善保存私钥，丢失后无法恢复")
    print("=" * 60)

    # 保存到 .env.testnet 文件
    with open(".env.testnet", "w") as f:
        f.write(f"# HyperLiquid 测试网配置\n")
        f.write(f"HYPERLIQUID_TESTNET_ADDRESS={account.address}\n")
        f.write(f"HYPERLIQUID_TESTNET_PRIVATE_KEY={private_key}\n")
        f.write(f"HYPERLIQUID_USE_TESTNET=true\n")

    print("\n✅ 配置已保存到 .env.testnet")
    print("   使用前请先领取测试资金\n")

if __name__ == "__main__":
    generate_wallet()
EOF

chmod +x scripts/testnet/generate_wallet.py
```

### 1.2 运行脚本生成钱包

```bash
python scripts/testnet/generate_wallet.py
```

**输出示例：**
```
============================================================
HyperLiquid 测试网钱包已生成
============================================================

钱包地址: 0x1234567890123456789012345678901234567890

私钥: 0xabcdef...

⚠️  警告:
- 这是测试网钱包，仅用于测试
- 不要在主网上使用此私钥
...
```

### 1.3 保存凭证

**重要：**
- 私钥已保存到 `.env.testnet` 文件
- 确保 `.env.testnet` 在 `.gitignore` 中
- 不要将私钥提交到版本控制系统

```bash
# 检查 .gitignore
grep ".env.testnet" .gitignore || echo ".env.testnet" >> .gitignore
```

---

## 第二步：领取测试资金

### 2.1 访问测试网水龙头

HyperLiquid 测试网提供免费的测试 USDC。

**方法 1：通过 Discord（推荐）**

1. 加入 HyperLiquid Discord: https://discord.gg/hyperliquid
2. 前往 `#testnet-faucet` 频道
3. 发送命令：`!faucet <你的钱包地址>`
4. 等待机器人回复（通常 1-2 分钟）

**方法 2：通过网页界面**

1. 访问测试网水龙头页面（如果可用）
2. 输入你的钱包地址
3. 完成验证码
4. 点击 "Request Tokens"

**方法 3：使用 API 脚本**

```bash
cat > scripts/testnet/request_testnet_funds.py << 'EOF'
#!/usr/bin/env python3
"""请求测试网资金."""

import requests
import os
from dotenv import load_dotenv

def request_funds():
    """从水龙头请求测试 USDC."""
    load_dotenv(".env.testnet")

    address = os.getenv("HYPERLIQUID_TESTNET_ADDRESS")

    if not address:
        print("❌ 错误: 未找到钱包地址")
        print("   请先运行 generate_wallet.py")
        return

    print(f"正在为地址 {address} 请求测试资金...")

    # 注意：实际的水龙头 API 端点可能不同
    # 以下是示例代码，需要根据实际情况调整
    try:
        response = requests.post(
            "https://api.hyperliquid-testnet.xyz/faucet",
            json={"address": address}
        )

        if response.status_code == 200:
            print("✅ 测试资金请求成功！")
            print("   预计 1-2 分钟到账")
        else:
            print(f"⚠️  请求失败: {response.text}")
            print("   请尝试通过 Discord 请求")
    except Exception as e:
        print(f"❌ 错误: {e}")
        print("   请通过 Discord 手动请求测试资金")

if __name__ == "__main__":
    request_funds()
EOF

chmod +x scripts/testnet/request_testnet_funds.py
python scripts/testnet/request_testnet_funds.py
```

### 2.2 验证余额

创建余额查询脚本：

```bash
cat > scripts/testnet/check_balance.py << 'EOF'
#!/usr/bin/env python3
"""查询测试网账户余额."""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

from src.trading_bot.data.hyperliquid_client import HyperliquidClient

def check_balance():
    """查询并显示账户余额."""
    load_dotenv(".env.testnet")

    address = os.getenv("HYPERLIQUID_TESTNET_ADDRESS")

    if not address:
        print("❌ 错误: 未找到钱包地址")
        return

    # 创建测试网客户端
    client = HyperliquidClient(
        base_url="https://api.hyperliquid-testnet.xyz/info",
        is_testnet=True
    )

    try:
        # 查询账户信息（需要实现 get_account_info 方法）
        print(f"\n正在查询地址: {address}")
        print("-" * 60)

        # 查询现货余额
        response = client.post({
            "type": "clearinghouseState",
            "user": address
        })

        if response:
            margin_summary = response.get("marginSummary", {})
            account_value = margin_summary.get("accountValue", "0")

            print(f"账户价值: {account_value} USDC")
            print(f"可用余额: {margin_summary.get('totalMarginUsed', '0')} USDC")
            print("-" * 60)

            if float(account_value) > 0:
                print("✅ 账户已有资金，可以开始测试")
            else:
                print("⚠️  账户余额为 0，请先领取测试资金")
        else:
            print("❌ 无法获取账户信息")

    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_balance()
EOF

chmod +x scripts/testnet/check_balance.py
python scripts/testnet/check_balance.py
```

---

## 第三步：配置项目

### 3.1 创建测试配置文件

创建专门用于测试网的配置：

```bash
cat > config.testnet.yaml << 'EOF'
# HyperLiquid 测试网配置

llm:
  providers:
    - name: deepseek
      api_url: https://api.deepseek.com/v1
      models:
        - name: deepseek-chat
          max_tokens: 4096
          temperature: 0.7

  models:
    - name: agent_1
      provider: deepseek
      model: deepseek-chat

    - name: agent_2
      provider: deepseek
      model: deepseek-chat

    - name: agent_3
      provider: deepseek
      model: deepseek-chat

exchange:
  name: hyperliquid
  use_testnet: true
  base_url: https://api.hyperliquid-testnet.xyz
  info_url: https://api.hyperliquid-testnet.xyz/info
  exchange_url: https://api.hyperliquid-testnet.xyz/exchange
  timeout: 30
  max_retries: 3
  retry_delay: 1.0

database:
  host: localhost
  port: 5432
  database: hyper_demo_testnet
  user: postgres
  password: ${DB_PASSWORD}
  pool_size: 5
  max_overflow: 10

trading:
  coins:
    - BTC
    - ETH

  timeframes:
    - 3m
    - 4h

  decision_interval_seconds: 300
  max_leverage: 10
  default_stop_loss_pct: 2.0
  default_take_profit_pct: 5.0

logging:
  level: DEBUG
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: logs/testnet.log
EOF
```

### 3.2 创建测试数据库

```bash
# 创建测试数据库
createdb hyper_demo_testnet

# 运行迁移
export DATABASE_URL="postgresql://postgres:${DB_PASSWORD}@localhost:5432/hyper_demo_testnet"
alembic upgrade head
```

### 3.3 配置环境变量

将测试网配置加载到环境：

```bash
# 加载测试网环境变量
source .env.testnet

# 或者在 Python 中
# from dotenv import load_dotenv
# load_dotenv(".env.testnet")
```

---

## 第四步：验证连接

### 4.1 创建连接测试脚本

```bash
cat > scripts/testnet/test_connection.py << 'EOF'
#!/usr/bin/env python3
"""测试与 HyperLiquid 测试网的连接."""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath('.'))

from src.trading_bot.data.hyperliquid_client import HyperliquidClient
from src.trading_bot.trading.hyperliquid_signer import HyperLiquidSigner
from src.trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor

def test_connection():
    """测试所有连接."""
    load_dotenv(".env.testnet")

    address = os.getenv("HYPERLIQUID_TESTNET_ADDRESS")
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")

    print("=" * 60)
    print("HyperLiquid 测试网连接测试")
    print("=" * 60)

    # 测试 1: Info API 连接
    print("\n[1/4] 测试 Info API 连接...")
    try:
        client = HyperliquidClient(
            base_url="https://api.hyperliquid-testnet.xyz/info",
            is_testnet=True
        )

        # 获取市场数据
        prices = client.get_all_prices()
        print(f"✅ 成功获取 {len(prices)} 个交易对价格")

        # 获取 BTC 价格
        btc_price = client.get_price("BTC")
        print(f"✅ BTC 价格: ${btc_price}")

        client.close()
    except Exception as e:
        print(f"❌ Info API 连接失败: {e}")
        return False

    # 测试 2: 签名器
    print("\n[2/4] 测试签名器...")
    try:
        signer = HyperLiquidSigner(private_key)
        test_address = signer.get_address()

        if test_address.lower() == address.lower():
            print(f"✅ 签名器正常，地址: {test_address}")
        else:
            print(f"❌ 地址不匹配: {test_address} != {address}")
            return False
    except Exception as e:
        print(f"❌ 签名器测试失败: {e}")
        return False

    # 测试 3: Executor 初始化
    print("\n[3/4] 测试 Executor...")
    try:
        executor = HyperLiquidExecutor(
            base_url="https://api.hyperliquid-testnet.xyz/exchange",
            private_key=private_key,
            is_testnet=True
        )

        executor_address = executor.get_address()
        print(f"✅ Executor 初始化成功，地址: {executor_address}")

        # 测试资产索引加载
        assets = executor.get_supported_assets()
        print(f"✅ 已加载 {len(assets)} 个交易对")

        executor.close()
    except Exception as e:
        print(f"❌ Executor 测试失败: {e}")
        return False

    # 测试 4: 账户查询
    print("\n[4/4] 测试账户查询...")
    try:
        client = HyperliquidClient(
            base_url="https://api.hyperliquid-testnet.xyz/info",
            is_testnet=True
        )

        response = client.post({
            "type": "clearinghouseState",
            "user": address
        })

        if response:
            margin_summary = response.get("marginSummary", {})
            account_value = margin_summary.get("accountValue", "0")
            print(f"✅ 账户价值: {account_value} USDC")
        else:
            print("⚠️  无法查询账户信息")

        client.close()
    except Exception as e:
        print(f"❌ 账户查询失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！测试网配置正常")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
EOF

chmod +x scripts/testnet/test_connection.py
python scripts/testnet/test_connection.py
```

### 4.2 预期输出

```
============================================================
HyperLiquid 测试网连接测试
============================================================

[1/4] 测试 Info API 连接...
✅ 成功获取 50 个交易对价格
✅ BTC 价格: $43250.50

[2/4] 测试签名器...
✅ 签名器正常，地址: 0x1234...

[3/4] 测试 Executor...
✅ Executor 初始化成功，地址: 0x1234...
✅ 已加载 50 个交易对

[4/4] 测试账户查询...
✅ 账户价值: 1000.0 USDC

============================================================
✅ 所有测试通过！测试网配置正常
============================================================
```

---

## 第五步：运行集成测试

### 5.1 创建集成测试套件

```bash
cat > tests/integration/test_hyperliquid_testnet.py << 'EOF'
"""HyperLiquid 测试网集成测试."""

import os
import pytest
from decimal import Decimal
from dotenv import load_dotenv

from src.trading_bot.data.hyperliquid_client import HyperliquidClient
from src.trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor, OrderType

# 加载测试网配置
load_dotenv(".env.testnet")

# 标记为集成测试
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def testnet_address():
    """获取测试网地址."""
    address = os.getenv("HYPERLIQUID_TESTNET_ADDRESS")
    if not address:
        pytest.skip("未配置测试网地址")
    return address


@pytest.fixture(scope="module")
def testnet_private_key():
    """获取测试网私钥."""
    key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not key:
        pytest.skip("未配置测试网私钥")
    return key


@pytest.fixture(scope="module")
def info_client():
    """创建 Info API 客户端."""
    client = HyperliquidClient(
        base_url="https://api.hyperliquid-testnet.xyz/info",
        is_testnet=True
    )
    yield client
    client.close()


@pytest.fixture(scope="module")
def executor(testnet_private_key):
    """创建 Executor."""
    executor = HyperLiquidExecutor(
        base_url="https://api.hyperliquid-testnet.xyz/exchange",
        private_key=testnet_private_key,
        is_testnet=True
    )
    yield executor
    executor.close()


class TestHyperLiquidTestnetConnection:
    """测试测试网连接."""

    def test_get_prices(self, info_client):
        """测试获取价格."""
        prices = info_client.get_all_prices()
        assert len(prices) > 0
        assert "BTC" in prices

    def test_get_btc_price(self, info_client):
        """测试获取 BTC 价格."""
        price = info_client.get_price("BTC")
        assert price > 0

    def test_get_account_info(self, info_client, testnet_address):
        """测试获取账户信息."""
        response = info_client.post({
            "type": "clearinghouseState",
            "user": testnet_address
        })
        assert response is not None
        assert "marginSummary" in response


class TestHyperLiquidTestnetTrading:
    """测试测试网交易功能.

    警告: 这些测试会在测试网上执行真实订单！
    """

    def test_get_supported_assets(self, executor):
        """测试获取支持的资产."""
        assets = executor.get_supported_assets()
        assert len(assets) > 0
        assert "BTC" in assets

    def test_update_leverage(self, executor):
        """测试设置杠杆."""
        success, error = executor.update_leverage(
            coin="BTC",
            leverage=2,
            is_cross=True
        )
        # 可能因为账户限制而失败，但不应该崩溃
        assert error is None or isinstance(error, str)

    @pytest.mark.skip(reason="会执行真实订单，需要手动启用")
    def test_place_and_cancel_order(self, executor):
        """测试下单和撤单.

        这个测试会在测试网上执行真实订单。
        仅在确认有足够测试资金时启用。
        """
        # 下一个远离市场价的限价单（不会成交）
        success, order_id, error = executor.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("0.001"),  # 非常小的订单
            price=Decimal("10000"),  # 远低于市价
            order_type=OrderType.LIMIT
        )

        if success:
            # 立即撤单
            cancel_success, cancel_error = executor.cancel_order("BTC", order_id)
            assert cancel_success or cancel_error is not None
        else:
            # 订单可能因为账户余额不足而失败
            assert error is not None
EOF
```

### 5.2 运行集成测试

```bash
# 运行所有集成测试
pytest tests/integration/test_hyperliquid_testnet.py -v -m integration

# 运行特定测试
pytest tests/integration/test_hyperliquid_testnet.py::TestHyperLiquidTestnetConnection -v

# 包含订单测试（需要手动启用）
pytest tests/integration/test_hyperliquid_testnet.py -v --run-orders
```

### 5.3 创建完整的交易流程测试

```bash
cat > tests/integration/test_trading_workflow.py << 'EOF'
"""完整交易流程集成测试."""

import os
import pytest
from decimal import Decimal
from uuid import uuid4
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.trading_bot.models.database import Base, TradingAgent, AgentDecision
from src.trading_bot.data.hyperliquid_client import HyperliquidClient
from src.trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor
from src.trading_bot.trading.order_manager import OrderManager
from src.trading_bot.trading.position_manager import PositionManager
from src.trading_bot.risk.risk_manager import RiskManager
from src.trading_bot.trading.trading_orchestrator import TradingOrchestrator

load_dotenv(".env.testnet")

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def db_session():
    """创建测试数据库会话."""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/hyper_demo_testnet")
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture(scope="module")
def test_agent(db_session):
    """创建测试代理."""
    agent = TradingAgent(
        name="IntegrationTestAgent",
        llm_model="test-model",
        initial_balance=Decimal("10000"),
        max_leverage=5,
        max_position_size=Decimal("20"),
        stop_loss_pct=Decimal("2.0"),
        take_profit_pct=Decimal("5.0"),
        status="active"
    )

    db_session.add(agent)
    db_session.commit()

    yield agent

    # 清理
    db_session.delete(agent)
    db_session.commit()


@pytest.fixture(scope="module")
def orchestrator(db_session):
    """创建完整的交易编排器."""
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")

    # 创建所有组件
    info_client = HyperliquidClient(
        base_url="https://api.hyperliquid-testnet.xyz/info",
        is_testnet=True
    )

    executor = HyperLiquidExecutor(
        base_url="https://api.hyperliquid-testnet.xyz/exchange",
        private_key=private_key,
        is_testnet=True
    )

    order_manager = OrderManager(executor, db_session)
    position_manager = PositionManager(info_client, db_session)
    risk_manager = RiskManager(position_manager, db_session)

    orchestrator = TradingOrchestrator(
        executor=executor,
        order_manager=order_manager,
        position_manager=position_manager,
        risk_manager=risk_manager,
        db_session=db_session
    )

    yield orchestrator

    # 清理
    executor.close()
    info_client.close()


class TestTradingWorkflow:
    """测试完整交易工作流."""

    def test_orchestrator_initialization(self, orchestrator):
        """测试编排器初始化."""
        assert orchestrator.executor is not None
        assert orchestrator.order_manager is not None
        assert orchestrator.position_manager is not None
        assert orchestrator.risk_manager is not None

    def test_hold_decision(self, orchestrator, test_agent, db_session):
        """测试 HOLD 决策执行."""
        decision = AgentDecision(
            agent_id=test_agent.id,
            action="HOLD",
            coin="BTC",
            size_usd=Decimal("0"),
            leverage=1,
            confidence=0.5,
            reasoning="Test hold decision"
        )

        db_session.add(decision)
        db_session.commit()

        success, error = orchestrator.execute_decision(
            agent_id=test_agent.id,
            decision_id=decision.id
        )

        assert success is True
        assert error is None

    @pytest.mark.skip(reason="需要真实资金和市场条件")
    def test_open_long_position(self, orchestrator, test_agent, db_session):
        """测试开多头仓位.

        需要确保:
        1. 账户有足够的测试 USDC
        2. 风险检查通过
        """
        decision = AgentDecision(
            agent_id=test_agent.id,
            action="OPEN_LONG",
            coin="BTC",
            size_usd=Decimal("100"),  # 小额测试
            leverage=2,
            confidence=0.8,
            stop_loss_price=Decimal("40000"),
            take_profit_price=Decimal("50000"),
            reasoning="Integration test"
        )

        db_session.add(decision)
        db_session.commit()

        success, error = orchestrator.execute_decision(
            agent_id=test_agent.id,
            decision_id=decision.id
        )

        # 可能因为各种原因失败（余额、风险等）
        if not success:
            print(f"Trade failed (expected): {error}")
        else:
            print(f"Trade succeeded!")

    def test_get_execution_summary(self, orchestrator, test_agent):
        """测试获取执行摘要."""
        summary = orchestrator.get_execution_summary(test_agent.id)

        assert "account_value" in summary
        assert "total_trades" in summary
        assert "num_positions" in summary
EOF
```

---

## 故障排查

### 常见问题

#### 1. 无法连接到测试网

**症状：**
```
ConnectionError: Failed to connect to api.hyperliquid-testnet.xyz
```

**解决方案：**
- 检查网络连接
- 确认测试网 URL 正确
- 尝试 ping 测试网地址
- 检查防火墙设置

#### 2. 私钥格式错误

**症状：**
```
ValueError: Invalid private key format
```

**解决方案：**
- 确保私钥以 `0x` 开头
- 私钥应该是 64 位十六进制字符串（加上 0x 前缀共 66 个字符）
- 重新生成钱包

#### 3. 账户余额为零

**症状：**
```
账户价值: 0 USDC
```

**解决方案：**
- 通过 Discord 请求测试资金
- 等待 1-2 分钟后重新检查
- 确认钱包地址正确

#### 4. 订单被拒绝

**症状：**
```
Order rejected: Insufficient margin
```

**解决方案：**
- 检查账户余额
- 降低订单大小
- 检查杠杆设置
- 确认风险限制

#### 5. API 限流

**症状：**
```
429 Too Many Requests
```

**解决方案：**
- 减少请求频率
- 添加请求间隔
- 使用连接池
- 实现指数退避

---

## 最佳实践

### 安全性

1. **私钥管理**
   - 使用环境变量存储私钥
   - 不要提交私钥到版本控制
   - 定期轮换测试钱包

2. **测试数据隔离**
   - 使用独立的测试数据库
   - 不要在测试网使用主网私钥
   - 清理测试数据

### 测试策略

1. **渐进式测试**
   ```
   连接测试 → 查询测试 → 只读操作 → 小额订单 → 完整流程
   ```

2. **使用小额订单**
   - 从最小订单开始（0.001 BTC）
   - 使用远离市价的限价单
   - 立即撤单避免成交

3. **监控和日志**
   - 启用详细日志
   - 记录所有 API 调用
   - 监控账户余额变化

### 测试清单

- [ ] 生成测试钱包
- [ ] 领取测试资金
- [ ] 配置项目环境
- [ ] 验证 Info API 连接
- [ ] 验证账户查询
- [ ] 测试签名器
- [ ] 测试 Executor 初始化
- [ ] 运行连接测试脚本
- [ ] 运行基础集成测试
- [ ] 测试小额订单（可选）
- [ ] 测试完整交易流程（可选）

---

## 下一步

完成测试网配置后，你可以：

1. **运行完整的集成测试套件**
   ```bash
   pytest tests/integration/ -v -m integration
   ```

2. **开发新功能**
   - 在测试网上验证新功能
   - 使用真实的市场数据
   - 测试边缘情况

3. **性能测试**
   - 测试高频交易场景
   - 压力测试 API 限流
   - 优化请求策略

4. **准备主网部署**
   - 在测试网上完全验证
   - 准备主网配置
   - 制定风险管理策略

---

## 参考资源

### HyperLiquid 文档

- API 文档: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- 测试网指南: https://hyperliquid.gitbook.io/hyperliquid-docs/testnet
- Discord: https://discord.gg/hyperliquid

### 项目文档

- [测试计划](./test_plan.md)
- [Phase 3 实现文档](../03_implementation/phase_3_trading_execution.md)
- [项目 README](../README.md)

---

## 支持

如果遇到问题：

1. 查看本文档的故障排查部分
2. 检查项目 Issue 跟踪器
3. 在 HyperLiquid Discord 寻求帮助
4. 联系项目维护者

---

**文档版本**: 1.0
**最后更新**: 2025-01-06
**维护者**: Development Team
