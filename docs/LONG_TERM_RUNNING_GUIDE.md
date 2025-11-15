# HyperLiquid AI Trading Bot - 长期运行指南

## 概述

本指南详细说明如何在 Testnet 上长期运行交易机器人，模拟 Mainnet 的真实运行场景。系统支持**断点续传**和**无缝重启**。

---

## 核心特性

### 1. 状态持久化 ✅
- **自动保存状态**: 所有交易决策、订单、持仓都保存到数据库
- **断点续传**: 关机/重启后自动恢复上次运行状态
- **运行统计**: 记录总运行时间、交易次数、周期数等

### 2. 自动化调度 ✅
- **3分钟周期**: 每3分钟自动执行一次完整的交易周期
- **防重叠**: 如果上一个周期未完成，不会启动新周期
- **错误恢复**: 单次失败不影响后续周期，自动继续

### 3. 数据持久化 ✅
系统会自动保存以下数据到 PostgreSQL：

| 表名 | 说明 | 用途 |
|------|------|------|
| `trading_agents` | AI 代理配置 | 保存每个 AI 代理的配置和参数 |
| `agent_decisions` | AI 决策记录 | 记录每次 AI 分析和决策内容 |
| `agent_trades` | 交易执行记录 | 记录所有订单和执行详情 |
| `agent_performance` | 性能统计 | 记录盈亏、胜率、夏普比率等 |
| `bot_state` | 系统状态 | 保存运行状态用于断点续传 |

---

## 前置要求

### 必需组件
1. **PostgreSQL 数据库** (用于状态持久化)
   - 如果没有安装，系统仍可运行但**不支持断点续传**
   - 推荐使用 Docker 快速部署

2. **Testnet 钱包** (已激活)
   - 确保已通过 faucet 领取测试币
   - 当前钱包: `0xYOUR_WALLET_ADDRESS_HERE`

3. **LLM API 密钥**
   - DeepSeek API (推荐，性价比高)
   - 或 OpenAI API

---

## 快速开始

### 方案 A: 使用数据库（完整功能，支持断点续传）

#### Step 1: 安装 PostgreSQL

**选项 1 - Docker (推荐，最快捷)**
```bash
# 启动 PostgreSQL 容器
docker run -d \
  --name trading-bot-db \
  -e POSTGRES_USER=trading_bot \
  -e POSTGRES_PASSWORD=your_secure_password \
  -e POSTGRES_DB=trading_bot \
  -p 5432:5432 \
  --restart unless-stopped \
  postgres:15

# 验证容器运行
docker ps | grep trading-bot-db
```

**选项 2 - 本地安装**
- Windows: https://www.postgresql.org/download/windows/
- 创建数据库: `createdb -U postgres trading_bot`

#### Step 2: 配置环境变量

编辑 `.env` 文件：
```bash
# HyperLiquid Testnet
HYPERLIQUID_PRIVATE_KEY=your_private_key_here
HYPERLIQUID_INFO_URL=https://api.hyperliquid-testnet.xyz/info
HYPERLIQUID_EXCHANGE_URL=https://api.hyperliquid-testnet.xyz

# LLM API (DeepSeek 推荐)
DEEPSEEK_API_KEY=sk-YOUR_DEEPSEEK_API_KEY_HERE

# 数据库配置
DB_USER=trading_bot
DB_PASSWORD=your_secure_password  # 与 Docker 命令中的密码一致
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_bot
```

#### Step 3: 运行数据库迁移
```bash
# 创建所有必需的表
alembic upgrade head
```

#### Step 4: 验证设置
```bash
# 测试数据库连接
python tests/testnet/test_database_simple.py

# 测试 LLM 集成
python tests/testnet/test_llm_integration.py
```

#### Step 5: 启动机器人（长期运行）
```bash
# 启动交易机器人
python tradingbot.py start

# 输出示例:
# ============================================================
# 🚀 Starting HyperLiquid AI Trading Bot
# ============================================================
# 📋 Loading configuration from: config.yaml
# ✅ Configuration loaded
#
# 🔧 Initializing service...
# ✅ Database initialized
# ✅ Database connection OK
# ✅ HyperLiquid API connection OK (BTC price: $96,075.00)
# ✅ Phase 1 components initialized
# ✅ Phase 2 components initialized (AI agents: 1)
# ✅ Phase 3 components initialized
# ✅ Phase 4 components initialized
# ✅ Scheduler started. Next cycle: 2025-11-15 10:03:00
# ✅ TradingBotService started successfully
# TradingBotService is running. Press Ctrl+C to stop.
```

### 方案 B: 不使用数据库（简化模式，无断点续传）

如果暂时不想安装数据库，可以跳过数据库相关步骤，但会失去以下功能：
- ❌ 断点续传（重启后丢失历史状态）
- ❌ 历史决策记录
- ❌ 性能统计分析
- ✅ 基本交易功能仍然可用

---

## 运行管理

### 启动服务
```bash
python tradingbot.py start
```

### 停止服务（优雅停止）
```bash
# 方法 1: Ctrl+C (推荐)
# 系统会等待当前交易周期完成后再停止

# 方法 2: 使用 stop 命令
python tradingbot.py stop
```

### 查看运行状态
```bash
python tradingbot.py status

# 输出示例:
# Trading Bot Status
# ==================
# Running: Yes
# Uptime: 2h 15m
# Cycle Count: 45
# Last Cycle: 2025-11-15 12:15:00
# Next Cycle: 2025-11-15 12:18:00
#
# Components:
#   ✅ Database: Connected
#   ✅ Data Collector: Ready
#   ✅ AI Orchestrator: Ready (1 agent)
#   ✅ Trading Orchestrator: Ready
#   ✅ Scheduler: Running
```

### 查看实时日志
```bash
python tradingbot.py logs -f

# 输出示例:
# 2025-11-15 12:00:00 | INFO     | scheduler | Cycle #45 starting...
# 2025-11-15 12:00:01 | INFO     | data_collector | Collecting market data for BTC, ETH, SOL...
# 2025-11-15 12:00:02 | INFO     | agent_manager | AI analyzing market (DeepSeek)...
# 2025-11-15 12:00:05 | INFO     | decision_parser | Decision: HOLD BTC (confidence: 0.65)
# 2025-11-15 12:00:05 | INFO     | cycle_executor | Cycle #45 completed (5.2s)
```

---

## 断点续传机制

### 自动保存状态
系统每次交易周期都会自动保存以下状态：

```python
{
  "service_start_time": "2025-11-15T10:00:00",  # 服务启动时间
  "cycle_count": 45,                            # 已执行周期数
  "last_cycle_time": "2025-11-15T12:15:00",    # 最后执行时间
  "last_error": null                            # 最后的错误（如有）
}
```

### 重启后自动恢复
1. **停止服务**: `Ctrl+C` 或关机
2. **重新启动**: `python tradingbot.py start`
3. **自动恢复**:
   - 从数据库加载上次的运行状态
   - 继续累计周期计数
   - 读取历史持仓和订单
   - 继续3分钟周期调度

### 示例场景
```bash
# 第一次启动
> python tradingbot.py start
✅ TradingBotService started successfully
Cycle #1 completed
Cycle #2 completed
...
Cycle #10 completed

# Ctrl+C 停止
^C
⚠️  Received interrupt signal
🛑 Shutting down gracefully...
✅ Trading bot stopped successfully

# 重新启动（可能是几小时或几天后）
> python tradingbot.py start
✅ Database initialized
📊 Loaded previous state: 10 cycles completed
✅ TradingBotService started successfully
Cycle #11 starting...  # 从第11次开始继续
```

---

## 长期运行最佳实践

### 1. 监控和日志
```bash
# 实时监控日志
python tradingbot.py logs -f

# 或者将日志保存到文件
python tradingbot.py start > bot.log 2>&1 &
tail -f bot.log
```

### 2. 定期检查（推荐每天一次）
```bash
# 检查运行状态
python tradingbot.py status

# 检查数据库统计
python tests/testnet/test_database_simple.py
```

### 3. 性能分析（推荐每周一次）
```sql
-- 查询决策统计
SELECT
    action,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence
FROM agent_decisions
GROUP BY action;

-- 查询交易统计
SELECT
    coin,
    COUNT(*) as trade_count,
    SUM(realized_pnl) as total_pnl
FROM agent_trades
WHERE status = 'CLOSED'
GROUP BY coin;

-- 查询性能指标
SELECT
    total_trades,
    winning_trades,
    win_rate,
    total_pnl,
    sharpe_ratio
FROM agent_performance
ORDER BY updated_at DESC
LIMIT 1;
```

### 4. 备份数据库（推荐每周一次）
```bash
# Docker 方式
docker exec trading-bot-db pg_dump -U trading_bot trading_bot > backup_$(date +%Y%m%d).sql

# 本地安装方式
pg_dump -U trading_bot trading_bot > backup_$(date +%Y%m%d).sql
```

### 5. 资源监控
```bash
# 监控 Docker 容器资源使用
docker stats trading-bot-db

# 监控 Python 进程
ps aux | grep tradingbot
```

---

## Windows 开机自启动（可选）

### 方法 1: 使用 Windows 任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
   - 名称: `HyperLiquid Trading Bot`
   - 触发器: 计算机启动时
   - 操作: 启动程序
   - 程序: `python`
   - 参数: `D:\trae_projs\hyper-demo\tradingbot.py start`
   - 起始于: `D:\trae_projs\hyper-demo`

### 方法 2: 使用批处理脚本

创建 `start_bot.bat`:
```batch
@echo off
cd /d D:\trae_projs\hyper-demo
python tradingbot.py start
pause
```

将此批处理文件添加到开机启动文件夹：
`C:\Users\YourName\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

---

## Testnet vs Mainnet 差异

### Testnet (当前配置)
- ✅ 零风险，使用测试代币
- ✅ 可以随意实验各种策略
- ✅ 完整的交易功能
- ⚠️ 流动性可能较低
- ⚠️ 市场行为可能与 Mainnet 不同

### 切换到 Mainnet (未来)
修改 `.env` 和 `config.yaml`:

```yaml
# config.yaml
hyperliquid:
  info_url: 'https://api.hyperliquid.xyz/info'        # 去掉 -testnet
  exchange_url: 'https://api.hyperliquid.xyz'         # 去掉 -testnet
  is_testnet: false                                    # 改为 false
```

**⚠️ 重要提醒**:
- Mainnet 使用真实资金，请谨慎操作
- 建议先在 Testnet 稳定运行至少1-2周
- 充分测试 AI 决策质量
- 设置严格的风险控制参数

---

## 故障排查

### 问题 1: 数据库连接失败
```
[ERROR] Connection failed: connection to server at "localhost", port 5432 failed
```

**解决方案**:
```bash
# 检查 Docker 容器是否运行
docker ps | grep trading-bot-db

# 如果未运行，启动它
docker start trading-bot-db

# 检查端口是否被占用
netstat -an | findstr 5432
```

### 问题 2: LLM API 调用失败
```
[ERROR] LLM API call failed: API key invalid
```

**解决方案**:
```bash
# 验证 API 密钥
echo $DEEPSEEK_API_KEY  # Linux/Mac
echo %DEEPSEEK_API_KEY%  # Windows

# 测试 API
python tests/testnet/test_llm_integration.py
```

### 问题 3: Testnet 交易失败
```
[ERROR] Order failed: insufficient balance
```

**解决方案**:
```bash
# 检查钱包余额
# 访问: https://app.hyperliquid-testnet.xyz/

# 重新领取 faucet
# 每24小时可以领取一次
```

### 问题 4: 调度器未运行
```
[WARNING] Scheduler is not running
```

**解决方案**:
```bash
# 停止并重新启动服务
python tradingbot.py stop
python tradingbot.py start

# 检查日志
python tradingbot.py logs -f
```

---

## 性能优化建议

### 1. 数据库优化
```sql
-- 为常用查询创建索引
CREATE INDEX idx_decisions_created ON agent_decisions(created_at DESC);
CREATE INDEX idx_trades_status ON agent_trades(status);
CREATE INDEX idx_trades_coin ON agent_trades(coin);
```

### 2. 日志级别调整
在 `config.yaml` 中:
```yaml
logging:
  level: 'INFO'  # 生产环境使用 INFO，调试时使用 DEBUG
  file: 'logs/trading_bot.log'
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

### 3. 连接池配置
```yaml
database:
  pool_size: 5          # 连接池大小
  max_overflow: 10      # 最大溢出连接
  pool_timeout: 30      # 连接超时（秒）
```

---

## 总结

✅ **完整支持长期运行**
- 3分钟自动周期执行
- 完整的状态持久化
- 断点续传机制
- 错误自动恢复

✅ **Testnet 安全测试**
- 零资金风险
- 完整功能验证
- 策略优化测试

✅ **随时可切换 Mainnet**
- 配置文件即可切换
- 无代码修改

---

## 下一步建议

1. **立即开始**: 使用 Docker 启动数据库，运行第一次完整周期
2. **观察1周**: 监控 AI 决策质量、交易执行情况
3. **调优参数**: 根据表现调整风险参数、仓位大小
4. **准备 Mainnet**: 在 Testnet 稳定后考虑切换到真实环境

需要帮助随时询问！
