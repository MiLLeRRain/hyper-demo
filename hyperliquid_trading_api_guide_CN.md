# HyperLiquid 交易API完整指南

## 目录

1. [概述](#概述)
2. [Exchange API 基础](#exchange-api-基础)
3. [订单类型详解](#订单类型详解)
4. [下单接口](#下单接口)
5. [订单管理](#订单管理)
6. [持仓管理](#持仓管理)
7. [认证和签名](#认证和签名)
8. [Python代码示例](#python代码示例)
9. [风险管理最佳实践](#风险管理最佳实践)
10. [常见错误和解决方案](#常见错误和解决方案)

---

## 概述

HyperLiquid 提供完整的交易API，支持永续合约交易的所有操作。

### API端点

```
主网: https://api.hyperliquid.xyz/exchange
测试网: https://api.hyperliquid-testnet.xyz/exchange
```

### 核心功能

- ✅ 下单（限价、市价、触发单）
- ✅ 撤单（单个、批量、按条件）
- ✅ 改单（单个、批量）
- ✅ 杠杆管理
- ✅ 保证金调整
- ✅ 持仓管理
- ✅ TWAP订单
- ✅ 死人开关（Dead Man's Switch）

### 请求方式

- **方法**: POST
- **Content-Type**: application/json
- **认证**: 需要私钥签名

---

## Exchange API 基础

### 请求结构

所有Exchange API请求都遵循以下基本结构：

```json
{
  "action": {
    "type": "order",  // 操作类型
    "orders": [...],   // 订单数据
    "grouping": "na"   // 订单分组
  },
  "nonce": 1730123456789,  // 当前时间戳（毫秒）
  "signature": {
    "r": "0x...",
    "s": "0x...",
    "v": 28
  },
  "vaultAddress": null  // 可选：子账户地址
}
```

### 响应格式

**成功响应：**
```json
{
  "status": "ok",
  "response": {
    "type": "order",
    "data": {
      "statuses": [
        {
          "resting": {
            "oid": 77738308  // 订单ID
          }
        }
      ]
    }
  }
}
```

**错误响应：**
```json
{
  "status": "err",
  "response": "错误信息描述"
}
```

---

## 订单类型详解

### 1. 限价单 (Limit Order)

限价单以指定价格或更好的价格成交。

**Time-In-Force (TIF) 选项：**

| TIF类型 | 说明 | 使用场景 |
|--------|------|---------|
| **GTC** (Good-Til-Canceled) | 一直有效直到成交或撤销 | 普通限价单 |
| **IOC** (Immediate-Or-Cancel) | 立即成交，未成交部分撤销 | 快速部分成交 |
| **ALO** (Add-Liquidity-Only) | 只做Maker，不吃单 | 赚取Maker返佣 |

**订单结构：**
```json
{
  "a": 0,              // 资产索引 (0=BTC, 1=ETH, etc.)
  "b": true,           // true=买入, false=卖出
  "p": "50000.0",      // 价格（字符串格式）
  "s": "0.1",          // 数量（字符串格式）
  "r": false,          // 是否只减仓
  "t": {
    "limit": {
      "tif": "Gtc"     // 时间有效性
    }
  }
}
```

### 2. 市价单 (Market Order)

市价单立即以当前最优价格成交。

**实现方式：**
- 使用 `IOC` 的限价单
- 价格设置为极端值（买入设高价，卖出设低价）

**示例：**
```json
{
  "a": 0,
  "b": true,
  "p": "1000000.0",    // 极高价格确保成交
  "s": "0.1",
  "r": false,
  "t": {
    "limit": {
      "tif": "Ioc"     // 立即成交或取消
    }
  }
}
```

### 3. 触发单 (Trigger Order)

触发单在价格触发后自动下单，用于止损/止盈。

**触发类型：**

| 类型 | 说明 | 触发条件 |
|-----|------|---------|
| **tp** (Take-Profit) | 止盈单 | 价格 ≥ 触发价 |
| **sl** (Stop-Loss) | 止损单 | 价格 ≤ 触发价 |

**订单结构：**
```json
{
  "a": 0,
  "b": false,          // 平多仓用卖单
  "p": "55000.0",      // 执行价格
  "s": "0.1",
  "r": true,           // 触发单通常设为只减仓
  "t": {
    "trigger": {
      "isMarket": false,     // false=限价触发, true=市价触发
      "triggerPx": "55000.0", // 触发价格
      "tpsl": "tp"            // tp或sl
    }
  }
}
```

### 4. TWAP订单 (时间加权平均价格)

TWAP订单在指定时间内分批执行，减少市场冲击。

**订单结构：**
```json
{
  "a": 0,
  "b": true,
  "s": "1.0",          // 总数量
  "r": false,
  "t": {
    "twap": {
      "m": 60000,      // 执行时长（毫秒）
      "randomize": false  // 是否随机化
    }
  }
}
```

---

## 下单接口

### 基本下单

**Endpoint:** `POST /exchange`

**Action Type:** `order`

**完整请求示例：**
```json
{
  "action": {
    "type": "order",
    "orders": [
      {
        "a": 0,              // BTC
        "b": true,           // 买入
        "p": "50000.0",      // $50,000
        "s": "0.1",          // 0.1 BTC
        "r": false,
        "t": {
          "limit": {
            "tif": "Gtc"
          }
        },
        "c": "0x1234567890abcdef"  // 可选：客户端订单ID
      }
    ],
    "grouping": "na"
  },
  "nonce": 1730123456789,
  "signature": {
    "r": "0x...",
    "s": "0x...",
    "v": 28
  }
}
```

**响应示例：**
```json
{
  "status": "ok",
  "response": {
    "type": "order",
    "data": {
      "statuses": [
        {
          "resting": {
            "oid": 77738308
          }
        }
      ]
    }
  }
}
```

### 订单分组 (Grouping)

**分组类型：**

| Grouping | 说明 | 使用场景 |
|----------|------|---------|
| **na** | 无分组 | 普通订单 |
| **normalTpsl** | 普通止盈止损 | 独立的TP/SL订单 |
| **positionTpsl** | 持仓止盈止损 | 与持仓绑定的TP/SL |

**使用场景：**
- `normalTpsl`: 止盈止损订单独立存在，不随持仓平仓而取消
- `positionTpsl`: 止盈止损订单与持仓绑定，平仓时自动取消

### 批量下单

可在一个请求中提交多个订单：

```json
{
  "action": {
    "type": "order",
    "orders": [
      {
        "a": 0,
        "b": true,
        "p": "50000.0",
        "s": "0.05",
        "r": false,
        "t": {"limit": {"tif": "Gtc"}}
      },
      {
        "a": 0,
        "b": true,
        "p": "49000.0",
        "s": "0.05",
        "r": false,
        "t": {"limit": {"tif": "Gtc"}}
      }
    ],
    "grouping": "na"
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

### 只减仓订单 (Reduce-Only)

只减仓订单只能减少持仓，不会增加持仓或开反向仓位。

**设置方式：**
```json
{
  "a": 0,
  "b": false,     // 平多仓用卖单
  "p": "55000.0",
  "s": "0.1",
  "r": true,      // ← 设置为true
  "t": {"limit": {"tif": "Gtc"}}
}
```

**使用场景：**
- 止盈止损订单
- 平仓订单
- 避免意外开反向仓

---

## 订单管理

### 撤单

#### 1. 按订单ID撤单

**Action Type:** `cancel`

**请求示例：**
```json
{
  "action": {
    "type": "cancel",
    "cancels": [
      {
        "a": 0,              // 资产索引
        "o": 77738308        // 订单ID
      }
    ]
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

#### 2. 按客户端订单ID撤单

**Action Type:** `cancelByCloid`

**请求示例：**
```json
{
  "action": {
    "type": "cancelByCloid",
    "cancels": [
      {
        "a": 0,
        "cloid": "0x1234567890abcdef"  // 客户端订单ID
      }
    ]
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

#### 3. 批量撤单

一次撤销多个订单：

```json
{
  "action": {
    "type": "cancel",
    "cancels": [
      {"a": 0, "o": 77738308},
      {"a": 0, "o": 77738309},
      {"a": 1, "o": 77738310}
    ]
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

### 改单

#### 1. 单个改单

**Action Type:** `modify`

**请求示例：**
```json
{
  "action": {
    "type": "modify",
    "oid": 77738308,     // 订单ID
    "order": {
      "a": 0,
      "b": true,
      "p": "51000.0",    // 新价格
      "s": "0.15",       // 新数量
      "r": false,
      "t": {"limit": {"tif": "Gtc"}}
    }
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

#### 2. 批量改单

**Action Type:** `batchModify`

**请求示例：**
```json
{
  "action": {
    "type": "batchModify",
    "modifies": [
      {
        "oid": 77738308,
        "order": {
          "a": 0,
          "b": true,
          "p": "51000.0",
          "s": "0.15",
          "r": false,
          "t": {"limit": {"tif": "Gtc"}}
        }
      },
      {
        "oid": 77738309,
        "order": {
          "a": 0,
          "b": true,
          "p": "50500.0",
          "s": "0.2",
          "r": false,
          "t": {"limit": {"tif": "Gtc"}}
        }
      }
    ]
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

---

## 持仓管理

### 调整杠杆

**Action Type:** `updateLeverage`

**请求示例：**
```json
{
  "action": {
    "type": "updateLeverage",
    "asset": 0,           // 资产索引
    "isCross": true,      // true=全仓, false=逐仓
    "leverage": 10        // 杠杆倍数
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

**注意事项：**
- 只能在没有持仓或持仓较小时调整
- 杠杆必须在允许范围内（1x - 最大杠杆）
- 全仓模式下，所有持仓共享保证金

### 调整逐仓保证金

**Action Type:** `updateIsolatedMargin`

**增加保证金：**
```json
{
  "action": {
    "type": "updateIsolatedMargin",
    "asset": 0,
    "isBuy": true,
    "ntli": 1000.0       // 增加1000 USDC
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

**减少保证金：**
```json
{
  "action": {
    "type": "updateIsolatedMargin",
    "asset": 0,
    "isBuy": false,      // false表示减少
    "ntli": 500.0        // 减少500 USDC
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

### 目标杠杆调整保证金

**Action Type:** `topUpIsolatedOnlyMargin`

自动计算需要增加的保证金以达到目标杠杆。

**请求示例：**
```json
{
  "action": {
    "type": "topUpIsolatedOnlyMargin",
    "asset": 0,
    "targetLeverage": 5.0  // 目标杠杆
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

### 平仓方法

HyperLiquid没有专门的平仓接口，通过**只减仓订单**实现平仓。

**方法1：市价平仓**
```json
{
  "action": {
    "type": "order",
    "orders": [
      {
        "a": 0,
        "b": false,          // 平多仓用卖单
        "p": "0.1",          // 极低价格确保成交
        "s": "0.1",          // 持仓数量
        "r": true,           // 只减仓
        "t": {"limit": {"tif": "Ioc"}}
      }
    ],
    "grouping": "na"
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

**方法2：限价平仓**
```json
{
  "action": {
    "type": "order",
    "orders": [
      {
        "a": 0,
        "b": false,
        "p": "55000.0",      // 指定平仓价格
        "s": "0.1",
        "r": true,
        "t": {"limit": {"tif": "Gtc"}}
      }
    ],
    "grouping": "na"
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

---

## 认证和签名

### 签名机制概述

HyperLiquid使用 **EIP-712** 签名标准保护API请求。

**关键点：**
- ✅ 使用以太坊私钥签名
- ✅ 签名基于结构化数据
- ✅ 需要正确的字段顺序
- ⚠️ **强烈建议使用官方SDK**

### 签名流程

1. **构建请求payload**
2. **计算payload的结构化哈希**
3. **使用私钥签名哈希**
4. **将签名添加到请求中**

### 常见签名错误

| 错误 | 原因 | 解决方案 |
|-----|------|---------|
| **字段顺序错误** | msgpack编码对顺序敏感 | 严格按照文档顺序 |
| **数字尾随零** | "50.00"会导致签名失败 | 使用"50.0" |
| **地址大小写** | 地址未转为小写 | 签名前统一转小写 |
| **签名恢复失败** | 签名不匹配 | 检查所有参数 |

### 签名最佳实践

**❌ 不建议：手动实现签名**
```python
# 手动签名容易出错，难以调试
import hashlib
import eth_account
# ... 复杂的签名逻辑 ...
```

**✅ 建议：使用官方SDK**
```python
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

# SDK自动处理签名
exchange = Exchange(
    wallet_address="0xYourAddress",
    private_key="0xYourPrivateKey"
)
```

### 两种签名方案

HyperLiquid有两种签名方案（参考Python SDK）：

1. **`sign_l1_action`** - 用于L1操作
2. **`sign_user_signed_action`** - 用于用户签名操作

具体使用哪种方案，请参考官方SDK源码。

---

## Python代码示例

### 安装SDK

```bash
pip install hyperliquid-python-sdk
```

### 1. 初始化连接

```python
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

# 初始化Info API（只读，无需私钥）
info = Info(constants.MAINNET_API_URL)

# 初始化Exchange API（交易，需要私钥）
exchange = Exchange(
    wallet_address="0xYourWalletAddress",
    private_key="0xYourPrivateKey",
    base_url=constants.MAINNET_API_URL
)
```

### 2. 查询账户信息

```python
# 获取账户状态
account_state = info.clearinghouse_state("0xYourAddress")

print(f"账户价值: ${account_state['marginSummary']['accountValue']}")
print(f"可用余额: ${account_state['withdrawable']}")

# 查看持仓
for position in account_state['assetPositions']:
    pos = position['position']
    print(f"币种: {pos['coin']}")
    print(f"数量: {pos['szi']}")
    print(f"入场价: {pos['entryPx']}")
    print(f"未实现盈亏: {pos['unrealizedPnl']}")
    print(f"清算价: {pos['liquidationPx']}")
    print("---")
```

### 3. 下限价单

```python
# 下BTC限价买单
order_result = exchange.order(
    coin="BTC",           # 币种
    is_buy=True,          # True=买, False=卖
    sz=0.1,               # 数量
    limit_px=50000.0,     # 限价
    order_type={"limit": {"tif": "Gtc"}},  # 订单类型
    reduce_only=False     # 是否只减仓
)

print(order_result)
# {'status': 'ok', 'response': {'type': 'order', 'data': {'statuses': [{'resting': {'oid': 12345}}]}}}
```

### 4. 下市价单

```python
# 下市价单（使用IOC限价单实现）
order_result = exchange.market_order(
    coin="BTC",
    is_buy=True,
    sz=0.05
)

print(f"订单ID: {order_result['response']['data']['statuses'][0]['filled']['oid']}")
```

### 5. 设置止损止盈

```python
# 假设持有0.1 BTC多仓，入场价$50,000

# 设置止盈单 @ $55,000
tp_order = exchange.order(
    coin="BTC",
    is_buy=False,         # 平多仓用卖单
    sz=0.1,
    limit_px=55000.0,     # 止盈价
    order_type={
        "trigger": {
            "isMarket": False,
            "triggerPx": "55000.0",
            "tpsl": "tp"
        }
    },
    reduce_only=True
)

# 设置止损单 @ $48,000
sl_order = exchange.order(
    coin="BTC",
    is_buy=False,
    sz=0.1,
    limit_px=48000.0,     # 止损价
    order_type={
        "trigger": {
            "isMarket": False,
            "triggerPx": "48000.0",
            "tpsl": "sl"
        }
    },
    reduce_only=True
)

print(f"止盈订单ID: {tp_order['response']['data']['statuses'][0]['resting']['oid']}")
print(f"止损订单ID: {sl_order['response']['data']['statuses'][0]['resting']['oid']}")
```

### 6. 撤单

```python
# 撤销单个订单
cancel_result = exchange.cancel(
    coin="BTC",
    oid=12345  # 订单ID
)

print(cancel_result)
```

### 7. 批量撤单

```python
# 撤销多个订单
cancels = [
    {"coin": "BTC", "oid": 12345},
    {"coin": "BTC", "oid": 12346},
    {"coin": "ETH", "oid": 67890}
]

for cancel in cancels:
    result = exchange.cancel(**cancel)
    print(f"撤销订单 {cancel['oid']}: {result['status']}")
```

### 8. 改单

```python
# 修改订单价格和数量
modify_result = exchange.modify(
    oid=12345,
    coin="BTC",
    is_buy=True,
    sz=0.15,           # 新数量
    limit_px=51000.0,  # 新价格
    order_type={"limit": {"tif": "Gtc"}},
    reduce_only=False
)

print(modify_result)
```

### 9. 调整杠杆

```python
# 设置BTC为10x杠杆，全仓模式
leverage_result = exchange.update_leverage(
    leverage=10,
    coin="BTC",
    is_cross=True  # True=全仓, False=逐仓
)

print(leverage_result)
```

### 10. 平仓

```python
# 市价平掉所有BTC持仓
close_result = exchange.market_close(
    coin="BTC"
)

print(f"平仓结果: {close_result}")
```

### 11. 完整交易策略示例

```python
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import time

class SimpleTradingBot:
    def __init__(self, address, private_key):
        self.info = Info(constants.MAINNET_API_URL)
        self.exchange = Exchange(address, private_key, constants.MAINNET_API_URL)
        self.address = address

    def get_current_price(self, coin):
        """获取当前价格"""
        all_mids = self.info.all_mids()
        return float(all_mids[coin])

    def get_position(self, coin):
        """获取持仓"""
        state = self.info.clearinghouse_state(self.address)
        for pos in state['assetPositions']:
            if pos['position']['coin'] == coin:
                return pos['position']
        return None

    def enter_long(self, coin, size, leverage=10):
        """开多仓"""
        # 设置杠杆
        self.exchange.update_leverage(leverage, coin, is_cross=True)

        # 获取当前价格
        current_price = self.get_current_price(coin)

        # 下市价单
        order = self.exchange.market_order(coin, is_buy=True, sz=size)
        print(f"开多仓 {coin}: {size} @ ~${current_price}")

        # 等待成交
        time.sleep(2)

        # 获取实际入场价
        position = self.get_position(coin)
        if position:
            entry_price = float(position['entryPx'])

            # 设置止盈止损
            tp_price = entry_price * 1.10  # 止盈+10%
            sl_price = entry_price * 0.95  # 止损-5%

            # 下止盈单
            self.exchange.order(
                coin=coin,
                is_buy=False,
                sz=size,
                limit_px=tp_price,
                order_type={"trigger": {"isMarket": False, "triggerPx": str(tp_price), "tpsl": "tp"}},
                reduce_only=True
            )

            # 下止损单
            self.exchange.order(
                coin=coin,
                is_buy=False,
                sz=size,
                limit_px=sl_price,
                order_type={"trigger": {"isMarket": False, "triggerPx": str(sl_price), "tpsl": "sl"}},
                reduce_only=True
            )

            print(f"入场价: ${entry_price:.2f}")
            print(f"止盈价: ${tp_price:.2f} (+10%)")
            print(f"止损价: ${sl_price:.2f} (-5%)")

    def monitor_position(self, coin):
        """监控持仓"""
        position = self.get_position(coin)
        if position:
            print(f"\n持仓状态 - {coin}")
            print(f"数量: {position['szi']}")
            print(f"入场价: ${float(position['entryPx']):.2f}")
            print(f"当前价: ${self.get_current_price(coin):.2f}")
            print(f"未实现盈亏: ${float(position['unrealizedPnl']):.2f}")
            print(f"清算价: ${float(position['liquidationPx']):.2f}")
        else:
            print(f"无{coin}持仓")

# 使用示例
if __name__ == "__main__":
    # 初始化机器人
    bot = SimpleTradingBot(
        address="0xYourAddress",
        private_key="0xYourPrivateKey"
    )

    # 开10倍杠杆BTC多仓
    bot.enter_long("BTC", size=0.01, leverage=10)

    # 监控持仓
    while True:
        bot.monitor_position("BTC")
        time.sleep(60)  # 每分钟检查一次
```

---

## 风险管理最佳实践

### 1. 仓位管理

**推荐仓位规则：**

| 账户余额 | 单笔风险 | 杠杆 | 最大持仓 |
|---------|---------|------|---------|
| < $1,000 | 1-2% | 5-10x | 30% |
| $1,000-$10,000 | 1-2% | 5-15x | 50% |
| > $10,000 | 0.5-1% | 5-20x | 70% |

**计算示例：**
```python
def calculate_position_size(account_value, risk_percent, stop_loss_percent, leverage):
    """
    计算合理的仓位大小

    account_value: 账户价值 (USDC)
    risk_percent: 单笔风险百分比 (1-2%)
    stop_loss_percent: 止损百分比 (3-5%)
    leverage: 杠杆倍数
    """
    risk_amount = account_value * (risk_percent / 100)
    position_value = risk_amount / (stop_loss_percent / 100)
    position_size_usd = position_value * leverage

    return {
        'risk_usd': risk_amount,
        'position_value': position_value,
        'notional_usd': position_size_usd
    }

# 示例：$10,000账户，1%风险，3%止损，10x杠杆
result = calculate_position_size(10000, 1, 3, 10)
print(result)
# {'risk_usd': 100, 'position_value': 3333.33, 'notional_usd': 33333.3}
```

### 2. 止损设置

**止损距离建议：**

| 交易周期 | 止损距离 | ATR倍数 |
|---------|---------|---------|
| **日内** | 1-2% | 0.5-1x |
| **短线** | 2-3% | 1-1.5x |
| **波段** | 3-5% | 1.5-2x |
| **长线** | 5-10% | 2-3x |

**代码示例：**
```python
def calculate_stop_loss(entry_price, atr, multiplier=1.5, is_long=True):
    """
    基于ATR计算止损价

    entry_price: 入场价格
    atr: 平均真实波幅
    multiplier: ATR倍数
    is_long: 是否做多
    """
    stop_distance = atr * multiplier

    if is_long:
        stop_price = entry_price - stop_distance
    else:
        stop_price = entry_price + stop_distance

    return {
        'stop_price': stop_price,
        'stop_distance': stop_distance,
        'stop_percent': (stop_distance / entry_price) * 100
    }

# 示例：BTC $50,000入场，ATR=$1000，1.5倍ATR止损
result = calculate_stop_loss(50000, 1000, 1.5, is_long=True)
print(result)
# {'stop_price': 48500.0, 'stop_distance': 1500.0, 'stop_percent': 3.0}
```

### 3. 杠杆使用指南

**杠杆与风险关系：**

| 杠杆 | 清算距离 | 风险等级 | 适用场景 |
|-----|---------|---------|---------|
| **1-3x** | -33% ~ -50% | 极低 | 长线持仓 |
| **5x** | -20% | 低 | 波段交易 |
| **10x** | -10% | 中 | 短线交易 |
| **15-20x** | -5% ~ -6.7% | 高 | 日内交易 |
| **>20x** | < -5% | 极高 | 专业交易者 |

**清算价格计算：**
```python
def calculate_liquidation_price(entry_price, leverage, is_long=True):
    """
    计算清算价格

    entry_price: 入场价格
    leverage: 杠杆倍数
    is_long: 是否做多
    """
    if is_long:
        liq_price = entry_price * (1 - 1/leverage)
    else:
        liq_price = entry_price * (1 + 1/leverage)

    distance_percent = abs(liq_price - entry_price) / entry_price * 100

    return {
        'liquidation_price': liq_price,
        'distance_percent': distance_percent
    }

# 示例：$50,000做多，10x杠杆
result = calculate_liquidation_price(50000, 10, is_long=True)
print(result)
# {'liquidation_price': 45000.0, 'distance_percent': 10.0}
```

### 4. 避免清算的策略

**策略1：保持充足保证金**
```python
def check_margin_safety(account_value, position_value, leverage, safety_buffer=2.0):
    """
    检查保证金安全性

    account_value: 账户价值
    position_value: 持仓价值
    leverage: 杠杆
    safety_buffer: 安全缓冲倍数（建议2-3倍）
    """
    required_margin = position_value / leverage
    maintenance_margin = required_margin * 0.5  # 维持保证金是初始保证金的50%
    safe_margin = maintenance_margin * safety_buffer

    is_safe = account_value >= safe_margin

    return {
        'required_margin': required_margin,
        'maintenance_margin': maintenance_margin,
        'safe_margin': safe_margin,
        'current_margin': account_value,
        'is_safe': is_safe,
        'margin_ratio': account_value / maintenance_margin if maintenance_margin > 0 else float('inf')
    }

# 示例
result = check_margin_safety(
    account_value=5000,
    position_value=50000,
    leverage=10,
    safety_buffer=2.0
)
print(result)
```

**策略2：分批建仓**
```python
def pyramid_entry(total_size, entry_count=3):
    """
    金字塔式分批建仓

    total_size: 总仓位
    entry_count: 分批次数
    """
    # 递减分配：第一批最大，逐步减小
    weights = [1.0 / (i + 1) for i in range(entry_count)]
    total_weight = sum(weights)

    batches = [(w / total_weight) * total_size for w in weights]

    return {
        'batches': batches,
        'batch_percents': [(b / total_size) * 100 for b in batches]
    }

# 示例：0.3 BTC分3批
result = pyramid_entry(0.3, 3)
print(result)
# {'batches': [0.164, 0.082, 0.054], 'batch_percents': [54.5%, 27.3%, 18.2%]}
```

### 5. 资金管理

**每日/每周止损规则：**

```python
class DailyRiskManager:
    def __init__(self, initial_balance, daily_loss_limit_pct=5, weekly_loss_limit_pct=10):
        self.initial_balance = initial_balance
        self.daily_loss_limit = initial_balance * (daily_loss_limit_pct / 100)
        self.weekly_loss_limit = initial_balance * (weekly_loss_limit_pct / 100)
        self.daily_loss = 0
        self.weekly_loss = 0

    def record_trade(self, pnl):
        """记录交易盈亏"""
        self.daily_loss += pnl if pnl < 0 else 0
        self.weekly_loss += pnl if pnl < 0 else 0

    def can_trade(self):
        """检查是否可以继续交易"""
        if abs(self.daily_loss) >= self.daily_loss_limit:
            return False, "已达到每日止损限额"
        if abs(self.weekly_loss) >= self.weekly_loss_limit:
            return False, "已达到每周止损限额"
        return True, "可以交易"

    def reset_daily(self):
        """重置每日统计"""
        self.daily_loss = 0

    def reset_weekly(self):
        """重置每周统计"""
        self.weekly_loss = 0

# 使用示例
risk_manager = DailyRiskManager(initial_balance=10000, daily_loss_limit_pct=5)
risk_manager.record_trade(-300)  # 亏损$300
can_trade, msg = risk_manager.can_trade()
print(f"{msg} - 今日亏损: ${abs(risk_manager.daily_loss)}")
```

---

## 常见错误和解决方案

### 错误1: 签名验证失败

**错误信息：**
```json
{
  "status": "err",
  "response": "Invalid signature"
}
```

**原因：**
- 私钥错误
- 请求payload格式错误
- 字段顺序错误
- nonce不正确

**解决方案：**
```python
# ✅ 使用官方SDK避免签名问题
from hyperliquid.exchange import Exchange

exchange = Exchange(
    wallet_address="0xYourAddress",
    private_key="0xYourPrivateKey"  # 确保私钥正确
)
```

### 错误2: 杠杆超过限制

**错误信息：**
```json
{
  "status": "err",
  "response": "Leverage exceeds maximum"
}
```

**原因：**
- 设置的杠杆超过资产最大杠杆
- 持仓太大，触发杠杆档位限制

**解决方案：**
```python
# 先查询资产元数据
meta = info.meta()
for asset in meta['universe']:
    print(f"{asset['name']}: 最大杠杆 {asset['maxLeverage']}x")

# 设置合理杠杆
exchange.update_leverage(leverage=10, coin="BTC", is_cross=True)
```

### 错误3: 保证金不足

**错误信息：**
```json
{
  "status": "err",
  "response": "Insufficient margin"
}
```

**原因：**
- 可用余额不足
- 已有持仓占用保证金

**解决方案：**
```python
# 检查账户余额
state = info.clearinghouse_state(address)
available = float(state['withdrawable'])
print(f"可用余额: ${available}")

# 计算所需保证金
position_value = price * size
required_margin = position_value / leverage
print(f"所需保证金: ${required_margin}")

if available >= required_margin:
    # 下单
    exchange.order(...)
else:
    print("保证金不足！")
```

### 错误4: 订单被拒绝

**错误信息：**
```json
{
  "status": "ok",
  "response": {
    "type": "order",
    "data": {
      "statuses": [{"error": "Order rejected"}]
    }
  }
}
```

**可能原因：**
- 价格远离市场价（限价单）
- 数量低于最小值
- 价格精度错误

**解决方案：**
```python
# 获取当前市场价
current_price = float(info.all_mids()["BTC"])

# 确保限价接近市场价（±5%内）
if is_buy:
    limit_px = current_price * 0.95  # 买单价格不要太低
else:
    limit_px = current_price * 1.05  # 卖单价格不要太高

# 使用合理精度（BTC通常0.5或1.0）
limit_px = round(limit_px, 1)
```

### 错误5: Nonce错误

**错误信息：**
```json
{
  "status": "err",
  "response": "Invalid nonce"
}
```

**原因：**
- nonce不是当前时间戳
- 系统时间不同步

**解决方案：**
```python
import time

# 确保nonce是当前毫秒时间戳
nonce = int(time.time() * 1000)

# SDK会自动处理nonce
exchange.order(...)  # 无需手动设置nonce
```

---

## 总结

### 核心要点

1. **使用官方SDK** - 避免签名和编码错误
2. **风险管理优先** - 永远设置止损
3. **合理使用杠杆** - 高杠杆=高风险
4. **分批建仓** - 降低平均成本
5. **监控清算价** - 保持安全边距

### 推荐资源

- **官方文档**: https://hyperliquid.gitbook.io/hyperliquid-docs
- **Python SDK**: https://github.com/hyperliquid-dex/hyperliquid-python-sdk
- **API参考**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- **社区**: https://discord.gg/hyperliquid

### 下一步

1. 阅读《HyperLiquid 保证金和费用详解》了解成本
2. 在测试网练习交易
3. 从小仓位开始
4. 逐步提高复杂度

---

**免责声明**:
杠杆交易存在巨大风险，可能导致全部资金损失。本指南仅供教育目的，不构成投资建议。请根据自己的风险承受能力谨慎交易。

**文档版本**: 1.0
**最后更新**: 2025-10-29
