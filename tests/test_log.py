"""The prediction log is append-only: re-running adds nothing, and resolving an entry only
fills in its outcome fields."""
import copy

import numpy as np
import pandas as pd

from pipeline import live_log

OUTCOME_FIELDS = {"status", "outcomePrice", "wentUp", "correct", "resolvedOn"}


def _prices(days, seed=7):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=days, freq="D")
    return pd.DataFrame({"close": 100 * np.exp(np.cumsum(rng.normal(0, 0.03, days)))}, index=idx)


def test_same_day_rerun_adds_nothing():
    df = _prices(1200)
    today = df.index[-1] + pd.Timedelta(days=1)
    log = {"entries": []}
    assert live_log.update(log, "TEST", df, today) == (3, 0)
    before = copy.deepcopy(log)
    assert live_log.update(log, "TEST", df, today) == (0, 0)
    assert log == before


def test_resolving_changes_only_outcome_fields():
    full = _prices(1300)
    df = full.iloc[:1200]
    log = {"entries": []}
    live_log.update(log, "TEST", df, df.index[-1] + pd.Timedelta(days=1))
    first = copy.deepcopy(log["entries"])

    later = full.iloc[:1240]                     # 40 days on: the 30-day entry is due
    added, resolved = live_log.update(log, "TEST", later, later.index[-1] + pd.Timedelta(days=1))
    assert (added, resolved) == (3, 1)

    for old, new in zip(first, log["entries"]):
        changed = {k for k in old if old[k] != new[k]}
        assert changed <= OUTCOME_FIELDS
    done = next(e for e in log["entries"] if e["status"] == "resolved")
    assert done["horizon"] == 30
    target = pd.Timestamp(done["targetDate"])
    assert done["outcomePrice"] == later.loc[target, "close"]
    assert done["wentUp"] == (done["outcomePrice"] > done["priceAtPrediction"])
    assert done["correct"] == ((done["pUp"] > 0.5) == done["wentUp"])


def test_stale_data_adds_nothing():
    df = _prices(1200)
    log = {"entries": []}
    assert live_log.update(log, "TEST", df, df.index[-1] + pd.Timedelta(days=10)) == (0, 0)
