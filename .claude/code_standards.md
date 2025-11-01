# 代码规范

> Python代码规范和最佳实践

## Python代码规范

### 1. 代码格式化

#### 使用工具
- **Black**: 代码格式化
- **isort**: import排序
- **autopep8**: PEP8自动修复

#### 配置文件 (`pyproject.toml`)
```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100
```

### 2. 命名规范

#### 变量和函数
```python
# ✅ 好的命名
user_name = "Alice"
total_price = 100.0
def calculate_total_price(items):
    pass

# ❌ 不好的命名
un = "Alice"  # 太短
totalPriceInUSD = 100.0  # camelCase（应该用snake_case）
def calc(items):  # 不清晰
    pass
```

#### 类
```python
# ✅ 好的命名
class DataCollector:
    pass

class TradingBot:
    pass

# ❌ 不好的命名
class data_collector:  # 应该是PascalCase
    pass
```

#### 常量
```python
# ✅ 好的命名
MAX_RETRY_COUNT = 3
API_BASE_URL = "https://api.example.com"

# ❌ 不好的命名
max_retry_count = 3  # 常量应该全大写
```

### 3. Docstring规范

#### 函数Docstring (Google Style)
```python
def collect_market_data(coin: str, interval: str = '3m') -> pd.DataFrame:
    """
    采集指定币种的市场数据

    Args:
        coin: 币种代码，如 'BTC', 'ETH'
        interval: K线间隔，默认'3m'，可选'3m', '4h'

    Returns:
        包含OHLCV和技术指标的DataFrame，至少包含以下列:
        - timestamp: 时间戳
        - open, high, low, close, volume: OHLCV数据
        - ema_20, rsi_7: 技术指标

    Raises:
        NetworkError: 网络请求失败
        APIError: API返回错误
        ValueError: 参数不合法

    Example:
        >>> collector = DataCollector()
        >>> data = collector.collect_market_data('BTC', '3m')
        >>> print(data.columns)
        ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'ema_20']
    """
    pass
```

#### 类Docstring
```python
class DataCollector:
    """
    数据采集器，负责从HyperLiquid获取市场数据

    该类封装了与HyperLiquid API的交互，提供统一的数据采集接口。
    支持多个时间框架的K线数据采集，并自动计算技术指标。

    Attributes:
        coins: 支持的币种列表
        cache: Redis缓存实例
        client: HyperLiquid客户端

    Example:
        >>> collector = DataCollector()
        >>> data = collector.collect_all()
        >>> print(list(data.keys()))
        ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP']
    """
    pass
```

### 4. 类型注解

#### 基本类型
```python
from typing import List, Dict, Optional, Union

def get_prices(coins: List[str]) -> Dict[str, float]:
    """获取多个币种的价格"""
    pass

def find_coin(symbol: str) -> Optional[Coin]:
    """查找币种，找不到返回None"""
    pass

def process_value(value: Union[int, float]) -> float:
    """处理数值，可以是int或float"""
    pass
```

#### 复杂类型
```python
from typing import TypedDict, Callable

class MarketData(TypedDict):
    """市场数据类型定义"""
    price: float
    volume: float
    timestamp: int

def process_data(
    data: List[MarketData],
    processor: Callable[[MarketData], float]
) -> List[float]:
    """处理市场数据"""
    pass
```

### 5. 错误处理

#### 具体异常
```python
# ✅ 好的错误处理
try:
    data = api.get_data()
except NetworkError as e:
    logger.error(f"Network error: {e}")
    retry()
except APIError as e:
    logger.error(f"API error: {e}")
    raise
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    raise

# ❌ 不好的错误处理
try:
    data = api.get_data()
except:  # 捕获所有异常太宽泛
    pass  # 静默错误
```

#### 自定义异常
```python
class TradingError(Exception):
    """交易相关错误的基类"""
    pass

class InsufficientBalanceError(TradingError):
    """余额不足错误"""
    pass

class PositionTooLargeError(TradingError):
    """仓位过大错误"""
    pass
```

### 6. 日志规范

```python
import logging

logger = logging.getLogger(__name__)

# ✅ 好的日志
logger.debug(f"Fetching data for {coin} at interval {interval}")
logger.info(f"AI decision generated: {decision.action}")
logger.warning(f"Cache miss for key {key}, fetching from API")
logger.error(f"Failed to execute trade: {error}", exc_info=True)
logger.critical(f"Max drawdown exceeded: {drawdown}%")

# ❌ 不好的日志
logger.info("data fetched")  # 太笼统
logger.error(str(e))  # 没有上下文
print("Debug info")  # 不要用print
```

### 7. 代码组织

#### 模块结构
```python
"""
模块docstring: 说明这个模块的作用
"""

# 标准库导入
import os
import sys
from datetime import datetime

# 第三方库导入
import pandas as pd
import numpy as np
from loguru import logger

# 本地导入
from backend.app.core.base import BaseCollector
from backend.app.utils.cache import RedisCache

# 常量定义
MAX_RETRY = 3
DEFAULT_TIMEOUT = 5

# 类定义
class MyClass:
    pass

# 函数定义
def my_function():
    pass

# 主程序入口
if __name__ == "__main__":
    pass
```

### 8. 函数设计

#### 单一职责
```python
# ✅ 好的设计
def fetch_data(coin: str) -> dict:
    """只负责获取数据"""
    pass

def calculate_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """只负责计算指标"""
    pass

def cache_data(key: str, data: dict) -> None:
    """只负责缓存"""
    pass

# ❌ 不好的设计
def fetch_and_process_and_cache(coin: str):
    """一个函数做太多事情"""
    data = fetch()
    processed = calculate()
    cache(processed)
```

#### 函数长度
- 理想: 10-20行
- 最大: 50行
- 超过50行应该考虑拆分

### 9. 注释规范

```python
# ✅ 好的注释：解释"为什么"
# 使用3分钟间隔是为了与NoF1.ai保持一致
INTERVAL = '3m'

# 缓存180秒（3分钟），确保每次循环都能获取新数据
CACHE_TTL = 180

# ❌ 不好的注释：重复代码内容
# 设置间隔为3分钟
INTERVAL = '3m'  # 没有解释为什么

# 计算总和
total = sum(values)  # 这个注释多余
```

### 10. 测试代码规范

```python
import pytest
from unittest.mock import Mock, patch

class TestDataCollector:
    """测试数据采集器"""

    def test_collect_3min_data_success(self):
        """测试成功采集3分钟数据"""
        # Arrange
        collector = DataCollector()
        expected_columns = ['open', 'high', 'low', 'close', 'volume']

        # Act
        data = collector.collect_3min_data('BTC')

        # Assert
        assert all(col in data.columns for col in expected_columns)
        assert len(data) == 10

    def test_collect_3min_data_network_error(self):
        """测试网络错误时的重试机制"""
        # Arrange
        collector = DataCollector()

        # Act & Assert
        with patch('backend.app.core.api.get') as mock_get:
            mock_get.side_effect = NetworkError("Connection failed")
            with pytest.raises(NetworkError):
                collector.collect_3min_data('BTC')

            # 验证重试了3次
            assert mock_get.call_count == 3
```

---

## TypeScript/JavaScript 代码规范 (Web前端)

### TODO: 待补充
- ESLint配置
- Prettier配置
- React/Next.js最佳实践
- TypeScript类型定义规范

---

## Git Commit规范

### Commit Message格式
```
[模块名] 动作 + 简述

详细说明（可选）

Closes #issue编号
```

### 示例
```
[DataCollector] Add Redis caching for market data

- Implement cache layer with 180s TTL
- Add cache hit/miss metrics
- Handle cache failures gracefully

Closes #42
```

### 动作词汇表
- `Add`: 新增功能
- `Update`: 更新功能
- `Fix`: 修复bug
- `Remove`: 删除功能
- `Refactor`: 重构代码
- `Docs`: 更新文档
- `Test`: 添加/修改测试
- `Style`: 代码格式化（不影响功能）
- `Perf`: 性能优化

---

## 代码审查清单

在提交PR或commit前，检查以下项：

- [ ] 代码已经过Black和isort格式化
- [ ] 所有函数有docstring和类型注解
- [ ] 所有测试通过
- [ ] 测试覆盖率 > 80%
- [ ] 无Pylint错误（评分>8.0）
- [ ] 无硬编码的敏感信息
- [ ] 日志级别合适
- [ ] 错误处理完整
- [ ] 文档已更新

---

## 参考资料

- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Black Code Style](https://black.readthedocs.io/)
- [Type Hints PEP 484](https://peps.python.org/pep-0484/)
