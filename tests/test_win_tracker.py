"""Tests for the win rate tracker."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import tempfile
from unittest.mock import patch
from datetime import timedelta

from utils.timezone import now_gst


def _make_tracker(tmp_path):
    """Patch TRACKER_FILE to use a temp file."""
    return os.path.join(tmp_path, "test_win_tracker.json")


def test_log_and_load():
    """Signals are persisted to JSON and can be reloaded."""
    import utils.win_tracker as wt
    with tempfile.TemporaryDirectory() as td:
        tf = _make_tracker(td)
        with patch.object(wt, "TRACKER_FILE", tf):
            payload = {
                "asset": "BTCUSDT", "interval": "1m", "signal": "BUY",
                "confidence": 80.0, "close_price": 75000.0,
            }
            wt.log_signal(payload)
            wt.log_signal(payload)

            entries = wt._load_entries()
            assert len(entries) == 2
            assert entries[0]["outcome"] is None
            assert entries[0]["asset"] == "BTCUSDT"


def test_check_outcomes_respects_wait_period():
    """Outcomes aren't checked until the wait period has elapsed."""
    import utils.win_tracker as wt
    with tempfile.TemporaryDirectory() as td:
        tf = _make_tracker(td)
        with patch.object(wt, "TRACKER_FILE", tf):
            # Log a signal just now — shouldn't be checked yet
            payload = {
                "asset": "ETHUSDT", "interval": "1m", "signal": "BUY",
                "confidence": 80.0, "close_price": 3000.0,
            }
            wt.log_signal(payload)
            entries = wt.check_outcomes()
            assert entries[0]["outcome"] is None  # too soon


def test_check_outcomes_after_wait():
    """After the wait period, outcome should be determined."""
    import utils.win_tracker as wt
    with tempfile.TemporaryDirectory() as td:
        tf = _make_tracker(td)
        with patch.object(wt, "TRACKER_FILE", tf):
            # Create an entry with a timestamp in the past
            old_time = now_gst() - timedelta(minutes=10)
            entries = [{
                "asset": "BTCUSDT", "interval": "1m", "signal": "BUY",
                "confidence": 80.0, "entry_price": 75000.0,
                "timestamp": old_time.isoformat(), "outcome": None,
            }]
            wt._save_entries(entries)

            # Mock current price higher than entry = WIN for BUY
            with patch("utils.win_tracker.fetch_current_price", return_value=76000.0):
                result = wt.check_outcomes()
                assert result[0]["outcome"] == "WIN"


def test_sell_signal_win():
    """SELL signal wins when price goes down."""
    import utils.win_tracker as wt
    with tempfile.TemporaryDirectory() as td:
        tf = _make_tracker(td)
        with patch.object(wt, "TRACKER_FILE", tf):
            old_time = now_gst() - timedelta(minutes=20)
            entries = [{
                "asset": "ETHUSDT", "interval": "5m", "signal": "SELL",
                "confidence": 80.0, "entry_price": 3000.0,
                "timestamp": old_time.isoformat(), "outcome": None,
            }]
            wt._save_entries(entries)

            # Price dropped = WIN for SELL
            with patch("utils.win_tracker.fetch_current_price", return_value=2900.0):
                result = wt.check_outcomes()
                assert result[0]["outcome"] == "WIN"


def test_sell_signal_loss():
    """SELL signal loses when price goes up."""
    import utils.win_tracker as wt
    with tempfile.TemporaryDirectory() as td:
        tf = _make_tracker(td)
        with patch.object(wt, "TRACKER_FILE", tf):
            old_time = now_gst() - timedelta(minutes=20)
            entries = [{
                "asset": "ETHUSDT", "interval": "5m", "signal": "SELL",
                "confidence": 80.0, "entry_price": 3000.0,
                "timestamp": old_time.isoformat(), "outcome": None,
            }]
            wt._save_entries(entries)

            with patch("utils.win_tracker.fetch_current_price", return_value=3100.0):
                result = wt.check_outcomes()
                assert result[0]["outcome"] == "LOSS"
