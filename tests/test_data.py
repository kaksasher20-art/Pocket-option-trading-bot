"""Tests for Binance data fetcher."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch, MagicMock
from utils.data import fetch_binance_klines, fetch_current_price


def _mock_kline_response():
    """Minimal Binance kline response (one candle)."""
    return [[
        1693612800000,   # open_time
        "26000.00",      # open
        "26100.00",      # high
        "25900.00",      # low
        "26050.00",      # close
        "150.5",         # volume
        1693612859999,   # close_time
        "0", "0", "0", "0", "0"
    ]]


@patch("utils.data.requests.get")
def test_fetch_klines_parses_correctly(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = _mock_kline_response()
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    result = fetch_binance_klines("BTCUSDT", "1m", 1)
    assert len(result) == 1
    assert result[0]["close"] == 26050.0
    assert result[0]["high"] == 26100.0
    assert result[0]["volume"] == 150.5


@patch("utils.data.requests.get")
def test_fetch_klines_returns_empty_on_error(mock_get):
    mock_get.side_effect = Exception("Network error")
    result = fetch_binance_klines("BTCUSDT", "1m", 100)
    assert result == []


@patch("utils.data.requests.get")
def test_fetch_current_price(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"symbol": "BTCUSDT", "price": "76543.21"}
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    price = fetch_current_price("BTCUSDT")
    assert price == 76543.21


@patch("utils.data.requests.get")
def test_fetch_current_price_failure(mock_get):
    mock_get.side_effect = Exception("Timeout")
    price = fetch_current_price("BTCUSDT")
    assert price is None
