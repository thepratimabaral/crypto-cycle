"""Download full daily history from free public APIs (no API keys needed).

BTC  -> blockchain.info charts API (price since 2010, hash rate, miner revenue)
Alts -> Binance public market-data API (daily candles since listing)
"""
import json
import ssl
import time
import urllib.request
from pathlib import Path

import certifi
import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
HEADERS = {"User-Agent": "crypto-cycle/0.1"}
# certifi's CA bundle: python.org builds on macOS ship without system certificates.
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def get_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60, context=SSL_CONTEXT) as r:
                return json.load(r)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def _today():
    return pd.Timestamp.now(tz="UTC").normalize().tz_localize(None)


def blockchain_series(chart):
    d = get_json(f"https://api.blockchain.info/charts/{chart}?timespan=all&format=json&sampled=false")
    s = pd.Series({pd.Timestamp(v["x"], unit="s").normalize(): float(v["y"]) for v in d["values"]})
    return s[~s.index.duplicated(keep="last")].sort_index()


def btc_history():
    price = blockchain_series("market-price")
    price = price[price > 0]
    hashrate = blockchain_series("hash-rate")
    revenue = blockchain_series("miners-revenue")
    idx = pd.date_range(price.index[0], price.index[-1], freq="D")
    return pd.DataFrame({
        "close": price.reindex(idx).ffill(),
        "hashrate": hashrate.reindex(idx).ffill(),
        "miners_revenue": revenue.reindex(idx).ffill(),
    })


def binance_daily(symbol):
    rows, start = [], 0
    while True:
        batch = get_json(
            "https://data-api.binance.vision/api/v3/klines"
            f"?symbol={symbol}&interval=1d&limit=1000&startTime={start}"
        )
        if not batch:
            break
        rows += batch
        if len(batch) < 1000:
            break
        start = batch[-1][0] + 1
    idx = pd.to_datetime([r[0] for r in rows], unit="ms").normalize()
    df = pd.DataFrame({
        "close": [float(r[4]) for r in rows],
        "volume": [float(r[7]) for r in rows],  # quote volume in USDT
    }, index=idx)
    df = df[~df.index.duplicated(keep="last")]
    return df.reindex(pd.date_range(df.index[0], df.index[-1], freq="D")).ffill()


def load_coin(symbol, binance_symbol):
    """Fetch fresh data; fall back to the last cached copy if the API is down."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_DIR / f"{symbol}.csv"
    try:
        df = btc_history() if binance_symbol is None else binance_daily(binance_symbol)
        df = df[df.index < _today()]  # drop today's unfinished candle
        df.to_csv(cache, index_label="date")
    except Exception as e:
        if not cache.exists():
            raise
        print(f"  ! {symbol}: fetch failed ({e}); using cached data")
        df = pd.read_csv(cache, index_col="date", parse_dates=True)
    return df


def fear_greed():
    """Crypto Fear & Greed Index (since 2018). Shown on the dashboard, not used in the score."""
    try:
        d = get_json("https://api.alternative.me/fng/?limit=1")["data"][0]
        return {"value": int(d["value"]), "label": d["value_classification"]}
    except Exception:
        return None
