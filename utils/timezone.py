"""
Centralized timezone helper — all display timestamps use UTC+4 (Gulf Standard Time).
"""

from datetime import datetime, timezone, timedelta

GST = timezone(timedelta(hours=4))  # UTC+4


def now_gst() -> datetime:
    """Current datetime in UTC+4."""
    return datetime.now(GST)


def utc_to_gst(dt: datetime) -> datetime:
    """Convert a UTC-aware datetime to UTC+4."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(GST)


def now_gst_str(fmt: str = "%Y-%m-%d %H:%M:%S UTC+4") -> str:
    """Formatted current time string in UTC+4."""
    return now_gst().strftime(fmt)
