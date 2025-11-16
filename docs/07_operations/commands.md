# 快速命令参考

## 🧪 测试命令

### 1. 集成测试 (推荐 - 零风险)
```bash
# 快速测试 (30秒)
python scripts/run_integration_tests.py --fast

# 完整测试 (包括性能测试)
python scripts/run_integration_tests.py
```

### 2. Testnet 连接测试 (零风险)
```bash
# 测试市场数据、账户认证、K线数据
python tests/testnet/test_testnet_connection.py
```

### 3. 快速订单测试 (低风险)
```bash
# 下单 → 立即取消 (实际下单但立即取消)
python tests/testnet/test_order_placement.py
```

### 4. 完整交易测试 (中等风险)
```bash
# 测试限价单、杠杆设置、多币种操作
python tests/testnet/test_testnet_trading.py
```

### 5. 钱包验证
```bash
# 验证私钥对应的钱包地址
python scripts/verify_wallet.py
```

---

## 📊 测试覆盖率

```bash
# 生成测试覆盖率报告
pytest tests/integration/ --cov=src/trading_bot --cov-report=html

# 查看报告 (在浏览器中打开)
start htmlcov/index.html
```

---

## 🔍 单元测试

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行特定模块测试
pytest tests/unit/test_data_client.py -v
pytest tests/unit/test_risk_manager.py -v
```

---

## 🛠️ 开发工具

### 代码格式化
```bash
# 自动格式化代码
black src/ tests/

# 检查导入顺序
isort src/ tests/

# 代码质量检查
pylint src/
mypy src/
```

### 依赖管理
```bash
# 安装所有依赖
pip install -r requirements.txt

# 查看已安装包
pip list

# 查看特定包信息
pip show hyperliquid-python-sdk
```

---

## 📝 配置文件

### .env (私钥配置)
```bash
# 编辑环境变量
notepad .env

# 必需配置:
HYPERLIQUID_PRIVATE_KEY=your_private_key_here
```

### config.yaml (系统配置)
```bash
# 编辑配置文件
notepad config.yaml

# 切换到 testnet:
environment: 'testnet'

# 切换到 mainnet (谨慎):
environment: 'mainnet'
```

---

## 🚀 运行交易机器人

```bash
# DRY-RUN 模式 (模拟交易)
# 修改 config.yaml:
dry_run:
  enabled: true

# 运行机器人 (TODO: 实现主程序)
python main.py
```

---

## 📦 数据库管理

```bash
# 初始化数据库
alembic upgrade head

# 创建新的迁移
alembic revision --autogenerate -m "description"

# 查看迁移历史
alembic history

# 回滚迁移
alembic downgrade -1
```

---

## 🐛 调试命令

### 查看日志
```bash
# 实时查看日志 (如果有日志文件)
tail -f logs/trading_bot.log
```

### Python 调试
```bash
# 交互式 Python
python

# 导入模块测试
>>> import sys
>>> sys.path.insert(0, 'src')
>>> from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor
>>> # 测试代码...
```

### 环境检查
```bash
# Python 版本
python --version

# 已安装包版本
pip freeze

# 检查特定模块
python -c "import hyperliquid; print(hyperliquid.__version__)"
```

---

## 🎯 常用组合

### 完整验证流程
```bash
# 1. 验证钱包
python scripts/verify_wallet.py

# 2. 测试连接
python tests/testnet/test_testnet_connection.py

# 3. 快速订单测试
python tests/testnet/test_order_placement.py

# 4. 运行集成测试
python scripts/run_integration_tests.py --fast
```

### 开发前检查
```bash
# 代码格式化
black src/ tests/

# 运行所有测试
pytest tests/ -v

# 检查覆盖率
pytest tests/ --cov=src/trading_bot --cov-report=term-missing
```

---

## 📖 文档

```bash
# 查看快速开始指南
cat TESTNET_QUICK_START.md

# 查看测试结果
cat TEST_RESULTS.md

# 查看 Testnet 设置指南
cat docs/TESTNET_SETUP_GUIDE.md
```

---

## 🔗 有用的链接

- **HyperLiquid Testnet**: https://app.hyperliquid-testnet.xyz
- **HyperLiquid Mainnet**: https://app.hyperliquid.xyz
- **官方文档**: https://hyperliquid.gitbook.io
- **官方 SDK**: https://github.com/hyperliquid-dex/hyperliquid-python-sdk

---

## ⚡ 快捷方式

### Windows
```batch
# 设置 PYTHONPATH (每次新终端需要运行)
set PYTHONPATH=D:\trae_projs\hyper-demo\src

# 或者创建 bat 文件:
# run_tests.bat
@echo off
set PYTHONPATH=%~dp0src
python scripts/run_integration_tests.py --fast
```

### Linux/Mac
```bash
# 添加到 .bashrc 或 .zshrc
export PYTHONPATH="${HOME}/projects/hyper-demo/src"

# 或者创建 alias
alias test-fast='PYTHONPATH=./src python scripts/run_integration_tests.py --fast'
alias test-testnet='python tests/testnet/test_testnet_connection.py'
```

---

**提示**: 从 `python tests/testnet/test_order_placement.py` 开始是最快的验证方式！
