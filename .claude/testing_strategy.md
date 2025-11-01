# 测试策略

> 本项目的测试方法和要求

## 测试金字塔

```
       /\
      /E2E\         端到端测试 (5%)
     /------\
    /场景测试\       Scenario Tests (10%)
   /----------\
  /业务规则验证\     Business Rules (15%)
 /--------------\
/   单元测试    \    Unit Tests (70%)
----------------
```

---

## 1. 单元测试 (Unit Tests)

### 目标
- 测试单个函数或方法
- 隔离外部依赖（使用Mock）
- 快速执行（< 1秒）
- 覆盖率 > 80%

### 要求
- 每个公共方法必须有单元测试
- 测试正常情况（Happy Path）
- 测试边界情况（Boundary Cases）
- 测试错误情况（Error Cases）

### 示例
```python
# tests/unit/test_data_collector.py
import pytest
from unittest.mock import Mock, patch
from backend.app.core.data_collector import DataCollector

class TestDataCollector:
    def test_collect_3min_data_success(self):
        """测试正常情况：成功采集数据"""
        collector = DataCollector()
        data = collector.collect_3min_data('BTC')

        assert len(data) == 10
        assert 'ema_20' in data.columns

    def test_collect_3min_data_invalid_coin(self):
        """测试错误情况：无效的币种"""
        collector = DataCollector()

        with pytest.raises(ValueError, match="Invalid coin"):
            collector.collect_3min_data('INVALID')

    @patch('backend.app.core.hyperliquid_client.get_candles')
    def test_collect_3min_data_network_error(self, mock_get):
        """测试错误情况：网络错误重试机制"""
        mock_get.side_effect = NetworkError("Connection failed")

        collector = DataCollector()

        with pytest.raises(NetworkError):
            collector.collect_3min_data('BTC')

        # 验证重试了3次
        assert mock_get.call_count == 3
```

---

## 2. 集成测试 (Integration Tests)

### 目标
- 测试模块间的集成
- 使用真实的外部依赖（测试网API、测试数据库）
- 验证数据流

### 要求
- 测试与HyperLiquid API的交互
- 测试与数据库的交互
- 测试与Redis的交互
- 可以运行较慢（< 10秒）

### 示例
```python
# tests/integration/test_hyperliquid_integration.py
import pytest
from backend.app.core.data_collector import DataCollector

@pytest.mark.integration
class TestHyperLiquidIntegration:
    def test_fetch_real_btc_data(self):
        """测试从真实的HyperLiquid测试网获取BTC数据"""
        collector = DataCollector(testnet=True)
        data = collector.collect_3min_data('BTC')

        # 验证数据格式
        assert not data.empty
        assert 'close' in data.columns

        # 验证数据合理性
        assert data['close'].min() > 0
        assert data['close'].max() < 1000000
```

---

## 3. 业务规则验证 (Business Rules Tests)

### 目标
- 确保实现符合NoF1.ai的业务逻辑
- 验证与NoF1.ai的一致性
- 这些测试失败意味着严重问题

### 要求
- 技术指标计算必须与NoF1一致
- AI调用频率必须是3分钟
- 提示词格式必须符合NoF1
- 风险管理规则必须满足

### 示例
```python
# tests/business_rules/test_nof1_compliance.py
import pytest
from backend.app.core.trading_bot import TradingBot

class TestNoF1Compliance:
    def test_ai_call_frequency(self):
        """业务规则：必须每3分钟调用AI一次"""
        bot = TradingBot()
        bot.start()

        # 监控10分钟
        call_times = monitor_ai_calls(duration=600)

        # 验证调用间隔
        for i in range(1, len(call_times)):
            interval = (call_times[i] - call_times[i-1]).total_seconds()
            assert 175 <= interval <= 185, \
                f"调用间隔{interval}秒，应该是180秒±5秒"

    def test_technical_indicators_match_nof1(self):
        """业务规则：技术指标必须与NoF1.ai一致"""
        # 使用NoF1的实际数据
        nof1_data = load_nof1_test_data('BTC')

        our_indicators = calculate_indicators(nof1_data['prices'])

        # 验证误差 < 0.1%
        assert abs(our_indicators['ema_20'] - nof1_data['expected_ema_20']) < 1.0
```

---

## 4. 场景测试 (Scenario Tests)

### 目标
- 测试完整的业务流程
- 端到端验证
- 模拟真实使用场景

### 要求
- 测试完整的交易循环
- 测试异常恢复流程
- 测试性能要求

### 示例
```python
# tests/scenarios/test_trading_cycle.py
import pytest

def test_complete_trading_cycle():
    """
    场景：完整的交易流程
    - 数据采集 → AI决策 → 交易执行
    """
    # 1. 采集数据
    collector = DataCollector()
    market_data = collector.collect_all()
    assert len(market_data) == 6

    # 2. AI决策
    ai = AIManager()
    decision = ai.get_decision(market_data, [], {})
    assert decision is not None

    # 3. 执行交易
    executor = TradeExecutor(testnet=True)
    result = executor.execute_decision(decision)
    assert result['success'] is True
```

---

## 5. 性能测试 (Performance Tests)

### 目标
- 验证性能指标
- 发现性能瓶颈

### 要求
- 数据采集 < 2秒
- AI决策 < 10秒
- 完整循环 < 30秒

### 示例
```python
# tests/performance/test_performance.py
import pytest
import time

@pytest.mark.performance
def test_data_collection_performance():
    """测试数据采集性能"""
    collector = DataCollector()

    start = time.time()
    collector.collect_all()
    elapsed = time.time() - start

    assert elapsed < 5.0, f"数据采集耗时{elapsed}秒，应该<5秒"
```

---

## 测试工具和框架

### Python
- **pytest**: 测试框架
- **pytest-cov**: 覆盖率报告
- **pytest-mock**: Mock工具
- **pytest-benchmark**: 性能测试
- **faker**: 测试数据生成

### 配置文件 (`pytest.ini`)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=backend
    --cov-report=term-missing
    --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    business: Business rules tests
    scenario: Scenario tests
    performance: Performance tests
    slow: Slow running tests
```

---

## 测试覆盖率要求

### 目标
- 整体覆盖率 > 80%
- 核心模块覆盖率 > 90%

### 关键模块
- `data_collector.py`: > 90%
- `ai_manager.py`: > 90%
- `trade_executor.py`: > 95% (关键)
- `risk_manager.py`: > 95% (关键)

### 豁免
- `__init__.py`
- 配置文件
- 脚本文件

---

## 测试数据管理

### Fixtures
```python
# tests/conftest.py
import pytest

@pytest.fixture
def mock_market_data():
    """提供模拟的市场数据"""
    return {
        'BTC': {
            'price': 70000,
            'ema_20': 69500,
            ...
        }
    }

@pytest.fixture
def hyperliquid_client(testnet=True):
    """提供HyperLiquid客户端"""
    return HyperLiquidClient(testnet=testnet)
```

### 测试数据文件
```
tests/
├── fixtures/
│   ├── nof1_btc_data.json      # NoF1实际数据
│   ├── market_data_sample.json # 市场数据样本
│   └── ai_response_sample.json # AI响应样本
```

---

## CI/CD 测试流程

### 每次Commit
```bash
# 快速测试（单元测试）
pytest tests/unit/ -v

# 代码质量检查
black --check backend/
pylint backend/
```

### 每次PR
```bash
# 完整测试
pytest tests/ -v --cov=backend

# 业务规则验证
pytest tests/business_rules/ -v

# 性能测试
pytest tests/performance/ -v
```

### 每天
```bash
# 集成测试（使用真实API）
pytest tests/integration/ -v

# 端到端测试
pytest tests/scenarios/ -v
```

---

## TODO: 待补充

- [ ] 前端测试策略（React Testing Library）
- [ ] API测试策略（Postman/Newman）
- [ ] 安全测试（Bandit, Safety）
- [ ] 压力测试（Locust）
