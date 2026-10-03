"""Indicators, cycle score and P(up) forecasts, exactly as fixed in docs/method-v1.md.

Every value on day t uses only rows up to and including t (tests/test_model.py checks this).
"""
import math
from bisect import bisect_left, bisect_right, insort

import numpy as np
import pandas as pd

HORIZONS = (30, 90, 365)
MIN_HISTORY = 365        # prior readings an indicator needs before it gets a score
WINDOW_4Y = 1460         # prior readings used by the cycle-w4y variant
PRIOR_DAYS = 20          # shrinkage toward the base rate, in pseudo-days
MIN_PER_GROUP = 2        # indicator scores needed for a valuation or trend value

VALUATION = ("mayer", "wma200", "athDistance", "puell")
TREND = ("goldenCross", "momentum90", "rsi30", "hashRibbons")

REGIMES = ((80, "Euphoria"), (60, "Mid Bull"), (40, "Early Expansion"),
           (20, "Accumulation"), (0, "Capitulation"))


def _sma(x, n):
    return x.rolling(n, min_periods=n).mean()


def _rsi(close, n=30):
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + gain / loss)


def indicators(df):
    """Raw indicator values. BTC-only indicators are left out when their column is missing."""
    close = df["close"]
    out = {
        "mayer": close / _sma(close, 200),
        "wma200": close / _sma(close, 1400),
        "athDistance": close / close.cummax(),
        "goldenCross": _sma(close, 50) / _sma(close, 200) - 1,
        "momentum90": close / close.shift(90) - 1,
        "rsi30": _rsi(close),
    }
    if "miners_revenue" in df:
        rev = df["miners_revenue"]
        out["puell"] = rev / _sma(rev, 365)
    if "hashrate" in df:
        hr = df["hashrate"]
        out["hashRibbons"] = _sma(hr, 30) / _sma(hr, 60) - 1
    # 0/0 in flat early markets gives NaN; x/0 gives inf. Neither is a reading.
    return pd.DataFrame(out, index=df.index).replace([np.inf, -np.inf], np.nan)


def expanding_percentile(x, window=None, min_history=MIN_HISTORY):
    """Percentile of each value among the earlier non-null values (all of them, or the last
    `window`): 100 × (count below + half the count equal) ÷ count. Null until `min_history`
    earlier values exist."""
    values = x.to_numpy(float)
    out = np.full(len(values), np.nan)
    seen, order = [], []          # sorted earlier values; the same values in arrival order
    for i, v in enumerate(values):
        if math.isnan(v):
            continue
        m = len(seen)
        if m >= min_history:
            lo, hi = bisect_left(seen, v), bisect_right(seen, v)
            out[i] = 100 * (lo + 0.5 * (hi - lo)) / m
        insort(seen, v)
        if window is not None:
            order.append(v)
            if len(order) > window:
                seen.pop(bisect_left(seen, order.pop(0)))
    return pd.Series(out, index=x.index)


def _group_mean(scores, keys):
    cols = [k for k in keys if k in scores]
    block = scores[cols]
    return block.mean(axis=1).where(block.notna().sum(axis=1) >= MIN_PER_GROUP)


def regime(score):
    if score is None or math.isnan(score):
        return None
    return next(name for floor, name in REGIMES if score >= floor)


def cycle_scores(df, window=None):
    """Indicator scores plus valuation, trend and composite score (0–100)."""
    raw = indicators(df)
    scores = raw.apply(lambda col: expanding_percentile(col, window=window))
    valuation = _group_mean(scores, VALUATION)
    trend = _group_mean(scores, TREND)
    out = scores.add_suffix("_score")
    out["valuation"] = valuation
    out["trend"] = trend
    out["score"] = (valuation + trend) / 2
    return pd.concat([raw, out], axis=1)


def bucket(score):
    """10-point bucket 0–9 (100 falls in 9); NaN stays NaN."""
    return np.minimum(np.floor(score / 10), 9)


def outcomes(close, horizon):
    """1.0 if close is higher `horizon` days later, 0.0 if not, NaN if not yet known."""
    c = close.to_numpy(float)
    up = np.full(len(c), np.nan)
    if horizon < len(c):
        up[:-horizon] = (c[horizon:] > c[:-horizon]).astype(float)
    return up


def group_forecast(groups, close, horizon, prior=PRIOR_DAYS):
    """P(up) on each day from the known outcomes of earlier days in the same group, shrunk
    toward the known base rate. A day's outcome counts once `horizon` days have passed.

    Returns a DataFrame with pUp, baseRate and samples (days in the group with a known outcome).
    """
    g = np.asarray(groups, float)
    up = outcomes(close, horizon)
    n = len(g)
    p_up, base, samples = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    counts = {}                   # group -> [days, ups]
    total, total_up = 0, 0.0
    for t in range(n):
        s = t - horizon           # this day's outcome became known today
        if s >= 0:
            total += 1
            total_up += up[s]
            if not math.isnan(g[s]):
                c = counts.setdefault(g[s], [0, 0.0])
                c[0] += 1
                c[1] += up[s]
        if total == 0:
            continue
        base[t] = total_up / total
        if math.isnan(g[t]):
            continue
        days, ups = counts.get(g[t], (0, 0.0))
        p_up[t] = (ups + prior * base[t]) / (days + prior)
        samples[t] = days
    return pd.DataFrame({"pUp": p_up, "baseRate": base, "samples": samples}, index=close.index)


def forecast(df, scores, horizon):
    """The cycle model's P(up) for one horizon."""
    return group_forecast(bucket(scores["score"]), df["close"], horizon)
