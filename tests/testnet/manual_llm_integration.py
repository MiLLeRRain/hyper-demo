#!/usr/bin/env python3
"""LLM API Integration Test with Testnet Trading.

这个测试验证完整的 AI 决策到交易执行流程：
1. 获取市场数据
2. 构建 AI Prompt
3. 调用 LLM API 获取决策
4. 解析决策
5. 在 Testnet 上执行交易
"""

import os
import sys
from pathlib import Path
from decimal import Decimal

# Add src directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from trading_bot.data.hyperliquid_client import HyperliquidClient
from trading_bot.ai.prompt_builder import PromptBuilder
from trading_bot.ai.decision_parser import DecisionParser
from trading_bot.ai.providers import OfficialAPIProvider
from trading_bot.trading.hyperliquid_executor import HyperLiquidExecutor as HyperliquidExecutor


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    """Run LLM integration test."""
    load_dotenv()

    print_section("LLM API Integration Test (Testnet)")

    print("\n[!] This test will:")
    print("  1. Call real LLM API (DeepSeek/OpenAI)")
    print("  2. Execute real orders on Testnet")
    print("  3. Use test tokens (no value)")

    # Configuration
    private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")
    if not private_key:
        private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY_DEFAULT")
        
    if not private_key:
        print("\n[ERROR] HYPERLIQUID_PRIVATE_KEY not found in .env")
        return 1

    # Check for LLM API keys
    has_deepseek = bool(os.getenv("DEEPSEEK_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    if not has_deepseek and not has_openai:
        print("\n[WARNING] No LLM API keys found!")
        print("  Please add to .env:")
        print("  - DEEPSEEK_API_KEY=your_key")
        print("  - OPENAI_API_KEY=your_key")
        return 1

    print(f"\n[OK] LLM API available:")
    if has_deepseek:
        print("  - DeepSeek API OK")
    if has_openai:
        print("  - OpenAI API OK")

    # Confirmation
    response = input("\n  Continue with LLM integration test? (yes/no): ")
    if response.lower() != "yes":
        print("\n[CANCELLED] Test cancelled by user")
        return 0

    try:
        # ====================================================================
        # Step 1: Initialize Components
        # ====================================================================
        print_section("Step 1: Initialize Components")

        # Market data client
        client = HyperliquidClient(base_url="https://api.hyperliquid-testnet.xyz")
        print("  [OK] HyperliquidClient initialized")

        # Trading executor
        executor = HyperliquidExecutor(
            base_url="https://api.hyperliquid-testnet.xyz",
            private_key=private_key,
            dry_run=False  # Real testnet trading
        )
        print(f"  [OK] Executor initialized (Testnet)")
        print(f"       Wallet: {executor.get_address()}")

        # AI components
        prompt_builder = PromptBuilder()
        decision_parser = DecisionParser()

        # Create LLM provider directly
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        llm_provider = OfficialAPIProvider(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            model_name="deepseek-chat"
        )
        print("  [OK] AI components initialized")

        # ====================================================================
        # Step 2: Collect Market Data
        # ====================================================================
        print_section("Step 2: Collect Market Data")

        # Test with BTC
        coin = "BTC"
        print(f"\n  Collecting data for {coin}...")

        # Get current price
        prices = client.get_all_prices()
        current_price = prices[coin].price
        print(f"  Current Price: ${current_price:,.2f}")

        # Get K-line data (last 50 candles, 15-minute)
        candles = client.get_klines(coin, "15m", limit=50)
        print(f"  K-line Data: {len(candles)} candles (15-minute)")

        # Calculate simple technical indicators
        import pandas as pd
        df = pd.DataFrame(candles)

        # Simple moving averages
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()

        # Get last values
        latest = df.iloc[-1]
        sma_20 = latest['sma_20'] if not pd.isna(latest['sma_20']) else latest['close']
        sma_50 = latest['sma_50'] if not pd.isna(latest['sma_50']) else latest['close']

        print(f"\n  Technical Indicators:")
        print(f"    SMA(20): ${sma_20:,.2f}")
        print(f"    SMA(50): ${sma_50:,.2f}")
        print(f"    Trend: {'BULLISH' if sma_20 > sma_50 else 'BEARISH'}")

        # ====================================================================
        # Step 3: Build AI Prompt
        # ====================================================================
        print_section("Step 3: Build AI Prompt")

        # Build a simple trading prompt
        trend_desc = 'BULLISH' if sma_20 > sma_50 else 'BEARISH'

        prompt = f"""You are an expert cryptocurrency trader analyzing {coin}.

Current Market Data:
- Price: ${current_price:,.2f}
- SMA(20): ${sma_20:,.2f}
- SMA(50): ${sma_50:,.2f}
- Trend: {trend_desc}

Recent Price Action (last 10 candles):
{df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail(10).to_string()}

Trading Constraints:
- Available Balance: $100 USDC
- Max Position Size: $50
- Max Leverage: 2x

Task:
Analyze the market data and provide a trading decision.

Respond in the following JSON format:
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "entry_price": optional_price,
    "position_size": optional_size_usd,
    "stop_loss": optional_price,
    "take_profit": optional_price
}}

Provide only the JSON response, no additional text."""

        print(f"\n  Prompt built successfully")
        print(f"  Prompt length: {len(prompt)} characters")
        print(f"\n  Preview (first 300 chars):")
        print(f"  {prompt[:300]}...")

        # ====================================================================
        # Step 4: Call LLM API
        # ====================================================================
        print_section("Step 4: Call LLM API")

        print(f"\n  Using: DeepSeek Chat")
        print(f"  Model: deepseek-chat")

        print(f"\n  Calling LLM API...")

        try:
            # Call LLM
            response = llm_provider.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )

            print(f"  [OK] LLM response received")
            print(f"  Response length: {len(response)} characters")
            print(f"\n  Response preview:")
            print(f"  {response[:300]}...")

        except Exception as e:
            print(f"\n[ERROR] LLM API call failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

        # ====================================================================
        # Step 5: Parse Decision
        # ====================================================================
        print_section("Step 5: Parse Decision")

        try:
            # Parse JSON response
            import json
            decision = json.loads(response)

            print(f"\n  Decision parsed successfully:")
            print(f"    Action: {decision['action']}")
            print(f"    Confidence: {decision['confidence']:.1%}")
            print(f"    Reasoning: {decision['reasoning'][:100]}...")

            if decision['action'] != "HOLD":
                if decision.get('entry_price'):
                    print(f"    Entry Price: ${decision['entry_price']:,.2f}")
                if decision.get('position_size'):
                    print(f"    Position Size: ${decision['position_size']:.2f}")
                if decision.get('stop_loss'):
                    print(f"    Stop Loss: ${decision['stop_loss']:,.2f}")
                if decision.get('take_profit'):
                    print(f"    Take Profit: ${decision['take_profit']:,.2f}")

        except Exception as e:
            print(f"\n[ERROR] Failed to parse decision: {e}")
            print(f"\n  Raw response:")
            print(f"  {response}")
            return 1

        # ====================================================================
        # Step 6: Execute Trade (if not HOLD)
        # ====================================================================
        print_section("Step 6: Execute Trade on Testnet")

        if decision['action'] == "HOLD":
            print("\n  [INFO] Decision is HOLD - no trade to execute")
            print("\n  This is normal - AI decided to wait for better opportunity")

        else:
            print(f"\n  Executing {decision['action']} order...")

            # Determine order parameters
            is_buy = (decision['action'] == "BUY" or decision['action'] == "LONG")

            # Use a very small size for testing (0.001 BTC)
            test_size = Decimal("0.001")

            # Use entry price from AI, or slightly below/above current price
            if decision.get('entry_price'):
                # Round to tick size ($10 for BTC)
                test_price = round(decision['entry_price'] / 10) * 10
            else:
                # Default: 1% below market for buy, 1% above for sell
                if is_buy:
                    test_price = round(current_price * 0.99 / 10) * 10
                else:
                    test_price = round(current_price * 1.01 / 10) * 10

            print(f"\n  Order Details:")
            print(f"    Type: {'BUY' if is_buy else 'SELL'}")
            print(f"    Size: {test_size} BTC")
            print(f"    Price: ${test_price:,.2f}")
            print(f"    Market Price: ${current_price:,.2f}")

            try:
                # Place order
                success, order_id, error = executor.place_order(
                    coin=coin,
                    is_buy=is_buy,
                    size=test_size,
                    price=Decimal(str(test_price)),
                    order_type="limit"
                )

                if success:
                    print(f"\n  [OK] Order placed successfully!")
                    print(f"       Order ID: {order_id}")

                    # Wait a moment
                    import time
                    time.sleep(2)

                    # Cancel the order (cleanup)
                    print(f"\n  Cancelling test order...")
                    cancel_success, cancel_error = executor.cancel_order(coin, order_id)

                    if cancel_success:
                        print(f"  [OK] Order cancelled successfully")
                    else:
                        print(f"  [WARNING] Failed to cancel: {cancel_error}")
                        print(f"  Please cancel manually: Order ID {order_id}")
                else:
                    print(f"\n  [ERROR] Order failed: {error}")
                    return 1

            except Exception as e:
                print(f"\n[ERROR] Trade execution failed: {e}")
                return 1

        # ====================================================================
        # Test Summary
        # ====================================================================
        print_section("Test Summary")

        print("\n  [OK] LLM Integration Test Completed!")
        print("\n  Verified components:")
        print("    OK Market data collection")
        print("    OK AI prompt building")
        print("    OK LLM API call")
        print("    OK Decision parsing")
        if decision['action'] != "HOLD":
            print("    OK Testnet order execution")

        print("\n  Next steps:")
        print("    1. Review the AI decision quality")
        print("    2. Adjust prompt if needed")
        print("    3. Test with different market conditions")
        print("    4. Run full backtesting")

        return 0

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
