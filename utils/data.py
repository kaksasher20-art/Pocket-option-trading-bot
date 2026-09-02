"""
Binance public kline fetcher.
Always fetches fresh data — no caching, no local storage.
"""

import requests

BINANCE_BASE = "https://api.binance.com"


def fetch_binance_klines(symbol: str = "BTCUSDT", interval: str = "1m", limit: int = 200) -> list[dict]:
    """
    Fetch fresh kline/candlestick data from Binance REST API.
    Returns list of dicts with OHLCV fields, newest candle last.
    """
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        raw = resp.json()
        candles = []
        for k in raw:
            candles.append({
                "open_time": k[0],
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "close_time": k[6],
            })
        return candles
    except Exception as e:
        print(f"[ERROR] Binance klines fetch failed for {symbol}/{interval}: {e}")
        return []


def fetch_current_price(symbol: str) -> float | None:
    """Fetch the latest ticker price for a symbol (used by win tracker)."""
    url = f"{BINANCE_BASE}/api/v3/ticker/price"
    try:
        resp = requests.get(url, params={"symbol": symbol}, timeout=10)
        resp.raise_for_status()
        return float(resp.json()["price"])
    except Exception as e:
        print(f"[ERROR] Price fetch failed for {symbol}: {e}")
        return None
