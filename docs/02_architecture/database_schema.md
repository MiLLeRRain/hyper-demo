# 数据库设计

SQLite数据库表结构设计（Phase 6可选功能 - 用于数据持久化和Web仪表盘）

---

## 1. 数据库选择

### 1.1 开发/测试环境
- **SQLite**: 轻量级，无需独立服务，适合单机部署

### 1.2 生产环境（可选）
- **PostgreSQL**: 更强大的功能，支持并发，适合有Web界面的场景

---

## 2. 表结构设计

### 2.1 conversations (AI对话历史)

存储每次AI决策的完整对话内容

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    decisions_json TEXT,  -- JSON格式的决策列表
    risk_assessment TEXT,
    market_sentiment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp DESC)
);
```

**字段说明**:
- `id`: 主键
- `timestamp`: 对话发生时间
- `prompt`: 发送给AI的完整提示词（约11k字符）
- `response`: AI返回的原始响应
- `decisions_json`: 解析后的决策JSON
- `risk_assessment`: AI评估的风险级别
- `market_sentiment`: 市场情绪评估

**示例数据**:
```sql
INSERT INTO conversations VALUES (
    1,
    '2025-11-02 12:34:56',
    'Market Analysis Request...',  -- 11k字符省略
    '{"decisions": [...], "risk_assessment": "Medium", ...}',
    '[{"coin": "BTC", "action": "OPEN_LONG", ...}]',
    'Medium',
    'Bullish',
    '2025-11-02 12:34:58'
);
```

---

### 2.2 orders (订单历史)

存储所有订单记录

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE NOT NULL,  -- 交易所返回的订单ID
    coin TEXT NOT NULL,
    side TEXT NOT NULL,  -- BUY | SELL
    order_type TEXT NOT NULL,  -- MARKET | LIMIT
    size REAL NOT NULL,
    price REAL,  -- 限价单价格，市价单为NULL
    status TEXT NOT NULL,  -- PENDING | FILLED | PARTIALLY_FILLED | CANCELLED | REJECTED
    filled_size REAL DEFAULT 0,
    average_price REAL,
    leverage INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    filled_at DATETIME,
    INDEX idx_coin (coin),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at DESC)
);
```

**字段说明**:
- `order_id`: 交易所返回的唯一订单ID
- `size`: 订单数量（币的数量）
- `filled_size`: 已成交数量
- `average_price`: 平均成交价格

**示例数据**:
```sql
INSERT INTO orders VALUES (
    1,
    '0x1234567890abcdef',
    'BTC',
    'BUY',
    'MARKET',
    0.01,
    NULL,
    'FILLED',
    0.01,
    95420.0,
    5,
    '2025-11-02 12:35:00',
    '2025-11-02 12:35:05'
);
```

---

### 2.3 positions (持仓历史)

存储持仓的开仓和平仓记录

```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin TEXT NOT NULL,
    side TEXT NOT NULL,  -- LONG | SHORT
    entry_price REAL NOT NULL,
    exit_price REAL,
    size REAL NOT NULL,
    leverage INTEGER,
    stop_loss REAL,
    take_profit REAL,
    realized_pnl REAL,  -- 平仓后的实际盈亏
    realized_pnl_pct REAL,  -- 盈亏百分比
    opened_at DATETIME NOT NULL,
    closed_at DATETIME,
    close_reason TEXT,  -- TAKE_PROFIT | STOP_LOSS | MANUAL | AI_DECISION
    INDEX idx_coin (coin),
    INDEX idx_opened_at (opened_at DESC)
);
```

**字段说明**:
- `entry_price`: 开仓价格
- `exit_price`: 平仓价格（未平仓为NULL）
- `realized_pnl`: 实现盈亏（平仓后计算）
- `close_reason`: 平仓原因

**示例数据**:
```sql
-- 未平仓
INSERT INTO positions VALUES (
    1,
    'BTC',
    'LONG',
    95000.0,
    NULL,
    0.01,
    5,
    93500.0,
    98000.0,
    NULL,
    NULL,
    '2025-11-02 12:35:00',
    NULL,
    NULL
);

-- 已平仓
INSERT INTO positions VALUES (
    2,
    'ETH',
    'SHORT',
    3500.0,
    3450.0,
    0.1,
    3,
    3600.0,
    3400.0,
    15.0,  -- 盈利$15
    0.0143,  -- 1.43%
    '2025-11-01 10:00:00',
    '2025-11-02 08:00:00',
    'TAKE_PROFIT'
);
```

---

### 2.4 risk_events (风险事件)

记录所有风险告警和处理

```sql
CREATE TABLE risk_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,  -- POSITION_LOSS | ACCOUNT_DRAWDOWN | LEVERAGE_EXCEEDED
    severity TEXT NOT NULL,  -- WARNING | CRITICAL
    coin TEXT,  -- 涉及的币种（可为NULL）
    message TEXT NOT NULL,
    action_taken TEXT,  -- AUTO_CLOSE | STOP_TRADING | NONE
    metadata_json TEXT,  -- 额外的JSON数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_severity (severity),
    INDEX idx_created_at (created_at DESC)
);
```

**示例数据**:
```sql
INSERT INTO risk_events VALUES (
    1,
    'POSITION_LOSS',
    'CRITICAL',
    'BTC',
    'BTC loss -15.2% exceeds limit',
    'AUTO_CLOSE',
    '{"position_id": 1, "unrealized_pnl_pct": -0.152}',
    '2025-11-02 14:00:00'
);
```

---

### 2.5 bot_status (系统状态)

记录Bot运行状态

```sql
CREATE TABLE bot_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL,  -- RUNNING | STOPPED | PAUSED | ERROR
    cycle_count INTEGER DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    loss_count INTEGER DEFAULT 0,
    total_pnl REAL DEFAULT 0.0,
    max_drawdown REAL DEFAULT 0.0,
    started_at DATETIME,
    stopped_at DATETIME,
    error_message TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**注意**: 此表通常只有一条记录，表示当前状态

---

### 2.6 market_snapshots (市场快照) - 可选

存储历史市场数据，用于回测和分析

```sql
CREATE TABLE market_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    price REAL NOT NULL,
    indicators_json TEXT,  -- 所有技术指标的JSON
    open_interest REAL,
    funding_rate REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_coin_timestamp (coin, timestamp DESC)
);
```

**注意**: 此表数据量较大，建议定期清理（如只保留最近30天）

---

## 3. 索引策略

### 3.1 查询优化索引

```sql
-- conversations: 按时间倒序查询最近对话
CREATE INDEX idx_conversations_timestamp ON conversations(timestamp DESC);

-- orders: 按币种和状态筛选
CREATE INDEX idx_orders_coin ON orders(coin);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- positions: 按币种查询，按时间排序
CREATE INDEX idx_positions_coin ON positions(coin);
CREATE INDEX idx_positions_opened_at ON positions(opened_at DESC);

-- risk_events: 按严重性和时间查询
CREATE INDEX idx_risk_events_severity ON risk_events(severity);
CREATE INDEX idx_risk_events_created_at ON risk_events(created_at DESC);

-- market_snapshots: 复合索引优化时间范围查询
CREATE INDEX idx_market_snapshots_coin_timestamp ON market_snapshots(coin, timestamp DESC);
```

---

## 4. 数据库操作层 (ORM)

使用 SQLAlchemy 定义模型：

```python
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    decisions_json = Column(Text)
    risk_assessment = Column(String(50))
    market_sentiment = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_id = Column(String(100), unique=True, nullable=False)
    coin = Column(String(10), nullable=False)
    side = Column(String(10), nullable=False)
    order_type = Column(String(10), nullable=False)
    size = Column(Float, nullable=False)
    price = Column(Float)
    status = Column(String(20), nullable=False)
    filled_size = Column(Float, default=0.0)
    average_price = Column(Float)
    leverage = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    filled_at = Column(DateTime)

class Position(Base):
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True)
    coin = Column(String(10), nullable=False)
    side = Column(String(10), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    size = Column(Float, nullable=False)
    leverage = Column(Integer)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    realized_pnl = Column(Float)
    realized_pnl_pct = Column(Float)
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime)
    close_reason = Column(String(50))

# Database initialization
engine = create_engine('sqlite:///trading_bot.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
```

---

## 5. 数据保留策略

### 5.1 长期保留
- `orders`: 所有订单永久保留
- `positions`: 所有持仓记录永久保留

### 5.2 定期清理
- `conversations`: 保留最近3个月，超过后归档或删除
- `market_snapshots`: 保留最近30天（如果启用）
- `risk_events`: 保留最近6个月

### 5.3 备份策略
- 每日备份数据库文件
- 保留最近7天的备份

---

## 6. 迁移到PostgreSQL（生产环境）

将SQLite迁移到PostgreSQL的步骤：

1. 修改连接字符串：
```python
# SQLite
engine = create_engine('sqlite:///trading_bot.db')

# PostgreSQL
engine = create_engine('postgresql://user:password@localhost/trading_bot')
```

2. 数据迁移：
```bash
# 导出SQLite数据
sqlite3 trading_bot.db .dump > dump.sql

# 转换并导入PostgreSQL
# 使用工具如 pgloader 或手动调整SQL语法
```

3. 修改SQL语法差异：
   - SQLite的 `AUTOINCREMENT` → PostgreSQL的 `SERIAL`
   - JSON字段：SQLite使用 `TEXT` → PostgreSQL使用 `JSONB`

---

## 7. 性能优化建议

1. **分区表**（PostgreSQL）:
   - `conversations` 按月分区
   - `market_snapshots` 按天分区

2. **批量插入**:
   - 使用 `bulk_insert_mappings()` 而非单条插入

3. **查询缓存**:
   - 常用查询结果缓存5-60秒

4. **连接池**:
```python
engine = create_engine(
    'postgresql://...',
    pool_size=10,
    max_overflow=20
)
```

---

## 8. 参考
- SQLAlchemy文档: https://docs.sqlalchemy.org/
- `docs/02_architecture/system_overview.md`: 系统架构
- `.claude/code_standards.md`: 代码规范
