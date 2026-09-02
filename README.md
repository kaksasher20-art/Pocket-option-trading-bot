# Pocket Signals Bot v2.0 — Multi-Asset Auto-Scanner

Automated trading signal bot that scans **6 Binance pairs** across **2 timeframes**, computes signals using **5 technical indicators**, and delivers alerts via **Telegram** + **Google Sheets**.

> ⚠️ **Educational only.** Signals are not financial advice. No trades are placed.

## Features

- **Multi-asset scanning** — BTCUSDT, ETHUSDT, XRPUSDT, SOLUSDT, XAUUSDT, XAGUSDT
- **Dual timeframes** — 1-minute and 5-minute candles
- **5-indicator consensus engine** — RSI, EMA crossover, MACD histogram, Bollinger Bands, trend filter
- **75% confidence threshold** — signals fire only when ≥4 of 5 indicators agree
- **Telegram alerts** — instant push notifications with formatted signal details
- **Google Sheets logging** — persistent signal history with all indicator values
- **Win rate tracker** — automatic outcome evaluation and win/loss statistics
- **UTC+4 timestamps** — all times displayed in Gulf Standard Time

## Indicators

| # | Indicator | BUY Condition | SELL Condition |
|---|-----------|---------------|----------------|
| 1 | RSI (14) | < 35 (oversold) | > 65 (overbought) |
| 2 | EMA 10/25 | EMA10 crosses above EMA25 | EMA10 crosses below EMA25 |
| 3 | MACD Histogram | Positive & rising | Negative & falling |
| 4 | Bollinger Bands | Price near lower band (%B < 0.20) | Price near upper band (%B > 0.80) |
| 5 | Trend (EMA50/200) | Price above both EMAs | Price below both EMAs |

## Setup

### 1. Clone & install
```bash
git clone <repo-url>
cd pocket-signal-upgrade
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your values
```

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Yes | Your Telegram chat/group ID |
| `SHEET_ID` | No | Google Sheet ID for logging |
| `GCP_SERVICE_ACCOUNT_JSON` | If using Sheets | Service account JSON blob |
| `CANDLES` | No | Number of candles to fetch (default: 250) |
| `LOOP_SECONDS` | No | Scan interval in seconds (default: 60) |

### 3. Google Sheets (optional)
- Create a Google Sheet and share it with your service account email (Editor role)
- Copy the Sheet ID from the URL
- Set `SHEET_ID` and `GCP_SERVICE_ACCOUNT_JSON` in `.env`

### 4. Run
```bash
# Continuous loop (every 60s by default)
python Main.py

# Single scan and exit
python Main.py --once
```

## Sheet Columns
```
Timestamp | Asset | Interval | Close | Signal | Reasons | Confidence |
RSI | MACD | MACD_Signal | EMA_Fast | EMA_Slow | BB_Upper | BB_Lower
```

## Telegram Alert Format
```
🚨 SIGNAL ALERT
📊 BTC/USD | 1M
📈 CALL (BUY)
💰 Price: 77,335.20
🎯 Confidence: 80%
📌 Reasons: EMA crossover bullish, RSI oversold, MACD histogram rising, Bollinger lower band
⏰ 2026-09-02 23:01:34 UTC+4
```

## Win Rate Tracker
Signals are logged to `win_tracker.json`. After each scan cycle, the bot automatically:
- Checks past signals where enough time has elapsed (5 min for 1m, 15 min for 5m)
- Compares entry price vs current price in the signal direction
- Prints a summary: total signals, wins, losses, win rate %

## Project Structure
```
pocket-signal-upgrade/
├── Main.py                        # Entry point — multi-asset loop
├── strategies/
│   └── signal_engine.py           # 5-indicator consensus engine
├── sheets/
│   └── sheet_writer.py            # Google Sheets writer
├── utils/
│   ├── data.py                    # Binance kline fetcher (always fresh)
│   ├── timezone.py                # UTC+4 timestamp helpers
│   ├── telegram_notifier.py       # Telegram alert sender
│   └── win_tracker.py             # Signal outcome tracker
├── requirements.txt
├── .env.example
└── README.md
```
