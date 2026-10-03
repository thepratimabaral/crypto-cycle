"""The model must never use the future: a run cut off at date d gives exactly the same values
on d as a run over the full history."""
import numpy as np
import pandas as pd
import pytest

from pipeline import model
from pipeline.fetch import RAW_DIR

CUTOFFS = {
    "BTC": ["2012-06-01", "2014-01-15", "2017-12-17", "2021-11-10", "2024-03-14"],
    "SOL": ["2022-03-01", "2023-06-30", "2025-01-20"],
}


def _load(symbol):
    return pd.read_csv(RAW_DIR / f"{symbol}.csv", index_col="date", parse_dates=True)


def _all_values(df, window=None):
    scores = model.cycle_scores(df, window=window)
    cols = [scores]
    for h in model.HORIZONS:
        cols.append(model.forecast(df, scores, h).add_suffix(f"_{h}"))
    return pd.concat(cols, axis=1)


@pytest.mark.parametrize("window", [None, model.WINDOW_4Y], ids=["all-history", "4y"])
@pytest.mark.parametrize("symbol", list(CUTOFFS))
def test_no_lookahead(symbol, window):
    df = _load(symbol)
    full = _all_values(df, window)
    for cutoff in CUTOFFS[symbol]:
        part = _all_values(df[df.index <= cutoff], window)
        a, b = full.loc[cutoff], part.loc[cutoff]
        assert a.notna().equals(b.notna()), f"{symbol} {cutoff}: different nulls"
        np.testing.assert_allclose(a.dropna().to_numpy(float), b.dropna().to_numpy(float),
                                   rtol=1e-12, err_msg=f"{symbol} {cutoff}")


def test_score_exists_on_cutoffs():
    full = _all_values(_load("BTC"))
    assert full.loc[CUTOFFS["BTC"][1:], ["score", "pUp_90"]].notna().all().all()


def test_percentile_bounds_and_history():
    x = pd.Series(np.arange(400, dtype=float))
    pct = model.expanding_percentile(x)
    assert pct.iloc[:365].isna().all()
    assert pct.iloc[365:].eq(100).all()                    # each value is a new high
    low = model.expanding_percentile(pd.Series(-np.arange(400, dtype=float)))
    assert low.iloc[365:].eq(0).all()                      # each value is a new low


def test_percentile_ties_and_window():
    x = pd.Series([1.0] * 365 + [1.0, 2.0, np.nan, 0.5])
    pct = model.expanding_percentile(x)
    assert pct.iloc[365] == 50                              # equal to every earlier value
    assert pct.iloc[366] == 100
    assert np.isnan(pct.iloc[367])
    assert pct.iloc[368] == 0
    # With a window, only the last `window` earlier values count.
    y = pd.Series([10.0] * 365 + [0.0] * 365 + [5.0])
    assert model.expanding_percentile(y, window=365).iloc[-1] == 100
    assert model.expanding_percentile(y).iloc[-1] == 50


def test_group_forecast_uses_only_known_outcomes():
    close = pd.Series([1.0, 2.0, 3.0, 2.0, 1.0, 5.0],
                      index=pd.date_range("2020-01-01", periods=6))
    f = model.group_forecast(np.zeros(6), close, horizon=2, prior=0)
    # Day 2 knows day 0's outcome only (1 → 3, up). Day 4 knows days 0–2: up, same, down.
    assert np.isnan(f["pUp"].iloc[1])
    assert f["pUp"].iloc[2] == 1.0
    assert f["pUp"].iloc[4] == pytest.approx(1 / 3)
    assert f["samples"].iloc[4] == 3


def test_regimes():
    assert model.regime(0) == "Capitulation"
    assert model.regime(20) == "Accumulation"
    assert model.regime(59.9) == "Early Expansion"
    assert model.regime(80) == "Euphoria"
    assert model.regime(float("nan")) is None
