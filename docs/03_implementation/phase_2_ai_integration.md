# Phase 2: AI集成

## 目标
- [ ] 集成DeepSeek/Qwen LLM（Model-Centric设计）
- [ ] 实现NoF1.ai风格的Prompt Engineering
- [ ] 实现决策生成和解析

## 任务列表

### 2.1 LLM Provider集成（Model-Centric架构）

#### 2.1.1 定义配置模型
**文件**: `src/trading_bot/config/llm_config.py`

- [ ] 实现 `ProviderConfig` Pydantic模型
  - 字段: `api_key`, `base_url`, `model_name`, `timeout`
- [ ] 实现 `ModelConfig` Pydantic模型
  - 字段: `provider`, `official`, `openrouter`
- [ ] 实现 `LLMConfig` Pydantic模型
  - 字段: `active_model`, `fallback_model`, `models`, `max_tokens`, `temperature`

**参考**: `docs/02_architecture/system_overview.md` 2.2.2节

---

#### 2.1.2 实现服务提供商基类
**文件**: `src/trading_bot/ai/providers/base.py`

- [ ] 定义 `BaseLLMProvider` 抽象类
  - 抽象方法: `generate(prompt: str, **kwargs) -> str`
- [ ] 添加通用错误处理
- [ ] 添加重试机制（使用 `tenacity` 库）

**示例代码**:
```python
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """生成AI回复"""
        pass
```

---

#### 2.1.3 实现Official API Provider
**文件**: `src/trading_bot/ai/providers/official.py`

- [ ] 实现 `OfficialAPIProvider` 类
  - 继承自 `BaseLLMProvider`
  - 使用 `openai` Python SDK（兼容所有OpenAI-compatible APIs）
  - 支持DeepSeek官方API、Qwen官方API
- [ ] 实现 `generate()` 方法
- [ ] 添加超时处理
- [ ] 添加日志记录

**依赖**:
```bash
pip install openai>=1.0.0
```

**示例代码**:
```python
from openai import OpenAI

class OfficialAPIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str, model_name: str, timeout: int):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.timeout = timeout
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            timeout=self.timeout,
            **kwargs
        )
        return response.choices[0].message.content
```

---

#### 2.1.4 实现OpenRouter Provider
**文件**: `src/trading_bot/ai/providers/openrouter.py`

- [ ] 实现 `OpenRouterProvider` 类
  - 继承自 `BaseLLMProvider`
  - 使用 `openai` Python SDK（OpenRouter兼容OpenAI API）
  - 支持所有OpenRouter上的模型
- [ ] 实现 `generate()` 方法
- [ ] 处理OpenRouter特有的HTTP Headers（可选）

**示例代码**:
```python
from openai import OpenAI

class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str, model_name: str, timeout: int):
        self.api_key = api_key
        self.base_url = base_url  # https://openrouter.ai/api/v1
        self.model_name = model_name  # e.g. "deepseek/deepseek-chat"
        self.timeout = timeout
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            timeout=self.timeout,
            **kwargs
        )
        return response.choices[0].message.content
```

---

#### 2.1.5 实现LLMProviderManager
**文件**: `src/trading_bot/ai/llm_manager.py`

- [ ] 实现 `LLMProviderManager` 类
  - 管理active和fallback模型
  - 实现工厂方法 `_create_provider()`
  - 实现 `generate_decision()` 方法，支持自动fallback
- [ ] 从config.yaml加载配置
- [ ] 实现模型切换逻辑（active失败 → fallback）
- [ ] 添加详细日志（记录使用的模型名和provider类型）

**参考**: `docs/02_architecture/system_overview.md` 2.2.2节

**示例代码**:
```python
class LLMProviderManager:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.active_model_name = config.active_model
        self.fallback_model_name = config.fallback_model

        self.active_provider = self._create_provider(
            self.active_model_name,
            config.models[self.active_model_name]
        )
        self.fallback_provider = self._create_provider(
            self.fallback_model_name,
            config.models[self.fallback_model_name]
        )

    def _create_provider(self, model_name: str, model_config: ModelConfig) -> BaseLLMProvider:
        provider_type = model_config.provider

        if provider_type == "official":
            provider_config = model_config.official
            return OfficialAPIProvider(...)
        elif provider_type == "openrouter":
            provider_config = model_config.openrouter
            return OpenRouterProvider(...)
        else:
            raise ValueError(f"Unknown provider: {provider_type}")

    def generate_decision(self, prompt: str) -> str:
        try:
            logger.info(f"Using active model: {self.active_model_name}")
            return self.active_provider.generate(
                prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
        except Exception as e:
            logger.warning(f"Active model failed: {e}, switching to fallback")
            return self.fallback_provider.generate(
                prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
```

---

### 2.2 Prompt Engineering

#### 2.2.1 分析NoF1.ai提示词结构
- [ ] 阅读 `docs/00_research/nof1_ai_system_prompts_and_outputs.md`
- [ ] 确定提示词各部分结构:
  - Header (时间戳、账户状态)
  - Portfolio (持仓、盈亏)
  - Market Data (6个币种的价格、K线、指标)
  - Constraints (风险规则)
  - Conversation History (最近3轮对话)
  - Task (输出格式要求)

---

#### 2.2.2 实现PromptFormatter
**文件**: `src/trading_bot/ai/prompt_formatter.py`

- [ ] 实现 `PromptFormatter` 类
- [ ] 实现 `format()` 方法
  - 输入: `market_data`, `positions`, `account`, `conversation_history`
  - 输出: 约11k字符的提示词字符串
- [ ] 实现各子方法:
  - `_build_header()`
  - `_build_portfolio_section()`
  - `_build_market_section()`
  - `_build_constraints_section()`
  - `_build_conversation_section()`
  - `_build_task_section()`
- [ ] 确保提示词长度在10k-12k之间（过长截断）

**参考**: `docs/02_architecture/system_overview.md` 2.2.1节

---

#### 2.2.3 实现对话历史管理
**文件**: `src/trading_bot/ai/conversation_manager.py`

- [ ] 实现 `ConversationManager` 类
- [ ] 保存对话到数据库（`conversations` 表）
- [ ] 查询最近N轮对话
- [ ] 格式化对话为提示词格式

---

### 2.3 决策解析

#### 2.3.1 定义决策数据模型
**文件**: `src/trading_bot/models/decision.py`

- [ ] 实现 `Decision` Pydantic模型
  - 字段: `coin`, `action`, `position_size_usd`, `leverage`, `entry_price`, `stop_loss`, `take_profit`, `reasoning`
- [ ] 实现 `AIDecisions` Pydantic模型
  - 字段: `decisions`, `risk_assessment`, `market_sentiment`

**参考**: `docs/02_architecture/system_overview.md` 2.2.3节

---

#### 2.3.2 实现DecisionParser
**文件**: `src/trading_bot/ai/decision_parser.py`

- [ ] 实现 `DecisionParser` 类
- [ ] 实现 `parse()` 方法
  - 从AI响应中提取JSON
  - 处理Markdown包裹的JSON (```json ... ```)
  - 使用Pydantic验证schema
- [ ] 实现 `_extract_json()` 辅助方法
- [ ] 错误处理（记录原始响应）

**示例代码**:
```python
import json
from typing import Optional

class DecisionParser:
    def parse(self, ai_response: str) -> AIDecisions:
        try:
            json_str = self._extract_json(ai_response)
            data = json.loads(json_str)
            return AIDecisions(**data)
        except Exception as e:
            logger.error(f"Parse failed: {e}")
            logger.error(f"Raw response: {ai_response}")
            raise

    def _extract_json(self, text: str) -> str:
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        return text
```

---

### 2.4 集成测试

#### 2.4.1 单元测试
- [ ] 测试 `OfficialAPIProvider`（使用mock）
- [ ] 测试 `OpenRouterProvider`（使用mock）
- [ ] 测试 `LLMProviderManager` fallback机制
- [ ] 测试 `PromptFormatter` 输出长度和格式
- [ ] 测试 `DecisionParser` 解析各种格式的JSON

**参考**: `docs/04_testing/test_plan.md` 2.2节

---

#### 2.4.2 集成测试
- [ ] 使用真实API Key调用DeepSeek（测试环境）
- [ ] 使用真实API Key调用Qwen（测试环境）
- [ ] 使用OpenRouter调用同一模型（测试环境）
- [ ] 测试fallback机制（故意让primary失败）

**参考**: `docs/04_testing/test_plan.md` 6.2节

## 验收标准
- [ ] AI能够生成有效的交易决策
- [ ] 决策解析准确率 > 95%
- [ ] 单元测试覆盖率 > 80%

## 依赖
- Phase 1: 数据采集完成
- LLM Provider选择: `docs/05_references/llm/llm_provider_guide.md`

---

## 参考
- `docs/00_research/nof1_ai_system_prompts_and_outputs.md`: NoF1.ai的Prompt示例
- `docs/00_research/nof1_ai_analysis.md`: NoF1.ai系统分析
- `docs/05_references/llm/llm_provider_guide.md`: LLM提供商选择指南
- `docs/05_references/llm/deepseek_model_comparison.md`: DeepSeek模型对比
- `docs/05_references/llm/cost_calculator.md`: 成本估算
