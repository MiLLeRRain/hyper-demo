# AI Trading System - MVP 设计方案

## 项目定位

**目标**: 复刻NoF1.ai的核心功能，实现最小可行产品(MVP)
**架构**: CLI工具 + 完整后端服务 + Web前端展示
**排除**: Telegram Bot、移动应用、桌面应用

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户接口层                             │
├─────────────────┬───────────────────────────────────────────┤
│   CLI 工具      │          Web 前端 (Next.js)                │
│  - 启动/停止    │      - 实时监控仪表盘                       │
│  - 手动交易     │      - 历史交易记录                         │
│  - 查看状态     │      - AI决策展示                          │
│  - 配置管理     │      - 性能图表                            │
└────────┬────────┴───────────────────┬───────────────────────┘
         │                            │
         │         REST API           │
         └────────────┬───────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                    核心后端服务 (FastAPI)                     │
├─────────────────────────────────────────────────────────────┤
│  API层           │  业务逻辑层       │  数据访问层            │
│  - /api/start    │  - Trading Bot   │  - Database          │
│  - /api/stop     │  - Data Collector│  - Cache (Redis)     │
│  - /api/status   │  - AI Manager    │                      │
│  - /api/trades   │  - Risk Manager  │                      │
│  - /api/positions│                  │                      │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
    ┌────┴────┐      ┌────────┴────────┐    ┌─────┴─────┐
    │HyperLiquid│     │  AI APIs        │    │ Database  │
    │  - 交易   │     │  - DeepSeek     │    │ PostgreSQL│
    │  - 数据   │     │  - Qwen         │    │ + Redis   │
    └──────────┘     └─────────────────┘    └───────────┘
```

---

## 技术栈选择

### 后端服务
```yaml
语言: Python 3.10+
Web框架: FastAPI
  - 原因: 高性能、自动API文档、异步支持
数据库: PostgreSQL + Redis
  - PostgreSQL: 交易记录、配置、历史数据
  - Redis: 实时价格缓存、任务队列
ORM: SQLAlchemy
任务调度: APScheduler
  - 3分钟定时任务
  - 后台运行
API客户端:
  - hyperliquid-python-sdk: HyperLiquid交易
  - openai: 统一LLM接口 (兼容DeepSeek/Qwen)
数据分析:
  - pandas: 数据处理
  - pandas-ta: 技术指标计算
日志: loguru
```

### CLI工具
```yaml
框架: Click / Typer
  - 命令行参数解析
  - 漂亮的输出格式
显示: Rich
  - 彩色输出
  - 进度条
  - 表格展示
配置: python-dotenv
  - 环境变量管理
```

### Web前端
```yaml
框架: Next.js 14 (App Router)
语言: TypeScript
UI库:
  - shadcn/ui: 组件库
  - TailwindCSS: 样式
图表:
  - recharts: 性能图表
  - lightweight-charts: K线图
状态管理: React Query
  - 自动缓存
  - 实时更新
实时通信:
  - Server-Sent Events (SSE)
  - 或 WebSocket (可选)
```

---

## 核心功能模块

### 1. 数据采集模块 (`data_collector.py`)

```python
class DataCollector:
    """
    负责从HyperLiquid采集市场数据
    """

    def __init__(self):
        self.info = Info()  # HyperLiquid Info API
        self.coins = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP']

    async def collect_3min_data(self, coin: str):
        """采集3分钟K线数据（最近200个）"""
        candles = self.info.candles_snapshot(
            coin=coin,
            interval='3m',
            limit=200
        )
        return self.calculate_indicators_3min(candles)

    async def collect_4h_data(self, coin: str):
        """采集4小时K线数据（最近100个）"""
        candles = self.info.candles_snapshot(
            coin=coin,
            interval='4h',
            limit=100
        )
        return self.calculate_indicators_4h(candles)

    def calculate_indicators_3min(self, candles):
        """计算3分钟级别指标"""
        df = pd.DataFrame(candles)
        df['ema_20'] = ta.ema(df['close'], length=20)
        df['rsi_7'] = ta.rsi(df['close'], length=7)
        df['rsi_14'] = ta.rsi(df['close'], length=14)
        df['macd'] = ta.macd(df['close'])
        return df.tail(10)  # 返回最新10个

    def calculate_indicators_4h(self, candles):
        """计算4小时级别指标"""
        df = pd.DataFrame(candles)
        df['ema_20'] = ta.ema(df['close'], length=20)
        df['ema_50'] = ta.ema(df['close'], length=50)
        df['atr_3'] = ta.atr(df['high'], df['low'], df['close'], length=3)
        df['atr_14'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        return df.tail(10)
```

### 2. AI决策模块 (`ai_manager.py`)

```python
class AIManager:
    """
    管理AI模型调用和决策生成
    """

    def __init__(self, provider='deepseek_chat'):
        self.llm_client = LLMClient(provider)

    def build_prompt(self, market_data, positions, account_info):
        """
        构建11,053字符的NoF1格式提示词
        """
        elapsed_minutes = self.get_elapsed_minutes()
        invocation_count = self.get_invocation_count()

        prompt = f"""
It has been {elapsed_minutes} minutes since you started trading.
The current time is {datetime.now()} and you've been invoked {invocation_count} times.

**ALL OF THE PRICE OR SIGNAL DATA BELOW IS ORDERED: OLDEST → NEWEST**

### CURRENT MARKET STATE FOR ALL COINS

{self.format_coin_data('BTC', market_data['BTC'])}
{self.format_coin_data('ETH', market_data['ETH'])}
{self.format_coin_data('SOL', market_data['SOL'])}
{self.format_coin_data('BNB', market_data['BNB'])}
{self.format_coin_data('DOGE', market_data['DOGE'])}
{self.format_coin_data('XRP', market_data['XRP'])}

### HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE

Current Total Return: {account_info['return_pct']}%
Available Cash: {account_info['cash']}
Current Account Value: {account_info['total_value']}

Current live positions: {positions}

**YOUR TASK:**
Analyze the data and output your trading decisions in JSON format...
"""
        return prompt

    async def get_decision(self, market_data, positions, account_info):
        """
        获取AI交易决策
        """
        prompt = self.build_prompt(market_data, positions, account_info)
        response = await self.llm_client.generate_decision(prompt)
        return self.parse_decision(response)

    def parse_decision(self, ai_response):
        """
        解析AI返回的JSON决策
        """
        # 提取JSON（AI可能返回markdown格式）
        json_match = re.search(r'```json\n(.*?)\n```', ai_response, re.DOTALL)
        if json_match:
            decision_json = json.loads(json_match.group(1))
        else:
            decision_json = json.loads(ai_response)

        return decision_json
```

### 3. 交易执行模块 (`trade_executor.py`)

```python
class TradeExecutor:
    """
    执行AI决策的交易操作
    """

    def __init__(self, wallet):
        self.exchange = Exchange(wallet)

    async def execute_decision(self, decision):
        """
        根据AI决策执行交易
        """
        for action in decision['actions']:
            coin = action['coin']
            operation = action['operation']  # 'open_long', 'open_short', 'close', 'hold'

            if operation == 'hold':
                continue
            elif operation == 'close':
                await self.close_position(coin)
            elif operation in ['open_long', 'open_short']:
                await self.open_position(
                    coin=coin,
                    side='long' if operation == 'open_long' else 'short',
                    size=action['size'],
                    leverage=action['leverage'],
                    stop_loss=action['stop_loss'],
                    take_profit=action['take_profit']
                )

    async def open_position(self, coin, side, size, leverage, stop_loss, take_profit):
        """
        开仓
        """
        # 设置杠杆
        await self.exchange.update_leverage(leverage, coin)

        # 市价开仓
        order = await self.exchange.market_order(
            coin=coin,
            is_buy=(side == 'long'),
            sz=size
        )

        # 设置止盈止损
        if stop_loss:
            await self.exchange.order(
                coin=coin,
                is_buy=(side == 'short'),  # 平仓方向相反
                sz=size,
                limit_px=stop_loss,
                order_type={'trigger': {'triggerPx': stop_loss, 'isMarket': True, 'tpsl': 'sl'}}
            )

        if take_profit:
            await self.exchange.order(
                coin=coin,
                is_buy=(side == 'short'),
                sz=size,
                limit_px=take_profit,
                order_type={'trigger': {'triggerPx': take_profit, 'isMarket': True, 'tpsl': 'tp'}}
            )

        return order

    async def close_position(self, coin):
        """
        平仓
        """
        position = await self.get_position(coin)
        if not position:
            return

        await self.exchange.market_order(
            coin=coin,
            is_buy=(position['side'] == 'short'),  # 平仓方向相反
            sz=abs(position['size'])
        )
```

### 4. 交易机器人主循环 (`trading_bot.py`)

```python
class TradingBot:
    """
    3分钟交易循环的主控制器
    """

    def __init__(self):
        self.data_collector = DataCollector()
        self.ai_manager = AIManager()
        self.trade_executor = TradeExecutor()
        self.is_running = False
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        """
        启动交易机器人
        """
        self.is_running = True
        logger.info("🤖 Trading Bot Started")

        # 立即执行一次
        await self.trading_loop()

        # 每3分钟执行一次
        self.scheduler.add_job(
            self.trading_loop,
            'interval',
            minutes=3,
            id='trading_loop'
        )
        self.scheduler.start()

    async def trading_loop(self):
        """
        3分钟交易循环
        """
        try:
            logger.info("📊 Starting trading cycle...")

            # 1. 采集所有币种的市场数据
            market_data = {}
            for coin in self.data_collector.coins:
                data_3min = await self.data_collector.collect_3min_data(coin)
                data_4h = await self.data_collector.collect_4h_data(coin)
                market_data[coin] = {
                    '3min': data_3min,
                    '4h': data_4h
                }

            # 2. 获取当前持仓和账户信息
            positions = await self.get_positions()
            account_info = await self.get_account_info()

            # 3. 调用AI获取决策
            decision = await self.ai_manager.get_decision(
                market_data,
                positions,
                account_info
            )

            # 4. 保存AI决策到数据库
            await self.save_decision(decision)

            # 5. 执行交易
            await self.trade_executor.execute_decision(decision)

            # 6. 记录执行结果
            logger.success("✅ Trading cycle completed")

        except Exception as e:
            logger.error(f"❌ Trading cycle failed: {e}")
            # 发送告警（可选）
            await self.send_alert(f"Trading error: {e}")

    def stop(self):
        """
        停止交易机器人
        """
        self.is_running = False
        self.scheduler.shutdown()
        logger.info("🛑 Trading Bot Stopped")
```

### 5. FastAPI后端服务 (`api_server.py`)

```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Trading System API")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局Bot实例
bot = TradingBot()

@app.post("/api/start")
async def start_bot():
    """启动交易机器人"""
    if bot.is_running:
        return {"status": "error", "message": "Bot already running"}

    await bot.start()
    return {"status": "success", "message": "Bot started"}

@app.post("/api/stop")
async def stop_bot():
    """停止交易机器人"""
    if not bot.is_running:
        return {"status": "error", "message": "Bot not running"}

    bot.stop()
    return {"status": "success", "message": "Bot stopped"}

@app.get("/api/status")
async def get_status():
    """获取机器人状态"""
    return {
        "is_running": bot.is_running,
        "uptime": bot.get_uptime(),
        "total_trades": await db.get_trade_count(),
        "current_return": await bot.get_account_info()['return_pct']
    }

@app.get("/api/positions")
async def get_positions():
    """获取当前持仓"""
    return await bot.get_positions()

@app.get("/api/trades")
async def get_trades(limit: int = 100):
    """获取历史交易"""
    return await db.get_trades(limit=limit)

@app.get("/api/conversations")
async def get_conversations(limit: int = 100):
    """获取AI对话历史（类似NoF1的/api/conversations）"""
    return await db.get_ai_conversations(limit=limit)

@app.get("/api/account")
async def get_account():
    """获取账户信息"""
    return await bot.get_account_info()

@app.get("/api/crypto-prices")
async def get_prices():
    """获取实时价格"""
    return await bot.data_collector.get_current_prices()

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时推送"""
    await websocket.accept()
    while True:
        # 每秒推送一次最新状态
        data = {
            "prices": await bot.data_collector.get_current_prices(),
            "positions": await bot.get_positions(),
            "account": await bot.get_account_info()
        }
        await websocket.send_json(data)
        await asyncio.sleep(1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 6. CLI工具 (`cli.py`)

```python
import click
from rich.console import Console
from rich.table import Table
from rich.live import Live
import requests

console = Console()
API_BASE = "http://localhost:8000"

@click.group()
def cli():
    """AI Trading System CLI"""
    pass

@cli.command()
def start():
    """启动交易机器人"""
    response = requests.post(f"{API_BASE}/api/start")
    if response.json()['status'] == 'success':
        console.print("✅ [green]Trading Bot Started![/green]")
    else:
        console.print(f"❌ [red]{response.json()['message']}[/red]")

@cli.command()
def stop():
    """停止交易机器人"""
    response = requests.post(f"{API_BASE}/api/stop")
    if response.json()['status'] == 'success':
        console.print("🛑 [yellow]Trading Bot Stopped[/yellow]")
    else:
        console.print(f"❌ [red]{response.json()['message']}[/red]")

@cli.command()
def status():
    """查看机器人状态"""
    response = requests.get(f"{API_BASE}/api/status")
    data = response.json()

    table = Table(title="Trading Bot Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Status", "🟢 Running" if data['is_running'] else "🔴 Stopped")
    table.add_row("Uptime", data['uptime'])
    table.add_row("Total Trades", str(data['total_trades']))
    table.add_row("Current Return", f"{data['current_return']}%")

    console.print(table)

@cli.command()
def positions():
    """查看当前持仓"""
    response = requests.get(f"{API_BASE}/api/positions")
    positions = response.json()

    table = Table(title="Current Positions")
    table.add_column("Coin", style="cyan")
    table.add_column("Side", style="magenta")
    table.add_column("Size", style="green")
    table.add_column("Entry", style="yellow")
    table.add_column("Current", style="yellow")
    table.add_column("PnL", style="red")

    for pos in positions:
        pnl_color = "green" if pos['unrealized_pnl'] > 0 else "red"
        table.add_row(
            pos['coin'],
            pos['side'],
            str(pos['size']),
            f"${pos['entry_price']}",
            f"${pos['current_price']}",
            f"[{pnl_color}]${pos['unrealized_pnl']}[/{pnl_color}]"
        )

    console.print(table)

@cli.command()
@click.option('--limit', default=20, help='Number of trades to show')
def trades(limit):
    """查看交易历史"""
    response = requests.get(f"{API_BASE}/api/trades?limit={limit}")
    trades = response.json()

    table = Table(title=f"Recent {limit} Trades")
    table.add_column("Time", style="cyan")
    table.add_column("Coin", style="magenta")
    table.add_column("Side", style="yellow")
    table.add_column("Price", style="green")
    table.add_column("Size", style="blue")
    table.add_column("PnL", style="red")

    for trade in trades:
        table.add_row(
            trade['timestamp'],
            trade['coin'],
            trade['side'],
            f"${trade['price']}",
            str(trade['size']),
            f"${trade['pnl']}" if trade['pnl'] else "-"
        )

    console.print(table)

@cli.command()
def monitor():
    """实时监控（持续刷新）"""
    def generate_table():
        response = requests.get(f"{API_BASE}/api/status")
        data = response.json()

        table = Table(title="Real-time Monitor")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Status", "🟢 Running" if data['is_running'] else "🔴 Stopped")
        table.add_row("Current Return", f"{data['current_return']}%")

        # 获取持仓
        pos_response = requests.get(f"{API_BASE}/api/positions")
        positions = pos_response.json()

        for pos in positions:
            pnl_color = "green" if pos['unrealized_pnl'] > 0 else "red"
            table.add_row(
                f"{pos['coin']} {pos['side']}",
                f"[{pnl_color}]${pos['unrealized_pnl']}[/{pnl_color}]"
            )

        return table

    with Live(generate_table(), refresh_per_second=1) as live:
        while True:
            live.update(generate_table())
            time.sleep(1)

if __name__ == '__main__':
    cli()
```

---

## 数据库设计

### PostgreSQL表结构

```sql
-- 交易记录表
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    coin VARCHAR(10) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'long' or 'short'
    operation VARCHAR(20) NOT NULL,  -- 'open', 'close'
    price DECIMAL(20, 8) NOT NULL,
    size DECIMAL(20, 8) NOT NULL,
    leverage INTEGER,
    pnl DECIMAL(20, 8),
    fee DECIMAL(20, 8),
    order_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'completed'
);

-- AI对话记录表
CREATE TABLE ai_conversations (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    model_id VARCHAR(50) NOT NULL,  -- 'deepseek-chat', 'qwen-plus'
    user_prompt TEXT NOT NULL,  -- 11k字符提示词
    response TEXT NOT NULL,  -- AI响应
    decision_json JSONB,  -- 解析后的决策JSON
    execution_status VARCHAR(20),  -- 'pending', 'executed', 'failed'
    invocation_count INTEGER
);

-- 持仓表
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(10) UNIQUE NOT NULL,
    side VARCHAR(10) NOT NULL,
    size DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    leverage INTEGER,
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 账户快照表（每次循环记录）
CREATE TABLE account_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_value DECIMAL(20, 8) NOT NULL,
    cash DECIMAL(20, 8) NOT NULL,
    unrealized_pnl DECIMAL(20, 8),
    realized_pnl DECIMAL(20, 8),
    return_pct DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4)
);

-- 市场数据缓存表（可选，也可以只用Redis）
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    coin VARCHAR(10) NOT NULL,
    interval VARCHAR(10) NOT NULL,  -- '3m', '4h'
    open DECIMAL(20, 8),
    high DECIMAL(20, 8),
    low DECIMAL(20, 8),
    close DECIMAL(20, 8),
    volume DECIMAL(20, 8),
    indicators JSONB  -- 存储计算的指标
);

-- 系统配置表
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 项目目录结构

```
hyper-demo/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI主程序
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── models/            # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── trade.py
│   │   │   ├── position.py
│   │   │   └── conversation.py
│   │   ├── core/              # 核心业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── data_collector.py
│   │   │   ├── ai_manager.py
│   │   │   ├── trade_executor.py
│   │   │   ├── risk_manager.py
│   │   │   └── trading_bot.py
│   │   ├── api/               # API路由
│   │   │   ├── __init__.py
│   │   │   ├── bot.py         # /api/start, /api/stop
│   │   │   ├── trading.py     # /api/trades, /api/positions
│   │   │   └── market.py      # /api/crypto-prices
│   │   └── utils/             # 工具函数
│   │       ├── __init__.py
│   │       ├── indicators.py  # 技术指标计算
│   │       └── llm_client.py  # LLM统一客户端
│   ├── requirements.txt
│   └── .env.example
│
├── cli/                        # CLI工具
│   ├── cli.py                 # Click CLI主程序
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── bot.py             # start, stop命令
│   │   ├── trading.py         # positions, trades命令
│   │   └── monitor.py         # monitor命令
│   └── requirements.txt
│
├── frontend/                   # Web前端
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx           # 主页
│   │   ├── dashboard/         # 仪表盘
│   │   │   └── page.tsx
│   │   ├── trades/            # 交易历史
│   │   │   └── page.tsx
│   │   └── conversations/     # AI对话
│   │       └── page.tsx
│   ├── components/
│   │   ├── ui/                # shadcn组件
│   │   ├── Dashboard.tsx
│   │   ├── PositionCard.tsx
│   │   ├── TradeTable.tsx
│   │   └── PriceChart.tsx
│   ├── lib/
│   │   ├── api.ts             # API调用
│   │   └── utils.ts
│   ├── package.json
│   └── next.config.js
│
├── docs/                       # 文档
├── config.example.yaml         # 配置示例
├── docker-compose.yml          # Docker编排
├── .gitignore
└── README.md
```

---

## MVP实现路线图

### Phase 1: 后端核心 (1周)
**目标**: 完成数据采集 + AI决策 + 交易执行

- [x] Day 1-2: 环境搭建
  - PostgreSQL + Redis安装
  - HyperLiquid SDK集成
  - DeepSeek/Qwen API测试

- [x] Day 3-4: 数据采集模块
  - K线数据采集
  - 技术指标计算
  - 数据库存储

- [x] Day 5-6: AI决策模块
  - 提示词构建
  - AI API调用
  - 决策解析

- [x] Day 7: 交易执行模块
  - 开平仓逻辑
  - 止盈止损设置

### Phase 2: 自动化 + API (3-4天)
**目标**: 3分钟循环 + REST API

- [x] Day 8-9: 交易机器人
  - 主循环实现
  - 定时任务
  - 错误处理

- [x] Day 10-11: FastAPI服务
  - API端点实现
  - WebSocket实时推送
  - API文档

### Phase 3: CLI工具 (2天)
**目标**: 命令行管理工具

- [x] Day 12: 基础命令
  - start/stop/status
  - positions/trades

- [x] Day 13: 高级功能
  - 实时监控
  - 配置管理

### Phase 4: Web前端 (1周)
**目标**: 可视化仪表盘

- [x] Day 14-15: 基础框架
  - Next.js项目搭建
  - API集成
  - 路由设置

- [x] Day 16-17: 核心页面
  - 仪表盘
  - 持仓展示
  - 交易历史

- [x] Day 18-19: 图表和实时数据
  - K线图
  - 性能图表
  - WebSocket连接

- [x] Day 20: UI优化
  - 响应式设计
  - 移动端适配

### Phase 5: 测试和优化 (3-5天)
**目标**: 测试网测试 + 优化

- [x] Day 21-22: 集成测试
  - 端到端测试
  - 压力测试

- [x] Day 23-24: 优化
  - 性能优化
  - 错误处理完善

- [x] Day 25: 文档
  - 部署文档
  - 使用手册

**总计: 约25天（3.5周）**

---

## 部署方案

### Docker部署（推荐）

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: trading
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # 后端API服务
  backend:
    build: ./backend
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://trading_user:${DB_PASSWORD}@postgres/trading
      REDIS_URL: redis://redis:6379
      DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY}
      QWEN_API_KEY: ${QWEN_API_KEY}
      HYPERLIQUID_PRIVATE_KEY: ${HYPERLIQUID_PRIVATE_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Web前端
  frontend:
    build: ./frontend
    depends_on:
      - backend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

volumes:
  postgres_data:
```

### 启动命令

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env填写API密钥

# 2. 启动所有服务
docker-compose up -d

# 3. 访问
# - Web界面: http://localhost:3000
# - API文档: http://localhost:8000/docs

# 4. 使用CLI
python cli/cli.py start
python cli/cli.py monitor
```

---

## 成本估算

### 开发成本
- 开发时间: 3-4周
- 人力: 1个全栈开发者

### 运行成本（月度）

| 项目 | 成本 | 说明 |
|------|------|------|
| **AI API** | $9-20 | DeepSeek-Chat + 缓存 |
| **服务器** | $5-10 | VPS (2核4G) |
| **数据库** | $0 | 自建PostgreSQL |
| **域名** | $1-2 | 可选 |
| **总计** | **$15-32/月** | |

### 交易资金
- 测试: 免费（测试网）
- 实盘最小: $100-500

---

## 风险管理

### 系统级风险控制

```python
class RiskManager:
    """风险管理模块"""

    MAX_POSITION_SIZE = 0.2  # 单币种最大20%仓位
    MAX_LEVERAGE = 10  # 最大10x杠杆
    MAX_DRAWDOWN = 0.3  # 最大30%回撤
    STOP_LOSS_PCT = 0.15  # 单笔止损15%

    def check_position_size(self, coin, size, account_value):
        """检查仓位是否超限"""
        position_value = size * price
        if position_value > account_value * self.MAX_POSITION_SIZE:
            raise PositionTooLargeError()

    def check_drawdown(self, current_value, peak_value):
        """检查回撤是否超限"""
        drawdown = (peak_value - current_value) / peak_value
        if drawdown > self.MAX_DRAWDOWN:
            self.emergency_close_all()
            raise MaxDrawdownExceededError()

    def emergency_close_all(self):
        """紧急平掉所有仓位"""
        logger.critical("🚨 Max drawdown exceeded! Closing all positions!")
        # 平仓逻辑...
```

---

## 总结

### MVP核心特性

✅ **后端完整**: FastAPI + PostgreSQL + Redis
✅ **CLI工具**: 启动/停止/监控
✅ **Web界面**: 实时仪表盘 + 交易历史
✅ **AI决策**: DeepSeek-Chat / Qwen-Plus
✅ **自动交易**: 3分钟循环
✅ **风险管理**: 止盈止损 + 仓位控制
✅ **实时监控**: WebSocket推送

### 与NoF1.ai的对比

| 功能 | NoF1.ai | 我们的MVP |
|------|---------|----------|
| AI模型 | 6个模型竞争 | DeepSeek/Qwen（可扩展） |
| 交易频率 | 每3分钟 | ✅ 相同 |
| 技术指标 | EMA/RSI/MACD/ATR | ✅ 相同 |
| Web界面 | ✅ | ✅ |
| 移动端 | ❌ | ❌ (MVP不包含) |
| Telegram | ❌ | ❌ (MVP不包含) |
| CLI工具 | ❌ | ✅ (我们的优势) |
| 完整后端 | ✅ | ✅ |

### 下一步

1. 按照Phase 1开始实现后端核心
2. 在测试网测试和验证
3. 逐步添加Web界面
4. 小资金实盘测试
5. 根据效果优化策略
