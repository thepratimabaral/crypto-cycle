"""Download full daily price history from free public APIs (no account or API key needed).

Run from the project root:  python pipeline/fetch.py
BTC    -> Blockchain.com (price since 2010, hash rate, miner revenue)
Others -> Binance (daily prices since each coin was listed)
Saves one file per coin in data/raw/.
"""

#importing libraries

import requests                         # requesting website for data
import pandas as pd
from pathlib import Path                # works with folders and file path

# where the downloaded files get saved.
# Built from this file's location, so it works no matter which folder you run from.
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
DATA_FOLDER = RAW_DIR                   # same folder, the name I used first


def _today():
    """Today's date in UTC, with no time part (e.g. 2026-10-03 00:00)."""
    return pd.Timestamp.now(tz="UTC").normalize().tz_localize(None)


def download(url):
    """Call an API address and return its answer as Python data."""
    response = requests.get(url, timeout=60)   # give up if no answer within 60 seconds
    response.raise_for_status()                # stop with an error if the website said "error"
    return response.json()


#------- for btc--------#
def get_blockchain_chart(chart):
    """One Blockchain.com chart (e.g. "market-price"): one value per day, with the date as label."""
    url = f"https://api.blockchain.info/charts/{chart}?timespan=all&format=json&sampled=false"     #API address
    data = download(url)                             #downloads the data from web and turns it in python data to use
    table = pd.DataFrame(data["values"])             #turns the list of daily values into a table
    table["x"] = pd.to_datetime(table["x"], unit="s").dt.normalize()   #Turn the timestamp numbers into real dates
    return table.set_index("x")["y"]                 # x is the date, y is the value


def get_btc():
    price = get_blockchain_chart("market-price")             # BTC price in USD
    hashrate = get_blockchain_chart("hash-rate")             # computing power securing Bitcoin (for Hash Ribbons)
    revenue = get_blockchain_chart("miners-revenue")         # USD paid to miners per day (for Puell Multiple)

    price = price[price > 0]                                 #Remove the days with price 0 (before 2010-08-18)

    # Put the three side by side, one row per price day.
    # If hash rate or revenue has no value on a day, copy the day before (ffill = "fill forward").
    table = pd.DataFrame({
        "close": price,
        "hashrate": hashrate.reindex(price.index).ffill(),
        "miners_revenue": revenue.reindex(price.index).ffill(),
    })
    table.index.name = "date"
    return table.reset_index()                               # date back as a normal column, like get_binance


#------- for other 6 coins-------#

def get_binance(symbol):
    all_days = []        # empty list; we'll add each page of days to it
    start_time = 0       # 0 = start from the very first day

    while True:          # keep repeating until the "break"
        url = (
            "https://data-api.binance.vision/api/v3/klines"
            f"?symbol={symbol}&interval=1d&limit=1000&startTime={start_time}"
        )
        page = download(url)                 # downloads the data from web and here one page = up to 1000 days

        all_days = all_days + page           # the new page's days are added to the end of the pile

        if len(page) < 1000:                 #Check if this was the last page  # how many days are in this page (max 1000)
            break                            # stop the loop

        start_time = page[-1][0] + 1         # next page starts after the last day

    # each day is a list: [open time, open, high, low, close, volume, ...]
    #                         index 0                    4
    table = pd.DataFrame({
        "date": [day[0] for day in all_days],
        "close": [float(day[4]) for day in all_days],
    })
    table["date"] = pd.to_datetime(table["date"], unit="ms")   # Binance uses milliseconds
    return table


#------- the one the rest of the project uses -------#
def load_coin(symbol, binance_symbol):                              # the name Binance uses, or none for BTC
    saved_file = RAW_DIR / f"{symbol}.csv"                          # e.g. data/raw/SOL.csv

    try:
        if binance_symbol is None:                # no Binance name → it's BTC
            table = get_btc()
        else:                                     # otherwise → ask Binance
            table = get_binance(binance_symbol)
    except Exception as error:
        # The website is down or changed: use the copy we saved last time instead of stopping.
        if not saved_file.exists():
            raise                                 # no saved copy either → we really can't continue
        print(f"  ! {symbol}: download failed ({error}); using the saved file")
        return pd.read_csv(saved_file, index_col="date", parse_dates=True)

    table = table.set_index("date")               # date becomes the row label
    table = table[table.index < _today()]         # drop today: its price isn't final until midnight UTC

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(saved_file)
    return table

# ---- TEST: only runs when I click ▶ on this file ----
if __name__ == "__main__":
    coins = {
        "BTC": None,
        "ETH": "ETHUSDT",
        "BNB": "BNBUSDT",
        "SOL": "SOLUSDT",
        "XRP": "XRPUSDT",
        "ADA": "ADAUSDT",
        "DOGE": "DOGEUSDT",
    }
    for name, binance_name in coins.items():
        table = load_coin(name, binance_name)
        print(name, "→", len(table), "days saved to data/raw/" + name + ".csv")
