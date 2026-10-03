---
name: cycle-model
description: The Crypto Cycle model in pipeline/model.py and pipeline/run.py. The 8 indicators, expanding-percentile scoring, valuation/trend/composite score and regimes, the bucket P(up) forecast for 30/90/365 days, the walk-forward backtest, baselines and metrics, the prediction log, and the no-lookahead tests. Use when writing or changing indicators, scoring, forecasting, backtest or export code, or tests/test_model.py and tests/test_log.py. Triggers on "indicator", "Mayer", "200-week", "Puell", "hash ribbons", "RSI", "golden cross", "percentile", "cycle score", "regime", "P(up)", "bucket", "base rate", "backtest", "walk-forward", "Brier", "calibration", "baseline", "lookahead", "prediction log".
---

# Cycle model

The method is **frozen** in `docs/method-v1.md` (tag `method-v1`) and implemented in
`pipeline/model.py` and `pipeline/backtest.py`. v1 **failed** its pre-registered test: it is
worse than "always up" and the 200-day rule (`docs/results.md`). So:

- Never change v1's formulas or parameters, or tune anything, to improve a result. A code
  bug may be fixed; say so in `docs/results.md`.
- A new idea is a new pre-registered version (`docs/method-v2.md`, its own tag), written down
  before it is run. The backtest history has been seen, so a v2's real test is the live log.
- The score may be shown as a description of the cycle, never as a forecast.

This skill restates the method so new code matches it.

Input: `load_coin(symbol, pair)` from `pipeline/fetch.py`, a daily `DataFrame` indexed by
date with `close` (all coins), `hashrate` and `miners_revenue` (BTC only), `volume` (others).
The calendar has no gaps (`check_data` guarantees it).

## The one rule: no lookahead

Every value on day *t* uses only rows ≤ *t*. Concretely:

- `rolling(n).mean()`, `cummax()`, `shift(+k)` are fine. They look backwards.
- `rank(pct=True)` over the whole series, `quantile()` over the whole series, centred windows,
  `bfill()`, and normalising by the full-series min/max are **lookahead**. Don't use them.
- `shift(-N)` is allowed **only** to build the outcome label (`close` N days later). A label
  for day *s* becomes known on day *s + N*. When forecasting on day *t*, use only days *s*
  with *s + N ≤ t*.
- The base rate used on day *t* is also computed from known outcomes only.

The test that proves it (`tests/test_model.py`): pick several cutoff dates, run the model on
`df[df.index <= cutoff]`, and assert the cutoff row equals the same row from the full run
(score, valuation, trend, every indicator score, pUp30/90/365). Run it for BTC and for one
short coin (SOL). Any mismatch is a lookahead bug.

## Indicators

| Key | Group | Raw value | Coins | Window needed |
|---|---|---|---|---|
| `mayer` | valuation | close ÷ 200-day mean | all | 200 |
| `wma200` | valuation | close ÷ 1,400-day mean | all | 1,400 |
| `athDistance` | valuation | close ÷ running max close | all | 1 |
| `puell` | valuation | miners_revenue ÷ its 365-day mean | BTC | 365 |
| `goldenCross` | trend | 50-day mean ÷ 200-day mean − 1 | all | 200 |
| `momentum90` | trend | close ÷ close 90 days ago − 1 | all | 90 |
| `rsi30` | trend | 30-day RSI, 0–100 | all | 30 |
| `hashRibbons` | trend | 30-day mean hashrate ÷ 60-day mean − 1 | BTC | 60 |

Fear & Greed (`fetch.fear_greed()`) is shown on the dashboard only. It is never in the score:
its history starts in 2018.

Keys and display names go into `coin_*.json` → `indicators[]` with `raw`, `unit`, `score` and
a plain-English `detail` ("Price is 12% above its 200-day average"). Keep keys stable once the
web track uses them.

## Scoring

```
indicator score = expanding percentile of today's raw value among all raw values up to and
                  including today, 0 = lowest so far, 100 = highest so far.
                  null until that indicator has 365 non-null values.
valuation       = mean of available valuation indicator scores (null if fewer than 2)
trend           = mean of available trend indicator scores     (null if fewer than 2)
score           = (valuation + trend) / 2                       (null if either is null)
disagreement    = |valuation − trend| > 25
```

A workable percentile: `(count of past values < x + 0.5 × count equal to x, excluding today) ÷
(count of past values) × 100`, or any definition that maps the lowest-so-far to 0 and the
highest-so-far to 100. Pick one, write it in a docstring, and keep it. At ~6,000 rows a
straightforward loop with `bisect.insort` on a sorted list is fast enough; don't reach for
something clever.

Regimes (lower bound inclusive): `Capitulation` 0–20, `Accumulation` 20–40,
`Early Expansion` 40–60, `Mid Bull` 60–80, `Euphoria` 80–100.

Expected gaps: SOL has a 200-week value only from mid-2024 and DOGE from 2023, so their
valuation uses the remaining indicators until then. BTC scores start around 2011.

## Forecast: P(up) for N = 30, 90, 365

On day *t*, for each horizon N:

1. Bucket today's score into 10-point bins (58 → `50-60`; 100 goes in `90-100`).
2. Take past days *s* in the same bucket with *s + N ≤ t* (outcome known).
3. `ups` = how many had `close[s+N] > close[s]`; `n` = how many there were.
4. `baseRate` = up-rate over **all** known past days, any bucket.
5. `pUp = (ups + 20 × baseRate) / (n + 20)`.
6. `samples = n`; `confidence` = `High` if n ≥ 500, `Medium` if n ≥ 150, else `Low`.
7. `medianReturn` = median of `close[s+N] / close[s] − 1` over those same days.

No score → no prediction (`null`). Do not add ML or extra parameters in v1; anything fancier
must beat this model in the same backtest first.

## Backtest

Walk-forward: compute P(up) for every past day exactly as above (it is already causal), then
score it against the realised outcome. Test days start once the score exists and there is at
least some history in the buckets; record `from`, `to`, `n` per horizon.

Models to report (keys in `backtest[N].models[]`):

| Key | Prediction on day *t* |
|---|---|
| `cycle` | The bucket P(up) above |
| `baseRate` | Known up-rate so far ("always up" when > 0.5) |
| `ma200` | Up if close > 200-day mean. As a probability, use the known up-rate on past days with the same above/below state |
| `coinFlip` | 0.5 |
| `valuationOnly`, `trendOnly` | Same bucket method on the valuation or trend score alone |

`valuationOnly` and `trendOnly` keys are not in the contract example yet. Add them to
`docs/data-contract.md` when they land.

Metrics per model:

- `hitRate`: share of days where `(p > 0.5) == wentUp`. Treat p = 0.5 as "down" consistently.
- `brier`: mean of `(p − wentUp)²`. 0.25 is a coin flip.
- `brierSkill`: `1 − brier / brier_baseRate`. Above 0 means it beats "always up".
- `calibration` (cycle model): 10 bins of p, with `meanP`, `observed` up-rate and `n`.
- `returnSpread`: mean N-day return after "up" calls minus after "down" calls.

`buckets[]`: for each 10-point score bucket, `days`, and per horizon the `upRate` and
`medianReturn`, over all days with a known outcome.

Overlap caveat: consecutive days share most of their future window, so 4,000 test days of
365-day predictions are about 11 independent years. Say this next to the results; don't
present the sample count as if the days were independent.

If `cycle` doesn't beat `baseRate`, report that. Don't retune bucket width, shrinkage or
indicator choices against the backtest to make it win; that's fitting to the test set.

## Prediction log (`web/data/predictions_log.json`)

Each daily run, for each coin and horizon with a non-null prediction, append one entry with
`id = f"{coin}-{horizon}-{madeOn}"`. If that id exists already, skip it (re-running the same
day must not duplicate or overwrite). Then, for every `pending` entry whose `targetDate` has
a close, fill `outcomePrice`, `wentUp`, `correct = (pUp > 0.5) == wentUp`, `resolvedOn`, and set
`status = "resolved"`. Nothing else is ever changed or removed.

`tests/test_log.py`: run the log update twice on the same day and on a later day; assert old
entries' prediction fields are byte-identical and only the resolution fields changed.

## Export

Write with `json.dump(..., allow_nan=False)` after converting `NaN` to `None`, so a stray NaN
fails loudly instead of producing invalid JSON. Round floats (prices to the coin's precision,
scores to 1 dp, probabilities to 3 dp) to keep `coin_*.json` small. All `timeline` arrays must
have the same length as `dates`. Check the shapes against `docs/data-contract.md` before
committing.
