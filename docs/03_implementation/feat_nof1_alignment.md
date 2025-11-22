# Feature: NoF1.ai Prompt Alignment

## Overview
Refactor the `PromptBuilder` and data collection pipeline to strictly adhere to the NoF1.ai design specification. This involves moving from scalar data points to time-series arrays, removing hardcoded risk constraints, and adopting the specific `CHAIN_OF_THOUGHT` output format.

## Gap Analysis

| Component | Current Implementation | Target Specification (NoF1.ai) | Action |
|-----------|------------------------|--------------------------------|--------|
| **Market Data** | Scalar values (Current Price, Current EMA/RSI) | Time-series arrays (Lists of last 10-20 values) | **Update** |
| **Indicators** | EMA, MACD, RSI-14, ATR | EMA, MACD, **RSI-7**, RSI-14, ATR, **OI**, **Funding**, **Volume** | **Add** |
| **Prompt Structure** | Markdown headers, Risk Constraints section | Specific text blocks (`ALL {COIN} DATA`), No constraints | **Refactor** |
| **Output Format** | Single JSON object | Natural Language + `CHAIN_OF_THOUGHT` JSON + `TRADING_DECISIONS` | **Update** |
| **Context** | Current Time only | Start Time, Minutes Elapsed, Invocation Count | **Add** |

## Implementation Plan

### Phase 1: Data Model & Collection Updates
1.  **Modify `MarketData` Model**:
    *   Add fields for `open_interest`, `funding_rate`.
    *   Add fields for `volume_current`, `volume_average`.
    *   Update `indicators` to support list/array storage.
2.  **Update Data Fetching Logic**:
    *   Ensure `pandas-ta` calculation returns the tail of the dataframe (last 10-20 rows) as lists, not just the last row.
    *   Fetch Open Interest and Funding Rate from HyperLiquid API.

### Phase 2: Prompt Builder Refactoring
1.  **`PromptBuilder` Class**:
    *   Implement `_format_coin_data` to generate the specific text block format.
    *   Implement `_format_account_info` to match the target style.
    *   Remove `_build_constraints_section`.
    *   Update System Prompt to request `CHAIN_OF_THOUGHT` format.
2.  **State Tracking**:
    *   Add `start_time` and `invocation_count` tracking to `TradingBotService` or `PromptBuilder`.

### Phase 3: Response Parsing
1.  **Update Parser**:
    *   Modify the logic that parses the LLM response to extract the JSON block from the mixed text output.

## Task List
- [ ] **Task 1**: Update `MarketData` model in `src/trading_bot/models/market_data.py`.
- [ ] **Task 2**: Update data fetching in `TradingBotService` / `MarketDataService` to populate arrays and new fields.
- [ ] **Task 3**: Refactor `src/trading_bot/ai/prompt_builder.py` to match the NoF1.ai prompt structure.
- [ ] **Task 4**: Update response parsing logic (likely in `TradingOrchestrator` or `Agent`).
