# 数据挖掘与反向训练指南

本系统内置了强大的数据挖掘工具，旨在将 LLM 的历史交易决策转化为高质量的训练数据，从而实现模型的自我进化。

## 🛠️ 核心工具：决策分析器

脚本路径：`scripts/analyze_decisions.py`

该工具负责从数据库中提取“决策-结果”对，并进行清洗和格式化。

### 功能特性

1.  **自动关联**：将 `AgentDecision`（AI 的思考）与 `AgentTrade`（实际盈亏）进行匹配。
2.  **结果标注**：自动计算每笔交易的 PnL (盈亏额) 和 ROI (投资回报率)，并标记为 `WIN` (盈利) 或 `LOSS` (亏损)。
3.  **格式化导出**：生成标准的 `.jsonl` 文件，可直接用于 OpenAI 或 Llama 等模型的 Fine-tuning。

---

## 🚀 使用方法

### 1. 生成分析报告

在项目根目录下运行：

```bash
python scripts/analyze_decisions.py
```

### 2. 查看输出

运行成功后，会在 `data/` 目录下生成 `decision_analysis.jsonl` 文件。

**输出示例**：

```json
{
  "decision_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-22T10:30:00",
  "agent": "DeepSeek-V3-Trader",
  "coin": "ETH",
  "action": "OPEN_LONG",
  "confidence": 0.85,
  "reasoning": "RSI 在 30 以下出现底背离，且 4H 均线支撑有效...",
  "chain_of_thought": { ... },
  "outcome": "WIN",
  "realized_pnl": 150.50,
  "roi_percent": 5.2,
  "prompt_content": "...",
  "llm_response": "..."
}
```

### 3. 终端摘要

脚本运行结束后，会在终端打印统计摘要：

```text
=== Analysis Summary ===
Total Decisions Analyzed: 150
Wins: 85
Losses: 45
Open: 20
Win Rate (Closed Trades): 65.38%
```

---

## 🧠 如何利用数据进行反向训练？

### 场景 A：强化盈利模式 (Fine-tuning)

**目标**：让模型“记住”那些赚钱的决策逻辑。

1.  **筛选数据**：提取 `outcome == "WIN"` 的样本。
2.  **构建数据集**：
    *   **Input**: `prompt_content` (当时的市场状态)
    *   **Output**: `llm_response` (当时的高质量思考)
3.  **微调模型**：使用 OpenAI Fine-tuning API 或本地 LoRA 训练。

### 场景 B：修正错误逻辑 (Error Correction)

**目标**：识别并修正导致亏损的思维盲点。

1.  **筛选数据**：提取 `outcome == "LOSS"` 且 `confidence > 0.8` 的样本（高置信度但亏损）。
2.  **AI 诊断**：
    *   将这些样本发送给更强大的模型（如 GPT-4o）。
    *   Prompt: "这个决策导致了亏损，请分析当时的思维链 `chain_of_thought` 哪里出了问题？是忽略了趋势？还是止损设置太窄？"
3.  **优化 Prompt**：根据诊断结果，更新 `PromptBuilder` 中的系统指令（System Instruction），加入“负面清单”或“注意事项”。

### 场景 C：自我反思机制 (Self-Reflection)

**目标**：在运行时动态提醒模型。

1.  **建立向量库**：将历史亏损案例存入向量数据库（如 ChromaDB）。
2.  **RAG 检索**：在每次生成新决策前，检索相似的历史亏损场景。
3.  **动态提示**：在 Prompt 中加入：“注意！在类似的市场结构下，你过去曾因为忽略成交量而亏损，这次请务必检查成交量。”

---

## 📊 最佳实践

*   **定期运行**：建议每周运行一次分析脚本，监控胜率变化。
*   **数据积累**：建议至少积累 50-100 笔已平仓交易后再进行微调，以避免过拟合。
*   **多模型对比**：如果您运行了多个 Agent（如 DeepSeek vs Claude），可以通过对比它们的 `decision_analysis.jsonl` 来评估不同模型的优劣。
