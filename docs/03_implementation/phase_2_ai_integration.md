# Phase 2: AI集成（Multi-Agent架构）

## 目标
- [ ] 实现Multi-Agent并行决策系统
- [ ] 集成多个LLM Provider (DeepSeek, Qwen, GPT-4, Claude等)
- [ ] 实现NoF1.ai风格的Prompt Engineering
- [ ] 实现决策生成、解析和数据库存储

## 架构概述

**Multi-Agent设计原则**：
- 配置文件定义**可用模型池**（`llm.models`）
- 数据库定义**运行哪些agents**（`trading_agents`表）
- 每个agent = 1个LLM + 1个独立HyperLiquid账户
- 所有agents并行决策，各自交易，真实竞争

```
Market Data (共享)
    ↓
┌─────────────────────────────────────┐
│  AgentManager (加载活跃agents)     │
│  - DeepSeek Agent (账户 0x1234...) │
│  - Qwen Agent (账户 0x5678...)     │
│  - GPT-4 Agent (账户 0xabcd...)    │
└─────────────────────────────────────┘
    ↓         ↓         ↓
[Prompt]  [Prompt]  [Prompt]
    ↓         ↓         ↓
[DeepSeek][Qwen]   [GPT-4]  (并行调用)
    ↓         ↓         ↓
[Parse]   [Parse]  [Parse]
    ↓         ↓         ↓
[Execute] [Execute][Execute] (各自账户)
```

---

## 任务列表

### 2.1 LLM Provider层

#### 2.1.1 ✅ 配置模型 (已完成 Phase 1.5)
**文件**: `src/trading_bot/config/models.py`

已实现:
- ✅ `ProviderConfig` - API密钥、base_url、model_name、timeout
- ✅ `ModelConfig` - provider选择、official/openrouter配置
- ✅ `LLMConfig` - models池、max_tokens、temperature

**重要**: 已移除`active_model`/`fallback_model`字段，改为纯数据库驱动。

---

#### 2.1.2 实现LLM Provider基类
**文件**: `src/trading_bot/ai/providers/base.py`

- [ ] 定义 `BaseLLMProvider` 抽象类
  - 抽象方法: `generate(prompt: str, **kwargs) -> str`
  - 抽象方法: `generate_async(prompt: str, **kwargs) -> str` (异步版本)
- [ ] 添加通用错误处理
- [ ] 添加重试机制（使用 `tenacity` 库）
- [ ] 添加日志记录（记录调用时间、token使用等）

**示例代码**:
```python
from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    """LLM Provider抽象基类"""

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int, temperature: float, **kwargs) -> str:
        """同步生成AI回复"""
        pass

    @abstractmethod
    async def generate_async(self, prompt: str, max_tokens: int, temperature: float, **kwargs) -> str:
        """异步生成AI回复"""
        pass
```

---

#### 2.1.3 实现Official API Provider
**文件**: `src/trading_bot/ai/providers/official.py`

- [ ] 实现 `OfficialAPIProvider` 类
  - 继承自 `BaseLLMProvider`
  - 使用 `openai` Python SDK（兼容所有OpenAI-compatible APIs）
  - 支持DeepSeek官方API、Qwen官方API
- [ ] 实现 `generate()` 同步方法
- [ ] 实现 `generate_async()` 异步方法
- [ ] 添加超时处理和重试机制
- [ ] 添加详细日志（包含token消耗）

**依赖**:
```bash
pip install openai>=1.0.0
```

**示例代码**:
```python
from openai import OpenAI, AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class OfficialAPIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str, model_name: str, timeout: int = 30):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, prompt: str, max_tokens: int, temperature: float, **kwargs) -> str:
        logger.info(f"Calling {self.model_name} at {self.base_url}")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        logger.info(f"Tokens used: {response.usage.total_tokens}")
        return response.choices[0].message.content

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_async(self, prompt: str, max_tokens: int, temperature: float, **kwargs) -> str:
        logger.info(f"Async calling {self.model_name} at {self.base_url}")
        response = await self.async_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        logger.info(f"Tokens used: {response.usage.total_tokens}")
        return response.choices[0].message.content
```

---

#### 2.1.4 实现OpenRouter Provider
**文件**: `src/trading_bot/ai/providers/openrouter.py`

- [ ] 实现 `OpenRouterProvider` 类
  - 继承自 `BaseLLMProvider`
  - 使用 `openai` Python SDK（OpenRouter兼容OpenAI API）
  - 支持所有OpenRouter上的模型
- [ ] 实现 `generate()` 和 `generate_async()` 方法
- [ ] 处理OpenRouter特有的HTTP Headers（可选）

**示例代码**:
```python
from openai import OpenAI, AsyncOpenAI

class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str, timeout: int = 30):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.timeout = timeout
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=timeout
        )
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=timeout
        )

    # generate() 和 generate_async() 实现与OfficialAPIProvider类似
```

---

### 2.2 Multi-Agent编排层

#### 2.2.1 实现AgentManager
**文件**: `src/trading_bot/orchestration/agent_manager.py`

这是**核心组件**，管理所有trading agents。

- [ ] 实现 `AgentManager` 类
  - 从数据库加载活跃agents（`status='active'`）
  - 为每个agent创建对应的LLM Provider实例
  - 为每个agent创建HyperLiquid客户端（使用agent自己的API密钥）
- [ ] 实现 `_create_llm_provider()` 工厂方法
- [ ] 实现 `get_active_agents()` 方法
- [ ] 实现 `reload_agents()` 方法（动态刷新agent列表）

**示例代码**:
```python
from sqlalchemy.orm import Session
from src.trading_bot.models.database import TradingAgent
from src.trading_bot.config.models import LLMConfig
from src.trading_bot.ai.providers.official import OfficialAPIProvider
from src.trading_bot.ai.providers.openrouter import OpenRouterProvider
import logging

logger = logging.getLogger(__name__)

class AgentManager:
    """管理所有trading agents"""

    def __init__(self, db_session: Session, llm_config: LLMConfig):
        self.db = db_session
        self.llm_config = llm_config
        self.agents: list[TradingAgent] = []
        self.llm_providers: dict[str, BaseLLMProvider] = {}  # agent_id -> provider
        self._load_active_agents()

    def _load_active_agents(self):
        """从数据库加载活跃的agents"""
        self.agents = self.db.query(TradingAgent)\
            .filter(TradingAgent.status == 'active')\
            .all()

        logger.info(f"Loaded {len(self.agents)} active trading agents")

        # 为每个agent创建LLM provider
        for agent in self.agents:
            self.llm_providers[str(agent.id)] = self._create_llm_provider(agent)

    def _create_llm_provider(self, agent: TradingAgent) -> BaseLLMProvider:
        """为agent创建LLM provider"""
        model_name = agent.llm_model

        # 检查模型是否在配置中定义
        if model_name not in self.llm_config.models:
            raise ValueError(f"Model '{model_name}' not found in config.llm.models")

        model_config = self.llm_config.models[model_name]
        provider_type = model_config.provider

        if provider_type == "official":
            provider_cfg = model_config.official
            return OfficialAPIProvider(
                api_key=provider_cfg.api_key,
                base_url=provider_cfg.base_url,
                model_name=provider_cfg.model_name,
                timeout=provider_cfg.timeout
            )
        elif provider_type == "openrouter":
            provider_cfg = model_config.openrouter
            return OpenRouterProvider(
                api_key=provider_cfg.api_key,
                model_name=provider_cfg.model_name,
                timeout=provider_cfg.timeout
            )
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

    def get_llm_provider(self, agent: TradingAgent) -> BaseLLMProvider:
        """获取agent的LLM provider"""
        return self.llm_providers[str(agent.id)]

    def reload_agents(self):
        """重新加载agents（支持热更新）"""
        self._load_active_agents()
```

---

#### 2.2.2 实现MultiAgentOrchestrator
**文件**: `src/trading_bot/orchestration/multi_agent_orchestrator.py`

这是**决策循环的核心**，协调所有agents并行决策。

- [ ] 实现 `MultiAgentOrchestrator` 类
- [ ] 实现 `run_decision_cycle()` 方法（主循环）
  - 采集市场数据（共享）
  - 并行调用所有agents的LLM生成决策
  - 解析每个agent的决策
  - 将决策存储到数据库（`agent_decisions`表）
- [ ] 实现 `_generate_agent_decision()` 方法（单个agent决策）
- [ ] 实现异步并行调用（使用`asyncio.gather`）

**示例代码**:
```python
import asyncio
from datetime import datetime
from src.trading_bot.data.collector import DataCollector
from src.trading_bot.ai.prompt_builder import PromptBuilder
from src.trading_bot.ai.decision_parser import DecisionParser
from src.trading_bot.models.database import AgentDecision
import logging

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """多agent并行决策编排器"""

    def __init__(self, db_session: Session, config: TradingBotConfig):
        self.db = db_session
        self.config = config
        self.agent_manager = AgentManager(db_session, config.llm)
        self.data_collector = DataCollector(config.exchange, config.trading)
        self.prompt_builder = PromptBuilder()
        self.decision_parser = DecisionParser()

    async def run_decision_cycle(self):
        """运行一轮决策周期（所有agents并行）"""
        logger.info("=== Starting decision cycle ===")

        # 1. 采集市场数据（所有agents共享）
        logger.info("Collecting market data...")
        market_data = self.data_collector.collect_all()

        # 2. 并行调用所有agents的LLM决策
        logger.info(f"Generating decisions for {len(self.agent_manager.agents)} agents...")
        tasks = []
        for agent in self.agent_manager.agents:
            task = self._generate_agent_decision(agent, market_data)
            tasks.append(task)

        decisions = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. 统计结果
        successful = sum(1 for d in decisions if not isinstance(d, Exception))
        failed = len(decisions) - successful
        logger.info(f"Decision cycle complete: {successful} succeeded, {failed} failed")

        return decisions

    async def _generate_agent_decision(self, agent: TradingAgent, market_data: dict):
        """为单个agent生成决策"""
        agent_id = str(agent.id)
        start_time = datetime.utcnow()

        try:
            logger.info(f"Agent {agent.name} ({agent.llm_model}): generating decision...")

            # 构建prompt
            prompt = self.prompt_builder.build(
                market_data=market_data,
                # TODO: 添加agent的持仓、账户信息、对话历史
            )

            # 调用LLM（异步）
            llm_provider = self.agent_manager.get_llm_provider(agent)
            llm_response = await llm_provider.generate_async(
                prompt=prompt,
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature
            )

            # 解析决策
            parsed_decision = self.decision_parser.parse(llm_response)

            # 保存到数据库
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            decision_record = AgentDecision(
                agent_id=agent.id,
                timestamp=start_time,
                market_data_snapshot=market_data,
                llm_prompt=prompt,
                llm_response=llm_response,
                parsed_decision=parsed_decision.dict(),
                execution_status='pending',
                processing_time_ms=int(processing_time)
            )
            self.db.add(decision_record)
            self.db.commit()

            logger.info(f"Agent {agent.name}: decision generated successfully ({processing_time:.0f}ms)")
            return decision_record

        except Exception as e:
            logger.error(f"Agent {agent.name}: decision failed - {e}")

            # 保存失败记录
            decision_record = AgentDecision(
                agent_id=agent.id,
                timestamp=start_time,
                market_data_snapshot=market_data,
                llm_prompt=prompt if 'prompt' in locals() else None,
                llm_response=str(e),
                execution_status='failed',
                error_message=str(e)
            )
            self.db.add(decision_record)
            self.db.commit()

            raise
```

---

### 2.3 Prompt Engineering

#### 2.3.1 分析NoF1.ai提示词结构
- [ ] 阅读 `docs/00_research/nof1_ai_system_prompts_and_outputs.md`
- [ ] 确定提示词各部分结构:
  - Header (时间戳、账户状态)
  - Portfolio (持仓、盈亏)
  - Market Data (6个币种的价格、K线、指标)
  - Constraints (风险规则)
  - Conversation History (最近3轮对话)
  - Task (输出格式要求)

---

#### 2.3.2 实现PromptBuilder
**文件**: `src/trading_bot/ai/prompt_builder.py`

- [ ] 实现 `PromptBuilder` 类
- [ ] 实现 `build()` 方法
  - 输入: `market_data`, `positions`, `account`, `conversation_history`
  - 输出: 约11k字符的提示词字符串
- [ ] 实现各子方法:
  - `_build_header()`
  - `_build_portfolio_section()`
  - `_build_market_section()`
  - `_build_constraints_section()`
  - `_build_conversation_section()`
  - `_build_task_section()`
- [ ] 确保提示词长度在10k-12k之间

**参考**: `docs/00_research/nof1_ai_system_prompts_and_outputs.md`

---

### 2.4 决策解析

#### 2.4.1 定义决策数据模型
**文件**: `src/trading_bot/models/decision.py`

- [ ] 实现 `Decision` Pydantic模型
  - 字段: `coin`, `action`, `position_size_usd`, `leverage`, `entry_price`, `stop_loss`, `take_profit`, `reasoning`
- [ ] 实现 `AIDecisions` Pydantic模型
  - 字段: `decisions`, `risk_assessment`, `market_sentiment`

**示例代码**:
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class Decision(BaseModel):
    """单个交易决策"""
    coin: str
    action: str  # 'long', 'short', 'close', 'hold'
    position_size_usd: Optional[float] = None
    leverage: Optional[int] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reasoning: str

class AIDecisions(BaseModel):
    """AI返回的完整决策"""
    decisions: List[Decision]
    risk_assessment: str
    market_sentiment: str
```

---

#### 2.4.2 实现DecisionParser
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
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)

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
        """从文本中提取JSON（支持Markdown包裹）"""
        # 尝试提取 ```json ... ``` 包裹的JSON
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 尝试提取 ``` ... ``` 包裹的JSON
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 假设整个文本就是JSON
        return text.strip()
```

---

### 2.5 测试

#### 2.5.1 单元测试
**文件**: `tests/unit/test_llm_providers.py`, `tests/unit/test_agent_manager.py`, `tests/unit/test_prompt_builder.py`, `tests/unit/test_decision_parser.py`

- [ ] 测试 `OfficialAPIProvider`（使用mock）
- [ ] 测试 `OpenRouterProvider`（使用mock）
- [ ] 测试 `AgentManager` 加载agents
- [ ] 测试 `AgentManager` 创建provider
- [ ] 测试 `PromptBuilder` 输出长度和格式
- [ ] 测试 `DecisionParser` 解析各种格式的JSON
- [ ] 测试 `MultiAgentOrchestrator` 并行决策逻辑

**参考**: `docs/04_testing/test_plan.md` 2.2节

---

#### 2.5.2 集成测试
**文件**: `tests/integration/test_ai_integration.py`

- [ ] 使用真实API Key调用DeepSeek（测试环境）
- [ ] 使用真实API Key调用Qwen（测试环境）
- [ ] 测试多agent并行决策
- [ ] 测试决策存储到数据库

**注意**: 集成测试需要真实API密钥，标记为`@pytest.mark.integration`，不在CI中运行。

---

## 验收标准
- [ ] 能够从数据库加载多个agents
- [ ] 每个agent能够独立生成交易决策
- [ ] 所有agents能够并行决策（使用asyncio）
- [ ] 决策解析准确率 > 95%
- [ ] 决策数据正确存储到`agent_decisions`表
- [ ] 单元测试覆盖率 > 80%

---

## 依赖
- ✅ Phase 1: 数据采集完成
- ✅ Phase 1.5: 数据库Schema和模型完成
- [ ] DeepSeek/Qwen API密钥
- [ ] PostgreSQL数据库运行

---

## 参考
- `docs/00_research/nof1_ai_system_prompts_and_outputs.md`: NoF1.ai的Prompt示例
- `docs/00_research/nof1_ai_analysis.md`: NoF1.ai系统分析
- `docs/02_architecture/system_overview.md`: 系统架构设计
- `docs/02_architecture/database_schema.md`: 数据库Schema
- `docs/05_references/llm/llm_provider_guide.md`: LLM提供商选择指南
- `docs/05_references/llm/deepseek_model_comparison.md`: DeepSeek模型对比
- `docs/05_references/llm/cost_calculator.md`: 成本估算
