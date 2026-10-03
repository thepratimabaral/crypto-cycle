"""Append today's v1 forecasts to the live prediction log and resolve the ones that came due.

Run from the project root:  python -m pipeline.live_log
Downloads fresh data for all 7 coins (falls back to data/raw/ if an API is down), then
updates web/data/predictions_log.json. Entries are never edited, except that a pending one
gets its outcome once its target date has a close. Running twice on one day adds nothing.
Exits with code 1 if any coin was skipped or had stale data (the log is still saved).
"""
import json
import math
import sys
from pathlib import Path

import pandas as pd

from pipeline import model
from pipeline.check_data import ASSETS, MAX_STALE_DAYS
from pipeline.fetch import _today, load_coin

LOG_PATH = Path(__file__).resolve().parent.parent / "web" / "data" / "predictions_log.json"
METHOD = "v1"


def load_log(path=LOG_PATH):
    return json.loads(path.read_text()) if path.exists() else {"entries": []}


def save_log(log, path=LOG_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=1, allow_nan=False) + "\n")


def update(log, symbol, df, today):
    """Add today's forecasts for one coin and resolve its due entries. Returns (added, resolved)."""
    entries = log["entries"]
    known = {e["id"] for e in entries}
    added = resolved = 0

    last = df.index[-1]
    scores = model.cycle_scores(df)
    score = scores["score"].iloc[-1]
    fresh = (today - last).days <= MAX_STALE_DAYS
    if fresh and not math.isnan(score):
        for horizon in model.HORIZONS:
            entry_id = f"{symbol}-{horizon}-{last:%Y-%m-%d}"
            if entry_id in known:
                continue
            f = model.forecast(df, scores, horizon).iloc[-1]
            entries.append({
                "id": entry_id,
                "coin": symbol,
                "madeOn": f"{last:%Y-%m-%d}",
                "horizon": horizon,
                "targetDate": f"{last + pd.Timedelta(days=horizon):%Y-%m-%d}",
                "method": METHOD,
                "score": round(float(score), 1),
                "regime": model.regime(score),
                "pUp": round(float(f["pUp"]), 4),
                "baseRate": round(float(f["baseRate"]), 4),
                "priceAtPrediction": float(df["close"].iloc[-1]),
                "status": "pending",
                "outcomePrice": None,
                "wentUp": None,
                "correct": None,
                "resolvedOn": None,
            })
            added += 1

    for e in entries:
        target = pd.Timestamp(e["targetDate"])
        if e["coin"] == symbol and e["status"] == "pending" and target in df.index:
            outcome = float(df.loc[target, "close"])
            e["outcomePrice"] = outcome
            e["wentUp"] = outcome > e["priceAtPrediction"]
            e["correct"] = (e["pUp"] > 0.5) == e["wentUp"]
            e["resolvedOn"] = f"{today:%Y-%m-%d}"
            e["status"] = "resolved"
            resolved += 1
    return added, resolved


def main():
    log, today = load_log(), _today()
    problems = 0
    for symbol, pair in ASSETS.items():
        try:
            df = load_coin(symbol, pair)
        except Exception as e:
            print(f"✗ {symbol}: could not load ({e}); skipped")
            problems += 1
            continue
        added, resolved = update(log, symbol, df, today)
        stale = (today - df.index[-1]).days > MAX_STALE_DAYS
        problems += stale
        note = f" · data is stale (last day {df.index[-1]:%Y-%m-%d}), nothing added" if stale else ""
        print(f"{symbol}: +{added} new, {resolved} resolved{note}")
    save_log(log)
    pending = sum(e["status"] == "pending" for e in log["entries"])
    print(f"Log: {len(log['entries'])} entries, {pending} pending → {LOG_PATH.relative_to(LOG_PATH.parents[2])}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
