# 集成测试

本目录包含 HyperLiquid 测试网的集成测试。

## 概述

集成测试在真实的测试网环境中运行，验证：
- API 连接
- 订单执行
- 仓位管理
- 风险控制
- 完整交易流程

## 前置要求

在运行集成测试之前，请完成：

1. **配置测试网环境**
   - 参考：[集成测试准备指南](../../docs/04_testing/integration_test_setup_guide.md)
   - 生成测试钱包
   - 领取测试资金
   - 配置环境变量

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置数据库**
   ```bash
   createdb hyper_demo_testnet
   alembic upgrade head
   ```

## 运行测试

### 运行所有集成测试

```bash
pytest tests/integration/ -v -m integration
```

### 运行特定测试文件

```bash
# 测试连接
pytest tests/integration/test_hyperliquid_testnet.py -v

# 测试交易流程
pytest tests/integration/test_trading_workflow.py -v
```

### 运行特定测试类

```bash
pytest tests/integration/test_hyperliquid_testnet.py::TestHyperLiquidTestnetConnection -v
```

## 测试标记

集成测试使用 pytest 标记进行分类：

- `@pytest.mark.integration` - 所有集成测试
- `@pytest.mark.skip` - 需要真实订单的测试（默认跳过）

### 启用订单测试

一些测试会在测试网上执行真实订单，默认被跳过。要启用：

```bash
# 移除 @pytest.mark.skip 装饰器
# 或者使用 --run-orders 标志（需要自定义 pytest 配置）
```

## 测试结构

```
tests/integration/
├── README.md                        # 本文件
├── test_hyperliquid_testnet.py      # 基础连接和 API 测试
├── test_trading_workflow.py         # 完整交易流程测试
└── conftest.py                      # 共享 fixtures（待添加）
```

## 注意事项

### ⚠️ 测试网限制

- 测试网可能不稳定
- API 限流可能更严格
- 订单簿流动性较低
- 测试网可能定期重置

### 💡 最佳实践

1. **使用小额订单**
   - 最小订单量（0.001 BTC）
   - 远离市价的限价单
   - 立即撤单避免成交

2. **检查余额**
   ```bash
   python scripts/testnet/check_balance.py
   ```

3. **监控测试**
   - 启用详细日志（`-v -s`）
   - 检查测试网账户活动
   - 记录失败原因

4. **清理资源**
   - 撤销未成交订单
   - 平仓所有测试仓位
   - 清理测试数据库

## 故障排查

### 连接失败

```bash
# 测试连接
python scripts/testnet/test_connection.py

# 检查网络
ping api.hyperliquid-testnet.xyz
```

### 余额不足

```bash
# 检查余额
python scripts/testnet/check_balance.py

# 请求测试资金（通过 Discord）
# 或使用水龙头脚本
python scripts/testnet/request_testnet_funds.py
```

### 测试失败

1. 检查日志输出
2. 确认测试网服务状态
3. 验证配置文件
4. 查看详细错误信息

## 示例测试会话

```bash
# 1. 配置环境
source .env.testnet

# 2. 测试连接
python scripts/testnet/test_connection.py

# 3. 运行基础测试
pytest tests/integration/test_hyperliquid_testnet.py::TestHyperLiquidTestnetConnection -v

# 4. 检查结果
python scripts/testnet/check_balance.py
```

## 参考资料

- [集成测试准备指南](../../docs/04_testing/integration_test_setup_guide.md)
- [测试计划](../../docs/04_testing/test_plan.md)
- [HyperLiquid API 文档](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)

## 支持

遇到问题？

1. 查看[故障排查指南](../../docs/04_testing/integration_test_setup_guide.md#故障排查)
2. 检查 HyperLiquid Discord
3. 提交 Issue
