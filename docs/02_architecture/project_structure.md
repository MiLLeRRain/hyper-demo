# 项目目录结构

```
hyper-demo/
├── .claude/                          # Claude Code 配置
│   └── settings.local.json
│
├── docs/                             # 📚 项目文档
│   ├── TESTNET_QUICK_START.md       # Testnet 快速开始指南
│   ├── TEST_RESULTS.md              # 测试结果报告
│   ├── COMMANDS.md                  # 快速命令参考
│   ├── TESTNET_SETUP_GUIDE.md       # Testnet 详细设置指南
│   └── 03_implementation/           # 实现文档
│       ├── phase_*.md
│       └── ...
│
├── scripts/                          # 🛠️ 实用脚本
│   ├── run_integration_tests.py     # 运行集成测试
│   ├── run_db_tests.py              # 运行数据库测试
│   ├── verify_wallet.py             # 验证钱包地址
│   └── debug_env.py                 # 调试环境变量
│
├── src/                              # 📦 源代码
│   └── trading_bot/
│       ├── __init__.py
│       ├── config.py                # 配置加载
│       ├── models/                  # 数据模型
│       │   ├── database.py
│       │   └── ...
│       ├── data/                    # 数据收集 (Phase 1)
│       │   ├── hyperliquid_client.py
│       │   └── data_collector.py
│       ├── ai/                      # AI 决策 (Phase 2)
│       │   ├── agent_manager.py
│       │   ├── prompt_builder.py
│       │   ├── decision_parser.py
│       │   └── orchestrator.py
│       ├── trading/                 # 交易执行 (Phase 3)
│       │   ├── hyperliquid_executor.py  # ⭐ 官方 SDK 集成
│       │   ├── hyperliquid_signer.py
│       │   ├── order_manager.py
│       │   ├── position_manager.py
│       │   └── trading_orchestrator.py
│       ├── risk/                    # 风险管理
│       │   └── risk_manager.py
│       └── automation/              # 自动化 (Phase 4)
│           ├── scheduler.py
│           └── ...
│
├── tests/                            # 🧪 测试
│   ├── README.md                    # 测试目录说明
│   ├── unit/                        # 单元测试
│   │   ├── test_data_client.py
│   │   ├── test_risk_manager.py
│   │   └── ...
│   ├── integration/                 # 集成测试 (DRY-RUN)
│   │   ├── test_data_collection.py
│   │   ├── test_phase2_integration.py
│   │   ├── test_trading_execution.py
│   │   └── ...
│   ├── testnet/                     # Testnet 实际测试
│   │   ├── test_testnet_connection.py    # 连接测试
│   │   ├── test_testnet_trading.py       # 完整交易测试
│   │   ├── test_order_placement.py       # 快速订单测试
│   │   └── test_wallet_activation.py     # 钱包验证
│   └── manual/                      # 手动调试脚本
│       ├── test_api_request.py
│       ├── test_tick_size.py
│       ├── test_sdk_rounding.py
│       └── test_get_tick_size.py
│
├── config.yaml                       # ⚙️ 系统配置
├── .env                             # 🔐 环境变量 (私钥等)
├── .env.example                     # .env 模板
├── requirements.txt                 # 📋 Python 依赖
├── pytest.ini                       # Pytest 配置
├── .gitignore                       # Git 忽略文件
└── README.md                        # 项目说明
```

---

## 📁 目录说明

### `/docs` - 文档
所有项目文档，包括：
- 快速开始指南
- API 文档
- 实现细节
- 测试报告

### `/scripts` - 工具脚本
日常使用的工具脚本：
- 测试运行器
- 钱包验证
- 调试工具

### `/src/trading_bot` - 核心代码
按功能模块组织：
- **data**: 市场数据收集
- **ai**: AI 决策引擎
- **trading**: 交易执行 (⭐ 使用官方 SDK)
- **risk**: 风险管理
- **automation**: 自动化和调度

### `/tests` - 测试
分为四类：
- **unit**: 单元测试（快速、隔离）
- **integration**: 集成测试（DRY-RUN、安全）
- **testnet**: Testnet 实际测试（实际下单）
- **manual**: 调试脚本（手动运行）

---

## 🚀 快速开始

### 1. 查看文档
```bash
# 快速开始
cat docs/TESTNET_QUICK_START.md

# 命令参考
cat docs/COMMANDS.md
```

### 2. 运行测试
```bash
# 集成测试（零风险）
python scripts/run_integration_tests.py --fast

# Testnet 测试
python tests/testnet/test_testnet_connection.py
python tests/testnet/test_order_placement.py
```

### 3. 验证钱包
```bash
python scripts/verify_wallet.py
```

---

## 📝 配置文件

### `.env` - 私钥和敏感信息
```bash
HYPERLIQUID_PRIVATE_KEY=your_private_key_here
DB_PASSWORD=your_db_password
```

### `config.yaml` - 系统配置
```yaml
environment: 'testnet'  # 或 'mainnet'

testnet:
  hyperliquid:
    base_url: 'https://api.hyperliquid-testnet.xyz'

mainnet:
  hyperliquid:
    base_url: 'https://api.hyperliquid.xyz'
```

---

## 🔑 关键文件

| 文件 | 用途 |
|------|------|
| `src/trading_bot/trading/hyperliquid_executor.py` | ⭐ 交易执行器（官方 SDK 集成）|
| `scripts/run_integration_tests.py` | 集成测试运行器 |
| `tests/testnet/test_order_placement.py` | 快速订单测试 |
| `tests/testnet/test_testnet_connection.py` | Testnet 连接测试 |
| `config.yaml` | 系统配置 |
| `.env` | 私钥配置 |

---

## 📊 代码组织原则

### ✅ 优点
1. **清晰分层**: 数据、AI、交易、风险分离
2. **测试隔离**: 单元、集成、实际测试分开
3. **文档完善**: 所有文档集中在 /docs
4. **工具分离**: 脚本放在 /scripts，不污染根目录

### 🎯 设计理念
- **关注点分离**: 每个模块专注一个职责
- **易于测试**: 完整的测试覆盖
- **清晰路径**: 文件位置符合直觉
- **安全优先**: 敏感信息隔离

---

## 🔗 相关文档

- [测试目录说明](tests/README.md)
- [快速命令参考](docs/COMMANDS.md)
- [Testnet 快速开始](docs/TESTNET_QUICK_START.md)
- [测试结果报告](docs/TEST_RESULTS.md)
