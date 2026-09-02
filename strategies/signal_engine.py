"""
Enhanced signal engine — 5 indicators, fires only when ≥4/5 agree.

Indicators:
  1. RSI (14)          — oversold < 35 = BUY, overbought > 65 = SELL
  2. EMA crossover     — EMA10 vs EMA25
  3. MACD histogram    — positive & rising = BUY, negative & falling = SELL
  4. Bollinger Bands   — price near lower band = BUY, near upper band = SELL
  5. Trend filter      — EMA50/EMA200 alignment
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Indicator helpers (pure numpy/pandas, no TA-Lib)
# ---------------------------------------------------------------------------

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _bollinger(series: pd.Series, period: int = 20, num_std: float = 2.0):
    mid = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


# ---------------------------------------------------------------------------
# Main signal generator
# ---------------------------------------------------------------------------

def get_signal_from_candles(candles: list[dict], asset: str, interval: str) -> dict | None:
    """
    Analyse candle data and return a signal payload if confidence >= 75%.
    Returns None when no clear signal or insufficient data.
    """
    if len(candles) < 210:
        # Need enough bars for EMA200 + warm-up
        print(f"[WARN] Not enough candles for {asset}/{interval} ({len(candles)})")
        return None

    closes = pd.Series([c["close"] for c in candles])
    latest_close = closes.iloc[-1]

    # --- Compute all indicators on latest bar ---
    rsi_series = _rsi(closes)
    rsi_val = rsi_series.iloc[-1]

    ema10 = _ema(closes, 10)
    ema25 = _ema(closes, 25)
    ema50 = _ema(closes, 50)
    ema200 = _ema(closes, 200)

    macd_line, signal_line, histogram = _macd(closes)
    bb_upper, bb_mid, bb_lower = _bollinger(closes)

    # Current values
    cur_ema10 = ema10.iloc[-1]
    cur_ema25 = ema25.iloc[-1]
    prev_ema10 = ema10.iloc[-2]
    prev_ema25 = ema25.iloc[-2]
    cur_ema50 = ema50.iloc[-1]
    cur_ema200 = ema200.iloc[-1]
    cur_macd = macd_line.iloc[-1]
    cur_signal = signal_line.iloc[-1]
    cur_hist = histogram.iloc[-1]
    prev_hist = histogram.iloc[-2]
    cur_bb_upper = bb_upper.iloc[-1]
    cur_bb_lower = bb_lower.iloc[-1]
    cur_bb_mid = bb_mid.iloc[-1]

    # Guard against NaN (early bars before warm-up)
    check_vals = [rsi_val, cur_ema10, cur_ema25, cur_ema50, cur_ema200,
                  cur_macd, cur_signal, cur_hist, prev_hist,
                  cur_bb_upper, cur_bb_lower]
    if any(np.isnan(v) for v in check_vals):
        return None

    # --- Vote per indicator ---
    buy_votes = 0
    sell_votes = 0
    reasons: list[str] = []

    # 1) RSI
    if rsi_val < 35:
        buy_votes += 1
        reasons.append(f"RSI oversold ({rsi_val:.1f})")
    elif rsi_val > 65:
        sell_votes += 1
        reasons.append(f"RSI overbought ({rsi_val:.1f})")

    # 2) EMA crossover (EMA10 vs EMA25)
    if prev_ema10 <= prev_ema25 and cur_ema10 > cur_ema25:
        buy_votes += 1
        reasons.append("EMA crossover bullish (10>25)")
    elif prev_ema10 >= prev_ema25 and cur_ema10 < cur_ema25:
        sell_votes += 1
        reasons.append("EMA crossover bearish (10<25)")
    else:
        # No fresh cross — still give credit for existing alignment
        if cur_ema10 > cur_ema25:
            buy_votes += 1
            reasons.append("EMA10 above EMA25")
        elif cur_ema10 < cur_ema25:
            sell_votes += 1
            reasons.append("EMA10 below EMA25")

    # 3) MACD histogram
    if cur_hist > 0 and cur_hist > prev_hist:
        buy_votes += 1
        reasons.append("MACD histogram positive & rising")
    elif cur_hist < 0 and cur_hist < prev_hist:
        sell_votes += 1
        reasons.append("MACD histogram negative & falling")

    # 4) Bollinger Bands — proximity to band edges
    bb_range = cur_bb_upper - cur_bb_lower
    if bb_range > 0:
        pct_b = (latest_close - cur_bb_lower) / bb_range
        if pct_b < 0.20:
            buy_votes += 1
            reasons.append(f"Price near lower Bollinger Band (%B={pct_b:.2f})")
        elif pct_b > 0.80:
            sell_votes += 1
            reasons.append(f"Price near upper Bollinger Band (%B={pct_b:.2f})")

    # 5) Trend filter (EMA50 / EMA200)
    if latest_close > cur_ema50 and latest_close > cur_ema200:
        buy_votes += 1
        reasons.append("Bullish trend (price > EMA50 & EMA200)")
    elif latest_close < cur_ema50 and latest_close < cur_ema200:
        sell_votes += 1
        reasons.append("Bearish trend (price < EMA50 & EMA200)")

    # --- Determine direction & confidence ---
    total = max(buy_votes, sell_votes)
    confidence = (total / 5) * 100

    if confidence < 75:
        return None  # Not enough agreement

    direction = "BUY" if buy_votes >= sell_votes else "SELL"

    # Filter reasons to only matching direction
    buy_keywords = {"oversold", "bullish", "above", "positive", "rising", "lower"}
    sell_keywords = {"overbought", "bearish", "below", "negative", "falling", "upper"}
    keep_kw = buy_keywords if direction == "BUY" else sell_keywords
    filtered_reasons = [r for r in reasons if any(k in r.lower() for k in keep_kw)]

    return {
        "asset": asset,
        "interval": interval,
        "close_price": round(latest_close, 6),
        "signal": direction,
        "confidence": round(confidence, 1),
        "reasons": filtered_reasons if filtered_reasons else reasons,
        "rsi": round(rsi_val, 2),
        "macd": round(cur_macd, 6),
        "macd_signal": round(cur_signal, 6),
        "ema_fast": round(cur_ema10, 6),
        "ema_slow": round(cur_ema25, 6),
        "bb_upper": round(cur_bb_upper, 6),
        "bb_lower": round(cur_bb_lower, 6),
    }
