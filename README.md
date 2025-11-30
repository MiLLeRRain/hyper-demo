# HyperLiquid AI Trading Bot

![Tests](https://github.com/MiLLeRRain/hyper-demo/actions/workflows/tests.yml/badge.svg)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)

[🇨🇳 中文文档](README_CN.md) | [🇺🇸 English](README.md)

AI-driven trading bot based on HyperLiquid Perpetual Exchange.

---

## 🎯 Introduction

This is a complete AI trading system using the official HyperLiquid Python SDK, supporting:

- ✅ **Multi-Model AI Decision** - OpenAI, Anthropic, DeepSeek, etc.
- ✅ **Real-time Market Data** - Prices, K-lines, Technical Indicators
- ✅ **Automated Execution** - Limit/Market orders, Leverage management
- ✅ **Risk Management** - Position sizing, Stop-loss/Take-profit
- ✅ **Testnet Support** - Zero-risk testing environment
- ✅ **Full Test Coverage** - 94% code coverage

---

## 🚀 Quick Start

### Option A: Quick Test (5 mins)

Ideal for verifying system functionality:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env (Add private key and API key)
cp .env.example .env
# Edit .env, set:
#   HYPERLIQUID_PRIVATE_KEY=your_private_key
#   DEEPSEEK_API_KEY=your_api_key

# 3. Verify readiness
python scripts/check_readiness.py

# 4. Run Testnet test
python tests/testnet/test_llm_integration.py
```

### Option B: Long-term Running (Production)

Suitable for real trading with state persistence:

```bash
# 1. Install PostgreSQL (Docker recommended)
scripts/setup_database.bat  # Windows
# or
scripts/setup_database.sh   # Linux/Mac

# 2. Run database migrations
alembic upgrade head

# 3. Verify configuration
python scripts/check_readiness.py

# 4. Start the bot (3-minute cycle)
python tradingbot.py start

# 5. Monitor status
python tradingbot.py status
python tradingbot.py logs -f
```

📖 **Detailed Guide**: [Long Term Running Guide](docs/06_deployment/long_term_running_guide.md)

---

## 📁 Project Structure

```
hyper-demo/
├── docs/                    # 📚 Documentation
│   ├── TESTNET_QUICK_START.md
│   ├── COMMANDS.md
│   ├── TEST_RESULTS.md
│   └── PROJECT_STRUCTURE.md
│
├── scripts/                 # 🛠️ Utility Scripts
│   ├── run_integration_tests.py
│   └── verify_wallet.py
│
├── src/trading_bot/         # 📦 Core Code
│   ├── data/               # Market Data Collection
│   ├── ai/                 # AI Decision Engine
│   ├── trading/            # Execution ⭐ Official SDK
│   ├── risk/               # Risk Management
│   └── automation/         # Automation & Scheduling
│
└── tests/                   # 🧪 Tests
    ├── unit/               # Unit Tests
    ├── integration/        # Integration Tests (DRY-RUN)
    ├── testnet/            # Testnet Live Tests
    └── manual/             # Debug Scripts
```

See [docs/02_architecture/project_structure.md](docs/02_architecture/project_structure.md) for details.

---

## 🧪 Testing

### Recommended Workflow

```bash
# 1. Verify wallet address
python scripts/verify_wallet.py

# 2. Test Testnet connection
python tests/testnet/test_testnet_connection.py

# 3. Quick order test (Place -> Cancel)
python tests/testnet/test_order_placement.py

# 4. Run integration tests
python scripts/run_integration_tests.py --fast
```

### Test Results

- ✅ 30/32 Integration tests passed
- ✅ Testnet order execution successful
- ✅ Official SDK integration verified
- ✅ 94% Test coverage

---

## 📚 Core Features

### 1️⃣ Data Collection (Phase 1)
- Real-time prices (473+ coins)
- K-line data (Multi-timeframe)
- Technical indicators
- Orderbook snapshots

### 2️⃣ AI Decision (Phase 2)
- Multi-model integration
- Intelligent Prompt Engineering
- Decision parsing & validation
- Multi-Agent collaboration
- **Prompt Logging** (Full interaction history in DB)

### 3️⃣ Execution (Phase 3) ⭐
- **Official SDK Integration**
- Limit / Market orders
- Leverage management
- Automatic tick size handling
- **Dynamic Precision** (Auto-adapt to coin decimals)
- Dry-run mode

### 4️⃣ Risk Management
- Position sizing
- Leverage limits
- **Stop-Loss/Take-Profit** (Auto-order protection)
- Daily loss limits

### 5️⃣ Automation (Phase 4)
- Task scheduling
- CLI tools
- Monitoring & Alerting

### 6️⃣ Data Mining & Self-Evolution (New!) 🧠
- **Decision Analysis**: `scripts/analyze_decisions.py`
- **Data Cleaning**: Link decisions with trade results (PnL/ROI)
- **Dataset Generation**: Export JSONL for LLM Fine-tuning
- **Evolution System**: "Sidecar" architecture for autonomous prompt optimization

### 7️⃣ Security & Audit (New!) 🛡️
- **Prompt Audit Layer**: Pre-flight check for all AI prompts
- **PII Masking**: Auto-redact wallet addresses and private keys
- **Injection Detection**: Block malicious prompt injection attempts
- **Configurable Rules**: Customizable security policies via `config.yaml`

---

## 📊 Development Roadmap

- [x] Phase 1: Data Collection ✅
- [x] Phase 2: AI Decision Engine ✅
- [x] Phase 3: Execution System ✅ (Official SDK)
- [x] Phase 4: Automation & CLI ✅
- [ ] Phase 5: Web Dashboard (Planned)
- [ ] **Phase 6: Hyper-Evolution (In Progress)** 🧬
    - [ ] **Architecture**: Dual-Loop System (Trading Body + Evolution Brain)
    - [ ] **Bridge**: Shared Database / Template Contract
    - [ ] **Optimizer**: Groq/Llama-3.1 based prompt mutation loop
    - [ ] **Goal**: Autonomous self-improvement of trading strategies
    - [x] **Security**: Prompt Audit & PII Protection Layer ✅

---

## ⚠️ Risk Warning

**IMPORTANT**:

- ⚠️ Cryptocurrency trading involves high risk
- ⚠️ Perpetual contract leverage is extremely risky
- ⚠️ AI trading does not guarantee profits
- ⚠️ Always test thoroughly on Testnet first
- ⚠️ Keep your private keys safe
- ✅ For educational and research purposes only

---

## 🤝 Contribution

Issues and Pull Requests are welcome!

---

## 📄 License

MIT License

---

## 🔗 Links

- [HyperLiquid Testnet](https://app.hyperliquid-testnet.xyz)
- [HyperLiquid Docs](https://hyperliquid.gitbook.io)
- [Official Python SDK](https://github.com/hyperliquid-dex/hyperliquid-python-sdk)
- [NoF1.ai Platform](https://nof1.ai/)

---

**Quick Start**: `python tests/testnet/test_order_placement.py` 🚀
