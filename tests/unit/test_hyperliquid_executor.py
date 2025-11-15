"""Unit tests for HyperLiquid Executor."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from src.trading_bot.trading.hyperliquid_executor import (
    HyperLiquidExecutor,
    OrderType
)


class TestHyperLiquidExecutor:
    """Test HyperLiquid Executor."""

    @pytest.fixture
    def mock_signer(self):
        """Create a mock signer."""
        signer = Mock()
        signer.address = "0x1234567890123456789012345678901234567890"
        signer.sign_l1_action.return_value = {
            "r": "0x" + "a" * 64,
            "s": "0x" + "b" * 64,
            "v": 27
        }
        return signer

    @pytest.fixture
    def executor(self, mock_signer):
        """Create executor with mocked SDK components."""
        with patch('src.trading_bot.trading.hyperliquid_executor.Exchange') as MockExchange:
            with patch('src.trading_bot.trading.hyperliquid_executor.Info') as MockInfo:
                executor = HyperLiquidExecutor(
                    base_url="https://api.hyperliquid-testnet.xyz",
                    private_key="0x" + "1" * 64,
                    use_dynamic_assets=False,  # Use hardcoded assets for testing
                    dry_run=True  # Use dry-run mode for testing
                )
                return executor

    def test_initialize_executor(self, executor, mock_signer):
        """Test executor initialization."""
        assert executor is not None
        assert executor.base_url == "https://api.hyperliquid-testnet.xyz"
        assert executor.signer == mock_signer
        assert executor.timeout == 10
        assert executor.vault_address is None

    def test_initialize_with_vault(self, mock_signer):
        """Test initialization with vault address."""
        with patch('src.trading_bot.trading.hyperliquid_executor.Exchange') as MockExchange:
            with patch('src.trading_bot.trading.hyperliquid_executor.Info') as MockInfo:
                vault = "0x" + "2" * 40
                executor = HyperLiquidExecutor(
                    base_url="https://api.hyperliquid-testnet.xyz",
                    private_key="0x" + "1" * 64,
                    vault_address=vault,
                    use_dynamic_assets=False,
                    dry_run=True
                )
                assert executor.vault_address == vault

    def test_get_address(self, executor, mock_signer):
        """Test getting wallet address."""
        address = executor.get_address()
        assert address == mock_signer.address

    def test_get_asset_index_valid(self, executor):
        """Test getting asset index for valid coins."""
        assert executor._get_asset_index("BTC") == 0
        assert executor._get_asset_index("ETH") == 1
        assert executor._get_asset_index("SOL") == 2

    def test_get_asset_index_invalid(self, executor):
        """Test getting asset index for invalid coin."""
        with pytest.raises(ValueError, match="Unsupported coin"):
            executor._get_asset_index("INVALID")

    def test_place_limit_order_success(self, executor):
        """Test placing a successful limit order."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{
                        "resting": {
                            "oid": 12345
                        }
                    }]
                }
            }
        }
        executor.session.post.return_value = mock_response

        # Place order
        success, order_id, error = executor.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("0.1"),
            price=Decimal("50000"),
            order_type=OrderType.LIMIT
        )

        assert success is True
        assert order_id == 12345
        assert error is None

    def test_place_market_order_filled(self, executor):
        """Test placing a market order that fills immediately."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{
                        "filled": {
                            "oid": 67890
                        }
                    }]
                }
            }
        }
        executor.session.post.return_value = mock_response

        success, order_id, error = executor.place_order(
            coin="ETH",
            is_buy=False,
            size=Decimal("1.0"),
            order_type=OrderType.MARKET
        )

        assert success is True
        assert order_id == 67890
        assert error is None

    def test_place_order_rejected(self, executor):
        """Test placing an order that gets rejected."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{
                        "error": "Insufficient margin"
                    }]
                }
            }
        }
        executor.session.post.return_value = mock_response

        success, order_id, error = executor.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("100.0"),
            price=Decimal("50000")
        )

        assert success is False
        assert order_id is None
        assert "Insufficient margin" in error

    def test_place_limit_order_without_price(self, executor):
        """Test that limit orders require a price."""
        with pytest.raises(ValueError, match="Limit orders require a price"):
            executor.place_order(
                coin="BTC",
                is_buy=True,
                size=Decimal("0.1"),
                price=None,
                order_type=OrderType.LIMIT
            )

    def test_place_order_with_client_order_id(self, executor):
        """Test placing order with client order ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{
                        "resting": {"oid": 12345}
                    }]
                }
            }
        }
        executor.session.post.return_value = mock_response

        success, order_id, error = executor.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("0.1"),
            price=Decimal("50000"),
            client_order_id="my-order-123"
        )

        assert success is True
        # Verify client order ID was included in request
        call_args = executor.session.post.call_args
        payload = call_args[1]["json"]
        assert payload["action"]["orders"][0]["c"] == "my-order-123"

    def test_cancel_order_success(self, executor):
        """Test canceling an order successfully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok"
        }
        executor.session.post.return_value = mock_response

        success, error = executor.cancel_order("BTC", 12345)

        assert success is True
        assert error is None

    def test_cancel_order_failure(self, executor):
        """Test cancel order failure."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "error",
            "response": "Order not found"
        }
        executor.session.post.return_value = mock_response

        success, error = executor.cancel_order("BTC", 99999)

        assert success is False
        assert "Order not found" in error

    def test_cancel_by_cloid_success(self, executor):
        """Test canceling order by client order ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok"
        }
        executor.session.post.return_value = mock_response

        success, error = executor.cancel_by_cloid("ETH", "my-order-123")

        assert success is True
        assert error is None

    def test_batch_cancel_success(self, executor):
        """Test batch canceling multiple orders."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok"
        }
        executor.session.post.return_value = mock_response

        cancels = [
            ("BTC", 12345),
            ("ETH", 67890),
            ("SOL", 11111)
        ]
        success, error = executor.batch_cancel(cancels)

        assert success is True
        assert error is None

        # Verify all cancels were included
        call_args = executor.session.post.call_args
        payload = call_args[1]["json"]
        assert len(payload["action"]["cancels"]) == 3

    def test_update_leverage_success(self, executor):
        """Test updating leverage successfully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok"
        }
        executor.session.post.return_value = mock_response

        success, error = executor.update_leverage("BTC", 10, True)

        assert success is True
        assert error is None

    def test_update_leverage_isolated(self, executor):
        """Test updating to isolated margin."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok"
        }
        executor.session.post.return_value = mock_response

        success, error = executor.update_leverage("ETH", 5, False)

        assert success is True
        # Verify isolated margin was set
        call_args = executor.session.post.call_args
        payload = call_args[1]["json"]
        assert payload["action"]["isCross"] is False

    def test_update_leverage_invalid_range(self, executor):
        """Test leverage validation."""
        success, error = executor.update_leverage("BTC", 0, True)
        assert success is False
        assert "Invalid leverage" in error

        success, error = executor.update_leverage("BTC", 51, True)
        assert success is False
        assert "Invalid leverage" in error

    def test_modify_order_success(self, executor):
        """Test modifying an order successfully."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok"
        }
        executor.session.post.return_value = mock_response

        success, error = executor.modify_order(
            coin="BTC",
            order_id=12345,
            new_size=Decimal("0.2"),
            new_price=Decimal("51000"),
            is_buy=True
        )

        assert success is True
        assert error is None

    def test_post_signed_retry_on_failure(self, executor):
        """Test retry logic on request failure."""
        # First two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = Exception("Network error")

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"status": "ok"}
        mock_response_success.raise_for_status.return_value = None

        executor.session.post.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]

        # Should succeed after retries
        action = {"type": "order", "orders": []}
        result = executor._post_signed(action)

        assert result["status"] == "ok"
        assert executor.session.post.call_count == 3

    def test_context_manager(self, executor):
        """Test context manager protocol."""
        with executor as ex:
            assert ex == executor

        # Session should be closed after exiting context
        executor.session.close.assert_called_once()

    def test_repr(self, executor, mock_signer):
        """Test string representation."""
        repr_str = repr(executor)
        assert "HyperLiquidExecutor" in repr_str
        assert mock_signer.address in repr_str
        assert "hyperliquid-testnet" in repr_str

    def test_close(self, executor):
        """Test explicit close."""
        executor.close()
        executor.session.close.assert_called_once()

    def test_reduce_only_order(self, executor):
        """Test placing reduce-only order."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{
                        "resting": {"oid": 12345}
                    }]
                }
            }
        }
        executor.session.post.return_value = mock_response

        success, order_id, error = executor.place_order(
            coin="BTC",
            is_buy=False,
            size=Decimal("0.1"),
            price=Decimal("50000"),
            reduce_only=True
        )

        assert success is True
        # Verify reduce_only flag was set
        call_args = executor.session.post.call_args
        payload = call_args[1]["json"]
        assert payload["action"]["orders"][0]["r"] is True

    def test_time_in_force_options(self, executor):
        """Test different time-in-force options."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{
                        "resting": {"oid": 12345}
                    }]
                }
            }
        }
        executor.session.post.return_value = mock_response

        # Test IOC
        executor.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("0.1"),
            price=Decimal("50000"),
            time_in_force="Ioc"
        )
        payload = executor.session.post.call_args[1]["json"]
        assert payload["action"]["orders"][0]["t"]["limit"]["tif"] == "Ioc"

        # Test ALO
        executor.place_order(
            coin="BTC",
            is_buy=True,
            size=Decimal("0.1"),
            price=Decimal("50000"),
            time_in_force="Alo"
        )
        payload = executor.session.post.call_args[1]["json"]
        assert payload["action"]["orders"][0]["t"]["limit"]["tif"] == "Alo"

    def test_get_supported_assets(self, executor):
        """Test getting list of supported assets."""
        assets = executor.get_supported_assets()
        assert isinstance(assets, list)
        assert "BTC" in assets
        assert "ETH" in assets
        assert len(assets) > 0

    def test_dynamic_asset_loading(self, mock_signer):
        """Test dynamic asset loading from API."""
        with patch('src.trading_bot.trading.hyperliquid_executor.Exchange') as MockExchange:
            with patch('src.trading_bot.trading.hyperliquid_executor.Info') as MockInfo:
                # Mock Info.meta() response
                mock_info = MockInfo.return_value
                mock_info.meta.return_value = {
                    "universe": [
                        {"name": "BTC"},
                        {"name": "ETH"},
                        {"name": "SOL"},
                        {"name": "TEST_COIN"}
                    ]
                }

                executor = HyperLiquidExecutor(
                    base_url="https://api.hyperliquid-testnet.xyz",
                    private_key="0x" + "1" * 64,
                    use_dynamic_assets=True,
                    dry_run=True
                )

                # Verify dynamic assets were loaded
                assert executor._get_asset_index("BTC") == 0
                assert executor._get_asset_index("ETH") == 1
                assert executor._get_asset_index("TEST_COIN") == 3

    def test_dynamic_asset_fallback_on_error(self, mock_signer):
        """Test fallback to hardcoded assets when API fails."""
        with patch('src.trading_bot.trading.hyperliquid_executor.Exchange') as MockExchange:
            with patch('src.trading_bot.trading.hyperliquid_executor.Info') as MockInfo:
                # Mock Info.meta() failure
                mock_info = MockInfo.return_value
                mock_info.meta.side_effect = Exception("API error")

                executor = HyperLiquidExecutor(
                    base_url="https://api.hyperliquid-testnet.xyz",
                    private_key="0x" + "1" * 64,
                    use_dynamic_assets=True,
                    dry_run=True
                )

                # Should have fallen back to hardcoded assets
                assert executor._get_asset_index("BTC") == 0
                assert executor._get_asset_index("ETH") == 1

    def test_refresh_assets(self, executor):
        """Test manual asset refresh."""
        # For hardcoded mode, refresh should be ignored
        executor.refresh_assets()
        # No exception should be raised

    def test_refresh_assets_dynamic_mode(self, mock_signer):
        """Test refreshing assets in dynamic mode."""
        with patch('src.trading_bot.trading.hyperliquid_executor.Exchange') as MockExchange:
            with patch('src.trading_bot.trading.hyperliquid_executor.Info') as MockInfo:
                # Mock Info.meta() responses
                mock_info = MockInfo.return_value

                # Initial load
                meta_response1 = {
                    "universe": [{"name": "BTC"}, {"name": "ETH"}]
                }

                # Refresh load with new asset
                meta_response2 = {
                    "universe": [{"name": "BTC"}, {"name": "ETH"}, {"name": "NEW"}]
                }

                mock_info.meta.side_effect = [meta_response1, meta_response2]

                executor = HyperLiquidExecutor(
                    base_url="https://api.hyperliquid-testnet.xyz",
                    private_key="0x" + "1" * 64,
                    use_dynamic_assets=True,
                    dry_run=True
                )

                # Initially only 2 assets
                assert len(executor.get_supported_assets()) == 2

                # After refresh, should have 3 assets
                executor.refresh_assets()
                assert len(executor.get_supported_assets()) == 3
                assert "NEW" in executor.get_supported_assets()

    def test_asset_auto_refresh_on_unknown_coin(self, mock_signer):
        """Test automatic asset refresh when unknown coin is encountered."""
        with patch('src.trading_bot.trading.hyperliquid_executor.Exchange') as MockExchange:
            with patch('src.trading_bot.trading.hyperliquid_executor.Info') as MockInfo:
                # Mock Info.meta() responses
                mock_info = MockInfo.return_value

                # Initial load without NEWCOIN
                meta_response1 = {
                    "universe": [{"name": "BTC"}, {"name": "ETH"}]
                }

                # Auto-refresh load with NEWCOIN
                meta_response2 = {
                    "universe": [{"name": "BTC"}, {"name": "ETH"}, {"name": "NEWCOIN"}]
                }

                mock_info.meta.side_effect = [meta_response1, meta_response2]

                executor = HyperLiquidExecutor(
                    base_url="https://api.hyperliquid-testnet.xyz",
                    private_key="0x" + "1" * 64,
                    use_dynamic_assets=True,
                    dry_run=True
                )

                # Try to get index for NEWCOIN - should trigger auto-refresh
                index = executor._get_asset_index("NEWCOIN")
                assert index == 2
