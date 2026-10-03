# Raw price data

Daily history for 7 coins, one row per day (UTC). Downloaded by [`pipeline/fetch.py`](../../pipeline/fetch.py)
from free public APIs (no account or API key). Refresh with `python pipeline/fetch.py`, then check with `python pipeline/check_data.py`.

| File | Coin | Source website | Exact API used | Columns | From |
|---|---|---|---|---|---|
| `BTC.csv` | Bitcoin | [blockchain.com](https://www.blockchain.com/explorer/charts/market-price) | `api.blockchain.info/charts/market-price?timespan=all&sampled=false` | close (USD) | 2010-08-18 |
| `ETH.csv` | Ethereum | [binance.com](https://www.binance.com/en/trade/ETH_USDT) | `data-api.binance.vision/api/v3/klines?symbol=ETHUSDT&interval=1d` | close (USDT) | 2017-08-17 |
| `BNB.csv` | BNB | [binance.com](https://www.binance.com/en/trade/BNB_USDT) | `…/klines?symbol=BNBUSDT&interval=1d` | close (USDT) | 2017-11-06 |
| `XRP.csv` | XRP | [binance.com](https://www.binance.com/en/trade/XRP_USDT) | `…/klines?symbol=XRPUSDT&interval=1d` | close (USDT) | 2018-05-04 |
| `ADA.csv` | Cardano | [binance.com](https://www.binance.com/en/trade/ADA_USDT) | `…/klines?symbol=ADAUSDT&interval=1d` | close (USDT) | 2018-04-17 |
| `DOGE.csv` | Dogecoin | [binance.com](https://www.binance.com/en/trade/DOGE_USDT) | `…/klines?symbol=DOGEUSDT&interval=1d` | close (USDT) | 2019-07-05 |
| `SOL.csv` | Solana | [binance.com](https://www.binance.com/en/trade/SOL_USDT) | `…/klines?symbol=SOLUSDT&interval=1d` | close (USDT) | 2020-08-11 |

## Columns

| Column | Meaning |
|---|---|
| `date` | Day in UTC (`YYYY-MM-DD`) |
| `close` | BTC: average USD price across major exchanges that day. Others: Binance closing price at 00:00 UTC, in USDT (≈ USD) |

## Notes

- Binance history starts at the **Binance listing date**, not the coin's launch.
- BTC prices before 2010-08-18 are `0` at the source and are removed.
- Binance files include today's unfinished day as the last row (its price changes until 00:00 UTC).
- Coverage checks and reviewed anomalies: [`docs/data-notes.md`](../../docs/data-notes.md).
