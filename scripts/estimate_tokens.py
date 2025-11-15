#!/usr/bin/env python3
"""Estimate token usage for AI trading decisions."""

# 示例 1: 简短决策（HOLD）
short_output = """
{
  "reasoning": "Market conditions are unclear with mixed signals across timeframes. RSI near neutral and no clear trend direction. Better to wait for confirmation.",
  "action": "HOLD",
  "coin": "BTC",
  "size_usd": 0.0,
  "leverage": 1,
  "stop_loss_price": 0.0,
  "take_profit_price": 0.0,
  "confidence": 0.50
}
"""

# 示例 2: 中等决策（BUY）
medium_output = """
{
  "reasoning": "BTC shows strong bullish momentum with RSI at 58 and price breaking above EMA on 4h chart. MACD golden cross confirms uptrend. Volume is increasing which supports the move. Given the overall bullish setup, I recommend a cautious long position with tight stop loss.",
  "action": "OPEN_LONG",
  "coin": "BTC",
  "size_usd": 500.0,
  "leverage": 2,
  "stop_loss_price": 95000.0,
  "take_profit_price": 98500.0,
  "confidence": 0.72
}
"""

# 示例 3: 详细决策（带策略分析）
detailed_output = """
{
  "reasoning": "BTC technical analysis shows multiple bullish confirmations: 1) Price action broke above 20-day EMA at $95,500 with strong volume, indicating institutional accumulation. 2) MACD histogram turned positive with bullish crossover on 4H timeframe. 3) RSI at 58 suggests room for upside before overbought territory. 4) Recent consolidation at $94,000-$96,000 formed a strong base. 5) On-chain metrics show declining exchange reserves. However, approaching resistance at $97,000 requires caution. Risk-reward ratio favors long entry with 2x leverage, targeting $98,500 resistance level. Stop loss below recent support at $95,000 limits downside to 2.1% of position.",
  "action": "OPEN_LONG",
  "coin": "BTC",
  "size_usd": 800.0,
  "leverage": 2,
  "stop_loss_price": 95000.0,
  "take_profit_price": 98500.0,
  "confidence": 0.78
}
"""

def estimate_tokens(text):
    """Estimate token count (rough: 1 token ≈ 4 chars for English)."""
    # 更准确的估算：
    # - 英文单词: 1 token ≈ 0.75 words
    # - 字符数: 1 token ≈ 4 chars
    char_count = len(text)
    word_count = len(text.split())

    # 使用字符估算（保守）
    estimated_tokens = char_count / 4

    return int(estimated_tokens), char_count, word_count

print("=" * 70)
print("  Token Usage Estimation for AI Trading Decisions")
print("=" * 70)
print()

# 分析三种场景
scenarios = [
    ("HOLD (简短)", short_output),
    ("BUY (中等)", medium_output),
    ("BUY (详细)", detailed_output)
]

for name, output in scenarios:
    tokens, chars, words = estimate_tokens(output)
    print(f"{name}:")
    print(f"  Characters: {chars}")
    print(f"  Words: {words}")
    print(f"  Estimated tokens: {tokens}")
    print(f"  Status with max_tokens=500: {'OK' if tokens < 500 else 'EXCEED'}")
    print()

print("=" * 70)
print("  Recommendations")
print("=" * 70)
print()

print("max_tokens = 300:")
print("  - Sufficient for HOLD decisions")
print("  - May cut off detailed BUY/SELL reasoning")
print("  - Risk: Incomplete JSON output")
print()

print("max_tokens = 500:")
print("  - Comfortable for most decisions")
print("  - Allows detailed reasoning (2-3 sentences)")
print("  - Good balance of detail and cost")
print()

print("max_tokens = 800:")
print("  - Plenty of room for very detailed analysis")
print("  - Useful for strategy agents with complex reasoning")
print("  - Higher cost (+60% vs 500 tokens)")
print()

print("max_tokens = 1000:")
print("  - Excessive for trading decisions")
print("  - Unnecessary cost")
print("  - May encourage verbose/unfocused reasoning")
print()

print("=" * 70)
print("  Recommendation for Your Setup")
print("=" * 70)
print()
print("Default Agent (no strategy):")
print("  -> max_tokens = 500 (good balance)")
print()
print("Strategy Agents (with detailed prompts):")
print("  -> max_tokens = 600-700 (more reasoning needed)")
print()
print("Production (cost-optimized):")
print("  -> max_tokens = 400 (still safe)")
print()
