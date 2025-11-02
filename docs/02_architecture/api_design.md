# REST API 设计

Web监控仪表盘的REST API端点设计（Phase 6可选功能）

---

## 1. API概述

### 1.1 基础信息
- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: API Key (Header: `X-API-Key`)
- **数据格式**: JSON
- **字符编码**: UTF-8

### 1.2 通用响应格式

**成功响应**:
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2025-11-02T12:34:56Z"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": { ... }
  },
  "timestamp": "2025-11-02T12:34:56Z"
}
```

---

## 2. Bot控制端点

### 2.1 启动交易机器人
```
POST /api/v1/bot/start
```

**请求体**: 无

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "starting",
    "message": "Trading bot is starting..."
  }
}
```

---

### 2.2 停止交易机器人
```
POST /api/v1/bot/stop
```

**请求体**: 无

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "stopped",
    "message": "Trading bot stopped successfully"
  }
}
```

---

### 2.3 获取运行状态
```
GET /api/v1/bot/status
```

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "running",
    "uptime_seconds": 3600,
    "last_cycle": "2025-11-02T12:34:56Z",
    "cycle_count": 142,
    "total_trades": 45,
    "win_rate": 0.5845,
    "total_pnl_pct": 0.1234
  }
}
```

---

## 3. 数据查询端点

### 3.1 获取当前持仓
```
GET /api/v1/positions
```

**响应**:
```json
{
  "success": true,
  "data": {
    "positions": [
      {
        "coin": "BTC",
        "side": "LONG",
        "size": 0.01,
        "entry_price": 95000.0,
        "current_price": 95420.0,
        "unrealized_pnl": 4.20,
        "unrealized_pnl_pct": 0.0044,
        "leverage": 5,
        "liquidation_price": 91000.0,
        "stop_loss": 93500.0,
        "take_profit": 98000.0
      }
    ],
    "total_unrealized_pnl": 4.20,
    "account_balance": 10004.20
  }
}
```

---

### 3.2 获取交易历史
```
GET /api/v1/trades?limit=20&offset=0
```

**Query参数**:
- `limit` (可选): 返回数量，默认20
- `offset` (可选): 偏移量，默认0
- `coin` (可选): 筛选币种

**响应**:
```json
{
  "success": true,
  "data": {
    "trades": [
      {
        "id": 123,
        "coin": "BTC",
        "side": "BUY",
        "order_type": "MARKET",
        "size": 0.01,
        "price": 95000.0,
        "status": "FILLED",
        "created_at": "2025-11-02T12:00:00Z",
        "filled_at": "2025-11-02T12:00:05Z"
      }
    ],
    "total": 142,
    "limit": 20,
    "offset": 0
  }
}
```

---

### 3.3 获取AI对话历史
```
GET /api/v1/conversations?limit=10
```

**Query参数**:
- `limit` (可选): 返回数量，默认10

**响应**:
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "id": 456,
        "timestamp": "2025-11-02T12:34:56Z",
        "prompt_length": 11053,
        "decisions": [
          {
            "coin": "BTC",
            "action": "OPEN_LONG",
            "reasoning": "EMA golden cross + RSI oversold"
          }
        ],
        "risk_assessment": "Medium",
        "market_sentiment": "Bullish"
      }
    ]
  }
}
```

---

### 3.4 获取实时价格
```
GET /api/v1/crypto-prices
```

**响应**:
```json
{
  "success": true,
  "data": {
    "prices": {
      "BTC": {
        "price": 95420.50,
        "change_24h_pct": 0.0234,
        "volume_24h": 1234567890,
        "timestamp": "2025-11-02T12:34:56Z"
      },
      "ETH": { ... },
      "SOL": { ... },
      "BNB": { ... },
      "DOGE": { ... },
      "XRP": { ... }
    }
  }
}
```

---

## 4. 配置管理端点

### 4.1 获取配置
```
GET /api/v1/config
```

**响应**:
```json
{
  "success": true,
  "data": {
    "trading": {
      "coins": ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"],
      "cycle_interval_minutes": 3,
      "enable_auto_trading": true
    },
    "risk": {
      "max_position_size_usd": 2000,
      "max_leverage": 10,
      "stop_loss_pct": 0.15,
      "max_drawdown_pct": 0.30
    }
  }
}
```

---

### 4.2 更新配置
```
PUT /api/v1/config
```

**请求体**:
```json
{
  "risk": {
    "max_leverage": 8
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "message": "Configuration updated successfully",
    "updated_fields": ["risk.max_leverage"]
  }
}
```

**注意**:
- 需要重启Bot才能生效
- 部分配置（如API密钥）不允许通过API修改

---

## 5. WebSocket端点（实时数据推送）

### 5.1 连接
```
WS /api/v1/ws
```

### 5.2 订阅事件

**客户端订阅**:
```json
{
  "action": "subscribe",
  "topics": ["prices", "positions", "trades"]
}
```

**服务端推送 - 价格更新**:
```json
{
  "topic": "prices",
  "data": {
    "BTC": {
      "price": 95430.0,
      "timestamp": "2025-11-02T12:35:00Z"
    }
  }
}
```

**服务端推送 - 新交易**:
```json
{
  "topic": "trades",
  "data": {
    "coin": "BTC",
    "action": "OPEN_LONG",
    "size": 0.01,
    "price": 95420.0,
    "timestamp": "2025-11-02T12:35:10Z"
  }
}
```

---

## 6. 错误代码

| 错误代码 | HTTP状态码 | 说明 |
|---------|-----------|------|
| `VALIDATION_ERROR` | 400 | 请求参数验证失败 |
| `UNAUTHORIZED` | 401 | API密钥无效或缺失 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `BOT_NOT_RUNNING` | 409 | Bot未运行 |
| `BOT_ALREADY_RUNNING` | 409 | Bot已经在运行 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

---

## 7. 认证

使用API Key认证：

**请求头**:
```
X-API-Key: your-api-key-here
```

**API Key生成**:
- 通过CLI生成: `bot api-key generate`
- 存储在 `config.yaml` 或环境变量中

---

## 8. 速率限制

- 每个API Key: 100 请求/分钟
- WebSocket: 10 连接/IP

超过限制返回:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "retry_after_seconds": 60
  }
}
```

---

## 9. OpenAPI规范

完整的OpenAPI 3.0规范见 `docs/02_architecture/openapi.yaml` (TODO)

---

## 10. 参考
- `docs/02_architecture/system_overview.md`: 系统架构
- FastAPI官方文档: https://fastapi.tiangolo.com/
