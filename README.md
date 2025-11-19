# HyperLiquid AI Trading Bot

![Tests](https://github.com/MiLLeRRain/hyper-demo/actions/workflows/tests.yml/badge.svg)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)

基于 HyperLiquid 永续合约交易所的 AI 驱动交易机器人

---

## 🎯 项目简介

这是一个完整的 AI 交易系统，使用官方 HyperLiquid Python SDK，支持：

- ✅ **多 AI 模型决策** - OpenAI, Anthropic, DeepSeek 等
- ✅ **实时市场数据** - 价格、K线、技术指标
- ✅ **自动交易执行** - 限价单、市价单、杠杆管理
- ✅ **风险管理** - 仓位控制、止损止盈
- ✅ **Testnet 测试** - 零风险测试环境
- ✅ **完整测试覆盖** - 94% 代码覆盖率

---

## 🚀 快速开始

### 方案 A: 快速测试（5分钟）

适合快速验证系统功能：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 .env（添加私钥和 API key）
cp .env.example .env
# 编辑 .env，设置：
#   HYPERLIQUID_PRIVATE_KEY=your_private_key
#   DEEPSEEK_API_KEY=your_api_key

# 3. 验证系统准备就绪
python scripts/check_readiness.py

# 4. 运行 Testnet 测试
python tests/testnet/test_llm_integration.py
```

### 方案 B: 长期运行（生产模式）

适合模拟真实交易，支持断点续传：

```bash
# 1. 安装 PostgreSQL 数据库（使用 Docker，最快捷）
scripts/setup_database.bat  # Windows
# 或
scripts/setup_database.sh   # Linux/Mac

# 2. 运行数据库迁移
alembic upgrade head

# 3. 验证完整配置
python scripts/check_readiness.py

# 4. 启动机器人（3分钟自动周期）
python tradingbot.py start

# 5. 监控运行状态
python tradingbot.py status
python tradingbot.py logs -f
```

📖 **详细指南**: [长期运行完整指南](docs/06_deployment/long_term_running_guide.md)

---

## 📁 项目结构

```
hyper-demo/
├── docs/                    # 📚 完整文档
│   ├── TESTNET_QUICK_START.md
│   ├── COMMANDS.md
│   ├── TEST_RESULTS.md
│   └── PROJECT_STRUCTURE.md
│
├── scripts/                 # 🛠️ 工具脚本
│   ├── run_integration_tests.py
│   └── verify_wallet.py
│
├── src/trading_bot/         # 📦 核心代码
│   ├── data/               # 市场数据收集
│   ├── ai/                 # AI 决策引擎
│   ├── trading/            # 交易执行 ⭐ 官方 SDK
│   ├── risk/               # 风险管理
│   └── automation/         # 自动化调度
│
└── tests/                   # 🧪 完整测试
    ├── unit/               # 单元测试
    ├── integration/        # 集成测试 (DRY-RUN)
    ├── testnet/            # Testnet 实际测试
    └── manual/             # 调试脚本
```

详细结构见 [docs/02_architecture/project_structure.md](docs/02_architecture/project_structure.md)

---

## 🧪 测试

### 推荐测试流程

```bash
# 1. 验证钱包地址
python scripts/verify_wallet.py

# 2. 测试 Testnet 连接
python tests/testnet/test_testnet_connection.py

# 3. 快速订单测试（下单→取消）
python tests/testnet/test_order_placement.py

# 4. 运行集成测试
python scripts/run_integration_tests.py --fast
```

### 测试结果

- ✅ 30/32 集成测试通过
- ✅ Testnet 订单执行成功
- ✅ 官方 SDK 集成验证
- ✅ 94% 测试覆盖率

---

## 📚 核心功能

### 1️⃣ 数据收集 (Phase 1)
- 实时价格数据（473+ 币种）
- K线数据（多时间周期）
- 技术指标计算
- 订单簿快照

### 2️⃣ AI 决策 (Phase 2)
- 多 AI 模型集成
- 智能 Prompt 构建
- 决策解析和验证
- 多 Agent 协作
- **Prompt 日志记录** (数据库存储完整交互)

### 3️⃣ 交易执行 (Phase 3) ⭐
- **官方 SDK 集成**
- 限价单 / 市价单
- 杠杆管理
- Tick size 自动处理
- **动态精度处理** (自动适配币种小数位)
- Dry-run 模式

### 4️⃣ 风险管理
- 仓位控制
- 杠杆限制
- **止损止盈** (自动挂单保护)
- 每日损失限制

### 5️⃣ 自动化 (Phase 4)
- 定时任务调度
- CLI 工具
- 监控和告警

---

## 🔑 关键特性

### ✅ 官方 SDK 集成
使用 `hyperliquid-python-sdk>=0.20.0`：
- EIP-712 签名
- 自动 tick size 处理
- 完整 API 支持

### ✅ Testnet 支持
零风险测试环境：
- 免费 testnet 代币
- 完整功能测试
- 安全的策略验证

### ✅ 完整测试
- 单元测试（快速、隔离）
- 集成测试（DRY-RUN）
- Testnet 实际测试
- 94% 代码覆盖率

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [LONG_TERM_RUNNING_GUIDE.md](docs/06_deployment/long_term_running_guide.md) | ⭐ 长期运行完整指南（断点续传） |
| [TESTNET_QUICK_START.md](docs/04_testing/testnet_quick_start.md) | Testnet 快速开始指南 |
| [LLM_INTEGRATION_GUIDE.md](docs/03_implementation/llm_integration.md) | LLM API 集成测试指南 |
| [COMMANDS.md](docs/07_operations/commands.md) | 所有命令参考 |
| [PROJECT_STRUCTURE.md](docs/02_architecture/project_structure.md) | 项目结构详解 |
| [tests/README.md](tests/README.md) | 测试目录说明 |

---

## ⚙️ 配置文件

### `.env` - 私钥配置
```bash
HYPERLIQUID_PRIVATE_KEY=your_private_key_here
```

### `config.yaml` - 系统配置
```yaml
environment: 'testnet'  # or 'mainnet'

testnet:
  hyperliquid:
    base_url: 'https://api.hyperliquid-testnet.xyz'
  risk:
    max_position_size_usdc: 1000.0
    max_leverage: 5
```

---

## 🔗 技术栈

### 核心技术
- **Python 3.12+** - 主语言
- **hyperliquid-python-sdk** - 官方交易 SDK
- **SQLAlchemy** - 数据库 ORM
- **OpenAI / DeepSeek** - AI 模型

### 数据处理
- **pandas** - 数据分析
- **pandas-ta** - 技术指标
- **numpy** - 数值计算

### 测试
- **pytest** - 测试框架
- **pytest-cov** - 覆盖率
- **pytest-asyncio** - 异步测试

### 自动化
- **APScheduler** - 任务调度
- **Click** - CLI 工具

---

## ⚠️ 风险提示

**重要提醒**：

- ⚠️ 加密货币交易涉及高风险
- ⚠️ 永续合约杠杆交易风险极高
- ⚠️ AI 交易不保证盈利
- ⚠️ 请先在 Testnet 充分测试
- ⚠️ 妥善保管私钥，切勿泄露
- ✅ 仅用于学习和研究目的

---

## 📊 开发进度

- [x] Phase 1: 数据收集 ✅
- [x] Phase 2: AI 决策 ✅
- [x] Phase 3: 交易执行 ✅ (官方 SDK)
- [x] Phase 4: 自动化 ✅
- [ ] Phase 5: Web 界面 (计划中)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 🔗 相关链接

- [HyperLiquid Testnet](https://app.hyperliquid-testnet.xyz)
- [HyperLiquid 文档](https://hyperliquid.gitbook.io)
- [官方 Python SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)
- [NoF1.ai 平台](https://nof1.ai/)

---

**快速开始**: `python tests/testnet/test_order_placement.py` 🚀
