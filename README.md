# HyperLiquid AI Trading Demo

基于 NoF1.ai 的 AI 交易系统研究与实现方案

## 项目简介

本项目研究了 NoF1.ai 的 AI 交易竞技场（Alpha Arena），该平台让多个 AI 模型在 HyperLiquid 去中心化永续合约交易所上进行实盘交易竞争。

## 文档结构

```
hyper-demo/
├── docs/                                          # 文档目录
│   ├── nof1_ai_analysis.md                       # NoF1.ai 平台完整技术分析
│   ├── nof1_ai_system_prompts_and_outputs.md     # AI 系统提示词和输出格式
│   ├── hyperliquid_api_data_availability_CN.md   # HyperLiquid API 数据可用性分析
│   ├── hyperliquid_trading_api_guide_CN.md       # HyperLiquid 交易 API 完整指南
│   └── hyperliquid_margin_and_fees_CN.md         # HyperLiquid 保证金和费用文档
├── architecture/                                  # 架构设计文档
│   └── implementation_approaches.md               # 多种实现方案对比
└── README.md                                      # 本文件
```

## NoF1.ai 核心特性

- **6 个 AI 模型竞争**：GPT-5, Claude Sonnet 4.5, Gemini 2.5 Pro, Grok 4, DeepSeek Chat V3.1, Qwen3 Max
- **实盘交易**：每个模型获得 $10,000 初始资金
- **交易市场**：BTC, ETH, SOL, BNB, DOGE, XRP 永续合约
- **数据驱动**：提供 EMA, MACD, RSI, ATR 等技术指标
- **REST API 轮询**：3 分钟间隔（非 WebSocket）

## HyperLiquid 平台特点

- **去中心化永续合约交易所（DEX）**
- **链上订单簿**：运行在 HyperLiquid L1 区块链
- **高杠杆**：BTC 最高 40x，ETH 最高 25x
- **低费用**：Maker 0%-0.015%, Taker 0.024%-0.045%
- **无借贷利息**：0% 借贷费用
- **完全免费的市场数据 API**

## 实现方案

详见 [implementation_approaches.md](./architecture/implementation_approaches.md)，包括：

1. **Web 应用** (Next.js + React)
2. **桌面应用** (Electron / Tauri)
3. **命令行工具** (Python CLI)
4. **Telegram Bot**
5. **移动应用** (React Native / Flutter)
6. **纯后端服务** (FastAPI + Celery)

## 快速开始

### 前置要求

- Python 3.8+
- Node.js 16+ (如果选择 Web/桌面应用)
- HyperLiquid 账户和私钥
- AI API 密钥 (OpenAI, Anthropic, Google, etc.)

### 安装依赖

```bash
# Python 依赖
pip install hyperliquid-python-sdk pandas numpy requests

# 如果使用 Web 应用
npm install
```

### 配置

```bash
# 创建环境变量文件
cp .env.example .env

# 编辑 .env 文件，添加：
# - HyperLiquid 私钥
# - AI API 密钥
# - 其他配置参数
```

## 技术栈建议

### 后端
- **Python**: 数据处理、AI 调用、交易逻辑
- **FastAPI**: REST API 服务
- **Celery + Redis**: 定时任务和异步处理
- **PostgreSQL**: 数据存储
- **TimescaleDB**: 时序数据优化

### 前端（可选）
- **Next.js 14+**: React 框架
- **TypeScript**: 类型安全
- **TailwindCSS**: 样式
- **Recharts**: 图表可视化
- **shadcn/ui**: UI 组件库

### 部署
- **Docker + Docker Compose**: 容器化
- **Vercel / Railway**: 前端部署
- **AWS / DigitalOcean**: 后端部署

## 核心功能模块

1. **市场数据采集**
   - HyperLiquid WebSocket 实时价格
   - 技术指标计算 (EMA, MACD, RSI, ATR)
   - 开放利息和资金费率追踪

2. **AI 决策引擎**
   - 多 AI 模型集成
   - 提示词工程和上下文管理
   - 决策结果解析和验证

3. **交易执行**
   - 订单管理（限价、市价、止损止盈）
   - 风险管理（仓位控制、杠杆管理）
   - 滑点和费用优化

4. **性能追踪**
   - 实时盈亏计算
   - 夏普比率和其他指标
   - 交易历史记录

5. **可视化界面**（可选）
   - 实时仪表盘
   - 图表和指标展示
   - AI 决策透明化

## 风险提示

⚠️ **重要提醒**

- 加密货币交易涉及高风险，可能导致全部资金损失
- AI 交易系统不保证盈利，历史表现不代表未来结果
- 永续合约杠杆交易风险极高，请谨慎使用
- 仅用于学习和研究目的，实盘交易需自行承担风险
- 妥善保管私钥，切勿泄露

## 许可证

MIT License

## 参考资源

- [NoF1.ai](https://nof1.ai/)
- [HyperLiquid 文档](https://hyperliquid.gitbook.io/hyperliquid-docs)
- [HyperLiquid Python SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)
