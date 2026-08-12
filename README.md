# Pocket-option-trading-bot
Pocket option  trading  bot 2025 edition 
# Pocket Signals Bot (No Auto-Trading)

This bot **does not** place trades. It fetches public market data (Binance), computes **RSI + EMA crossover + MACD** signals, and writes them to a **Google Sheet**.

## Columns (Sheet1)
`Timestamp | Asset | Interval | Close | Signal | Reasons | RSI | MACD | MACD_Signal | EMA10 | EMA25`

## Setup

### 1) Google Sheet
- Create a sheet and share it with your **service account** email (Editor).
- Copy the **Sheet ID** (from the URL).

### 2) Service Account
- Create a GCP service account and download credentials JSON.
- **Recommended:** Convert the whole JSON to a single line and set it as Heroku Config Var:
  - Key: `GCP_SERVICE_ACCOUNT_JSON`
  - Value: contents of the JSON file
- Alternatively (less safe), upload `credentials.json` into the repo.

### 3) Heroku Deploy
- Add buildpack: **heroku/python**
- Config Vars:
  - `SHEET_ID` = `<your sheet id>`
  - `ASSET` = `BTCUSDT` (default)
  - `INTERVAL` = `1m` (or `5m`)
  - `CANDLES` = `200`
  - `GCP_SERVICE_ACCOUNT_JSON` = `<paste JSON blob>` (recommended)

### 4) Run
- `worker: python main.py` (Procfile included)
- Option A: Add **Heroku Scheduler** (every 1 or 5 minutes).
- Option B: Manually run the dyno.
## Notes
- Educational only. Signals are not financial advice.
- No interaction with Pocket Option or any broker API.
