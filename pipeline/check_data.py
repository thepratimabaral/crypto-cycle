# ----------------------------------Part1--------------------------------------------------
# check_data.py: reads every saved coin file and checks the data is good
# Run from the project root:  python pipeline/check_data.py   (run pipeline/fetch.py first for fresh data)

import sys                              # lets the script tell other programs "PASS" (0) or "FAIL" (1)
from pathlib import Path
import pandas as pd                     #importing libraries

# Our name → Binance name (None = BTC, which comes from Blockchain.com).
# Other files (live_log.py) use this list too, so every coin is defined in one place.
ASSETS = {
    "BTC": None,
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "SOL": "SOLUSDT",
    "XRP": "XRPUSDT",
    "ADA": "ADAUSDT",
    "DOGE": "DOGEUSDT",
}
COINS = list(ASSETS)                    # just the names: ["BTC", "ETH", ...]

MAX_STALE_DAYS = 3                      # if the newest day is older than this, the data stopped updating

# where fetch.py saves the files, built from this file's location so it works from any folder
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def main():
    problems = []        # a notepad: we write down anything that looks wrong, so we can sum it up at the end
    today = pd.Timestamp.now(tz="UTC").normalize().tz_localize(None)

    for coin in COINS:
        # Read the CSV file, e.g. data/raw/SOL.csv
        table = pd.read_csv(
            RAW_DIR / f"{coin}.csv",
            index_col="date",       # Use the date column as row labels, the same as set_index("date")
            parse_dates=True,       # treat those labels as real dates
        )
    # ---- EXPERIMENT: break the data on purpose (delete this line after testing) ----
        #table = table.drop(table.index[10:13])     # remove 3 days (rows 10, 11, 12)

        # table.iloc[10, 0] = 0          # TEMPORARY: set one price to 0
        # table.iloc[20, 0] = None       # TEMPORARY: make one price empty

        first_day = table.index[0].date()           # The first date
        last_day = table.index[-1].date()           # The last date

        print(coin, ":", first_day, "→", last_day, ",", len(table), "days")

    # ----------------------------------Part2--------------------------------------------------
    # --------------------------- CHECK 1: missing days ---------------------------------------

        # Every date that SHOULD exist, from the first day to the last day
        expected_days = pd.date_range(start=table.index[0], end=table.index[-1], freq="D")

        # Dates that should exist but are not in our table
        missing_days = expected_days.difference(table.index)

        if len(missing_days) == 0:
            print("   ✓ no missing days")
        else:
            print("   ✗", len(missing_days), "missing days, e.g.", missing_days[:3].date)
            problems.append(f"{coin}: {len(missing_days)} missing days")   # note this problem in the notepad



    # ----------------------------------Part3--------------------------------------------------
    # -------------------------- CHECK 2: duplicate dates----------------------------------------

        duplicates = table.index.duplicated().sum()
        if duplicates == 0:
            print("   ✓ no duplicate dates")
        else:
            print("   ✗", duplicates, "duplicate dates")
            problems.append(f"{coin}: {duplicates} duplicate dates")
    # ----------------------------------Part4--------------------------------------------------
    # -------------------------- CHECK 3: empty prices ----------------------------------------

        empty = table["close"].isna().sum()
        if empty == 0:
            print("   ✓ no empty prices")
        else:
            print("   ✗", empty, "empty prices")
            problems.append(f"{coin}: {empty} empty prices")
    # ----------------------------------Part4--------------------------------------------------
    # ---------------------------- CHECK 4: zero or negative prices ---------------------------

        bad_prices = (table["close"] <= 0).sum()
        if bad_prices == 0:
            print("   ✓ no zero or negative prices")
        else:
            print("   ✗", bad_prices, "zero or negative prices")
            problems.append(f"{coin}: {bad_prices} zero or negative prices")

    # ---------------------------- CHECK 5: data is up to date --------------------------------

        days_old = (today - table.index[-1]).days    # how many days ago the newest row is
        if days_old <= MAX_STALE_DAYS:
            print("   ✓ up to date (newest day is", days_old, "day(s) old)")
        else:
            print("   ✗ newest day is", days_old, "days old")
            problems.append(f"{coin}: data is {days_old} days old")


    # -------------------------------------- FINAL RESULT ---------------------------------------
    # ---- FINAL RESULT: one clear answer, PASS if the notepad is empty, FAIL if it has anything written in it ----
    print()
    if len(problems) == 0:
        print("RESULT: PASS ✓  all", len(COINS), "coins look good")
        return 0                                      # 0 = "all good" for programs like GitHub Actions
    else:
        print("RESULT: FAIL ✗ ", len(problems), "problem(s) found:")
        for problem in problems:                      # read out each problem from the notepad
            print("  -", problem)
        return 1                                      # 1 = "something is wrong"


# Only run the checks when this file is run directly.
# live_log.py imports ASSETS and MAX_STALE_DAYS from here, and shouldn't trigger all the checks.
if __name__ == "__main__":
    sys.exit(main())
