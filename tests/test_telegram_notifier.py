"""Tests for Telegram notifier formatting."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch, MagicMock
from utils.telegram_notifier import send_signal_alert, _format_price, ASSET_LABELS


def test_format_price_large():
    assert _format_price(77335.2) == "77,335.20"


def test_format_price_small():
    assert _format_price(0.000123) == "0.000123"


def test_asset_labels_coverage():
    expected = {"BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "XAUUSDT", "XAGUSDT"}
    assert expected == set(ASSET_LABELS.keys())


def test_send_alert_skips_without_creds():
    """Should return False and not crash when no creds are set."""
    payload = {
        "asset": "BTCUSDT", "interval": "1m", "signal": "BUY",
        "confidence": 80.0, "close_price": 77000.0,
        "reasons": ["RSI oversold", "EMA crossover bullish"],
    }
    with patch("utils.telegram_notifier.BOT_TOKEN", ""), \
         patch("utils.telegram_notifier.CHAT_ID", ""):
        assert send_signal_alert(payload) is False


@patch("utils.telegram_notifier.requests.post")
def test_send_alert_message_format(mock_post):
    """Verify the message sent to Telegram contains correct elements."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    payload = {
        "asset": "BTCUSDT", "interval": "1m", "signal": "BUY",
        "confidence": 80.0, "close_price": 77335.2,
        "reasons": ["RSI oversold", "EMA crossover bullish"],
    }

    with patch("utils.telegram_notifier.BOT_TOKEN", "test_token"), \
         patch("utils.telegram_notifier.CHAT_ID", "12345"):
        result = send_signal_alert(payload)

    assert result is True
    call_args = mock_post.call_args
    msg = call_args.kwargs["json"]["text"] if "json" in call_args.kwargs else call_args[1]["json"]["text"]
    assert "SIGNAL ALERT" in msg
    assert "BTC/USD" in msg
    assert "CALL (BUY)" in msg
    assert "77,335.20" in msg
    assert "80%" in msg
    assert "UTC+4" in msg


@patch("utils.telegram_notifier.requests.post")
def test_sell_signal_format(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    payload = {
        "asset": "ETHUSDT", "interval": "5m", "signal": "SELL",
        "confidence": 100.0, "close_price": 3500.0,
        "reasons": ["RSI overbought", "Bearish trend"],
    }

    with patch("utils.telegram_notifier.BOT_TOKEN", "tok"), \
         patch("utils.telegram_notifier.CHAT_ID", "999"):
        result = send_signal_alert(payload)

    assert result is True
    msg = mock_post.call_args.kwargs["json"]["text"]
    assert "PUT (SELL)" in msg
    assert "ETH/USD" in msg
