"""Walk-forward backtest of the v1 cycle score on BTC, exactly as fixed in docs/method-v1.md.

Run from the project root:  python -m pipeline.backtest
Reads the committed data/raw/BTC.csv (no download) and writes docs/results-btc-v1.md
and data/results/btc_v1.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import model

ROOT = Path(__file__).resolve().parent.parent
END = pd.Timestamp("2026-10-01")          # data snapshot the method was frozen against
WINDOWS = {"full": pd.Timestamp("2013-01-01"), "post2019": pd.Timestamp("2019-01-01")}
BOOT_RESAMPLES = 5000
BOOT_SEED = 20261003
CI = (5, 95)                              # 90% percentile interval
PRIMARY = ("full", 90)
REFERENCES = ("baseRate", "ma200")        # the model must beat both

MODEL_NAMES = {
    "cycle": "Cycle score",
    "baseRate": "Always up (base rate)",
    "ma200": "200-day rule",
    "coinFlip": "Coin flip",
    "valuationOnly": "Valuation only",
    "trendOnly": "Trend only",
    "cycle-w4y": "Cycle score, 4-year window",
}


def load_btc():
    df = pd.read_csv(ROOT / "data" / "raw" / "BTC.csv", index_col="date", parse_dates=True)
    df = df[df.index <= END]
    expected = pd.date_range(df.index[0], df.index[-1], freq="D")
    assert df.index.equals(expected), "BTC calendar has gaps; run python -m pipeline.check_data"
    return df


def model_forecasts(df, horizon, scores, scores_4y):
    """P(up) of every model for one horizon, one column per model."""
    close = df["close"]
    sma200 = close.rolling(200, min_periods=200).mean()
    ma_state = (close > sma200).astype(float).where(sma200.notna())
    grouped = {
        "cycle": model.bucket(scores["score"]),
        "ma200": ma_state,
        "valuationOnly": model.bucket(scores["valuation"]),
        "trendOnly": model.bucket(scores["trend"]),
        "cycle-w4y": model.bucket(scores_4y["score"]),
    }
    out = {key: model.group_forecast(g, close, horizon)["pUp"] for key, g in grouped.items()}
    out["baseRate"] = model.group_forecast(np.zeros(len(close)), close, horizon)["baseRate"]
    out["coinFlip"] = pd.Series(0.5, index=close.index)
    return pd.DataFrame(out)[list(MODEL_NAMES)]


def block_bootstrap_means(series_list, block, resamples=BOOT_RESAMPLES, seed=BOOT_SEED):
    """Circular block bootstrap. Every series is resampled with the same indices, so paired
    statistics stay paired. Returns an array of shape (resamples, len(series_list))."""
    n = len(series_list[0])
    data = np.vstack(series_list)                     # (k, n)
    rng = np.random.default_rng(seed)
    blocks = -(-n // block)
    out = np.empty((resamples, len(series_list)))
    for start in range(0, resamples, 250):
        b = min(250, resamples - start)
        starts = rng.integers(0, n, size=(b, blocks))
        idx = ((starts[:, :, None] + np.arange(block)) % n).reshape(b, -1)[:, :n]
        out[start:start + b] = data[:, idx].mean(axis=2).T
    return out


def evaluate(df, preds, horizon, start):
    close = df["close"]
    up = pd.Series(model.outcomes(close, horizon), index=close.index)
    ret = close.shift(-horizon) / close - 1
    mask = (close.index >= start) & up.notna() & preds.notna().all(axis=1)
    p, y, r = preds[mask], up[mask].to_numpy(), ret[mask].to_numpy()
    n = int(mask.sum())

    keys = list(p)
    brier = {k: (p[k].to_numpy() - y) ** 2 for k in keys}
    # One shared resample for all models keeps every comparison paired. A mean of differences
    # is the difference of means, so per-model means are all that's needed.
    boot = dict(zip(keys, block_bootstrap_means([brier[k] for k in keys], horizon).T))
    base_brier = brier["baseRate"].mean()
    rows = []
    for key in keys:
        pk = p[key].to_numpy()
        hit = np.where(pk > 0.5, y == 1, np.where(pk < 0.5, y == 0, 0.5)).astype(float).mean()
        ups, downs = r[pk > 0.5], r[pk < 0.5]
        lo, hi = np.percentile(1 - boot[key] / boot["baseRate"], CI)
        row = {
            "key": key, "name": MODEL_NAMES[key],
            "brier": float(brier[key].mean()),
            "brierSkill": float(1 - brier[key].mean() / base_brier),
            "brierSkillCI": [float(lo), float(hi)],
            "hitRate": float(hit),
            "returnSpread": float(ups.mean() - downs.mean()) if len(ups) and len(downs) else None,
            "upCalls": float((pk > 0.5).mean()),
        }
        for ref in REFERENCES:
            if key != ref:
                lo, hi = np.percentile(boot[key] - boot[ref], CI)
                row[f"diff_{ref}"] = {"mean": float(brier[key].mean() - brier[ref].mean()),
                                      "lo": float(lo), "hi": float(hi)}
        rows.append(row)

    bins = np.minimum((p["cycle"].to_numpy() * 10).astype(int), 9)
    calibration = []
    for b in range(10):
        sel = bins == b
        if sel.any():
            calibration.append({"bin": f"{b / 10:.1f}-{(b + 1) / 10:.1f}",
                                "meanP": float(p["cycle"][sel].mean()),
                                "observed": float(y[sel].mean()), "n": int(sel.sum())})

    return {
        "from": f"{p.index[0]:%Y-%m-%d}", "to": f"{p.index[-1]:%Y-%m-%d}", "n": n,
        "effectiveWindows": round(n / horizon, 1),
        "upRate": float(y.mean()),
        "models": rows, "calibration": calibration,
    }


def verdict(result):
    cycle = next(m for m in result["models"] if m["key"] == "cycle")
    checks = {ref: cycle[f"diff_{ref}"]["hi"] < 0 for ref in REFERENCES}
    return {"pass": all(checks.values()), "checks": checks}


def run():
    df = load_btc()
    scores = model.cycle_scores(df)
    scores_4y = model.cycle_scores(df, window=model.WINDOW_4Y)
    results = {}
    for horizon in model.HORIZONS:
        preds = model_forecasts(df, horizon, scores, scores_4y)
        for window, start in WINDOWS.items():
            results[f"{window}/{horizon}"] = evaluate(df, preds, horizon, start)
    primary = results[f"{PRIMARY[0]}/{PRIMARY[1]}"]
    return {"asset": "BTC", "method": "v1", "dataEnd": f"{END:%Y-%m-%d}",
            "scoreStarts": f"{scores['score'].first_valid_index():%Y-%m-%d}",
            "primary": {"window": PRIMARY[0], "horizon": PRIMARY[1], **verdict(primary)},
            "results": results}


# ---------------------------------------------------------------- report

def _pct(x, signed=False):
    return "—" if x is None else (f"{x:+.1%}" if signed else f"{x:.1%}")


def _diff(d):
    if d is None:
        return "—"
    mark = " ✓" if d["hi"] < 0 else ""
    return f"{d['mean']:+.4f} [{d['lo']:+.4f}, {d['hi']:+.4f}]{mark}"


def report(out):
    p = out["primary"]
    lines = [
        "# BTC backtest, method v1",
        "",
        f"Generated by `python -m pipeline.backtest` from `data/raw/BTC.csv` through {out['dataEnd']}, "
        "following [`method-v1.md`](method-v1.md) (tag `method-v1`). "
        f"The cycle score exists from {out['scoreStarts']}.",
        "",
        "## Primary test",
        "",
        f"BTC, {p['horizon']}-day horizon, {p['window']} window. Passes only if the cycle score's Brier is "
        "lower than both the base rate and the 200-day rule, with the 90% interval of each "
        "difference entirely below zero.",
        "",
        f"- vs base rate: {'below zero ✓' if p['checks']['baseRate'] else 'not below zero ✗'}",
        f"- vs 200-day rule: {'below zero ✓' if p['checks']['ma200'] else 'not below zero ✗'}",
        "",
        f"**Result: {'PASS' if p['pass'] else 'FAIL'}**",
        "",
        "## All results",
        "",
        "Δ Brier is model − reference, mean [90% block-bootstrap interval]; negative is better, "
        "✓ means the whole interval is below zero. Brier skill is relative to the base rate. "
        "Effective windows = test days ÷ horizon.",
    ]
    for key, r in out["results"].items():
        window, horizon = key.split("/")
        label = "Full window" if window == "full" else "Post-publication window"
        lines += [
            "",
            f"### {horizon} days · {label} ({r['from']} → {r['to']})",
            "",
            f"{r['n']:,} test days · {r['effectiveWindows']} effective windows · "
            f"price was higher after {horizon} days on {_pct(r['upRate'])} of them",
            "",
            "| Model | Brier | Brier skill [90%] | Hit rate | Up calls | Return spread | Δ Brier vs base rate | Δ Brier vs 200-day |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for m in r["models"]:
            skill = "—" if m["key"] == "baseRate" else (
                f"{m['brierSkill']:+.1%} [{m['brierSkillCI'][0]:+.1%}, {m['brierSkillCI'][1]:+.1%}]")
            lines.append(
                f"| {m['name']} | {m['brier']:.4f} | {skill} | {_pct(m['hitRate'])} | "
                f"{_pct(m['upCalls'])} | {_pct(m['returnSpread'], signed=True)} | "
                f"{_diff(m.get('diff_baseRate'))} | {_diff(m.get('diff_ma200'))} |")
        if window == "full":
            lines += ["", "Calibration of the cycle score:", "",
                      "| P(up) bin | Mean P | Observed | Days |", "|---|---:|---:|---:|"]
            lines += [f"| {c['bin']} | {c['meanP']:.2f} | {c['observed']:.2f} | {c['n']:,} |"
                      for c in r["calibration"]]
    return "\n".join(lines) + "\n"


def main():
    out = run()
    results_dir = ROOT / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "btc_v1.json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    (ROOT / "docs" / "results-btc-v1.md").write_text(report(out))
    p = out["primary"]
    print(f"Primary test (BTC, {p['horizon']} days, {p['window']}): {'PASS' if p['pass'] else 'FAIL'}")
    print("Wrote docs/results-btc-v1.md and data/results/btc_v1.json")


if __name__ == "__main__":
    main()
