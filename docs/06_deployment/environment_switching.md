# Environment Switching Guide

This guide explains how to easily switch between different trading environments: Dry-Run, Testnet, and Mainnet.

## Quick Start

**Change only ONE line in `config.yaml` to switch environments:**

```yaml
environment: 'dry-run'  # Options: 'dry-run' | 'testnet' | 'mainnet'
```

That's it! The system automatically adjusts all settings based on your chosen environment.

---

## Environment Modes

### 1. Dry-Run Mode (Default - **SAFE FOR TESTING**)

**Perfect for integration testing without any risk!**

**What it does:**
- ✅ Fetches **real market data** from HyperLiquid
- ✅ Generates **real AI decisions** using DeepSeek/Qwen
- ✅ **Simulates** trade execution (NO real orders)
- ✅ Logs all "would-be" trades for analysis
- ✅ **Zero risk** - no real money involved

**When to use:**
- Integration testing
- Strategy validation
- System debugging
- When testnet faucet is unavailable

**Configuration:**
```yaml
environment: 'dry-run'

dry_run:
  enabled: true
  data_source: 'mainnet'  # Use mainnet data for realistic testing
  simulate_order_fill: true
  simulate_slippage: 0.001  # 0.1% slippage
  log_simulated_trades: true
```

**Log output example:**
```
[DRY-RUN] Simulated order: BTC BUY 0.1 @ 50000.0 (OID: 10001)
[DRY-RUN] Simulated cancel: BTC OID 10001
[DRY-RUN] Simulated leverage update: ETH -> 5x (cross)
```

---

### 2. Testnet Mode (**WHEN FAUCET WORKS**)

**For testing with fake money on testnet**

**What it does:**
- ✅ Uses testnet API
- ✅ Places **real orders** on testnet
- ✅ Uses testnet faucet tokens (no real value)
- ✅ Full system testing in production-like environment

**When to use:**
- After dry-run testing passes
- Before mainnet deployment
- When testnet faucet is available

**Configuration:**
```yaml
environment: 'testnet'

hyperliquid:
  # System auto-selects testnet_url
  testnet_url: 'https://api.hyperliquid-testnet.xyz'
  private_key: '${HYPERLIQUID_TESTNET_KEY}'  # Testnet wallet key
```

**How to switch to testnet:**

1. **Edit `config.yaml`:**
   ```yaml
   environment: 'testnet'  # ← Change this line
   ```

2. **Set environment variable:**
   ```bash
   # Windows (PowerShell)
   $env:HYPERLIQUID_PRIVATE_KEY="0xYourTestnetPrivateKey"

   # Linux/Mac
   export HYPERLIQUID_PRIVATE_KEY="0xYourTestnetPrivateKey"
   ```

3. **Get testnet funds:**
   - Visit testnet faucet (when available)
   - Or use existing testnet wallet with funds

4. **Run:**
   ```bash
   python tradingbot.py start
   ```

---

### 3. Mainnet Mode (**PRODUCTION - USE WITH CAUTION**)

**⚠️ WARNING: This uses REAL MONEY!**

**What it does:**
- ⚠️ Places **real orders** with **real funds**
- ⚠️ All trades execute on mainnet
- ⚠️ Profits and losses are **REAL**

**When to use:**
- Only after thorough testing on dry-run and testnet
- When you're confident in your strategy
- With appropriate risk management

**Configuration:**
```yaml
environment: 'mainnet'

hyperliquid:
  mainnet_url: 'https://api.hyperliquid.xyz'
  private_key: '${HYPERLIQUID_MAINNET_KEY}'  # Mainnet wallet key

  # Safety limits (IMPORTANT!)
  max_position_size: 0.1  # Max 0.1 BTC per position
  max_leverage: 3  # Max 3x leverage
  max_daily_trades: 20  # Max 20 trades per day
```

**How to switch to mainnet:**

1. **Edit `config.yaml`:**
   ```yaml
   environment: 'mainnet'  # ← Change this line
   ```

2. **Set environment variable:**
   ```bash
   # Windows (PowerShell)
   $env:HYPERLIQUID_PRIVATE_KEY="0xYourMainnetPrivateKey"

   # Linux/Mac
   export HYPERLIQUID_PRIVATE_KEY="0xYourMainnetPrivateKey"
   ```

3. **Double-check safety limits:**
   ```yaml
   hyperliquid:
     max_position_size: 0.1  # Adjust based on your risk tolerance
     max_leverage: 3
   ```

4. **Run with extreme caution:**
   ```bash
   python tradingbot.py start
   ```

---

## Environment Comparison

| Feature | Dry-Run | Testnet | Mainnet |
|---------|---------|---------|---------|
| Real market data | ✅ | ✅ | ✅ |
| Real AI decisions | ✅ | ✅ | ✅ |
| Real orders | ❌ Simulated | ✅ Testnet | ✅ Real |
| Real money | ❌ | ❌ | ⚠️ YES |
| Risk | ✅ Zero | ✅ Zero | ⚠️ HIGH |
| Best for | Testing | Pre-prod | Production |

---

## Switching Workflow

### Recommended Testing Flow:

```
1. Dry-Run Mode
   ↓ (Verify all functionality works)

2. Testnet Mode (when faucet available)
   ↓ (Verify on-chain execution works)

3. Small Mainnet Test ($10-50)
   ↓ (Verify with minimal risk)

4. Production Mainnet
   (Full deployment)
```

### Current Situation (Testnet Faucet Unavailable):

```
1. Dry-Run Mode ← START HERE
   ↓ (Complete integration testing)

2. Small Mainnet Test ($10-20) [OPTIONAL]
   ↓ (Optional verification with minimal funds)

3. Wait for Testnet Faucet
   ↓ (Resume when available)

4. Production Mainnet
   (Full deployment)
```

---

## Environment Variables

Store sensitive data in environment variables, not in config files!

### .env File (Recommended)

Create `.env` file in project root:

```bash
# .env file

# HyperLiquid Keys
HYPERLIQUID_TESTNET_KEY=0xYourTestnetPrivateKey
HYPERLIQUID_MAINNET_KEY=0xYourMainnetPrivateKey

# LLM API Keys
DEEPSEEK_API_KEY=sk-your-deepseek-key
QWEN_API_KEY=sk-your-qwen-key

# Database
DB_USER=trading_bot
DB_PASSWORD=your_secure_password

# Alerts (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Load Environment Variables

**Windows (PowerShell):**
```powershell
# Load from .env file
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*?)\s*=\s*(.+?)\s*$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}
```

**Linux/Mac:**
```bash
# Load from .env file
export $(cat .env | xargs)

# Or use direnv (auto-load)
direnv allow
```

---

## Safety Checklist

### Before Switching to Mainnet:

- [ ] All dry-run tests pass
- [ ] Tested on testnet (if available)
- [ ] Safety limits configured:
  - [ ] `max_position_size` set appropriately
  - [ ] `max_leverage` limited
  - [ ] `max_daily_trades` set
- [ ] Private key securely stored in environment variable
- [ ] Wallet has appropriate funds (not too much for testing)
- [ ] Monitoring and alerts configured
- [ ] Emergency stop procedures understood
- [ ] Risk management strategy defined

### During Testing:

- [ ] Start with minimal position sizes
- [ ] Monitor first few trades manually
- [ ] Check logs regularly
- [ ] Verify P&L matches expectations
- [ ] Have stop button ready: `python tradingbot.py stop`

---

## Troubleshooting

### Can't access testnet faucet?
**Solution:** Use dry-run mode for testing. It's just as effective for integration testing!

### How to verify which mode I'm in?
**Check logs on startup:**
```
INFO: Initialized HyperLiquidExecutor for 0x... [DRY-RUN MODE]
INFO: Initialized HyperLiquidExecutor for 0x... [LIVE MODE]
```

### Accidentally started in wrong mode?
**Stop immediately:**
```bash
python tradingbot.py stop --force
```

### Want to test specific trade without full automation?
**Use Python REPL:**
```python
from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor

# Dry-run test
executor = HyperLiquidExecutor(
    "https://api.hyperliquid.xyz",
    "0xYourKey",
    dry_run=True  # ← Safe mode
)

success, oid, err = executor.place_order("BTC", True, 0.01, 50000.0)
print(f"Success: {success}, Order ID: {oid}")
```

---

## Quick Reference

### Switch to Dry-Run:
```yaml
environment: 'dry-run'
```

### Switch to Testnet:
```yaml
environment: 'testnet'
```

### Switch to Mainnet:
```yaml
environment: 'mainnet'
```

### Check Current Mode:
```bash
python tradingbot.py status
```

### View Logs:
```bash
python tradingbot.py logs --follow
```

---

## Summary

✅ **For current testing (faucet unavailable):** Use `dry-run` mode
✅ **When faucet works:** Switch to `testnet` mode
✅ **For production:** Switch to `mainnet` mode (with caution!)

**Switching is as simple as changing ONE line in config.yaml!**

```yaml
environment: 'dry-run'  # ← Change this to switch modes
```

No code changes needed - the system handles everything automatically! 🚀
