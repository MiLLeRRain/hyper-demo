# Phase 3: 交易执行层（Trading Execution）

> **状态**: 🔄 规划中
> **依赖**: Phase 2 (AI集成) ✅ 已完成
> **目标**: 实现HyperLiquid交易执行、订单管理、风险控制

---

## 概述

Phase 3 实现完整的交易执行系统，将AI决策转化为实际交易操作。

### 核心功能

1. **HyperLiquid Exchange API集成** - 私钥签名、订单执行
2. **订单管理系统** - 订单生命周期管理、状态跟踪
3. **风险管理模块** - 仓位限制、止损止盈、资金管理
4. **执行策略** - 智能路由、滑点控制、重试机制

### 架构设计原则

- ✅ **安全优先**: 私钥隔离、多层验证
- ✅ **幂等性**: 防止重复下单
- ✅ **可观测性**: 完整的执行日志
- ✅ **容错性**: 优雅处理API错误
- ✅ **测试优先**: 使用模拟环境测试

---

## 目录

1. [架构设计](#架构设计)
2. [组件详解](#组件详解)
3. [实施计划](#实施计划)
4. [数据模型](#数据模型)
5. [API接口](#api接口)
6. [风险控制](#风险控制)
7. [测试策略](#测试策略)
8. [部署方案](#部署方案)

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     Phase 3: Trading Execution              │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Phase 2 Output  │
│  AI Decisions    │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Trading Orchestrator                      │
│  - 决策验证和风险检查                                          │
│  - 订单路由和优先级                                           │
│  - 执行协调                                                  │
└────────┬────────────────────────────────────────────────────┘
         │
         ├─────────────────┬─────────────────┬─────────────────┐
         ▼                 ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Risk Manager    │ │ Order       │ │ Position    │ │ HyperLiquid │
│                 │ │ Manager     │ │ Manager     │ │ Executor    │
│ - 仓位限制      │ │             │ │             │ │             │
│ - 杠杆检查      │ │ - 订单创建  │ │ - 仓位跟踪  │ │ - 签名认证  │
│ - 资金管理      │ │ - 状态管理  │ │ - 盈亏计算  │ │ - API调用   │
│ - 止损止盈      │ │ - 重试逻辑  │ │ - 保证金    │ │ - 错误处理  │
└─────────────────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
                           │                │                │
                           └────────────────┴────────────────┘
                                          │
                                          ▼
                           ┌──────────────────────────────┐
                           │     Database Storage         │
                           │  - agent_trades              │
                           │  - agent_decisions           │
                           │  - agent_performance         │
                           └──────────────────────────────┘
```

### 模块关系

```python
# 依赖关系
TradingOrchestrator
  ├── RiskManager          # 风险检查
  ├── OrderManager         # 订单管理
  ├── PositionManager      # 仓位管理
  └── HyperLiquidExecutor  # 执行器
      └── HyperLiquidSigner  # EIP-712签名
```

---

## 组件详解

### 3.1 HyperLiquid Exchange API集成

#### 3.1.1 私钥管理和签名

**文件**: `src/trading_bot/trading/hyperliquid_signer.py`

```python
"""EIP-712 signing for HyperLiquid Exchange API."""
from eth_account import Account
from eth_account.messages import encode_structured_data
from typing import Dict, Any
import json

class HyperLiquidSigner:
    """Handle EIP-712 signing for HyperLiquid."""

    def __init__(self, private_key: str):
        """
        Initialize signer with private key.

        Args:
            private_key: Ethereum private key (0x...)
        """
        self.account = Account.from_key(private_key)
        self.address = self.account.address

    def sign_l1_action(
        self,
        action: Dict[str, Any],
        nonce: int,
        vault_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sign L1 action (orders, cancels, etc).

        Args:
            action: Action payload
            nonce: Current timestamp in milliseconds
            vault_address: Optional vault/subaccount address

        Returns:
            Signature dict with r, s, v
        """
        # Construct EIP-712 structured data
        structured_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "Agent": [
                    {"name": "source", "type": "string"},
                    {"name": "connectionId", "type": "bytes32"}
                ],
                # ... 更多类型定义
            },
            "primaryType": "Agent",
            "domain": {
                "name": "HyperLiquid",
                "version": "1",
                "chainId": 1337,  # HyperLiquid L1
                "verifyingContract": "0x0000000000000000000000000000000000000000"
            },
            "message": {
                "action": action,
                "nonce": nonce,
                "vaultAddress": vault_address or "null"
            }
        }

        # Sign
        encoded_data = encode_structured_data(structured_data)
        signed_message = self.account.sign_message(encoded_data)

        return {
            "r": signed_message.r.to_bytes(32, 'big').hex(),
            "s": signed_message.s.to_bytes(32, 'big').hex(),
            "v": signed_message.v
        }
```

**关键点**:
- ✅ 使用 `eth_account` 库处理以太坊签名
- ✅ 实现EIP-712结构化签名
- ✅ 支持子账户（vault）
- ⚠️ 私钥安全存储（环境变量/密钥管理服务）

#### 3.1.2 HyperLiquid执行器

**文件**: `src/trading_bot/trading/hyperliquid_executor.py`

```python
"""HyperLiquid Exchange API executor."""
import logging
import time
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .hyperliquid_signer import HyperLiquidSigner
from ..models.market_data import OrderType, OrderSide, OrderStatus

logger = logging.getLogger(__name__)


class HyperLiquidExecutor:
    """Execute trades on HyperLiquid."""

    def __init__(
        self,
        base_url: str,
        private_key: str,
        vault_address: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Initialize executor.

        Args:
            base_url: Exchange API base URL
            private_key: Private key for signing
            vault_address: Optional vault/subaccount address
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.signer = HyperLiquidSigner(private_key)
        self.vault_address = vault_address
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _post_signed(self, action: Dict) -> Dict:
        """
        Make signed POST request to exchange API.

        Args:
            action: Action payload

        Returns:
            API response
        """
        nonce = int(time.time() * 1000)  # milliseconds
        signature = self.signer.sign_l1_action(action, nonce, self.vault_address)

        payload = {
            "action": action,
            "nonce": nonce,
            "signature": signature,
            "vaultAddress": self.vault_address
        }

        url = f"{self.base_url}/exchange"
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Exchange API request failed: {e}")
            raise

    def place_order(
        self,
        coin: str,
        is_buy: bool,
        size: Decimal,
        price: Optional[Decimal] = None,
        order_type: OrderType = OrderType.LIMIT,
        reduce_only: bool = False,
        client_order_id: Optional[str] = None
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Place an order on HyperLiquid.

        Args:
            coin: Trading pair (BTC, ETH, etc)
            is_buy: True for buy, False for sell
            size: Order size
            price: Limit price (None for market orders)
            order_type: Order type (LIMIT/MARKET)
            reduce_only: Whether order can only reduce position
            client_order_id: Optional client order ID

        Returns:
            Tuple of (success, order_id, error_message)
        """
        # Get asset index
        asset_index = self._get_asset_index(coin)

        # Construct order
        order = {
            "a": asset_index,
            "b": is_buy,
            "s": str(size),
            "r": reduce_only,
        }

        # Set order type
        if order_type == OrderType.MARKET:
            # Market order: IOC with extreme price
            order["p"] = "1000000.0" if is_buy else "0.1"
            order["t"] = {"limit": {"tif": "Ioc"}}
        else:
            order["p"] = str(price)
            order["t"] = {"limit": {"tif": "Gtc"}}

        # Add client order ID if provided
        if client_order_id:
            order["c"] = client_order_id

        # Submit order
        action = {
            "type": "order",
            "orders": [order],
            "grouping": "na"
        }

        try:
            response = self._post_signed(action)

            if response.get("status") == "ok":
                data = response["response"]["data"]
                status = data["statuses"][0]

                if "resting" in status:
                    order_id = status["resting"]["oid"]
                    logger.info(f"Order placed successfully: {order_id}")
                    return True, order_id, None
                elif "filled" in status:
                    order_id = status["filled"]["oid"]
                    logger.info(f"Order filled immediately: {order_id}")
                    return True, order_id, None
                else:
                    error = status.get("error", "Unknown error")
                    logger.error(f"Order rejected: {error}")
                    return False, None, error
            else:
                error = response.get("response", "API error")
                logger.error(f"Order failed: {error}")
                return False, None, str(error)

        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            return False, None, str(e)

    def cancel_order(self, coin: str, order_id: int) -> Tuple[bool, Optional[str]]:
        """
        Cancel an order.

        Args:
            coin: Trading pair
            order_id: Order ID to cancel

        Returns:
            Tuple of (success, error_message)
        """
        asset_index = self._get_asset_index(coin)

        action = {
            "type": "cancel",
            "cancels": [{
                "a": asset_index,
                "o": order_id
            }]
        }

        try:
            response = self._post_signed(action)

            if response.get("status") == "ok":
                logger.info(f"Order cancelled: {order_id}")
                return True, None
            else:
                error = response.get("response", "Cancel failed")
                logger.error(f"Cancel failed: {error}")
                return False, str(error)

        except Exception as e:
            logger.error(f"Cancel execution failed: {e}")
            return False, str(e)

    def update_leverage(
        self,
        coin: str,
        leverage: int,
        is_cross: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Update leverage for an asset.

        Args:
            coin: Trading pair
            leverage: Leverage value (1-50)
            is_cross: True for cross margin, False for isolated

        Returns:
            Tuple of (success, error_message)
        """
        asset_index = self._get_asset_index(coin)

        action = {
            "type": "updateLeverage",
            "asset": asset_index,
            "isCross": is_cross,
            "leverage": leverage
        }

        try:
            response = self._post_signed(action)

            if response.get("status") == "ok":
                logger.info(f"Leverage updated: {coin} -> {leverage}x")
                return True, None
            else:
                error = response.get("response", "Leverage update failed")
                logger.error(f"Leverage update failed: {error}")
                return False, str(error)

        except Exception as e:
            logger.error(f"Leverage update failed: {e}")
            return False, str(e)

    def _get_asset_index(self, coin: str) -> int:
        """Get asset index for coin symbol."""
        # This should query meta() endpoint or use cached mapping
        coin_to_index = {
            "BTC": 0,
            "ETH": 1,
            "SOL": 2,
            "XRP": 3,
            "DOGE": 4,
            "BNB": 5
        }
        return coin_to_index.get(coin, 0)
```

**功能**:
- ✅ 下单（限价、市价）
- ✅ 撤单
- ✅ 调整杠杆
- ✅ EIP-712签名集成
- ✅ 重试机制
- ✅ 完整错误处理

---

### 3.2 订单管理系统

#### 3.2.1 订单管理器

**文件**: `src/trading_bot/trading/order_manager.py`

```python
"""Order lifecycle management."""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.database import AgentTrade
from ..models.market_data import OrderSide, OrderStatus, OrderType
from .hyperliquid_executor import HyperLiquidExecutor

logger = logging.getLogger(__name__)


class OrderManager:
    """Manage order lifecycle and state."""

    def __init__(
        self,
        executor: HyperLiquidExecutor,
        db_session: Session
    ):
        """
        Initialize order manager.

        Args:
            executor: HyperLiquid executor instance
            db_session: Database session
        """
        self.executor = executor
        self.db = db_session

    def execute_trade(
        self,
        agent_id: UUID,
        decision_id: UUID,
        coin: str,
        side: OrderSide,
        size: Decimal,
        price: Optional[Decimal] = None,
        order_type: OrderType = OrderType.LIMIT,
        reduce_only: bool = False
    ) -> Tuple[bool, Optional[AgentTrade], Optional[str]]:
        """
        Execute a trade based on AI decision.

        Args:
            agent_id: Trading agent ID
            decision_id: AI decision ID
            coin: Trading pair
            side: Order side (LONG/SHORT)
            size: Order size
            price: Limit price
            order_type: Order type
            reduce_only: Reduce-only flag

        Returns:
            Tuple of (success, trade_record, error_message)
        """
        is_buy = (side == OrderSide.LONG)

        # Execute order
        success, order_id, error = self.executor.place_order(
            coin=coin,
            is_buy=is_buy,
            size=size,
            price=price,
            order_type=order_type,
            reduce_only=reduce_only
        )

        if not success:
            logger.error(f"Order execution failed: {error}")
            return False, None, error

        # Create trade record
        trade = AgentTrade(
            agent_id=agent_id,
            decision_id=decision_id,
            coin=coin,
            side=side.value,
            size=size,
            entry_price=price,
            entry_time=datetime.utcnow(),
            status="open",
            hyperliquid_order_id=str(order_id)
        )

        try:
            self.db.add(trade)
            self.db.commit()
            logger.info(f"Trade recorded: {trade.id}")
            return True, trade, None

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record trade: {e}")
            return False, None, str(e)

    def cancel_trade(self, trade_id: UUID) -> Tuple[bool, Optional[str]]:
        """
        Cancel an open trade.

        Args:
            trade_id: Trade ID

        Returns:
            Tuple of (success, error_message)
        """
        trade = self.db.query(AgentTrade).filter_by(id=trade_id).first()

        if not trade:
            return False, "Trade not found"

        if trade.status != "open":
            return False, f"Trade is {trade.status}, cannot cancel"

        # Cancel order on exchange
        order_id = int(trade.hyperliquid_order_id)
        success, error = self.executor.cancel_order(trade.coin, order_id)

        if success:
            trade.status = "cancelled"
            trade.exit_time = datetime.utcnow()
            self.db.commit()
            logger.info(f"Trade cancelled: {trade_id}")
            return True, None
        else:
            logger.error(f"Cancel failed: {error}")
            return False, error

    def update_trade_status(
        self,
        trade_id: UUID,
        exit_price: Optional[Decimal] = None,
        realized_pnl: Optional[Decimal] = None,
        fees: Optional[Decimal] = None
    ) -> bool:
        """
        Update trade status (called when position is closed).

        Args:
            trade_id: Trade ID
            exit_price: Exit price
            realized_pnl: Realized PnL
            fees: Trading fees

        Returns:
            Success flag
        """
        trade = self.db.query(AgentTrade).filter_by(id=trade_id).first()

        if not trade:
            logger.error(f"Trade not found: {trade_id}")
            return False

        trade.exit_price = exit_price
        trade.exit_time = datetime.utcnow()
        trade.realized_pnl = realized_pnl
        trade.fees = fees
        trade.status = "closed"

        try:
            self.db.commit()
            logger.info(f"Trade updated: {trade_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update trade: {e}")
            return False
```

**功能**:
- ✅ 执行交易并记录
- ✅ 撤单
- ✅ 更新交易状态
- ✅ 数据库持久化
- ✅ 错误处理

---

### 3.3 仓位管理

#### 3.3.1 仓位管理器

**文件**: `src/trading_bot/trading/position_manager.py`

```python
"""Position tracking and management."""
import logging
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.database import AgentTrade, TradingAgent
from ..models.market_data import Position, AccountInfo
from ..data.hyperliquid_client import HyperLiquidClient

logger = logging.getLogger(__name__)


class PositionManager:
    """Track and manage agent positions."""

    def __init__(
        self,
        info_client: HyperLiquidClient,
        db_session: Session
    ):
        """
        Initialize position manager.

        Args:
            info_client: HyperLiquid Info API client
            db_session: Database session
        """
        self.info_client = info_client
        self.db = db_session

    def get_current_positions(self, agent_id: UUID) -> List[Position]:
        """
        Get current open positions for an agent.

        Args:
            agent_id: Trading agent ID

        Returns:
            List of Position objects
        """
        # Query open trades from database
        open_trades = self.db.query(AgentTrade).filter_by(
            agent_id=agent_id,
            status="open"
        ).all()

        positions = []
        for trade in open_trades:
            # Get current market price
            try:
                current_price = self.info_client.get_price(trade.coin)

                # Calculate unrealized PnL
                if trade.side == "long":
                    unrealized_pnl = trade.size * (current_price - trade.entry_price)
                else:  # short
                    unrealized_pnl = trade.size * (trade.entry_price - current_price)

                position = Position(
                    coin=trade.coin,
                    side=trade.side,
                    size=trade.size,
                    entry_price=trade.entry_price,
                    current_price=current_price,
                    unrealized_pnl=unrealized_pnl,
                    leverage=10  # TODO: Get from agent config
                )
                positions.append(position)

            except Exception as e:
                logger.error(f"Failed to get position for {trade.coin}: {e}")

        return positions

    def get_account_value(self, agent_id: UUID) -> AccountInfo:
        """
        Calculate agent's account value and metrics.

        Args:
            agent_id: Trading agent ID

        Returns:
            AccountInfo object
        """
        agent = self.db.query(TradingAgent).filter_by(id=agent_id).first()

        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # Get all positions
        positions = self.get_current_positions(agent_id)

        # Calculate position value
        position_value = sum(
            pos.size * pos.current_price for pos in positions
        )

        # Calculate unrealized PnL
        unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)

        # Calculate realized PnL
        realized_pnl_query = self.db.query(
            func.sum(AgentTrade.realized_pnl)
        ).filter_by(
            agent_id=agent_id,
            status="closed"
        ).scalar()

        realized_pnl = realized_pnl_query or Decimal("0")

        # Calculate total value
        total_value = agent.initial_balance + realized_pnl + unrealized_pnl
        cash_balance = total_value - position_value

        return AccountInfo(
            total_value=total_value,
            cash_balance=cash_balance,
            position_value=position_value,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            available_margin=cash_balance  # Simplified
        )

    def calculate_position_size(
        self,
        agent_id: UUID,
        coin: str,
        target_value_usd: Decimal,
        leverage: int
    ) -> Decimal:
        """
        Calculate position size based on target value and leverage.

        Args:
            agent_id: Trading agent ID
            coin: Trading pair
            target_value_usd: Target position value in USD
            leverage: Leverage multiplier

        Returns:
            Position size in base currency
        """
        # Get current price
        current_price = self.info_client.get_price(coin)

        # Calculate size
        size = target_value_usd / current_price

        return size
```

**功能**:
- ✅ 实时仓位跟踪
- ✅ 账户价值计算
- ✅ 未实现盈亏计算
- ✅ 仓位大小计算

---

### 3.4 风险管理

#### 3.4.1 风险管理器

**文件**: `src/trading_bot/risk/risk_manager.py`

```python
"""Risk management and validation."""
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.database import TradingAgent
from ..models.market_data import Position
from .position_manager import PositionManager

logger = logging.getLogger(__name__)


class RiskManager:
    """Enforce risk management rules."""

    def __init__(
        self,
        position_manager: PositionManager,
        db_session: Session
    ):
        """
        Initialize risk manager.

        Args:
            position_manager: Position manager instance
            db_session: Database session
        """
        self.position_manager = position_manager
        self.db = db_session

    def validate_trade(
        self,
        agent_id: UUID,
        coin: str,
        size_usd: Decimal,
        leverage: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate trade against risk rules.

        Args:
            agent_id: Trading agent ID
            coin: Trading pair
            size_usd: Position size in USD
            leverage: Leverage to use

        Returns:
            Tuple of (is_valid, rejection_reason)
        """
        agent = self.db.query(TradingAgent).filter_by(id=agent_id).first()

        if not agent:
            return False, "Agent not found"

        # Get account info
        account = self.position_manager.get_account_value(agent_id)

        # Rule 1: Check max leverage
        if leverage > agent.max_leverage:
            return False, f"Leverage {leverage}x exceeds max {agent.max_leverage}x"

        # Rule 2: Check max position size (% of account)
        max_position_value = account.total_value * (agent.max_position_size / 100)
        if size_usd > max_position_value:
            return False, f"Position ${size_usd} exceeds max ${max_position_value} ({agent.max_position_size}% of account)"

        # Rule 3: Check available margin
        required_margin = size_usd / leverage
        if required_margin > account.available_margin:
            return False, f"Insufficient margin: need ${required_margin}, have ${account.available_margin}"

        # Rule 4: Check max total exposure
        current_exposure = account.position_value
        new_total_exposure = current_exposure + size_usd
        max_total_exposure = account.total_value * Decimal("0.8")  # 80% max

        if new_total_exposure > max_total_exposure:
            return False, f"Total exposure ${new_total_exposure} exceeds max ${max_total_exposure}"

        return True, None

    def calculate_stop_loss_price(
        self,
        entry_price: Decimal,
        stop_loss_pct: Decimal,
        is_long: bool
    ) -> Decimal:
        """
        Calculate stop loss price.

        Args:
            entry_price: Entry price
            stop_loss_pct: Stop loss percentage
            is_long: True for long, False for short

        Returns:
            Stop loss price
        """
        if is_long:
            return entry_price * (1 - stop_loss_pct / 100)
        else:
            return entry_price * (1 + stop_loss_pct / 100)

    def calculate_take_profit_price(
        self,
        entry_price: Decimal,
        take_profit_pct: Decimal,
        is_long: bool
    ) -> Decimal:
        """
        Calculate take profit price.

        Args:
            entry_price: Entry price
            take_profit_pct: Take profit percentage
            is_long: True for long, False for short

        Returns:
            Take profit price
        """
        if is_long:
            return entry_price * (1 + take_profit_pct / 100)
        else:
            return entry_price * (1 - take_profit_pct / 100)

    def check_liquidation_risk(
        self,
        agent_id: UUID,
        threshold_pct: Decimal = Decimal("20")
    ) -> Tuple[bool, List[str]]:
        """
        Check if any positions are close to liquidation.

        Args:
            agent_id: Trading agent ID
            threshold_pct: Warning threshold (% from liquidation)

        Returns:
            Tuple of (at_risk, warnings)
        """
        positions = self.position_manager.get_current_positions(agent_id)
        warnings = []
        at_risk = False

        for pos in positions:
            # Calculate distance to liquidation
            if pos.side == "long":
                liq_distance_pct = ((pos.current_price - pos.liquidation_price) / pos.current_price) * 100
            else:
                liq_distance_pct = ((pos.liquidation_price - pos.current_price) / pos.current_price) * 100

            if liq_distance_pct < threshold_pct:
                at_risk = True
                warnings.append(
                    f"{pos.coin}: {liq_distance_pct:.2f}% from liquidation"
                )

        return at_risk, warnings
```

**功能**:
- ✅ 交易前风险验证
- ✅ 仓位大小限制
- ✅ 杠杆检查
- ✅ 保证金检查
- ✅ 止损止盈计算
- ✅ 清算风险监控

---

### 3.5 交易编排器

#### 3.5.1 Trading Orchestrator

**文件**: `src/trading_bot/trading/trading_orchestrator.py`

```python
"""Orchestrate trading execution flow."""
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.database import AgentDecision, TradingAgent
from ..models.market_data import OrderType, OrderSide
from .hyperliquid_executor import HyperLiquidExecutor
from .order_manager import OrderManager
from .position_manager import PositionManager
from .risk_manager import RiskManager

logger = logging.getLogger(__name__)


class TradingOrchestrator:
    """Coordinate trading execution flow."""

    def __init__(
        self,
        executor: HyperLiquidExecutor,
        order_manager: OrderManager,
        position_manager: PositionManager,
        risk_manager: RiskManager,
        db_session: Session
    ):
        """
        Initialize trading orchestrator.

        Args:
            executor: HyperLiquid executor
            order_manager: Order manager
            position_manager: Position manager
            risk_manager: Risk manager
            db_session: Database session
        """
        self.executor = executor
        self.order_manager = order_manager
        self.position_manager = position_manager
        self.risk_manager = risk_manager
        self.db = db_session

    def execute_decision(
        self,
        agent_id: UUID,
        decision_id: UUID
    ) -> Tuple[bool, Optional[str]]:
        """
        Execute an AI trading decision.

        Args:
            agent_id: Trading agent ID
            decision_id: AI decision ID

        Returns:
            Tuple of (success, error_message)
        """
        # Load decision
        decision = self.db.query(AgentDecision).filter_by(id=decision_id).first()

        if not decision:
            return False, "Decision not found"

        # Load agent
        agent = self.db.query(TradingAgent).filter_by(id=agent_id).first()

        if not agent:
            return False, "Agent not found"

        # Handle different actions
        if decision.action == "HOLD":
            logger.info(f"Action is HOLD, no trade executed")
            return True, None

        elif decision.action == "CLOSE_POSITION":
            return self._close_position(agent_id, decision)

        elif decision.action in ["OPEN_LONG", "OPEN_SHORT"]:
            return self._open_position(agent_id, decision)

        else:
            return False, f"Unknown action: {decision.action}"

    def _open_position(
        self,
        agent_id: UUID,
        decision: AgentDecision
    ) -> Tuple[bool, Optional[str]]:
        """Open a new position."""
        # Validate risk
        is_valid, reason = self.risk_manager.validate_trade(
            agent_id=agent_id,
            coin=decision.coin,
            size_usd=decision.size_usd,
            leverage=decision.leverage
        )

        if not is_valid:
            logger.warning(f"Trade rejected by risk manager: {reason}")
            return False, reason

        # Set leverage
        success, error = self.executor.update_leverage(
            coin=decision.coin,
            leverage=decision.leverage,
            is_cross=True
        )

        if not success:
            return False, f"Failed to set leverage: {error}"

        # Calculate position size
        size = self.position_manager.calculate_position_size(
            agent_id=agent_id,
            coin=decision.coin,
            target_value_usd=decision.size_usd,
            leverage=decision.leverage
        )

        # Determine order side
        side = OrderSide.LONG if decision.action == "OPEN_LONG" else OrderSide.SHORT

        # Execute trade
        success, trade, error = self.order_manager.execute_trade(
            agent_id=agent_id,
            decision_id=decision.id,
            coin=decision.coin,
            side=side,
            size=size,
            price=None,  # Market order
            order_type=OrderType.MARKET,
            reduce_only=False
        )

        if not success:
            return False, f"Trade execution failed: {error}"

        # Place stop loss
        if decision.stop_loss_price > 0:
            self._place_stop_loss(agent_id, trade.id, decision)

        # Place take profit
        if decision.take_profit_price > 0:
            self._place_take_profit(agent_id, trade.id, decision)

        logger.info(f"Position opened successfully: {trade.id}")
        return True, None

    def _close_position(
        self,
        agent_id: UUID,
        decision: AgentDecision
    ) -> Tuple[bool, Optional[str]]:
        """Close existing position."""
        # Get open positions for the coin
        positions = self.position_manager.get_current_positions(agent_id)
        target_positions = [p for p in positions if p.coin == decision.coin]

        if not target_positions:
            return False, f"No open position for {decision.coin}"

        position = target_positions[0]

        # Execute market close (reduce-only)
        is_buy = (position.side == "short")  # Buy to close short, sell to close long

        success, order_id, error = self.executor.place_order(
            coin=decision.coin,
            is_buy=is_buy,
            size=position.size,
            price=None,
            order_type=OrderType.MARKET,
            reduce_only=True
        )

        if success:
            logger.info(f"Position closed: {decision.coin}")
            return True, None
        else:
            return False, f"Close failed: {error}"

    def _place_stop_loss(
        self,
        agent_id: UUID,
        trade_id: UUID,
        decision: AgentDecision
    ) -> bool:
        """Place stop loss order."""
        # Implementation for placing stop loss trigger order
        # Uses HyperLiquid trigger order API
        pass

    def _place_take_profit(
        self,
        agent_id: UUID,
        trade_id: UUID,
        decision: AgentDecision
    ) -> bool:
        """Place take profit order."""
        # Implementation for placing take profit trigger order
        pass
```

**功能**:
- ✅ 协调交易执行流程
- ✅ 风险验证
- ✅ 开仓
- ✅ 平仓
- ✅ 止损止盈设置
- ✅ 错误处理

---

## 实施计划

### 任务清单

#### 3.1 Exchange API集成 (5个任务)

- [ ] **3.1.1** 实现EIP-712签名器
  - 文件: `src/trading_bot/trading/hyperliquid_signer.py`
  - 依赖: `eth_account`
  - 测试: 签名验证测试

- [ ] **3.1.2** 实现HyperLiquid执行器
  - 文件: `src/trading_bot/trading/hyperliquid_executor.py`
  - 功能: 下单、撤单、改单、调整杠杆
  - 测试: Mock API测试

- [ ] **3.1.3** 添加资产索引映射
  - 功能: coin symbol → asset index
  - 数据源: `meta()` API端点
  - 缓存策略

- [ ] **3.1.4** 实现重试和错误处理
  - Exponential backoff
  - Circuit breaker
  - 错误分类

- [ ] **3.1.5** 集成测试
  - 使用HyperLiquid测试网
  - 完整交易流程测试

#### 3.2 订单管理 (4个任务)

- [ ] **3.2.1** 实现OrderManager
  - 文件: `src/trading_bot/trading/order_manager.py`
  - 功能: execute_trade, cancel_trade, update_status

- [ ] **3.2.2** 订单状态同步
  - WebSocket订单更新监听
  - 数据库状态更新

- [ ] **3.2.3** 客户端订单ID管理
  - UUID生成
  - 幂等性保证

- [ ] **3.2.4** 订单历史查询
  - 按agent查询
  - 按状态过滤
  - 分页支持

#### 3.3 仓位管理 (3个任务)

- [ ] **3.3.1** 实现PositionManager
  - 文件: `src/trading_bot/trading/position_manager.py`
  - 功能: 实时仓位跟踪

- [ ] **3.3.2** 账户价值计算
  - 总资产 = 现金 + 持仓价值 + 未实现盈亏
  - 可用保证金计算

- [ ] **3.3.3** 仓位聚合和报告
  - 按币种聚合
  - 盈亏统计
  - 性能指标

#### 3.4 风险管理 (5个任务)

- [ ] **3.4.1** 实现RiskManager
  - 文件: `src/trading_bot/risk/risk_manager.py`
  - 基础风险规则

- [ ] **3.4.2** 仓位大小验证
  - Max position size check
  - Max leverage check
  - Margin check

- [ ] **3.4.3** 清算风险监控
  - 清算价格距离计算
  - 预警阈值
  - 告警机制

- [ ] **3.4.4** 止损止盈管理
  - 自动计算SL/TP价格
  - 触发单设置
  - 跟踪止损

- [ ] **3.4.5** 资金管理规则
  - Daily loss limit
  - Maximum drawdown
  - Portfolio heat

#### 3.5 交易编排 (3个任务)

- [ ] **3.5.1** 实现TradingOrchestrator
  - 文件: `src/trading_bot/trading/trading_orchestrator.py`
  - 协调所有组件

- [ ] **3.5.2** 执行流程优化
  - 异步执行
  - 批量操作
  - 性能优化

- [ ] **3.5.3** 执行策略
  - TWAP执行
  - Smart order routing
  - Slippage control

#### 3.6 测试 (5个任务)

- [ ] **3.6.1** 单元测试
  - 所有manager测试
  - Mock dependencies
  - 覆盖率 > 80%

- [ ] **3.6.2** 集成测试
  - 完整交易流程
  - 使用测试网
  - 端到端测试

- [ ] **3.6.3** 风险测试
  - 边界条件测试
  - 错误场景测试
  - 压力测试

- [ ] **3.6.4** 性能测试
  - 延迟测试
  - 吞吐量测试
  - 并发测试

- [ ] **3.6.5** 安全测试
  - 私钥安全
  - 签名验证
  - 重放攻击防护

#### 3.7 部署和运维 (3个任务)

- [ ] **3.7.1** 配置管理
  - API密钥管理
  - 环境配置
  - 风险参数配置

- [ ] **3.7.2** 监控和告警
  - 执行监控
  - 风险监控
  - 性能监控

- [ ] **3.7.3** 文档
  - API文档
  - 部署文档
  - 运维手册

---

### 总计: 28个任务

**预估工作量**: 2-3周
**关键路径**: 3.1 → 3.2 → 3.4 → 3.5 → 3.6

---

## 数据模型

### 已有模型（Phase 2）

Phase 2已经创建了基础模型，Phase 3直接使用：

```python
# src/trading_bot/models/database.py

class AgentTrade(Base):
    """交易记录"""
    id: UUID
    agent_id: UUID
    decision_id: UUID
    coin: str
    side: str  # 'long' or 'short'
    size: Decimal
    entry_price: Decimal
    entry_time: datetime
    exit_price: Decimal
    exit_time: datetime
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    fees: Decimal
    status: str  # 'open', 'closed', 'liquidated'
    hyperliquid_order_id: str
```

### 新增模型（Phase 3需要）

无需新增数据库模型，现有模型已足够。

---

## API接口

### HyperLiquid Exchange API使用

Phase 3使用以下HyperLiquid端点：

#### 1. 下单 `POST /exchange`

```json
{
  "action": {
    "type": "order",
    "orders": [{
      "a": 0,  // asset index
      "b": true,  // is_buy
      "p": "50000.0",  // price
      "s": "0.1",  // size
      "r": false,  // reduce_only
      "t": {"limit": {"tif": "Gtc"}}
    }],
    "grouping": "na"
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

#### 2. 撤单 `POST /exchange`

```json
{
  "action": {
    "type": "cancel",
    "cancels": [{"a": 0, "o": 12345}]
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

#### 3. 调整杠杆 `POST /exchange`

```json
{
  "action": {
    "type": "updateLeverage",
    "asset": 0,
    "isCross": true,
    "leverage": 10
  },
  "nonce": 1730123456789,
  "signature": {...}
}
```

---

## 风险控制

### 风险管理策略

#### 1. 交易前验证

```python
# 检查项
✅ 最大杠杆限制
✅ 最大仓位大小
✅ 可用保证金
✅ 总敞口限制
✅ 单币种敞口
```

#### 2. 交易后监控

```python
# 监控项
✅ 清算风险距离
✅ 未实现盈亏
✅ 资金费率成本
✅ 持仓时间
```

#### 3. 止损止盈

```python
# 自动设置
✅ 基于ATR的动态止损
✅ 风险回报比验证
✅ 移动止损（trailing stop）
✅ 部分止盈
```

#### 4. 资金管理

```python
# 规则
✅ 单笔最大亏损：账户的1-2%
✅ 每日最大亏损：账户的5%
✅ 最大回撤：账户的10%
✅ 最大仓位：账户的80%
```

### 风险参数配置

```yaml
# config/risk_params.yaml
default:
  max_leverage: 10
  max_position_size_pct: 20.0
  stop_loss_pct: 2.0
  take_profit_pct: 5.0
  max_daily_loss_pct: 5.0
  max_drawdown_pct: 10.0
  liquidation_warning_threshold_pct: 20.0

conservative:
  max_leverage: 5
  max_position_size_pct: 10.0
  stop_loss_pct: 1.5

aggressive:
  max_leverage: 20
  max_position_size_pct: 30.0
  stop_loss_pct: 3.0
```

---

## 测试策略

### 测试环境

#### 1. 单元测试（Mock）

```python
# tests/unit/test_trading_executor.py
def test_place_order_success(mock_executor):
    """Test successful order placement with mocked API."""
    mock_executor._post_signed.return_value = {
        "status": "ok",
        "response": {"data": {"statuses": [{"resting": {"oid": 12345}}]}}
    }

    success, order_id, error = mock_executor.place_order(
        coin="BTC",
        is_buy=True,
        size=Decimal("0.1"),
        price=Decimal("50000")
    )

    assert success is True
    assert order_id == 12345
    assert error is None
```

#### 2. 集成测试（Testnet）

```python
# tests/integration/test_trading_flow.py
@pytest.mark.integration
def test_full_trading_cycle(testnet_executor, db_session):
    """Test complete trading cycle on testnet."""
    # 1. Set leverage
    success, _ = testnet_executor.update_leverage("BTC", 5, True)
    assert success

    # 2. Open position
    orchestrator = TradingOrchestrator(...)
    success, _ = orchestrator.execute_decision(agent_id, decision_id)
    assert success

    # 3. Check position
    positions = position_manager.get_current_positions(agent_id)
    assert len(positions) == 1

    # 4. Close position
    success, _ = orchestrator._close_position(agent_id, close_decision)
    assert success
```

#### 3. 模拟测试（Simulation）

```python
# tests/simulation/test_risk_scenarios.py
def test_liquidation_scenario():
    """Simulate liquidation scenario."""
    # 模拟极端市场波动
    # 验证风险管理是否正常工作
```

### 测试覆盖目标

- ✅ **单元测试覆盖率**: > 80%
- ✅ **集成测试**: 所有关键路径
- ✅ **风险场景测试**: 10+ scenarios
- ✅ **性能测试**: 延迟 < 500ms

---

## 部署方案

### 环境配置

#### 开发环境

```bash
# .env.development
HYPERLIQUID_API_URL=https://api.hyperliquid-testnet.xyz
HYPERLIQUID_PRIVATE_KEY=0x...  # Testnet key
DATABASE_URL=postgresql://localhost:5432/hyperliquid_trading_dev
```

#### 生产环境

```bash
# .env.production
HYPERLIQUID_API_URL=https://api.hyperliquid.xyz
HYPERLIQUID_PRIVATE_KEY=${SECRET_MANAGER_KEY}  # From secret manager
DATABASE_URL=${RDS_CONNECTION_STRING}
```

### 私钥管理

**开发环境**: 环境变量
**生产环境**: AWS Secrets Manager / HashiCorp Vault

```python
# src/trading_bot/config/secrets.py
import boto3
from botocore.exceptions import ClientError

def get_private_key(account_name: str) -> str:
    """Get private key from AWS Secrets Manager."""
    secret_name = f"hyperliquid/{account_name}/private_key"

    client = boto3.client('secretsmanager')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        logger.error(f"Failed to get secret: {e}")
        raise
```

### 监控和告警

```python
# Metrics to monitor
✅ Order success rate
✅ Order latency
✅ Position count
✅ Account value
✅ Unrealized PnL
✅ Risk metrics
✅ API errors
✅ Liquidation warnings
```

---

## 验收标准

### Phase 3完成标准

- [ ] ✅ **所有28个任务完成**
- [ ] ✅ **单元测试覆盖率 > 80%**
- [ ] ✅ **集成测试全部通过（testnet）**
- [ ] ✅ **能够成功执行完整交易流程**:
  - 设置杠杆
  - 开仓（限价/市价）
  - 设置止损止盈
  - 平仓
  - 撤单
- [ ] ✅ **风险管理规则100%执行**
- [ ] ✅ **所有交易记录正确存储到数据库**
- [ ] ✅ **错误处理完善，无未捕获异常**
- [ ] ✅ **文档完整（API文档、部署文档）**
- [ ] ✅ **在testnet完成至少10个完整交易周期**

### 性能指标

- ✅ **订单延迟**: < 500ms (P95)
- ✅ **订单成功率**: > 99%
- ✅ **风险检查延迟**: < 100ms
- ✅ **并发支持**: 10+ agents

---

## 依赖和前置条件

### 外部依赖

```txt
# requirements.txt (新增)
eth-account==0.10.0  # Ethereum account and signing
web3==6.11.0  # Web3 utilities
```

### 前置条件

- ✅ Phase 2完成（AI决策系统）
- ✅ PostgreSQL数据库运行
- ✅ HyperLiquid API访问（testnet/mainnet）
- ✅ 至少1个测试账户（带testnet资金）

---

## 风险和缓解

### 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|-----|------|------|---------|
| **EIP-712签名错误** | 高 | 中 | 使用官方参考实现，充分测试 |
| **API限流** | 中 | 低 | 实现重试和退避策略 |
| **网络延迟** | 中 | 中 | 使用testnet充分测试，优化重试 |
| **清算风险** | 高 | 低 | 严格风险管理，实时监控 |
| **私钥泄露** | 极高 | 极低 | 使用密钥管理服务，审计日志 |

### 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|-----|------|------|---------|
| **资金损失** | 极高 | 中 | 严格测试，从小资金开始 |
| **意外清算** | 高 | 低 | 保守杠杆，实时监控 |
| **API变更** | 中 | 低 | 版本锁定，定期更新 |

---

## 下一步（Phase 4）

Phase 3完成后，将进入Phase 4：

- 🔜 **Phase 4: 性能监控和优化**
  - 实时监控仪表板
  - 性能指标收集
  - 策略回测
  - A/B测试框架

---

## 参考资料

- **HyperLiquid Trading API Guide**: `docs/05_references/hyperliquid/hyperliquid_trading_api_guide_CN.md`
- **Margin and Fees**: `docs/05_references/hyperliquid/hyperliquid_margin_and_fees_CN.md`
- **EIP-712 Spec**: https://eips.ethereum.org/EIPS/eip-712
- **eth-account Docs**: https://eth-account.readthedocs.io/

---

**文档版本**: 1.0
**创建日期**: 2025-01-05
**最后更新**: 2025-01-05
**状态**: 🔄 规划完成，待开始实施
