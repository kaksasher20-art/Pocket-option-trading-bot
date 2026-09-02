"""Tests for UTC+4 timezone helpers."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timezone, timedelta
from utils.timezone import now_gst, utc_to_gst, now_gst_str, GST


def test_gst_offset():
    """GST should be UTC+4."""
    assert GST.utcoffset(None) == timedelta(hours=4)


def test_now_gst_is_utc_plus4():
    dt = now_gst()
    assert dt.tzinfo is not None
    assert dt.utcoffset() == timedelta(hours=4)


def test_utc_to_gst_conversion():
    utc_dt = datetime(2026, 9, 2, 20, 0, 0, tzinfo=timezone.utc)
    gst_dt = utc_to_gst(utc_dt)
    assert gst_dt.hour == 0  # 20:00 UTC = 00:00 next day UTC+4
    assert gst_dt.day == 3


def test_utc_to_gst_naive_input():
    """Naive datetime should be treated as UTC."""
    naive = datetime(2026, 1, 1, 12, 0, 0)
    result = utc_to_gst(naive)
    assert result.hour == 16  # 12:00 UTC -> 16:00 UTC+4


def test_now_gst_str_format():
    s = now_gst_str()
    assert "UTC+4" in s
    assert len(s) > 15
