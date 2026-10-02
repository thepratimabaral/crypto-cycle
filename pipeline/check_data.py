"""Download every asset and report coverage and data-quality problems.

Run from the project root:  python -m pipeline.check_data
Exits with code 1 if any asset fails to load or has a blocking problem.
"""
import sys

import pandas as pd

from pipeline.fetch import load_coin

# symbol -> Binance pair (None = BTC from blockchain.info)
ASSETS = {
    "BTC": None,
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "SOL": "SOLUSDT",
    "XRP": "XRPUSDT",
    "ADA": "ADAUSDT",
    "DOGE": "DOGEUSDT",
}

MAX_STALE_DAYS = 3        # last row older than this = blocking
MAX_DAILY_MOVE = 0.60     # |1-day return| above this is flagged for review


def check(symbol, df):
    """Return (row dict, list of blocking problems, list of warnings)."""
    blocking, warnings = [], []
    close = df["close"]

    expected = pd.date_range(df.index.min(), df.index.max(), freq="D")
    missing = expected.difference(df.index)
    if len(missing):
        blocking.append(f"{len(missing)} missing days")

    if df.index.duplicated().any():
        blocking.append(f"{df.index.duplicated().sum()} duplicate dates")

    nonpos = int((close <= 0).sum())
    if nonpos:
        blocking.append(f"{nonpos} zero/negative prices")

    nulls = df.isna().sum()
    for col, n in nulls.items():
        if n:
            (blocking if col == "close" else warnings).append(f"{n} empty values in {col}")

    stale = (pd.Timestamp.now(tz="UTC").normalize().tz_localize(None) - df.index.max()).days
    if stale > MAX_STALE_DAYS:
        blocking.append(f"last row is {stale} days old")

    # Forward-filled gaps show up as long runs of identical prices.
    runs = (close != close.shift()).cumsum()
    longest_flat = int(close.groupby(runs).size().max())
    if longest_flat >= 5:
        warnings.append(f"price unchanged for {longest_flat} days in a row")

    moves = close.pct_change().abs()
    big = moves[moves > MAX_DAILY_MOVE]
    if len(big):
        days = ", ".join(f"{d:%Y-%m-%d} ({m:+.0%})" for d, m in big.head(3).items())
        more = f" +{len(big) - 3} more" if len(big) > 3 else ""
        warnings.append(f"{len(big)} daily moves over {MAX_DAILY_MOVE:.0%}: {days}{more}")

    row = {
        "asset": symbol,
        "first": f"{df.index.min():%Y-%m-%d}",
        "last": f"{df.index.max():%Y-%m-%d}",
        "rows": len(df),
        "years": round(len(df) / 365.25, 1),
        "first_close": close.iloc[0],
        "last_close": close.iloc[-1],
        "columns": ", ".join(df.columns),
    }
    return row, blocking, warnings


def main():
    rows, failed = [], False
    for symbol, pair in ASSETS.items():
        try:
            df = load_coin(symbol, pair)
        except Exception as e:
            print(f"✗ {symbol}: could not load ({e})")
            failed = True
            continue
        row, blocking, warnings = check(symbol, df)
        rows.append(row)
        status = "✗" if blocking else "✓"
        print(f"{status} {symbol}: {row['first']} → {row['last']} · {row['rows']:,} days")
        for msg in blocking:
            print(f"    BLOCKING  {msg}")
        for msg in warnings:
            print(f"    warning   {msg}")
        failed |= bool(blocking)

    if rows:
        print()
        table = pd.DataFrame(rows).set_index("asset")
        with pd.option_context("display.width", 140, "display.float_format", "{:,.4f}".format):
            print(table)

    print("\nRESULT:", "FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
