"""HyperLiquid Exchange API executor.

This module wraps the official HyperLiquid Python SDK to provide
trading execution with dry-run support.

Official SDK: https://github.com/hyperliquid-dex/hyperliquid-python-sdk
"""

import logging
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

logger = logging.getLogger(__name__)


class OrderType:
    """Order type constants."""
    LIMIT = "limit"
    MARKET = "market"


class HyperLiquidExecutor:
    """Execute trades on HyperLiquid Exchange using official SDK.

    This executor wraps the official HyperLiquid Python SDK and adds
    dry-run functionality for safe testing.

    Attributes:
        exchange: Official HyperLiquid Exchange instance
        info: Official HyperLiquid Info instance for market data
        dry_run: Whether to simulate trades without executing
        wallet_address: Wallet address derived from private key
    """

    def __init__(
        self,
        base_url: str,
        private_key: str,
        vault_address: Optional[str] = None,
        timeout: int = 10,
        use_dynamic_assets: bool = True,
        dry_run: bool = False
    ):
        """Initialize executor with official HyperLiquid SDK.

        Args:
            base_url: Exchange API base URL (mainnet or testnet)
            private_key: Private key for signing transactions
            vault_address: Optional vault/subaccount address
            timeout: Request timeout in seconds
            use_dynamic_assets: Compatibility parameter (always uses SDK's dynamic loading)
            dry_run: If True, simulate trades without executing

        Example:
            >>> # Real trading on testnet
            >>> executor = HyperLiquidExecutor(
            ...     "https://api.hyperliquid-testnet.xyz",
            ...     "0xprivatekey",
            ...     dry_run=False
            ... )
            >>> # Dry-run mode (testing)
            >>> executor = HyperLiquidExecutor(
            ...     "https://api.hyperliquid-testnet.xyz",
            ...     "0xprivatekey",
            ...     dry_run=True
            ... )
        """
        self.base_url = base_url.rstrip("/")
        self.dry_run = dry_run
        self.vault_address = vault_address

        # Create wallet from private key
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key

        self.wallet = Account.from_key(private_key)
        self.wallet_address = self.wallet.address

        # Initialize official SDK components
        # Info API for market data (read-only)
        self.info = Info(base_url, skip_ws=True)

        # Exchange API for trading (if not dry-run)
        if not dry_run:
            self.exchange = Exchange(
                wallet=self.wallet,
                base_url=base_url,
                vault_address=vault_address,
                timeout=timeout
            )
        else:
            self.exchange = None

        # Dry-run tracking
        self._dry_run_order_id_counter = 10000
        self._dry_run_orders: Dict[int, Dict[str, Any]] = {}

        mode_str = "DRY-RUN MODE" if self.dry_run else "LIVE MODE"
        logger.info(
            f"Initialized HyperLiquidExecutor for {self.wallet_address} [{mode_str}]"
        )

    def get_address(self) -> str:
        """Get wallet address.

        Returns:
            Wallet address (checksum format)
        """
        return self.wallet_address

    def get_supported_assets(self) -> List[str]:
        """Get list of supported trading assets.

        Returns:
            List of asset/coin symbols

        Example:
            >>> executor = HyperLiquidExecutor(...)
            >>> assets = executor.get_supported_assets()
            >>> print(assets[:5])
            ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC']
        """
        try:
            meta = self.info.meta()
            universe = meta.get("universe", [])
            return [asset["name"] for asset in universe]
        except Exception as e:
            logger.error(f"Failed to fetch supported assets: {e}")
            # Return common assets as fallback
            return ["BTC", "ETH", "SOL", "AVAX", "MATIC", "LINK", "UNI", "AAVE"]

    def _round_price_to_tick(self, coin: str, price: float) -> float:
        """Round price to valid tick size for the asset.

        Args:
            coin: Asset symbol
            price: Price to round

        Returns:
            Price rounded to valid tick size

        Note:
            This uses a simplified tick size mapping. For most assets at typical
            price ranges, this should work. For production, consider fetching
            exact tick sizes from exchange metadata if available.
        """
        # Common tick sizes based on price ranges
        # BTC, ETH use $10 tick at high prices
        # Most altcoins use smaller ticks
        if coin in ["BTC", "ETH"] and price > 1000:
            tick = 10.0
        elif price > 100:
            tick = 1.0
        elif price > 10:
            tick = 0.1
        elif price > 1:
            tick = 0.01
        else:
            tick = 0.001

        return round(price / tick) * tick

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
            coin: Asset symbol (e.g., "BTC", "ETH")
            is_buy: True for buy, False for sell
            size: Order size in base currency
            price: Limit price (required for limit orders)
            order_type: "limit" or "market"
            reduce_only: If True, order can only reduce position
            time_in_force: "Gtc", "Ioc", or "Alo"
            client_order_id: Optional client order ID

        Returns:
            Tuple of (success, order_id, error_message)

        Example:
            >>> success, oid, error = executor.place_order(
            ...     "BTC", True, Decimal("0.01"), Decimal("50000"), "limit"
            ... )
            >>> if success:
            ...     print(f"Order placed: {oid}")
        """
        # DRY-RUN MODE: Simulate order without executing
        if self.dry_run:
            self._dry_run_order_id_counter += 1
            order_id = self._dry_run_order_id_counter

            self._dry_run_orders[order_id] = {
                "coin": coin,
                "is_buy": is_buy,
                "size": float(size),
                "price": float(price) if price else None,
                "order_type": order_type,
                "reduce_only": reduce_only,
                "timestamp": time.time(),
                "status": "filled"  # Simulate immediate fill
            }

            logger.info(
                f"[DRY-RUN] Simulated order: {coin} {'BUY' if is_buy else 'SELL'} "
                f"{size} @ {price or 'MARKET'} (OID: {order_id})"
            )
            return True, order_id, None

        # LIVE MODE: Use official SDK
        try:
            # Prepare order type parameter
            if order_type == OrderType.MARKET:
                order_type_param = {"limit": {"tif": "Ioc"}}
                # For market orders, use extreme price
                if price is None:
                    price = Decimal("1000000") if is_buy else Decimal("0.1")
            else:
                if price is None:
                    return False, None, "Limit orders require a price"
                order_type_param = {"limit": {"tif": time_in_force}}

            # Round price to valid tick size
            rounded_price = self._round_price_to_tick(coin, float(price))

            # Place order using official SDK
            result = self.exchange.order(
                coin,
                is_buy=is_buy,
                sz=float(size),
                limit_px=rounded_price,
                order_type=order_type_param,
                reduce_only=reduce_only,
                cloid=client_order_id
            )

            # Parse result
            if result and result.get("status") == "ok":
                response_data = result.get("response", {}).get("data", {})
                statuses = response_data.get("statuses", [])

                if statuses:
                    status = statuses[0]

                    # Check if order was placed (resting) or filled immediately
                    if "resting" in status:
                        order_id = status["resting"]["oid"]
                        logger.info(
                            f"Order placed: {coin} {'BUY' if is_buy else 'SELL'} "
                            f"{size} @ {price} (OID: {order_id})"
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

            error_msg = result.get("response", "Unknown error") if result else "No response"
            logger.error(f"Order failed: {error_msg}")
            return False, None, str(error_msg)

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
            coin: Asset symbol
            order_id: Order ID to cancel

        Returns:
            Tuple of (success, error_message)

        Example:
            >>> success, error = executor.cancel_order("BTC", 12345)
            >>> if success:
            ...     print("Order cancelled")
        """
        # DRY-RUN MODE: Simulate cancellation
        if self.dry_run:
            if order_id in self._dry_run_orders:
                self._dry_run_orders[order_id]["status"] = "cancelled"
                logger.info(f"[DRY-RUN] Cancelled order {order_id}")
                return True, None
            else:
                logger.warning(f"[DRY-RUN] Order {order_id} not found")
                return False, "Order not found"

        # LIVE MODE: Use official SDK
        try:
            result = self.exchange.cancel(coin, order_id)

            if result and result.get("status") == "ok":
                logger.info(f"Cancelled order {order_id} for {coin}")
                return True, None
            else:
                error = result.get("response", "Unknown error") if result else "No response"
                logger.error(f"Cancel failed: {error}")
                return False, str(error)

        except Exception as e:
            logger.error(f"Cancel order failed: {e}")
            return False, str(e)

    def update_leverage(
        self,
        coin: str,
        leverage: int,
        is_cross: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """Update leverage for an asset.

        Args:
            coin: Asset symbol
            leverage: Leverage multiplier (1-50)
            is_cross: True for cross margin, False for isolated

        Returns:
            Tuple of (success, error_message)

        Example:
            >>> success, error = executor.update_leverage("BTC", 5, True)
            >>> if success:
            ...     print("Leverage updated to 5x cross margin")
        """
        # Validate leverage
        if not (1 <= leverage <= 50):
            error = f"Invalid leverage {leverage}x (must be 1-50x)"
            logger.error(error)
            return False, error

        # DRY-RUN MODE: Simulate leverage update
        if self.dry_run:
            logger.info(
                f"[DRY-RUN] Updated leverage for {coin}: {leverage}x "
                f"({'cross' if is_cross else 'isolated'})"
            )
            return True, None

        # LIVE MODE: Use official SDK
        try:
            result = self.exchange.update_leverage(leverage, coin, is_cross)

            if result and result.get("status") == "ok":
                logger.info(
                    f"Updated leverage for {coin}: {leverage}x "
                    f"({'cross' if is_cross else 'isolated'})"
                )
                return True, None
            else:
                error = result.get("response", "Unknown error") if result else "No response"
                logger.error(f"Leverage update failed: {error}")
                return False, str(error)

        except Exception as e:
            logger.error(f"Leverage update failed: {e}")
            return False, str(e)

    def __repr__(self) -> str:
        """String representation."""
        mode = "DRY-RUN" if self.dry_run else "LIVE"
        return f"HyperLiquidExecutor({self.wallet_address}, mode={mode})"
