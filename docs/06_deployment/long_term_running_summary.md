# 长期运行功能总结

## 核心问题

**用户需求**: "我想在 Testnet 上长期运行一段时间，模拟 Mainnet 的长期运行效果，关机重启后能随时续上继续工作"

## 解决方案

✅ **系统已完全支持长期运行和断点续传！**

---

## 系统架构特性

### 1. 自动化调度 (Scheduler)

**位置**: `src/trading_bot/automation/scheduler.py`

**核心功能**:
```python
class TradingScheduler:
    """每3分钟自动执行交易周期"""

    # 使用 APScheduler 后台调度
    scheduler = BackgroundScheduler(
        job_defaults={
            'coalesce': True,         # 合并错过的运行
            'max_instances': 1,       # 防止重叠执行
            'misfire_grace_time': 60  # 60秒容错
        }
    )
```

**特点**:
- ⏰ 每3分钟自动触发一次完整交易周期
- 🚫 防止同时运行多个周期（max_instances=1）
- 🔄 如果系统短暂暂停，会合并错过的运行
- ⚡ 即使单次失败，也会继续下一次周期

### 2. 状态持久化 (State Manager)

**位置**: `src/trading_bot/automation/state_manager.py`

**核心功能**:
```python
class StateManager:
    """管理机器人状态持久化"""

    def save_state(self, state: Dict[str, Any]):
        """保存状态到数据库（自动调用）"""
        # 保存到 bot_state 表

    def load_state(self) -> Optional[Dict[str, Any]]:
        """启动时自动加载上次状态"""
        # 从数据库恢复
```

**保存的状态**:
- `service_start_time`: 服务首次启动时间
- `cycle_count`: 累计执行周期数
- `last_cycle_time`: 最后执行时间
- `last_error`: 最后的错误信息（如有）

### 3. 数据库持久化

**5个核心表**:

| 表名 | 作用 | 断点续传用途 |
|------|------|-------------|
| `trading_agents` | AI 代理配置 | 恢复代理设置 |
| `agent_decisions` | AI 决策历史 | 查看历史决策 |
| `agent_trades` | 交易记录 | 恢复持仓状态 |
| `agent_performance` | 性能统计 | 累计盈亏统计 |
| `bot_state` | 系统状态 | **核心**：断点续传 |

### 4. 服务生命周期管理

**位置**: `src/trading_bot/automation/trading_bot_service.py`

**启动流程**:
```python
class TradingBotService:
    def start(self):
        """启动服务"""
        # 1. 初始化数据库
        # 2. 健康检查（API、数据库）
        # 3. 初始化所有组件
        # 4. 加载上次状态（自动）
        # 5. 启动调度器
        # 6. 进入运行循环
```

**停止流程**:
```python
    def stop(self):
        """优雅停止"""
        # 1. 设置停止信号
        # 2. 等待当前周期完成
        # 3. 保存当前状态
        # 4. 关闭数据库连接
        # 5. 关闭所有资源
```

**信号处理**:
```python
# 支持 Ctrl+C 优雅停止
signal.signal(signal.SIGINT, self._signal_handler)
signal.signal(signal.SIGTERM, self._signal_handler)
```

---

## 断点续传机制

### 工作流程

#### 首次启动
```bash
> python tradingbot.py start

# 输出:
✅ Database initialized
✅ Health checks passed
✅ Phase 1-4 components initialized
✅ Scheduler started. Next cycle: 2025-11-15 10:03:00
✅ TradingBotService started successfully

# 系统开始运行
Cycle #1 completed (4.2s)
Cycle #2 completed (4.5s)
Cycle #3 completed (4.1s)
...
```

#### 手动停止
```bash
# 用户按 Ctrl+C
^C

# 输出:
⚠️  Received interrupt signal
🛑 Shutting down gracefully...
⏳ Waiting for current cycle to complete...
💾 Saving state: {cycle_count: 45, last_cycle_time: ...}
✅ Trading bot stopped successfully
```

#### 重启恢复
```bash
# 几小时或几天后重启
> python tradingbot.py start

# 输出:
✅ Database initialized
📊 Loading previous state...
   - Total cycles run: 45
   - Last run: 2025-11-15 12:00:00
   - Uptime before: 2h 15m
✅ State recovered successfully
✅ TradingBotService started successfully

# 继续从第46次开始
Cycle #46 starting...  # 继续累计
Cycle #47 completed (4.3s)
...
```

### 状态恢复内容

1. **周期计数**: 从上次停止的地方继续累计
2. **持仓状态**: 从 `agent_trades` 表恢复所有未平仓的持仓
3. **历史决策**: 所有 AI 决策都已保存，可查询分析
4. **性能统计**: 累计盈亏、胜率等指标持续更新

---

## 实际使用场景

### 场景 1: 日常维护重启
```bash
# 白天运行中
Cycle #100 completed

# 晚上需要重启电脑
Ctrl+C
# 系统优雅停止，保存状态

# 第二天早上开机
python tradingbot.py start
# 自动从 Cycle #101 继续
```

### 场景 2: 系统崩溃恢复
```bash
# 运行中突然断电/崩溃
Cycle #200 completed
# [系统崩溃]

# 重启后
python tradingbot.py start
# 数据库中有最后保存的状态（Cycle #200）
# 从 Cycle #201 开始继续
# 所有历史交易和持仓都完整保留
```

### 场景 3: 长期测试（数周）
```bash
# 第1周
Cycles #1-3360 completed  # 7天 × 24小时 × 20周期/小时

# 第2周
Cycles #3361-6720 completed

# 数据库中保存：
# - 6720次决策记录
# - 完整的交易历史
# - 累计盈亏统计
# - 可生成完整的回测报告
```

---

## 配置和使用

### 最小配置（无数据库）

```bash
# .env
HYPERLIQUID_PRIVATE_KEY=your_key
DEEPSEEK_API_KEY=your_key

# 启动
python tradingbot.py start
```

**限制**:
- ❌ 无断点续传
- ❌ 无历史记录
- ✅ 基本交易功能正常

### 完整配置（带数据库）

```bash
# 1. 启动数据库
scripts/setup_database.bat

# 2. .env
HYPERLIQUID_PRIVATE_KEY=your_key
DEEPSEEK_API_KEY=your_key
DB_PASSWORD=trading_bot_2025

# 3. 迁移
alembic upgrade head

# 4. 启动
python tradingbot.py start
```

**完整功能**:
- ✅ 断点续传
- ✅ 完整历史记录
- ✅ 性能分析
- ✅ 状态查询

---

## 监控和管理

### 查看运行状态
```bash
python tradingbot.py status

# 输出:
Running: Yes
Uptime: 2h 15m
Cycle Count: 45
Last Cycle: 2025-11-15 12:15:00
Next Cycle: 2025-11-15 12:18:00

Components:
  ✅ Database: Connected
  ✅ Data Collector: Ready
  ✅ AI Orchestrator: Ready (1 agent)
  ✅ Trading Orchestrator: Ready
  ✅ Scheduler: Running
```

### 查看实时日志
```bash
python tradingbot.py logs -f

# 输出:
2025-11-15 12:00:00 | INFO | scheduler | Cycle #45 starting...
2025-11-15 12:00:01 | INFO | data_collector | Collecting BTC, ETH, SOL...
2025-11-15 12:00:03 | INFO | agent_manager | AI decision: HOLD BTC
2025-11-15 12:00:05 | INFO | cycle_executor | Cycle #45 completed (5.2s)
```

### 数据分析
```sql
-- 查看总运行统计
SELECT
    COUNT(*) as total_decisions,
    SUM(CASE WHEN action = 'HOLD' THEN 1 ELSE 0 END) as hold_count,
    SUM(CASE WHEN action IN ('BUY', 'LONG') THEN 1 ELSE 0 END) as buy_count,
    SUM(CASE WHEN action IN ('SELL', 'SHORT') THEN 1 ELSE 0 END) as sell_count
FROM agent_decisions;

-- 查看交易统计
SELECT
    coin,
    COUNT(*) as trade_count,
    SUM(realized_pnl) as total_pnl,
    AVG(realized_pnl) as avg_pnl
FROM agent_trades
WHERE status = 'CLOSED'
GROUP BY coin;
```

---

## 对比：Testnet vs Mainnet

| 特性 | Testnet | Mainnet |
|------|---------|---------|
| 资金风险 | ✅ 零风险（测试币） | ⚠️ 真实资金 |
| 功能完整性 | ✅ 100%相同 | ✅ 100%相同 |
| 断点续传 | ✅ 支持 | ✅ 支持 |
| 数据持久化 | ✅ 支持 | ✅ 支持 |
| API 限制 | ⚠️ 可能较宽松 | ⚠️ 较严格 |
| 市场深度 | ⚠️ 较浅 | ✅ 较深 |
| 测试目的 | ✅ 验证策略 | 💰 真实交易 |

**切换方法**:
```yaml
# config.yaml
hyperliquid:
  info_url: 'https://api.hyperliquid.xyz/info'      # 去掉 -testnet
  exchange_url: 'https://api.hyperliquid.xyz'       # 去掉 -testnet
  is_testnet: false                                  # 改为 false
```

---

## 总结

### ✅ 完全满足需求

1. **长期运行** ✅
   - 每3分钟自动执行
   - 后台调度器管理
   - 无需人工干预

2. **断点续传** ✅
   - 关机重启自动恢复
   - 保留所有历史数据
   - 累计统计持续更新

3. **Testnet 模拟** ✅
   - 完整功能验证
   - 零资金风险
   - 真实市场数据

4. **随时切换 Mainnet** ✅
   - 配置文件即可切换
   - 代码无需修改
   - 建议先在 Testnet 稳定运行1-2周

### 📊 技术实现

- **状态持久化**: PostgreSQL + bot_state 表
- **自动调度**: APScheduler 3分钟周期
- **优雅停止**: 信号处理 + 等待当前周期
- **健康检查**: 启动时自动验证所有组件
- **错误恢复**: 单次失败不影响后续运行

### 🎯 推荐使用流程

1. **第1周**: Testnet 运行 + 每天检查
2. **第2周**: 继续运行 + 调优参数
3. **第3周**: 分析数据 + 评估性能
4. **第4周**: 决定是否切换 Mainnet

---

**文档**: [完整指南](LONG_TERM_RUNNING_GUIDE.md)
**脚本**: `scripts/check_readiness.py`
**测试**: `tests/testnet/test_llm_integration.py`
