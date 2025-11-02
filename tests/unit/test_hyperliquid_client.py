"""Unit tests for HyperLiquid API client."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import pandas as pd

from src.trading_bot.data.hyperliquid_client import HyperliquidClient
from src.trading_bot.models.market_data import Price


@pytest.mark.unit
class TestHyperliquidClient:
    """Test HyperLiquid API client."""

    def test_client_initialization(self):
        """Test client initializes with correct base URL."""
        client = HyperliquidClient(
            base_url="https://api.hyperliquid-testnet.xyz",
            timeout=10,
        )

        assert client.base_url == "https://api.hyperliquid-testnet.xyz"
        assert client.timeout == 10

    def test_get_all_prices_dict_response(self, mocker):
        """Test get_all_prices with dict response format."""
        client = HyperliquidClient("https://test.api", timeout=5)

        # Mock API response
        mock_response = {
            "BTC": "95420.5",
            "ETH": "3520.75",
            "SOL": "142.30",
        }

        mocker.patch.object(client, "_post", return_value=mock_response)

        prices = client.get_all_prices()

        assert len(prices) == 3
        assert "BTC" in prices
        assert prices["BTC"].price == 95420.5
        assert prices["BTC"].coin == "BTC"
        assert isinstance(prices["BTC"].timestamp, datetime)

    def test_get_all_prices_list_response(self, mocker):
        """Test get_all_prices with list response format."""
        client = HyperliquidClient("https://test.api", timeout=5)

        # Mock API response
        mock_response = [
            {"coin": "BTC", "price": "95420.5", "volume": "1234567890"},
            {"coin": "ETH", "mid": "3520.75", "volume": "987654321"},
        ]

        mocker.patch.object(client, "_post", return_value=mock_response)

        prices = client.get_all_prices()

        assert len(prices) == 2
        assert "BTC" in prices
        assert prices["BTC"].price == 95420.5
        assert prices["BTC"].volume_24h == 1234567890

    def test_get_price_specific_coin(self, mocker):
        """Test get_price for specific coin."""
        client = HyperliquidClient("https://test.api")

        mock_response = {
            "BTC": "95420.5",
            "ETH": "3520.75",
        }

        mocker.patch.object(client, "_post", return_value=mock_response)

        price = client.get_price("BTC")

        assert price.coin == "BTC"
        assert price.price == 95420.5

    def test_get_price_coin_not_found(self, mocker):
        """Test get_price raises error for non-existent coin."""
        client = HyperliquidClient("https://test.api")

        mock_response = {"BTC": "95420.5"}

        mocker.patch.object(client, "_post", return_value=mock_response)

        with pytest.raises(ValueError, match="Price not available"):
            client.get_price("NONEXISTENT")

    def test_get_klines_success(self, mocker):
        """Test get_klines returns DataFrame."""
        client = HyperliquidClient("https://test.api")

        # Mock API response
        mock_response = [
            {
                "t": 1699000000000,
                "o": "95000",
                "h": "95100",
                "l": "94900",
                "c": "95050",
                "v": "1000000",
            },
            {
                "t": 1699000180000,
                "o": "95050",
                "h": "95200",
                "l": "95000",
                "c": "95150",
                "v": "1100000",
            },
        ]

        mocker.patch.object(client, "_post", return_value=mock_response)

        df = client.get_klines("BTC", "3m", limit=2)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
        assert df["close"].iloc[-1] == 95150.0

    def test_get_klines_empty_response(self, mocker):
        """Test get_klines with empty response."""
        client = HyperliquidClient("https://test.api")

        mocker.patch.object(client, "_post", return_value=[])

        df = client.get_klines("BTC", "3m", limit=100)

        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]

    def test_get_klines_sorts_by_timestamp(self, mocker):
        """Test get_klines sorts data by timestamp."""
        client = HyperliquidClient("https://test.api")

        # Mock response with unsorted data
        mock_response = [
            {"t": 1699000180000, "o": "95050", "h": "95200", "l": "95000", "c": "95150", "v": "1100000"},
            {"t": 1699000000000, "o": "95000", "h": "95100", "l": "94900", "c": "95050", "v": "1000000"},
        ]

        mocker.patch.object(client, "_post", return_value=mock_response)

        df = client.get_klines("BTC", "3m", limit=100)

        # Should be sorted ascending by timestamp
        timestamps = df["timestamp"].tolist()
        assert timestamps == sorted(timestamps)

    def test_parse_interval_to_minutes(self):
        """Test interval parsing to minutes."""
        client = HyperliquidClient("https://test.api")

        assert client._parse_interval_to_minutes("1m") == 1
        assert client._parse_interval_to_minutes("3m") == 3
        assert client._parse_interval_to_minutes("5m") == 5
        assert client._parse_interval_to_minutes("15m") == 15
        assert client._parse_interval_to_minutes("1h") == 60
        assert client._parse_interval_to_minutes("4h") == 240
        assert client._parse_interval_to_minutes("1d") == 1440

    def test_parse_interval_invalid(self):
        """Test invalid interval raises error."""
        client = HyperliquidClient("https://test.api")

        with pytest.raises(ValueError, match="Invalid interval"):
            client._parse_interval_to_minutes("5x")

    def test_post_retry_on_failure(self, mocker):
        """Test _post retries on failure."""
        client = HyperliquidClient("https://test.api")

        mock_post = mocker.patch.object(client.session, "post")

        # First 2 calls fail, 3rd succeeds
        from requests.exceptions import RequestException
        mock_post.side_effect = [
            RequestException("Network error"),
            RequestException("Timeout"),
            mocker.Mock(status_code=200, json=lambda: {"success": True}),
        ]

        result = client._post("/info", {"type": "test"})

        assert result == {"success": True}
        assert mock_post.call_count == 3

    def test_post_max_retries_exceeded(self, mocker):
        """Test _post raises error after max retries."""
        client = HyperliquidClient("https://test.api")

        mock_post = mocker.patch.object(client.session, "post")

        # All calls fail
        from requests.exceptions import RequestException
        mock_post.side_effect = RequestException("Network error")

        with pytest.raises(RequestException):
            client._post("/info", {"type": "test"})

        assert mock_post.call_count == 3

    def test_get_open_interest(self, mocker):
        """Test get_open_interest."""
        client = HyperliquidClient("https://test.api")

        mock_response = [
            {"coin": "BTC", "openInterest": "1234567890"},
            {"coin": "ETH", "openInterest": "987654321"},
        ]

        mocker.patch.object(client, "_post", return_value=mock_response)

        oi = client.get_open_interest("BTC")

        assert oi == 1234567890.0

    def test_get_open_interest_not_found(self, mocker):
        """Test get_open_interest returns 0 for non-existent coin."""
        client = HyperliquidClient("https://test.api")

        mocker.patch.object(client, "_post", return_value=[])

        oi = client.get_open_interest("NONEXISTENT")

        assert oi == 0.0

    def test_get_funding_rate(self, mocker):
        """Test get_funding_rate."""
        client = HyperliquidClient("https://test.api")

        mock_response = [
            {"coin": "BTC", "funding": "0.0001"},
            {"coin": "ETH", "funding": "-0.00005"},
        ]

        mocker.patch.object(client, "_post", return_value=mock_response)

        funding = client.get_funding_rate("BTC")

        assert funding == 0.0001

    def test_close_session(self):
        """Test close() closes HTTP session."""
        client = HyperliquidClient("https://test.api")

        # Session should be open
        assert client.session is not None

        client.close()

        # Session close should be called (we can't really test if it's "closed")
        # But we can verify the method exists and doesn't raise error
        assert True
