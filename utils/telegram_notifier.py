"""
Telegram alert sender.
Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from env vars.
All timestamps displayed in UTC+4.
"""

import os
import requests
from utils.timezone import now_gst_str

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Human-readable asset labels
ASSET_LABELS = {
    "BTCUSDT": "BTC/USD",
    "ETHUSDT": "ETH/USD",
    "XRPUSDT": "XRP/USD",
    "SOLUSDT": "SOL/USD",
    "XAUUSDT": "XAU/USD",
    "XAGUSDT": "XAG/USD",
}


def _format_price(price: float) -> str:
    """Format price with comma separators."""
    if price >= 1:
        return f"{price:,.2f}"
    return f"{price:.6f}"


def send_signal_alert(payload: dict) -> bool:
    """
    Send a formatted signal alert to Telegram.
    Returns True on success, False on failure.
    """
    if not BOT_TOKEN or not CHAT_ID:
        print("[WARN] Telegram credentials not set — skipping alert.")
        return False

    asset_label = ASSET_LABELS.get(payload["asset"], payload["asset"])
    tf_label = payload["interval"].upper()
    direction_emoji = "📈" if payload["signal"] == "BUY" else "📉"
    call_put = "CALL (BUY)" if payload["signal"] == "BUY" else "PUT (SELL)"
    confidence = int(payload["confidence"])
    reasons_str = ", ".join(payload["reasons"])
    price_str = _format_price(payload["close_price"])
    timestamp = now_gst_str()

    message = (
        f"🚨 SIGNAL ALERT\n"
        f"📊 {asset_label} | {tf_label}\n"
        f"{direction_emoji} {call_put}\n"
        f"💰 Price: {price_str}\n"
        f"🎯 Confidence: {confidence}%\n"
        f"📌 Reasons: {reasons_str}\n"
        f"⏰ {timestamp}"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }, timeout=10)
        if resp.status_code == 200:
            print(f"[TG] Alert sent for {asset_label} {tf_label}")
            return True
        else:
            print(f"[TG ERROR] {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"[TG ERROR] {e}")
        return False
