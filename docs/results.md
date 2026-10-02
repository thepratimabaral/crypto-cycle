# Results

## Phase A: BTC backtest of method v1 (2026-10-03)

**Result: FAIL.** The v1 cycle score does not forecast BTC better than the baselines. It does
worse.

The method, the parameters and this pass/fail test were committed and tagged `method-v1`
(`8103d8f`) before the backtest code was written. The code was committed (`efea6d8`) before
it was run, and it was run once. Full tables: [`results-btc-v1.md`](results-btc-v1.md). Raw
numbers: `data/results/btc_v1.json`.

### Primary test: BTC, 90 days, 2013-01-01 → 2026-07-03 (55 effective windows)

| Model | Brier (lower is better) | Δ vs cycle score [90% interval] |
|---|---:|---|
| Cycle score | 0.2798 | — |
| Always up (base rate) | 0.2578 | cycle is worse by 0.022 [0.004, 0.040] |
| 200-day rule | 0.2508 | cycle is worse by 0.029 [0.011, 0.049] |
| Coin flip | 0.2500 | |

Passing needed both intervals entirely **below** zero. Both are entirely **above** zero: the
cycle score is reliably worse than either baseline, and worse than a coin flip.

### Secondary results (reported, cannot change the verdict)

- **Every horizon and window fails.** Brier skill against the base rate is negative at 30, 90
  and 365 days, in the full window and in the post-publication window (from 2019).
- **Neither half works alone.** Valuation-only and trend-only are both worse than the base rate.
- **The 4-year window doesn't fix it.** `cycle-w4y` is slightly less bad but still clearly
  worse than the base rate everywhere.
- **Nothing beats "always up" reliably.** The 200-day rule has +2.7% skill at 90 days, but its
  interval (−4.1% to +9.1%) includes zero.

### Why it fails

The forecasts are badly calibrated, and in the wrong direction. At 90 days, days given
P(up) below 0.4 went up 71–84% of the time; days given above 0.9 went up 55% of the time. The most
confident "down" forecasts fall in early 2015 and early 2019, which were the cycle
bottoms. The bucket method learns "after a low score, price kept falling" from the
*previous* bear market, then says it again at the turn. With three or four cycles to learn
from, each new cycle mostly contradicts the last one.

The score is still a reasonable **description** of the cycle. It read 89 at the 2013 top,
91 at the 2017 top, 9 at the 2015 bottom and 4 at the 2018 bottom. But describing where
you are compared with history is not the same as forecasting what happens next. The 2021
top read only 70 ("Mid Bull"), as expected from BTC's shrinking peaks.

The code was checked after the run: the forecasts match a separate brute-force version
exactly, and the no-lookahead tests pass. No code changes were made after seeing results.

### What this means (per section 7 of the method)

- v1 does **not** ship as a forecast. No P(up) is shown as advice or as "the chance it goes up".
- The site becomes a **public scorecard**: the cycle score as a description, every indicator
  and baseline, these backtest results, and the live log, shown as they are.
- Any v2 needs its own pre-registration. Because this history has now been seen, a v2 can't
  be proven on the same backtest; its real test is the live log, going forward.

## Live log

Started 2026-10-02 (UTC): 21 v1 forecasts (7 coins × 3 horizons) made from the
2026-10-01 close, in `web/data/predictions_log.json`. The first 30-day entries resolve on
2026-10-31. It keeps running even though v1 failed: it is the only out-of-sample record,
and it is the scorecard's evidence going forward.
