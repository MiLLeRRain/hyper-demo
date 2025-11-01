# API 设计

> TODO: 待填充REST API设计

## TODO: API端点设计

### Bot控制
- `POST /api/start` - 启动交易机器人
- `POST /api/stop` - 停止交易机器人
- `GET /api/status` - 获取运行状态

### 数据查询
- `GET /api/positions` - 获取当前持仓
- `GET /api/trades` - 获取交易历史
- `GET /api/conversations` - 获取AI对话历史
- `GET /api/crypto-prices` - 获取实时价格

### 配置管理
- `GET /api/config` - 获取配置
- `PUT /api/config` - 更新配置

---

## 参考
- OpenAPI/Swagger规范
- RESTful API设计最佳实践
