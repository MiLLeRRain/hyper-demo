# Project Evolution: "Hyper-Evolution" (AI Self-Improvement System)

## 1. Vision & Goal
To create a standalone "Brain" system that autonomously improves the trading performance of the "Body" (Trading Bot) by evolving its System Prompts based on historical data and feedback.

**Long-term Vision**: "Prompt-Optimization-as-a-Service" (SaaS) where clients send trade history + prompts, and receive optimized prompts.

## 2. Architecture: "Sidecar" / "Dual-Loop"

### The Components
1.  **Repo A (hyper-demo)**: The **Trading Body**.
    *   **Role**: Execution, Real-time Data, Stability.
    *   **State**: Reads prompt from DB/File.
2.  **Repo B (hyper-evolution)**: The **Evolution Brain**.
    *   **Role**: Analysis, Simulation, Optimization.
    *   **State**: Writes optimized prompts.

### The Bridge (Interaction)
*   **Phase 1 (Manual/GitOps)**: Repo B generates `candidate_prompt.txt`. Human reviews and copies to Repo A.
*   **Phase 2 (Shared DB)**: Repo B writes to `system_prompts` table. Repo A reads latest active prompt on every cycle.
*   **Phase 3 (API/SaaS)**: Repo B exposes REST API. Repo A (or external clients) request optimization.

## 3. Core Technology Stack (Repo B)
*   **Language**: Python 3.12+
*   **LLM Provider**: **Groq** (Llama 3.1 70B/8B) for high-speed, low-cost inference.
*   **Framework**: Custom "Evolution Loop" (inspired by DSPy/Reflexion).
*   **Data Source**:
    *   **Input**: Historical Trade Logs (from Repo A's DB).
    *   **Simulation**: Historical Market Data (fetched via HyperLiquid API/CCXT).

## 4. The "Evolution Loop" Algorithm
1.  **Data Mining**: Extract "Key Frames" (Volatile moments, Wins/Losses) from history.
2.  **Critique**: LLM analyzes *why* a trade failed based on the prompt instructions.
3.  **Mutation**: LLM generates a variation of the prompt to fix the flaw.
4.  **Validation**: Run a "Mini-Backtest" (Simulation) on Key Frames using the new prompt.
5.  **Selection**: If Score(V2) > Score(V1), save V2.

## 5. Implementation Plan (Phase 1)

### Step 1: Workspace Setup
*   Create new folder `hyper-evolution`.
*   Initialize Python environment & Git.

### Step 2: Data Pipeline
*   `fetch_history.py`: Script to download OHLCV data (HyperLiquid/Binance) for backtesting.
*   `extract_trades.py`: Script to pull trade logs from Repo A's database.

### Step 3: The Optimizer (Groq Integration)
*   `optimizer.py`: The core script.
    *   Connects to Groq API.
    *   Implements the "Critique -> Mutate -> Validate" loop.

### Step 4: Output
*   Generate `optimized_prompt_v1.txt`.

## 6. Cost Management Strategy
*   **Token Explosion**: Avoided by using **Groq** (Cheap/Free Tier) instead of GPT-4o.
*   **Compute**: Run locally or on Google Colab (if needed).

---

## Next Steps
1.  Close current workspace (`hyper-demo`).
2.  Create/Open new folder `d:\trae_projs\hyper-evolution`.
3.  Start implementing **Step 1 & 2**.
