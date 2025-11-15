# Tests Directory Structure

## 📁 Directory Organization

```
tests/
├── unit/                    # 单元测试 (隔离测试单个组件)
│   ├── test_data_client.py
│   ├── test_risk_manager.py
│   └── ...
│
├── integration/             # 集成测试 (测试组件协作)
│   ├── test_data_collection.py
│   ├── test_phase2_integration.py
│   ├── test_trading_execution.py
│   └── ...
│
├── testnet/                 # Testnet 实际交易测试
│   ├── test_testnet_connection.py    # 连接和数据测试
│   ├── test_testnet_trading.py       # 完整交易功能测试
│   ├── test_order_placement.py       # 快速订单测试
│   └── test_wallet_activation.py     # 钱包激活验证
│
└── manual/                  # 手动调试测试脚本
    ├── test_api_request.py           # API 请求测试
    ├── test_tick_size.py             # Tick size 测试
    ├── test_sdk_rounding.py          # SDK 四舍五入测试
    └── test_get_tick_size.py         # 获取 tick size 信息
```

---

## 🧪 测试类型说明

### Unit Tests (`unit/`)
**目的**: 测试单个组件的功能，完全隔离

**特点**:
- ✅ 使用 mock 对象
- ✅ 不依赖外部服务
- ✅ 运行速度快
- ✅ 覆盖率高

**运行方式**:
```bash
pytest tests/unit/ -v
```

---

### Integration Tests (`integration/`)
**目的**: 测试多个组件协作，验证集成点

**特点**:
- ✅ 使用真实 API 数据
- ✅ DRY-RUN 模式（不实际交易）
- ✅ 测试完整工作流
- ✅ 安全（零风险）

**运行方式**:
```bash
# 快速测试（跳过慢速测试）
python scripts/run_integration_tests.py --fast

# 完整测试
python scripts/run_integration_tests.py
```

**包含测试**:
- 数据收集模块
- AI 决策流程
- 交易执行模拟
- 风险管理
- 数据库操作

---

### Testnet Tests (`testnet/`)
**目的**: 在 HyperLiquid Testnet 上测试实际交易功能

**特点**:
- ⚠️ 实际下单（使用 testnet 代币）
- ✅ 无价值代币（安全）
- ✅ 验证完整交易流程
- ✅ 测试 SDK 集成

**运行方式**:
```bash
# 1. 连接测试（零风险）
python tests/testnet/test_testnet_connection.py

# 2. 快速订单测试（低风险 - 立即取消）
python tests/testnet/test_order_placement.py

# 3. 完整交易测试（中等风险 - 实际下单）
python tests/testnet/test_testnet_trading.py

# 4. 钱包验证
python tests/testnet/test_wallet_activation.py
```

**测试内容**:
- 市场数据获取
- 账户认证
- 订单下单/取消
- 杠杆设置
- 多币种操作

---

### Manual Tests (`manual/`)
**目的**: 手动调试和验证特定功能

**特点**:
- 🔧 调试工具
- 🔧 快速验证
- 🔧 探索性测试
- 🔧 问题排查

**使用场景**:
- 调试 API 请求
- 验证 tick size 计算
- 测试 SDK 行为
- 探索新功能

**运行方式**:
```bash
# 直接运行特定脚本
python tests/manual/test_api_request.py
python tests/manual/test_tick_size.py
```

---

## 📊 测试覆盖率

查看测试覆盖率：
```bash
# 生成 HTML 报告
pytest tests/integration/ --cov=src/trading_bot --cov-report=html

# 在浏览器中查看
start htmlcov/index.html
```

---

## 🎯 推荐测试流程

### 日常开发
```bash
# 1. 运行单元测试（快速反馈）
pytest tests/unit/ -v

# 2. 运行集成测试（验证集成）
python scripts/run_integration_tests.py --fast
```

### 发布前验证
```bash
# 1. 完整单元测试
pytest tests/unit/ -v --cov=src/trading_bot

# 2. 完整集成测试
python scripts/run_integration_tests.py

# 3. Testnet 验证
python tests/testnet/test_testnet_connection.py
python tests/testnet/test_order_placement.py
```

### Testnet 策略测试
```bash
# 1. 验证连接
python tests/testnet/test_testnet_connection.py

# 2. 快速订单测试
python tests/testnet/test_order_placement.py

# 3. 完整交易测试
python tests/testnet/test_testnet_trading.py
```

---

## ⚠️ 重要提醒

### Testnet vs Mainnet
- ✅ **Testnet**: 安全，使用无价值代币
- ⚠️ **Mainnet**: 真实资金，高风险

### 测试原则
1. 先运行单元测试
2. 再运行集成测试
3. 最后在 testnet 验证
4. 充分测试后再考虑 mainnet

### 安全建议
- 永远不要提交私钥
- 先在 testnet 充分测试
- 小额资金开始
- 持续监控

---

## 📝 配置要求

### 环境变量 (`.env`)
```bash
HYPERLIQUID_PRIVATE_KEY=your_private_key_here
```

### 系统配置 (`config.yaml`)
```yaml
environment: 'testnet'  # or 'mainnet'
```

---

## 🔗 相关文档

- [Testnet 快速开始](../docs/TESTNET_QUICK_START.md)
- [测试结果报告](../docs/TEST_RESULTS.md)
- [命令参考](../docs/COMMANDS.md)
- [Testnet 设置指南](../docs/TESTNET_SETUP_GUIDE.md)
