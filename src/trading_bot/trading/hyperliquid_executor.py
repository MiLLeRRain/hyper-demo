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

logger = logging.getLogger(__name__)


class OrderType:  # pylint: disable=too-few-public-methods
    """Order type constants."""
    LIMIT = "limit"
    MARKET = "market"


class HyperLiquidExecutor:  # pylint: disable=too-many-instance-attributes
    """Execute trades on HyperLiquid Exchange using official SDK.

    This executor wraps the official HyperLiquid Python SDK and adds
    dry-run functionality for safe testing.

    Attributes:
        exchange: Official HyperLiquid Exchange instance
        info: Official HyperLiquid Info instance for market data
        dry_run: Whether to simulate trades without executing
        wallet_address: Wallet address derived from private key
    """

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        base_url: str,
        private_key: str,
        vault_address: Optional[str] = None,
        timeout: int = 10,
        use_dynamic_assets: bool = True,  # pylint: disable=unused-argument
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
        """
        self.base_url = base_url.rstrip("/")
        self.dry_run = dry_run
        self.vault_address = vault_address

        # Create wallet from private key
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key

        self.wallet = Account.from_key(private_key)  # pylint: disable=no-value-for-parameter
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

        # Metadata cache
        self._meta_cache = None
        self._sz_decimals_cache = {}

        mode_str = "DRY-RUN MODE" if self.dry_run else "LIVE MODE"
        logger.info(
            "Initialized HyperLiquidExecutor for %s [%s]",
            self.wallet_address, mode_str
        )

    def _get_sz_decimals(self, coin: str) -> int:
        """Get allowed size decimals for a coin from exchange metadata.

        Args:
            coin: Asset symbol

        Returns:
            Number of decimals allowed for size
        """
        # Use cache if available
        if coin in self._sz_decimals_cache:
            return self._sz_decimals_cache[coin]

        try:
            # Fetch metadata if not cached
            if self._meta_cache is None:
                self._meta_cache = self.info.meta()

            universe = self._meta_cache.get("universe", [])
            for asset in universe:
                if asset["name"] == coin:
                    sz_decimals = asset.get("szDecimals", 3)  # Default to 3 if missing
                    self._sz_decimals_cache[coin] = sz_decimals
                    return sz_decimals

            # Fallback defaults if coin not found in meta
            defaults = {"BTC": 5, "ETH": 4, "SOL": 2}
            return defaults.get(coin, 3)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to fetch size decimals for %s: %s", coin, e)
            return 3  # Safe default

    def _round_size(self, coin: str, size: float) -> float:
        """Round size to allowed decimals.

        Args:
            coin: Asset symbol
            size: Size to round

        Returns:
            Rounded size
        """
        decimals = self._get_sz_decimals(coin)
        return round(size, decimals)

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
        """
        try:
            meta = self.info.meta()
            universe = meta.get("universe", [])
            return [asset["name"] for asset in universe]
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to fetch supported assets: %s", e)
            # Return common assets as fallback
            return ["BTC", "ETH", "SOL", "AVAX", "MATIC", "LINK", "UNI", "AAVE"]

    def _round_price_to_tick(self, coin: str, price: float) -> float:
        """Round price to valid tick size for the asset.

        Args:
            coin: Asset symbol
            price: Price to round

        Returns:
            Price rounded to valid tick size
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

    # pylint: disable=too-many-positional-arguments
    def _execute_dry_run_order(
        self,
        coin: str,
        is_buy: bool,
        size: Decimal,
        price: Optional[Decimal],
        order_type: str,
        reduce_only: bool
    ) -> Tuple[bool, int, None]:
        """Execute a dry-run order simulation."""
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
            "[DRY-RUN] Simulated order: %s %s %s @ %s (OID: %s)",
            coin,
            'BUY' if is_buy else 'SELL',
            size,
            price or 'MARKET',
            order_id
        )
        return True, order_id, None

    def _calculate_market_price(self, coin: str, is_buy: bool) -> Decimal:
        """Calculate market price with slippage for market orders."""
        try:
            # Fetch current market price
            all_mids = self.info.all_mids()
            current_price = float(all_mids.get(coin, 0))
            logger.info("Market price for %s: %s", coin, current_price)

            if current_price == 0:
                logger.warning(
                    "Could not fetch price for %s, using default extreme price",
                    coin
                )
                return Decimal("1000000") if is_buy else Decimal("0.1")

            # Add 5% slippage for market orders
            slippage = 0.05
            if is_buy:
                return Decimal(str(current_price * (1 + slippage)))
            return Decimal(str(current_price * (1 - slippage)))

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to fetch current price for market order: %s", e)
            return Decimal("1000000") if is_buy else Decimal("0.1")

    # pylint: disable=too-many-positional-arguments
    def _process_order_response(
        self,
        result: Dict[str, Any],
        coin: str,
        is_buy: bool,
        size: Decimal,
        price: Optional[Decimal]
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """Process the response from the exchange order placement."""
        if result and result.get("status") == "ok":
            response_data = result.get("response", {}).get("data", {})
            statuses = response_data.get("statuses", [])

            if statuses:
                status = statuses[0]

                # Check if order was placed (resting) or filled immediately
                if "resting" in status:
                    order_id = status["resting"]["oid"]
                    logger.info(
                        "Order placed: %s %s %s @ %s (OID: %s)",
                        coin,
                        'BUY' if is_buy else 'SELL',
                        size,
                        price,
                        order_id
                    )
                    return True, order_id, None

                if "filled" in status:
                    order_id = status["filled"]["oid"]
                    logger.info(
                        "Order filled immediately: %s %s %s (OID: %s)",
                        coin,
                        'BUY' if is_buy else 'SELL',
                        size,
                        order_id
                    )
                    return True, order_id, None

                error = status.get("error", "Unknown error")
                logger.error("Order rejected: %s", error)
                return False, None, error

        error_msg = result.get("response", "Unknown error") if result else "No response"
        logger.error("Order failed: %s", error_msg)
        return False, None, str(error_msg)

    # pylint: disable=too-many-positional-arguments
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
        """
        # DRY-RUN MODE: Simulate order without executing
        if self.dry_run:
            return self._execute_dry_run_order(
                coin, is_buy, size, price, order_type, reduce_only
            )

        # LIVE MODE: Use official SDK
        try:
            # Prepare order type parameter
            if order_type == OrderType.MARKET:
                order_type_param = {"limit": {"tif": "Ioc"}}
                # For market orders, calculate price with slippage
                if price is None:
                    price = self._calculate_market_price(coin, is_buy)
            else:
                if price is None:
                    return False, None, "Limit orders require a price"
                order_type_param = {"limit": {"tif": time_in_force}}

            # Round price to valid tick size
            rounded_price = self._round_price_to_tick(coin, float(price))

            # Round size to valid decimals
            rounded_size = self._round_size(coin, float(size))

            logger.info(
                "Placing order: %s %s @ %s (Raw price: %s)",
                coin, rounded_size, rounded_price, price
            )

            # Place order using official SDK
            result = self.exchange.order(
                coin,
                is_buy=is_buy,
                sz=rounded_size,
                limit_px=rounded_price,
                order_type=order_type_param,
                reduce_only=reduce_only,
                cloid=client_order_id
            )

            return self._process_order_response(
                result, coin, is_buy, size, price
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Order execution failed: %s", e)
            return False, None, str(e)

    # pylint: disable=too-many-positional-arguments,logging-too-few-args
    def place_trigger_order(
        self,
        coin: str,
        is_buy: bool,
        size: Decimal,
        trigger_price: Decimal,
        is_tp: bool,
        reduce_only: bool = True
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """Place a trigger order (Stop-Loss or Take-Profit).

        Args:
            coin: Asset symbol
            is_buy: True for buy, False for sell
            size: Order size in base currency
            trigger_price: Price to trigger the order
            is_tp: True for Take-Profit, False for Stop-Loss
            reduce_only: Whether to only reduce position (default True)

        Returns:
            Tuple of (success, order_id, error_message)
        """
        # DRY-RUN MODE
        if self.dry_run:
            self._dry_run_order_id_counter += 1
            order_id = self._dry_run_order_id_counter
            type_str = "Take-Profit" if is_tp else "Stop-Loss"

            logger.info(
                "[DRY-RUN] Simulated %s order: %s %s %s @ %s (OID: %s)",
                type_str,
                'BUY' if is_buy else 'SELL',
                size,
                trigger_price,
                order_id
            )
            return True, order_id, None

        # LIVE MODE
        try:
            # Round values
            rounded_price = self._round_price_to_tick(coin, float(trigger_price))
            rounded_size = self._round_size(coin, float(size))

            # Construct trigger order type
            order_type = {
                "trigger": {
                    "triggerPx": rounded_price,
                    "isMarket": True,
                    "tpsl": "tp" if is_tp else "sl"
                }
            }

            type_label = 'TP' if is_tp else 'SL'
            logger.info(  # pylint: disable=logging-too-few-args
                "Placing trigger order (%s): %s %s @ %s",
                type_label, coin, rounded_size, rounded_price
            )

            # Place order using official SDK
            result = self.exchange.order(
                coin,
                is_buy=is_buy,
                sz=rounded_size,
                limit_px=rounded_price,
                order_type=order_type,
                reduce_only=reduce_only
            )

            # Parse result
            if result and result.get("status") == "ok":
                response_data = result.get("response", {}).get("data", {})
                statuses = response_data.get("statuses", [])

                if statuses:
                    status = statuses[0]

                    # Trigger orders usually return "resting" status
                    if "resting" in status:
                        order_id = status["resting"]["oid"]
                        logger.info(
                            "Trigger order placed: %s %s %s @ %s (OID: %s)",
                            coin,
                            'BUY' if is_buy else 'SELL',
                            size,
                            trigger_price,
                            order_id
                        )
                        return True, order_id, None

                    if "filled" in status:
                        # Should not happen for trigger orders usually, but handle it
                        order_id = status["filled"]["oid"]
                        logger.info(
                            "Trigger order filled immediately: %s (OID: %s)",
                            coin, order_id
                        )
                        return True, order_id, None

                    error = status.get("error", "Unknown error")
                    logger.error("Trigger order rejected: %s", error)
                    return False, None, error

            error_msg = result.get("response", "Unknown error") if result else "No response"
            logger.error("Trigger order failed: %s", error_msg)
            return False, None, str(error_msg)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Trigger order execution failed: %s", e)
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
        """
        # DRY-RUN MODE: Simulate cancellation
        if self.dry_run:
            if order_id in self._dry_run_orders:
                self._dry_run_orders[order_id]["status"] = "cancelled"
                logger.info("[DRY-RUN] Cancelled order %s", order_id)
                return True, None

            logger.warning("[DRY-RUN] Order %s not found", order_id)
            return False, "Order not found"

        # LIVE MODE: Use official SDK
        try:
            result = self.exchange.cancel(coin, order_id)

            if result and result.get("status") == "ok":
                logger.info("Cancelled order %s for %s", order_id, coin)
                return True, None

            error = result.get("response", "Unknown error") if result else "No response"
            logger.error("Cancel failed: %s", error)
            return False, str(error)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Cancel order failed: %s", e)
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
        """
        # Validate leverage
        if not 1 <= leverage <= 50:
            error = f"Invalid leverage {leverage}x (must be 1-50x)"
            logger.error(error)
            return False, error

        # DRY-RUN MODE: Simulate leverage update
        if self.dry_run:
            logger.info(
                "[DRY-RUN] Updated leverage for %s: %sx (%s)",
                coin, leverage, 'cross' if is_cross else 'isolated'
            )
            return True, None

        # LIVE MODE: Use official SDK
        try:
            result = self.exchange.update_leverage(leverage, coin, is_cross)

            if result and result.get("status") == "ok":
                logger.info(
                    "Updated leverage for %s: %sx (%s)",
                    coin, leverage, 'cross' if is_cross else 'isolated'
                )
                return True, None

            error = result.get("response", "Unknown error") if result else "No response"
            logger.error("Leverage update failed: %s", error)
            return False, str(error)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Leverage update failed: %s", e)
            return False, str(e)

    def __repr__(self) -> str:
        """String representation."""
        mode = "DRY-RUN" if self.dry_run else "LIVE"
        return f"HyperLiquidExecutor({self.wallet_address}, mode={mode})"
