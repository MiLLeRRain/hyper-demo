"""HyperLiquid Exchange API executor.

This module implements the executor for placing orders and managing
positions on HyperLiquid exchange.
"""

import logging
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .hyperliquid_signer import HyperLiquidSigner

logger = logging.getLogger(__name__)


class OrderType:
    """Order type constants."""
    LIMIT = "limit"
    MARKET = "market"


class HyperLiquidExecutor:
    """Execute trades on HyperLiquid Exchange.

    This executor handles all trading operations including placing orders,
    canceling orders, and managing leverage on HyperLiquid.

    Attributes:
        base_url: Exchange API base URL
        signer: HyperLiquidSigner instance for signing requests
        vault_address: Optional vault/subaccount address
        timeout: Request timeout in seconds
        session: Requests session for connection pooling
    """

    def __init__(
        self,
        base_url: str,
        private_key: str,
        vault_address: Optional[str] = None,
        timeout: int = 10
    ):
        """Initialize executor.

        Args:
            base_url: Exchange API base URL (mainnet or testnet)
            private_key: Private key for signing transactions
            vault_address: Optional vault/subaccount address
            timeout: Request timeout in seconds

        Example:
            >>> executor = HyperLiquidExecutor(
            ...     "https://api.hyperliquid.xyz",
            ...     "0xprivatekey"
            ... )
        """
        self.base_url = base_url.rstrip("/")
        self.signer = HyperLiquidSigner(private_key)
        self.vault_address = vault_address
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        logger.info(
            f"Initialized HyperLiquidExecutor for {self.signer.address} "
            f"on {self.base_url}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _post_signed(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Make signed POST request to exchange API.

        This method:
        1. Generates a nonce (current timestamp)
        2. Signs the action using EIP-712
        3. Sends the signed request to the exchange
        4. Handles errors and retries

        Args:
            action: Action payload to sign and send

        Returns:
            API response dict

        Raises:
            requests.RequestException: On API error after retries
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
            data = response.json()

            logger.debug(f"Exchange API response: {data.get('status')}")
            return data

        except requests.RequestException as e:
            logger.error(f"Exchange API request failed: {e}")
            raise

    def place_order(
        self,
        coin: str,
        is_buy: bool,
        size: Decimal,
        price: Optional[Decimal] = None,
        order_type: str = OrderType.LIMIT,
        reduce_only: bool = False,
        time_in_force: str = "Gtc",
        client_order_id: Optional[str] = None
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """Place an order on HyperLiquid.

        Args:
            coin: Trading pair symbol (BTC, ETH, etc)
            is_buy: True for buy order, False for sell order
            size: Order size in base currency
            price: Limit price (None for market orders)
            order_type: "limit" or "market"
            reduce_only: If True, order can only reduce position
            time_in_force: "Gtc" (Good-til-Cancel), "Ioc" (Immediate-or-Cancel),
                          or "Alo" (Add-Liquidity-Only)
            client_order_id: Optional client-side order ID for tracking

        Returns:
            Tuple of (success, order_id, error_message)
            - success: True if order placed successfully
            - order_id: Exchange order ID if successful
            - error_message: Error description if failed

        Example:
            >>> # Market buy order
            >>> success, oid, err = executor.place_order(
            ...     "BTC", True, Decimal("0.1"), order_type="market"
            ... )
            >>> # Limit sell order
            >>> success, oid, err = executor.place_order(
            ...     "BTC", False, Decimal("0.1"), Decimal("51000")
            ... )
        """
        # Get asset index (will be implemented in 3.1.3)
        asset_index = self._get_asset_index(coin)

        # Construct order
        order = {
            "a": asset_index,
            "b": is_buy,
            "s": str(size),
            "r": reduce_only,
        }

        # Set order type and price
        if order_type == OrderType.MARKET:
            # Market order: IOC with extreme price
            order["p"] = "1000000.0" if is_buy else "0.1"
            order["t"] = {"limit": {"tif": "Ioc"}}
        else:
            if price is None:
                raise ValueError("Limit orders require a price")
            order["p"] = str(price)
            order["t"] = {"limit": {"tif": time_in_force}}

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
                    logger.info(
                        f"Order placed: {coin} {'BUY' if is_buy else 'SELL'} "
                        f"{size} @ {price or 'MARKET'} (OID: {order_id})"
                    )
                    return True, order_id, None

                elif "filled" in status:
                    order_id = status["filled"]["oid"]
                    logger.info(
                        f"Order filled immediately: {coin} {'BUY' if is_buy else 'SELL'} "
                        f"{size} (OID: {order_id})"
                    )
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

    def cancel_order(
        self,
        coin: str,
        order_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Cancel an order by order ID.

        Args:
            coin: Trading pair symbol
            order_id: Order ID to cancel

        Returns:
            Tuple of (success, error_message)

        Example:
            >>> success, err = executor.cancel_order("BTC", 12345)
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
                logger.info(f"Order cancelled: {coin} OID {order_id}")
                return True, None
            else:
                error = response.get("response", "Cancel failed")
                logger.error(f"Cancel failed for OID {order_id}: {error}")
                return False, str(error)

        except Exception as e:
            logger.error(f"Cancel execution failed: {e}")
            return False, str(e)

    def cancel_by_cloid(
        self,
        coin: str,
        client_order_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Cancel an order by client order ID.

        Args:
            coin: Trading pair symbol
            client_order_id: Client order ID

        Returns:
            Tuple of (success, error_message)

        Example:
            >>> success, err = executor.cancel_by_cloid("BTC", "my-order-123")
        """
        asset_index = self._get_asset_index(coin)

        action = {
            "type": "cancelByCloid",
            "cancels": [{
                "a": asset_index,
                "cloid": client_order_id
            }]
        }

        try:
            response = self._post_signed(action)

            if response.get("status") == "ok":
                logger.info(f"Order cancelled by CLOID: {coin} {client_order_id}")
                return True, None
            else:
                error = response.get("response", "Cancel failed")
                logger.error(f"Cancel by CLOID failed: {error}")
                return False, str(error)

        except Exception as e:
            logger.error(f"Cancel by CLOID failed: {e}")
            return False, str(e)

    def batch_cancel(
        self,
        cancels: List[Tuple[str, int]]
    ) -> Tuple[bool, Optional[str]]:
        """Cancel multiple orders at once.

        Args:
            cancels: List of (coin, order_id) tuples

        Returns:
            Tuple of (success, error_message)

        Example:
            >>> cancels = [("BTC", 12345), ("ETH", 67890)]
            >>> success, err = executor.batch_cancel(cancels)
        """
        cancel_list = []
        for coin, order_id in cancels:
            asset_index = self._get_asset_index(coin)
            cancel_list.append({
                "a": asset_index,
                "o": order_id
            })

        action = {
            "type": "cancel",
            "cancels": cancel_list
        }

        try:
            response = self._post_signed(action)

            if response.get("status") == "ok":
                logger.info(f"Batch cancelled {len(cancels)} orders")
                return True, None
            else:
                error = response.get("response", "Batch cancel failed")
                logger.error(f"Batch cancel failed: {error}")
                return False, str(error)

        except Exception as e:
            logger.error(f"Batch cancel failed: {e}")
            return False, str(e)

    def update_leverage(
        self,
        coin: str,
        leverage: int,
        is_cross: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """Update leverage for an asset.

        Args:
            coin: Trading pair symbol
            leverage: Leverage value (1-50x, depending on asset)
            is_cross: True for cross margin, False for isolated margin

        Returns:
            Tuple of (success, error_message)

        Example:
            >>> # Set BTC to 10x cross margin
            >>> success, err = executor.update_leverage("BTC", 10, True)
        """
        asset_index = self._get_asset_index(coin)

        # Validate leverage
        if leverage < 1 or leverage > 50:
            return False, f"Invalid leverage {leverage}x (must be 1-50x)"

        action = {
            "type": "updateLeverage",
            "asset": asset_index,
            "isCross": is_cross,
            "leverage": leverage
        }

        try:
            response = self._post_signed(action)

            if response.get("status") == "ok":
                mode = "cross" if is_cross else "isolated"
                logger.info(f"Leverage updated: {coin} -> {leverage}x ({mode})")
                return True, None
            else:
                error = response.get("response", "Leverage update failed")
                logger.error(f"Leverage update failed: {error}")
                return False, str(error)

        except Exception as e:
            logger.error(f"Leverage update failed: {e}")
            return False, str(e)

    def modify_order(
        self,
        coin: str,
        order_id: int,
        new_size: Decimal,
        new_price: Decimal,
        is_buy: bool,
        reduce_only: bool = False,
        time_in_force: str = "Gtc"
    ) -> Tuple[bool, Optional[str]]:
        """Modify an existing order.

        Args:
            coin: Trading pair symbol
            order_id: Order ID to modify
            new_size: New order size
            new_price: New limit price
            is_buy: True for buy, False for sell
            reduce_only: Reduce-only flag
            time_in_force: Time in force

        Returns:
            Tuple of (success, error_message)

        Example:
            >>> success, err = executor.modify_order(
            ...     "BTC", 12345, Decimal("0.15"), Decimal("51000"), True
            ... )
        """
        asset_index = self._get_asset_index(coin)

        action = {
            "type": "modify",
            "oid": order_id,
            "order": {
                "a": asset_index,
                "b": is_buy,
                "p": str(new_price),
                "s": str(new_size),
                "r": reduce_only,
                "t": {"limit": {"tif": time_in_force}}
            }
        }

        try:
            response = self._post_signed(action)

            if response.get("status") == "ok":
                logger.info(f"Order modified: {coin} OID {order_id}")
                return True, None
            else:
                error = response.get("response", "Modify failed")
                logger.error(f"Modify failed for OID {order_id}: {error}")
                return False, str(error)

        except Exception as e:
            logger.error(f"Modify failed: {e}")
            return False, str(e)

    def _get_asset_index(self, coin: str) -> int:
        """Get asset index for coin symbol.

        This is a temporary implementation. Task 3.1.3 will implement
        proper asset index mapping from the meta() API endpoint.

        Args:
            coin: Coin symbol (BTC, ETH, etc)

        Returns:
            Asset index

        Raises:
            ValueError: If coin is not supported
        """
        # Temporary hardcoded mapping
        # TODO: Implement dynamic loading from meta() API in Task 3.1.3
        coin_to_index = {
            "BTC": 0,
            "ETH": 1,
            "SOL": 2,
            "XRP": 3,
            "DOGE": 4,
            "BNB": 5
        }

        if coin not in coin_to_index:
            raise ValueError(
                f"Unsupported coin: {coin}. "
                f"Supported: {', '.join(coin_to_index.keys())}"
            )

        return coin_to_index[coin]

    def get_address(self) -> str:
        """Get the wallet address used by this executor.

        Returns:
            Ethereum address
        """
        return self.signer.address

    def close(self):
        """Close the executor and cleanup resources."""
        self.session.close()
        logger.info("HyperLiquidExecutor closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<HyperLiquidExecutor(address='{self.signer.address}', "
            f"url='{self.base_url}')>"
        )
