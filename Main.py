"""
Pocket Signals Bot — Multi-asset, multi-timeframe signal scanner.

Loops through 6 Binance pairs on 1m and 5m timeframes.
For each: fetches fresh candles, computes signal, and if confidence >= 75%:
  - Sends Telegram alert (UTC+4 timestamps)
  - Writes to Google Sheet
  - Logs to win tracker
After each cycle: checks past signal outcomes and prints win rate summary.
"""

import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()  # Load .env if present

from utils.data import fetch_binance_klines
from utils.timezone import now_gst_str
from strategies.signal_engine import get_signal_from_candles
from utils.telegram_notifier import send_signal_alert
from utils.win_tracker import log_signal, check_outcomes, print_summary
from sheets.sheet_writer import write_signal_row

# ---- Configuration (all from env) ----
ASSETS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "XAUUSDT", "XAGUSDT"]
TIMEFRAMES = ["1m", "5m"]
CANDLES = int(os.getenv("CANDLES", "250"))  # Need >=210 for EMA200 warm-up
SHEET_ID = os.getenv("SHEET_ID", "")
LOOP_SECONDS = int(os.getenv("LOOP_SECONDS", "60"))


def run_cycle():
    """Execute one full scan across all assets and timeframes."""
    print(f"\n{'─' * 60}")
    print(f"🔄 Scan started at {now_gst_str()}")
    print(f"{'─' * 60}")

    signals_fired = 0

    for asset in ASSETS:
        for tf in TIMEFRAMES:
            # Always fetch fresh data — no caching
            candles = fetch_binance_klines(symbol=asset, interval=tf, limit=CANDLES)
            if not candles:
                continue

            payload = get_signal_from_candles(candles, asset=asset, interval=tf)
            if payload is None:
                print(f"  ⚪ {asset}/{tf} — no signal")
                continue

            signals_fired += 1
            direction = payload["signal"]
            confidence = payload["confidence"]
            print(f"  🟢 {asset}/{tf} — {direction} ({confidence}%)")

            # 1) Telegram alert
            send_signal_alert(payload)

            # 2) Google Sheet (skip if no SHEET_ID configured)
            if SHEET_ID:
                ts = now_gst_str()
                row = [
                    ts,
                    payload["asset"],
                    payload["interval"],
                    payload["close_price"],
                    payload["signal"],
                    ", ".join(payload["reasons"]),
                    payload["confidence"],
                    payload["rsi"],
                    payload["macd"],
                    payload["macd_signal"],
                    payload["ema_fast"],
                    payload["ema_slow"],
                    payload["bb_upper"],
                    payload["bb_lower"],
                ]
                write_signal_row(sheet_id=SHEET_ID, row=row)

            # 3) Win tracker
            log_signal(payload)

    print(f"\n✅ Scan complete — {signals_fired} signal(s) fired at {now_gst_str()}")

    # Check past signal outcomes and print summary
    check_outcomes()
    print_summary()


def main():
    """Entry point — runs scan loop with configurable sleep interval."""
    print("=" * 60)
    print("  POCKET SIGNALS BOT v2.0 — Multi-Asset Scanner")
    print(f"  Assets    : {', '.join(ASSETS)}")
    print(f"  Timeframes: {', '.join(TIMEFRAMES)}")
    print(f"  Candles   : {CANDLES}")
    print(f"  Loop      : every {LOOP_SECONDS}s")
    print(f"  Timezone  : UTC+4 (GST)")
    print("=" * 60)

    # If --once flag, run single cycle and exit (useful for testing / cron)
    if "--once" in sys.argv:
        run_cycle()
        return

    while True:
        try:
            run_cycle()
        except KeyboardInterrupt:
            print("\n[EXIT] Stopped by user.")
            break
        except Exception as e:
            print(f"[ERROR] Cycle failed: {e}")

        print(f"💤 Sleeping {LOOP_SECONDS}s until next scan...")
        time.sleep(LOOP_SECONDS)


if __name__ == "__main__":
    main()
