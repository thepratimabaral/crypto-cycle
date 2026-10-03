# Method v1 (pre-registered)

**Frozen on 2026-10-03, before any forecast was scored.** This file fixes every formula,
parameter and success criterion for the v1 cycle score. It is committed and tagged
`method-v1` before the backtest code exists, so the result can't shape the method.

Rules for this file:

- Nothing below changes after results are seen. A fix to the method is **v2**, with its own
  file, tag and evaluation; v1's results stay published as they are.
- A clarification made *before* results are seen goes in **Amendments** at the bottom, dated.
- A bug fix in code that implements this file is not a method change. It is noted in the
  results.

## 1. Data

- Asset under test: **BTC only**. The six alts are logged live (section 8) but not evaluated in v1.
- Source: `data/raw/BTC.csv` as committed in `4158353` (blockchain.info: `close`, `hashrate`,
  `miners_revenue`), from 2010-08-18 to **2026-10-01**. The backtest truncates at
  2026-10-01, so later refreshes of the file can't change it.
- The calendar is daily with no gaps (checked by `pipeline/check_data.py`).

## 2. Indicators

`sma(x, n)` is the trailing n-day mean, null until n values exist.

| Key | Group | Raw value |
|---|---|---|
| `mayer` | valuation | close ÷ sma(close, 200) |
| `wma200` | valuation | close ÷ sma(close, 1400) |
| `athDistance` | valuation | close ÷ running max of close |
| `puell` | valuation | miners_revenue ÷ sma(miners_revenue, 365) |
| `goldenCross` | trend | sma(close, 50) ÷ sma(close, 200) − 1 |
| `momentum90` | trend | close ÷ close 90 days earlier − 1 |
| `rsi30` | trend | Wilder RSI, period 30: EWM of gains and losses with α = 1/30, not adjusted, at least 30 values; 100 − 100 ÷ (1 + gain ÷ loss) |
| `hashRibbons` | trend | sma(hashrate, 30) ÷ sma(hashrate, 60) − 1 |

## 3. Scoring

**Indicator score** on day *t*, for raw value *x* with prior non-null values *x₁…xₘ* (days before *t*):

```
score = 100 × (count(xᵢ < x) + 0.5 × count(xᵢ = x)) ÷ m        null if m < 365
```

0 means below every earlier reading and 100 means above every earlier reading. Only earlier
days are used.

```
valuation = mean of the non-null valuation indicator scores   (null if fewer than 2)
trend     = mean of the non-null trend indicator scores       (null if fewer than 2)
score     = (valuation + trend) ÷ 2                            (null if either is null)
```

Regimes, with the lower bound inclusive: Capitulation < 20 ≤ Accumulation < 40 ≤ Early Expansion < 60 ≤
Mid Bull < 80 ≤ Euphoria.

**Variant `cycle-w4y`** (secondary, decided now): the same, except the prior values are only the
last 1,460 non-null values (about 4 years). It tests whether scoring against recent history
handles BTC's shrinking cycle peaks better. It's the only variant; no others will be tried in v1.

## 4. Forecast

For horizon *N* ∈ {30, 90, 365}, the outcome of day *s* is `up(s) = close(s+N) > close(s)`.
It becomes **known** on day *s + N*.

On day *t*:

```
baseRate(t) = share of up outcomes among all days s with s + N ≤ t (whole history, any score)
bucket(d)   = min(floor(score(d) ÷ 10), 9)
n, ups      = count and up-count of days s with s + N ≤ t and bucket(s) = bucket(t)
P(up)       = (ups + 20 × baseRate) ÷ (n + 20)
```

No score on day *t* → no forecast.

## 5. Models compared

| Key | P(up) on day *t* |
|---|---|
| `cycle` | Section 4 on the composite score (**the model under test**) |
| `baseRate` | baseRate(t), meaning "always up" at today's known rate |
| `ma200` | Section 4, with the bucket replaced by the state close > sma(close, 200) (2 groups) |
| `coinFlip` | 0.5 |
| `valuationOnly` | Section 4 on the valuation score instead of the composite |
| `trendOnly` | Section 4 on the trend score instead of the composite |
| `cycle-w4y` | Section 4 on the `cycle-w4y` score |

## 6. Evaluation

**Test days:** every day *t* from **2013-01-01** to 2026-10-01 − N on which every model has a
forecast. All models are scored on the same days.

**Windows:**
- **Full:** from 2013-01-01.
- **Post-publication:** from 2019-01-01. By 2019 the Mayer Multiple (2017), Puell Multiple,
  Hash Ribbons and the 200-week MA (2019) were all public. Forecasts in this window were made
  with indicators nobody chose by looking at these days.

**Metrics** per model:
- Brier = mean (P − up)².
- Brier skill = 1 − Brier ÷ Brier(baseRate).
- Hit rate: a call is "up" if P > 0.5, "down" if P < 0.5, and P = 0.5 scores 0.5.
- Return spread: mean N-day return after up calls minus mean after down calls.
- Calibration (cycle only): 10 bins of P.

**Uncertainty:** circular block bootstrap of the daily paired Brier difference (model −
reference). Block length = *N* days, 5,000 resamples, seed `20261003`, 90% percentile
interval. **Effective windows** = test days ÷ *N*; this is reported next to every result.

## 7. Success criterion (decides the gate)

**Primary test:** BTC, N = 90, full window.

> The cycle score **passes** if its Brier score is lower than both `baseRate` and `ma200`, and
> for **both** comparisons the 90% bootstrap interval of the mean Brier difference lies
> entirely below zero.

Either way, the result is published as computed.

- **Pass** → build the dashboard as planned: BTC is the main product, alts are labelled
  experimental.
- **Fail** → v1 does not ship as a forecast. The site becomes a public scorecard of the
  indicators and baselines.

Everything else (30 and 365 days, the post-publication window, `cycle-w4y`, `valuationOnly`,
`trendOnly`, hit rates, calibration) is **secondary**. It is reported but cannot turn a fail
into a pass. A good secondary result is a reason to pre-register a v2, not to ship v1.

Expected power, stated in advance: about 55 effective windows at 90 days, 165 at 30 days and
13 at 365 days. The 365-day results are close to anecdotal.

## 8. Live log

From 2026-10-03, a daily run appends the v1 forecast for all 7 coins and 3 horizons to
`web/data/predictions_log.json` (format: `docs/data-contract.md`, plus `"method": "v1"`).
Entries are never edited. A pending entry is resolved once a close exists for its target date.
The log, unlike the backtest, is a genuine out-of-sample test of every coin.

## 9. Known limitations (accepted for v1)

- The indicator choice is informed by BTC history; the post-publication window only partly
  corrects for that.
- Overlapping windows: consecutive days are not independent (handled by the block bootstrap).
- BTC cycle peaks have shrunk over time, so all-history percentiles may under-score later
  tops (tested by `cycle-w4y`).
- Today's top coins are survivors; that's why alts are not evaluated from their backtests.

## Amendments

None.
