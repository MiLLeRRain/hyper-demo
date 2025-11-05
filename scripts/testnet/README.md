# HyperLiquid 测试网工具脚本

本目录包含用于 HyperLiquid 测试网配置和管理的实用脚本。

## 脚本列表

### 1. generate_wallet.py
生成新的测试网钱包。

**用法：**
```bash
python scripts/testnet/generate_wallet.py
```

**输出：**
- 钱包地址
- 私钥
- 自动保存到 `.env.testnet`

### 2. check_balance.py
查询测试网账户余额。

**用法：**
```bash
python scripts/testnet/check_balance.py
```

**要求：**
- 已配置 `.env.testnet`
- 已运行 `generate_wallet.py`

### 3. test_connection.py
测试与 HyperLiquid 测试网的连接。

**用法：**
```bash
python scripts/testnet/test_connection.py
```

**测试项目：**
- Info API 连接
- 签名器功能
- Executor 初始化
- 账户查询

### 4. request_testnet_funds.py
从水龙头请求测试资金。

**用法：**
```bash
python scripts/testnet/request_testnet_funds.py
```

**注意：**
- API 端点可能需要调整
- 也可以通过 Discord 手动请求

## 快速开始

按顺序运行以下脚本：

```bash
# 1. 生成钱包
python scripts/testnet/generate_wallet.py

# 2. 请求测试资金（或通过 Discord）
python scripts/testnet/request_testnet_funds.py

# 3. 检查余额
python scripts/testnet/check_balance.py

# 4. 测试连接
python scripts/testnet/test_connection.py
```

## 详细文档

完整的配置指南请参考：
[集成测试准备指南](../../docs/04_testing/integration_test_setup_guide.md)
