# Integration Testing Guide

Complete guide for running integration tests in Dry-Run mode.

## Overview

Our integration tests validate the entire trading system without risk:
- ✅ **Real market data** from HyperLiquid API
- ✅ **Simulated trade execution** (no real orders)
- ✅ **Zero cost** - no funds needed
- ✅ **Safe testing** - perfect for CI/CD

## Quick Start

### 1. Install Test Dependencies

```bash
pip install pytest pytest-asyncio
```

### 2. Set Environment Variables (Optional)

```bash
# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="sk-your-key"
$env:TEST_PRIVATE_KEY="0x1111111111111111111111111111111111111111111111111111111111111111"

# Linux/Mac
export DEEPSEEK_API_KEY="sk-your-key"
export TEST_PRIVATE_KEY="0x1111111111111111111111111111111111111111111111111111111111111111"
```

Note: Test private key can be any valid hex string - it's only used for dry-run simulation.

### 3. Run Tests

```bash
# Run all integration tests
python run_integration_tests.py

# Run specific test file
python run_integration_tests.py --file test_data_collection

# Skip slow tests
python run_integration_tests.py --fast

# Run with markers
python run_integration_tests.py -m "not slow"
```

## Test Suites

### 1. Data Collection Tests (`test_data_collection.py`)

Tests Phase 1 functionality - fetching market data from HyperLiquid.

**What it tests:**
- ✅ Fetching mid prices for all coins
- ✅ Fetching order book (L2 snapshot)
- ✅ Fetching user state
- ✅ Multi-coin data collection
- ✅ Performance (<5s target)
- ✅ Error handling

**Example output:**
```
✅ Fetched prices for 45 coins
   BTC: $50,123.45
   ETH: $3,001.23

✅ BTC Order Book:
   Best Bid: $50,120.00
   Best Ask: $50,125.00
   Spread: $5.00 (0.0100%)

✅ Data collection completed in 2.34s (target: <5s)
```

**Run only data collection tests:**
```bash
python run_integration_tests.py --file test_data_collection
```

### 2. Trading Execution Tests (`test_trading_execution.py`)

Tests Phase 3 functionality - trade execution in dry-run mode.

**What it tests:**
- ✅ Placing limit orders (simulated)
- ✅ Placing market orders (simulated)
- ✅ Canceling orders (simulated)
- ✅ Updating leverage (simulated)
- ✅ Error handling
- ✅ Performance

**Example output:**
```
✅ [DRY-RUN] Limit order placed successfully
   Order ID: 10001
   BTC BUY 0.1 @ $50,000

✅ [DRY-RUN] Order cancelled successfully
   Order ID: 10001

✅ [DRY-RUN] Leverage updated successfully
   BTC: 5x (cross margin)
```

**Run only trading execution tests:**
```bash
python run_integration_tests.py --file test_trading_execution
```

## Test Markers

Use markers to run specific types of tests:

```bash
# Skip slow tests (good for quick checks)
pytest tests/integration/ -m "not slow"

# Run only slow tests (performance tests)
pytest tests/integration/ -m "slow"

# Run only integration tests (default)
pytest tests/integration/ -m "integration"
```

## Writing New Tests

### Test Structure

```python
import pytest

@pytest.mark.integration
class TestMyFeature:
    """Integration tests for my feature."""

    def test_basic_functionality(self, test_config):
        """Test basic functionality."""
        # Your test code here
        assert True

    @pytest.mark.slow
    def test_performance(self, test_config):
        """Test performance (marked as slow)."""
        import time
        start = time.time()
        # ... test code ...
        duration = time.time() - start
        assert duration < 5.0
```

### Available Fixtures

From `conftest.py`:

- `test_config` - Test configuration dict
- `test_db_engine` - In-memory SQLite engine
- `test_db_session` - Database session
- `sample_agent` - Sample trading agent
- `sample_market_data` - Sample market data dict
- `sample_ai_decision` - Sample AI decision dict
- `mock_hyperliquid_client` - Mock HyperLiquid client
- `mock_deepseek_client` - Mock DeepSeek client
- `sample_position` - Sample position record
- `sample_order` - Sample order record

### Example Test

```python
@pytest.mark.integration
def test_place_order_dry_run(test_config):
    """Test placing order in dry-run mode."""
    from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor

    executor = HyperLiquidExecutor(
        base_url=test_config["hyperliquid"]["base_url"],
        private_key=test_config["hyperliquid"]["private_key"],
        dry_run=True
    )

    success, order_id, error = executor.place_order(
        coin="BTC",
        is_buy=True,
        size=Decimal("0.1"),
        price=Decimal("50000.0")
    )

    assert success is True
    assert order_id is not None
    print(f"✅ Order placed: {order_id}")
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run integration tests (fast only)
        run: |
          python run_integration_tests.py --fast
        env:
          TEST_PRIVATE_KEY: ${{ secrets.TEST_PRIVATE_KEY }}
```

## Debugging Tests

### Run Single Test

```bash
pytest tests/integration/test_data_collection.py::TestDataCollection::test_get_all_mids_real_api -v -s
```

### Show Print Statements

```bash
pytest tests/integration/ -s
```

### Stop on First Failure

```bash
pytest tests/integration/ -x
```

### Show Detailed Traceback

```bash
pytest tests/integration/ --tb=long
```

### Run with Debugger

```bash
pytest tests/integration/ --pdb
```

## Performance Benchmarks

Expected performance for integration tests:

| Test Suite | Target | Typical |
|------------|--------|---------|
| Data Collection | <5s | ~2-3s |
| Trading Execution (Dry-Run) | <0.1s | ~0.01s |
| Full Test Suite | <30s | ~10-15s |

## Troubleshooting

### "ModuleNotFoundError: No module named 'trading_bot'"

**Solution:** Make sure you're in the project root directory and have installed the package:

```bash
cd D:\trae_projs\hyper-demo
pip install -e .
```

### "Connection refused" or "API timeout"

**Cause:** Network issues or HyperLiquid API unavailable

**Solution:**
- Check internet connection
- Verify HyperLiquid API status
- Increase timeout in test_config

### Tests are very slow

**Solution:** Use `--fast` flag to skip performance tests:

```bash
python run_integration_tests.py --fast
```

### "Test private key invalid"

**Solution:** Set a valid test private key (can be any 64-char hex string):

```bash
$env:TEST_PRIVATE_KEY="0x1111111111111111111111111111111111111111111111111111111111111111"
```

## Safety Reminders

### ✅ Safe Practices

- All tests use **dry-run mode** by default
- No real trades are executed
- No real funds are needed
- Tests can run anywhere (local, CI/CD)

### ⚠️ Important Notes

- Data collection tests call **real HyperLiquid API**
  - They are **read-only** and safe
  - But they do use network bandwidth
  - Be mindful of rate limits

- Trading execution tests are **fully simulated**
  - No API calls for order placement
  - Orders stored in memory only
  - 100% safe to run repeatedly

## Next Steps

After integration tests pass:

1. ✅ **Dry-run integration tests** (current)
2. ⏭️ **Testnet testing** (when faucet available)
3. ⏭️ **Small mainnet test** ($10-20, optional)
4. ⏭️ **Production deployment**

## Summary

```bash
# Quick test run (recommended)
python run_integration_tests.py --fast

# Full test suite
python run_integration_tests.py

# Specific test file
python run_integration_tests.py --file test_data_collection

# With verbose output
python run_integration_tests.py --verbose
```

**All tests run in dry-run mode - completely safe! 🛡️**
