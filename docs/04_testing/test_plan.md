# 测试计划

AI交易系统的完整测试策略和测试用例

---

## 1. 测试策略概述

参考 `.claude/testing_strategy.md` 的测试金字塔模型：

```
       /\
      /E2E\         端到端测试 (5%)
     /------\
    /场景测试\       Scenario Tests (10%)
   /----------\
  /业务规则验证\     Business Rules (15%)
 /--------------\
/   单元测试    \    Unit Tests (70%)
```

### 1.1 测试目标
- 代码覆盖率 > 80%
- 所有Must Have功能100%测试覆盖
- 所有风险管理规则100%验证
- 关键路径端到端测试

### 1.2 测试工具
- **单元测试**: pytest
- **Mock**: pytest-mock, unittest.mock
- **覆盖率**: pytest-cov
- **代码质量**: pylint, mypy
- **性能测试**: pytest-benchmark

---

## 2. 单元测试 (70%)

### 2.1 数据层测试

#### 2.1.1 DataCollector测试
**文件**: `tests/unit/data/test_collector.py`

```python
def test_fetch_prices_success(mock_hyperliquid_client):
    """测试成功获取价格数据"""
    collector = DataCollector(config)
    prices = collector.fetch_prices()

    assert "BTC" in prices
    assert prices["BTC"].price > 0
    assert prices["BTC"].timestamp is not None

def test_fetch_prices_retry_on_failure(mock_hyperliquid_client):
    """测试API失败时重试机制"""
    # Mock第1-2次失败，第3次成功
    mock_hyperliquid_client.get_prices.side_effect = [
        NetworkError(), NetworkError(), {"BTC": {...}}
    ]

    collector = DataCollector(config)
    prices = collector.fetch_prices()

    assert mock_hyperliquid_client.get_prices.call_count == 3
    assert "BTC" in prices

def test_fetch_klines_returns_dataframe():
    """测试K线数据返回格式"""
    collector = DataCollector(config)
    klines = collector.fetch_klines("BTC", "3m", 100)

    assert isinstance(klines, pd.DataFrame)
    assert len(klines) == 100
    assert list(klines.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
```

#### 2.1.2 TechnicalIndicators测试
**文件**: `tests/unit/data/test_indicators.py`

```python
def test_ema_calculation():
    """测试EMA计算准确性"""
    klines = create_mock_klines()  # Helper function
    indicators = TechnicalIndicators()

    ema_20 = indicators.ema(klines, 20)

    # 与TradingView对比，误差 < 0.1%
    expected = 95123.45
    assert abs(ema_20 - expected) / expected < 0.001

def test_macd_calculation():
    """测试MACD计算"""
    klines = create_mock_klines()
    indicators = TechnicalIndicators()

    macd = indicators.macd(klines)

    assert "macd" in macd
    assert "signal" in macd
    assert "histogram" in macd
```

---

### 2.2 AI层测试

#### 2.2.1 PromptFormatter测试
**文件**: `tests/unit/ai/test_formatter.py`

```python
def test_prompt_length():
    """测试提示词长度在10k-12k之间"""
    formatter = PromptFormatter()
    prompt = formatter.format(market_data, positions, account, history)

    assert 10000 < len(prompt) < 12000

def test_prompt_contains_all_sections():
    """测试提示词包含所有必需部分"""
    formatter = PromptFormatter()
    prompt = formatter.format(market_data, positions, account, history)

    assert "Current Time" in prompt
    assert "Portfolio Status" in prompt
    assert "Market Data" in prompt
    assert "Trading Constraints" in prompt
    assert "Previous Conversation" in prompt

def test_prompt_includes_all_coins():
    """测试提示词包含所有6个币种"""
    formatter = PromptFormatter()
    prompt = formatter.format(market_data, positions, account, history)

    for coin in ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"]:
        assert coin in prompt
```

#### 2.2.2 DecisionParser测试
**文件**: `tests/unit/ai/test_parser.py`

```python
def test_parse_valid_json():
    """测试解析有效的JSON决策"""
    parser = DecisionParser()
    ai_response = '''
    ```json
    {
      "decisions": [
        {"coin": "BTC", "action": "OPEN_LONG", ...}
      ],
      "risk_assessment": "Medium"
    }
    ```
    '''

    decisions = parser.parse(ai_response)

    assert len(decisions.decisions) == 1
    assert decisions.decisions[0].coin == "BTC"
    assert decisions.risk_assessment == "Medium"

def test_parse_markdown_wrapped_json():
    """测试解析Markdown包裹的JSON"""
    # AI可能返回 ```json ... ``` 格式
    pass

def test_parse_invalid_json_raises_error():
    """测试无效JSON抛出异常"""
    parser = DecisionParser()
    invalid_response = "This is not JSON"

    with pytest.raises(ParsingError):
        parser.parse(invalid_response)
```

---

### 2.3 风险管理层测试

#### 2.3.1 RiskValidator测试
**文件**: `tests/unit/risk/test_validator.py`

```python
def test_validate_position_size_exceeds_limit():
    """测试仓位大小超过限制"""
    validator = RiskValidator(config, position_manager)
    decision = Decision(
        coin="BTC",
        action="OPEN_LONG",
        position_size_usd=3000,  # 超过$2000限制
        leverage=5,
        stop_loss=93500
    )

    assert validator.validate(decision) == False

def test_validate_leverage_exceeds_limit():
    """测试杠杆超过限制"""
    validator = RiskValidator(config, position_manager)
    decision = Decision(..., leverage=15)  # 超过10x限制

    assert validator.validate(decision) == False

def test_validate_no_stop_loss():
    """测试缺少止损"""
    validator = RiskValidator(config, position_manager)
    decision = Decision(..., stop_loss=None)

    assert validator.validate(decision) == False

def test_validate_all_checks_pass():
    """测试所有检查通过"""
    validator = RiskValidator(config, position_manager)
    decision = Decision(
        coin="BTC",
        action="OPEN_LONG",
        position_size_usd=1000,
        leverage=5,
        entry_price=95000,
        stop_loss=93500
    )

    assert validator.validate(decision) == True
```

---

## 3. 业务规则验证 (15%)

### 3.1 风险规则测试
**文件**: `tests/business_rules/test_risk_rules.py`

```python
@pytest.mark.business_rule
def test_rule_single_position_max_size():
    """业务规则: 单个币种最大仓位$2000"""
    # 场景：尝试开仓$2500
    # 期望：被风险验证拒绝
    pass

@pytest.mark.business_rule
def test_rule_max_leverage_10x():
    """业务规则: 最大杠杆10x"""
    pass

@pytest.mark.business_rule
def test_rule_auto_close_on_15_percent_loss():
    """业务规则: 单仓亏损15%自动止损"""
    # 场景：持仓亏损达到-15.1%
    # 期望：风险监控自动平仓
    pass

@pytest.mark.business_rule
def test_rule_stop_trading_on_30_percent_drawdown():
    """业务规则: 账户回撤30%停止交易"""
    # 场景：账户总回撤达到-30.1%
    # 期望：系统自动停止所有交易
    pass
```

---

## 4. 场景测试 (10%)

### 4.1 完整交易循环场景
**文件**: `tests/scenarios/test_trading_cycle.py`

```python
@pytest.mark.scenario
def test_complete_cycle_with_open_long():
    """场景：完整的开多仓交易循环"""
    # Given: 系统运行中，无持仓
    # When: AI建议开BTC多仓
    # Then: 验证整个流程
    #   1. 市场数据采集成功
    #   2. AI生成有效决策
    #   3. 风险验证通过
    #   4. 订单执行成功
    #   5. 持仓记录创建
    #   6. 对话历史保存
    pass

@pytest.mark.scenario
def test_cycle_with_risk_rejection():
    """场景：AI决策被风险规则拒绝"""
    # Given: AI建议开20x杠杆
    # When: 风险验证
    # Then: 决策被拒绝，记录日志，不执行交易
    pass

@pytest.mark.scenario
def test_cycle_with_api_failure_and_retry():
    """场景：API失败重试"""
    # Given: HyperLiquid API暂时不可用
    # When: 数据采集阶段
    # Then: 自动重试3次，最终成功或跳过本次循环
    pass
```

---

## 5. 端到端测试 (5%)

### 5.1 完整系统测试
**文件**: `tests/e2e/test_full_system.py`

```python
@pytest.mark.e2e
@pytest.mark.slow
def test_bot_start_to_stop_lifecycle():
    """E2E: Bot完整生命周期"""
    # 1. 启动Bot
    # 2. 运行3个完整交易循环
    # 3. 验证每个循环都成功
    # 4. 验证数据库记录正确
    # 5. 停止Bot
    pass

@pytest.mark.e2e
def test_emergency_stop_on_critical_drawdown():
    """E2E: 紧急停止"""
    # 场景：模拟账户回撤达到-30%
    # 期望：系统自动紧急停止
    pass
```

---

## 6. 集成测试

### 6.1 HyperLiquid API集成测试
**文件**: `tests/integration/test_hyperliquid.py`

```python
@pytest.mark.integration
@pytest.mark.skipif(not has_testnet_credentials(), reason="需要测试网凭证")
def test_place_real_order_on_testnet():
    """集成测试：在测试网下真实订单"""
    # 使用真实的HyperLiquid测试网
    # 下一个小额订单
    # 验证订单执行
    pass
```

### 6.2 LLM Provider集成测试
**文件**: `tests/integration/test_llm_providers.py`

```python
@pytest.mark.integration
def test_deepseek_api_call():
    """集成测试：DeepSeek API调用"""
    provider = DeepSeekProvider(api_key=os.getenv("DEEPSEEK_API_KEY"))
    response = provider.generate("Test prompt")

    assert response is not None
    assert len(response) > 0
```

---

## 7. 性能测试

### 7.1 交易循环性能
**文件**: `tests/performance/test_cycle_performance.py`

```python
@pytest.mark.performance
def test_cycle_completes_within_30_seconds(benchmark):
    """性能测试：交易循环30秒内完成"""
    result = benchmark(orchestrator.run_cycle)

    assert result.stats['mean'] < 30.0  # 平均耗时 < 30秒

@pytest.mark.performance
def test_ai_decision_within_10_seconds(benchmark):
    """性能测试：AI决策10秒内完成"""
    result = benchmark(llm_manager.generate_decision, prompt)

    assert result.stats['mean'] < 10.0
```

---

## 8. 测试数据管理

### 8.1 测试Fixtures
**文件**: `tests/conftest.py`

```python
@pytest.fixture
def mock_config():
    """模拟配置"""
    return Config(
        exchange=ExchangeConfig(...),
        llm=LLMConfig(...),
        risk=RiskConfig(
            max_position_size_usd=2000,
            max_leverage=10,
            stop_loss_pct=0.15
        )
    )

@pytest.fixture
def mock_market_data():
    """模拟市场数据"""
    return {
        "BTC": MarketData(
            price=Price(price=95420.0, ...),
            klines_3m=create_mock_klines(100),
            indicators_3m={...}
        ),
        ...
    }

@pytest.fixture
def mock_hyperliquid_client(mocker):
    """Mock HyperLiquid客户端"""
    client = mocker.Mock(spec=HyperliquidClient)
    client.get_prices.return_value = {...}
    return client
```

---

## 9. 测试执行流程

### 9.1 本地开发测试
```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行特定模块测试
pytest tests/unit/ai/ -v

# 生成覆盖率报告
pytest tests/ --cov=trading_bot --cov-report=html

# 运行性能测试
pytest tests/performance/ -v --benchmark-only
```

### 9.2 CI/CD测试流程
```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run unit tests
        run: pytest tests/unit/ --cov=trading_bot --cov-fail-under=80

      - name: Run business rules
        run: pytest tests/business_rules/ -v

      - name: Run scenarios
        run: pytest tests/scenarios/ -v

      - name: Lint
        run: pylint trading_bot/

      - name: Type check
        run: mypy trading_bot/
```

---

## 10. 测试覆盖率目标

| 模块 | 目标覆盖率 | 优先级 |
|------|----------|--------|
| data/ | > 85% | High |
| ai/ | > 80% | High |
| trading/ | > 90% | Critical |
| risk/ | **100%** | Critical |
| orchestration/ | > 75% | Medium |
| infrastructure/ | > 70% | Medium |

**关键模块100%覆盖**:
- `risk/validator.py`
- `risk/monitor.py`

---

## 11. 测试环境

### 11.1 环境配置
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    scenario: Scenario tests
    business_rule: Business rule validation
    performance: Performance tests
    slow: Slow running tests

addopts = -v --strict-markers --tb=short
```

### 11.2 测试数据库
- 使用临时SQLite数据库: `tests/test_trading_bot.db`
- 每个测试后自动清理

---

## 12. 回归测试

每个Phase完成后执行完整的回归测试套件：

```bash
# Phase 1完成后
pytest tests/unit/data/ tests/business_rules/test_data_collection.py -v

# Phase 2完成后
pytest tests/unit/ai/ tests/scenarios/test_ai_decision.py -v

# Phase 3完成后
pytest tests/unit/trading/ tests/business_rules/test_risk_rules.py -v

# 所有Phase完成后
pytest tests/ --cov=trading_bot --cov-report=html
```

---

## 13. 验收测试

### 13.1 阶段验收标准

**Phase 1: 数据采集**
- [ ] 所有单元测试通过
- [ ] 数据采集覆盖率 > 85%
- [ ] 能够稳定获取6个币种数据
- [ ] 技术指标计算准确（与TradingView对比误差 < 0.1%）

**Phase 2: AI集成**
- [ ] AI决策解析成功率 > 95%
- [ ] 提示词长度10k-12k
- [ ] Provider故障转移测试通过

**Phase 3: 交易执行**
- [ ] 所有风险规则测试通过（100%覆盖）
- [ ] 订单执行集成测试通过
- [ ] 风险管理模块覆盖率 100%

**Phase 4-5: 自动化和工具**
- [ ] 端到端测试通过
- [ ] 系统可连续运行24小时无崩溃
- [ ] 总代码覆盖率 > 80%

---

## 14. 参考
- `.claude/testing_strategy.md`: 完整测试策略
- `docs/01_requirements/functional_requirements.md`: 功能需求
- pytest文档: https://docs.pytest.org/
