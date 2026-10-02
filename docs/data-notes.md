# Data notes

Checked with `python -m pipeline.check_data` on 2026-10-02. Result: **PASS** for all 7 assets.

## Coverage

| Asset | Source | First day | Last day | Days | Years | Columns |
|---|---|---|---|---:|---:|---|
| BTC | blockchain.info | 2010-08-18 | 2026-10-01 | 5,889 | 16.1 | close, hashrate, miners_revenue |
| ETH | Binance `ETHUSDT` | 2017-08-17 | 2026-10-01 | 3,333 | 9.1 | close, volume |
| BNB | Binance `BNBUSDT` | 2017-11-06 | 2026-10-01 | 3,252 | 8.9 | close, volume |
| XRP | Binance `XRPUSDT` | 2018-05-04 | 2026-10-01 | 3,073 | 8.4 | close, volume |
| ADA | Binance `ADAUSDT` | 2018-04-17 | 2026-10-01 | 3,090 | 8.5 | close, volume |
| DOGE | Binance `DOGEUSDT` | 2019-07-05 | 2026-10-01 | 2,646 | 7.2 | close, volume |
| SOL | Binance `SOLUSDT` | 2020-08-11 | 2026-10-01 | 2,243 | 6.1 | close, volume |

No missing days, duplicate dates, empty prices, or zero/negative prices in any asset.
The last day is always yesterday (UTC): today's unfinished candle is dropped on purpose.

## Storage

Downloads are saved to `data/raw/<ASSET>.csv` (about 1 MB in total) and committed to Git, so everyone works
from the same snapshot. Each run refreshes them; if an API is down, the pipeline falls back to the committed copy.

## Source details

- **blockchain.info** (`/charts/{market-price,hash-rate,miners-revenue}?timespan=all&sampled=false`):
  one value per day. Prices before 2010-08-18 are `0` and are dropped. Hash rate and miner revenue
  are forward-filled onto the price calendar.
- **Binance** (`data-api.binance.vision/api/v3/klines`, 1d): paginated 1,000 candles per call.
  Prices are in **USDT**, not USD (the difference is normally under 0.5%). `volume` is quote volume in USDT.
  History starts at the Binance listing, not the coin's launch (e.g. ETH trading before Aug 2017 is missing).
- **Not usable on the free tier:** CoinGecko (365 days max), CryptoCompare (needs an API key).

## Anomalies reviewed

| Asset | Finding | Verdict |
|---|---|---|
| BTC | Price flat for 5–21 days at a time, 2010-08 to 2012-05 | Early prices rounded to cents in a very thin market. Fine: no score exists before ~2011 (indicators need 1–4 years of history first). |
| BTC | +67% on 2010-09-16 | Real move in a tiny early market. Keep. |
| BNB | +63% on 2018-01-05, +70% on 2021-02-19 | Real rallies. Keep. |
| XRP | +73% on 2023-07-13 | Real: SEC court ruling. Keep. |
| ADA | +72% on 2025-03-02 | Real: US crypto reserve announcement. Keep. |
| DOGE | +85% 2021-01-02, +392% 2021-01-28, +100% 2021-04-16 | Real social-media-driven spikes. Keep. Percentile scoring is robust to these. |

## Setup note

Python from python.org on macOS has no root certificates, which caused
`CERTIFICATE_VERIFY_FAILED`. `fetch.py` now uses the `certifi` bundle (added to `requirements.txt`),
so this works the same on every machine and in GitHub Actions.

## Impact on the model

- BTC has enough history for every indicator, including the 200-week MA (needs 1,400 days).
- SOL reaches a 200-week MA value only from mid-2024, and DOGE from 2023. Until then, their valuation score uses the other indicators.
- Backtests for SOL and DOGE cover only a few years, so their forecasts will carry a **Low/Medium** confidence label.
