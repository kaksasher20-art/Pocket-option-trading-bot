"""
Win rate tracker — logs every signal to win_tracker.json and
evaluates outcomes after the appropriate wait period.

All timestamps stored and displayed in UTC+4.
"""

import json
import os
from datetime import timedelta

from utils.data import fetch_current_price
from utils.timezone import now_gst, GST

TRACKER_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "win_tracker.json")

# How long to wait before checking outcome
WAIT_PERIODS = {
    "1m": timedelta(minutes=5),
    "5m": timedelta(minutes=15),
}


def _load_entries() -> list[dict]:
    if not os.path.exists(TRACKER_FILE):
        return []
    try:
        with open(TRACKER_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_entries(entries: list[dict]):
    with open(TRACKER_FILE, "w") as f:
        json.dump(entries, f, indent=2, default=str)


def log_signal(payload: dict):
    """Append a new signal entry to the tracker file."""
    entries = _load_entries()
    entry = {
        "asset": payload["asset"],
        "interval": payload["interval"],
        "signal": payload["signal"],
        "confidence": payload["confidence"],
        "entry_price": payload["close_price"],
        "timestamp": now_gst().isoformat(),
        "outcome": None,
    }
    entries.append(entry)
    _save_entries(entries)
    print(f"[TRACKER] Logged {payload['signal']} signal for {payload['asset']}/{payload['interval']}")


def check_outcomes():
    """
    Review pending signals: if enough time has passed, fetch the current
    price and determine WIN or LOSS.
    """
    entries = _load_entries()
    now = now_gst()
    updated = 0

    for entry in entries:
        if entry["outcome"] is not None:
            continue

        from datetime import datetime
        ts = datetime.fromisoformat(entry["timestamp"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=GST)

        wait = WAIT_PERIODS.get(entry["interval"], timedelta(minutes=5))
        if now - ts < wait:
            continue  # Not enough time elapsed

        current_price = fetch_current_price(entry["asset"])
        if current_price is None:
            continue

        price_moved_up = current_price > entry["entry_price"]

        if entry["signal"] == "BUY":
            entry["outcome"] = "WIN" if price_moved_up else "LOSS"
        else:  # SELL
            entry["outcome"] = "WIN" if not price_moved_up else "LOSS"

        entry["exit_price"] = current_price
        entry["checked_at"] = now.isoformat()
        updated += 1

    if updated:
        _save_entries(entries)
        print(f"[TRACKER] Updated {updated} outcome(s)")

    return entries


def print_summary():
    """Print win rate statistics."""
    entries = _load_entries()
    total = len(entries)
    resolved = [e for e in entries if e["outcome"] is not None]
    wins = sum(1 for e in resolved if e["outcome"] == "WIN")
    losses = sum(1 for e in resolved if e["outcome"] == "LOSS")
    pending = total - len(resolved)
    win_rate = (wins / len(resolved) * 100) if resolved else 0.0

    print("\n" + "=" * 50)
    print("📊 WIN RATE SUMMARY")
    print("=" * 50)
    print(f"  Total signals : {total}")
    print(f"  Resolved      : {len(resolved)}")
    print(f"  Wins          : {wins}")
    print(f"  Losses        : {losses}")
    print(f"  Pending       : {pending}")
    print(f"  Win rate      : {win_rate:.1f}%")
    print("=" * 50 + "\n")
