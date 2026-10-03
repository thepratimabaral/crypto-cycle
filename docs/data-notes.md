# Data notes

Downloaded with `python pipeline/fetch.py` and checked with `python pipeline/check_data.py` on 2026-10-03.
Result: **PASS** for all 7 assets (no missing days, duplicate dates, empty prices, or zero/negative prices).

## Coverage

| Asset | Source | First day | Last day | Days | Years | Columns |
|---|---|---|---|---:|---:|---|
| BTC | blockchain.info | 2010-08-18 | 2026-10-02 | 5,891 | 16.1 | close |
| ETH | Binance `ETHUSDT` | 2017-08-17 | 2026-10-03 | 3,335 | 9.1 | close |
| BNB | Binance `BNBUSDT` | 2017-11-06 | 2026-10-03 | 3,254 | 8.9 | close |
| XRP | Binance `XRPUSDT` | 2018-05-04 | 2026-10-03 | 3,075 | 8.4 | close |
| ADA | Binance `ADAUSDT` | 2018-04-17 | 2026-10-03 | 3,092 | 8.5 | close |
| DOGE | Binance `DOGEUSDT` | 2019-07-05 | 2026-10-03 | 2,648 | 7.2 | close |
| SOL | Binance `SOLUSDT` | 2020-08-11 | 2026-10-03 | 2,245 | 6.1 | close |

BTC ends yesterday (blockchain.info publishes one value per finished day).
Binance files include today's unfinished day as the last row; dropping it is a planned improvement.

## Storage

Downloads are saved to `data/raw/<ASSET>.csv` (about 1 MB in total) and committed to Git, so everyone works
from the same snapshot. Each run of `fetch.py` overwrites them with fresh data.

## Source details

- **blockchain.info** (`/charts/market-price?timespan=all&sampled=false`): one value per day.
  Prices before 2010-08-18 are `0` and are dropped.
- **Binance** (`data-api.binance.vision/api/v3/klines`, 1d): paginated 1,000 candles per call.
  Prices are in **USDT**, not USD (the difference is normally under 0.5%).
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

`fetch.py` uses `requests`, which ships its own certificate bundle, so downloads work on macOS
python.org builds without extra setup.

## Impact on the model

- BTC hash rate and miner revenue (for Hash Ribbons and Puell Multiple) are not downloaded yet; add them before M2.

- BTC has enough history for every indicator, including the 200-week MA (needs 1,400 days).
- SOL reaches a 200-week MA value only from mid-2024, and DOGE from 2023. Until then, their valuation score uses the other indicators.
- Backtests for SOL and DOGE cover only a few years, so their forecasts will carry a **Low/Medium** confidence label.
