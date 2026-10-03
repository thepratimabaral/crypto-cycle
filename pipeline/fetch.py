#importing libraries

import requests                         # requesting website for data
import pandas as pd
from pathlib import Path                # works with folders and file path

DATA_FOLDER = Path("data/raw")          #where the downloaded files get saved


#------- for btc--------#
def get_btc():
     
    url = "https://api.blockchain.info/charts/market-price?timespan=all&format=json&sampled=false"     #API address
    data = requests.get(url).json()                  #downloads the data from web and turns it in python data to use
    table = pd.DataFrame(data["values"])             #turns the list of daily prices into a table
    table = table.rename(columns={"x": "date", "y": "close"})               #Rename the columns: x is the date, y is the price
    table["date"] = pd.to_datetime(table["date"], unit="s")                 #Turn the timestamp numbers into real dates
    table = table[table["close"] > 0]                                       #Remove the days with price 0 (before 2010-08-18)
    return table

# ---- TEST: run the function and show the last 5 rows ----

#btc = get_btc()
#print(btc.head()) 

#------- for other 6 coins-------#

def get_binance(symbol):
    all_days = []        # empty list; we'll add each page of days to it
    start_time = 0       # 0 = start from the very first day

    while True:          # keep repeating until the "break"
        url = (
            "https://data-api.binance.vision/api/v3/klines"
            f"?symbol={symbol}&interval=1d&limit=1000&startTime={start_time}"
        )
        page = requests.get(url).json()      # downloads the data from web and here one page = up to 1000 days

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


# ---- TEST ----
#eth = get_binance("ETHUSDT")
#print(eth.head())                       # first 5 days
#print(eth.tail())                       # last 5 days
#print(len(eth), "days")                 # total count, e.g. 3335 days

# ---- TEST: every Binance coin ----
#coins = ["ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"]

# for coin in coins:
#     table = get_binance(coin)           # Download this coin
#     first_day = table["date"].iloc[0].date()
#     last_price = table["close"].iloc[-1]
#     print(coin, "→", len(table), "days, from", first_day, ", last price", last_price)


#------- the one the rest of the project uses -------#
def load_coin(symbol, binance_symbol):                              # the name Binance uses, or none for BTC
    if binance_symbol is None:                # no Binance name → it's BTC
        table = get_btc()
    else:                                     # otherwise → ask Binance
        table = get_binance(binance_symbol)

    table = table.set_index("date")           # date becomes the row label

    DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    table.to_csv(DATA_FOLDER / f"{symbol}.csv")   # e.g. data/raw/SOL.csv
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