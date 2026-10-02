# Data contract

The pipeline (Data & Model) writes these files. The dashboard (Web & Ops) only reads them.
If either side needs a change, update this file **in the same PR** and tag the other person.

All files live in `web/data/`. Dates are `YYYY-MM-DD` (UTC). Missing values are `null`.
Probabilities are 0–1. Scores are 0–100. Returns are fractions (`0.18` = +18%).

Until the pipeline is ready, the dashboard uses hand-made copies in `web/data/sample/`.

---

## `summary.json` — one row per coin, for the home view

```json
{
  "generatedAt": "2026-10-03T06:00:00Z",
  "disclaimer": "Not financial advice. Past cycles do not guarantee future results.",
  "fearGreed": { "value": 72, "label": "Greed" },
  "coins": [
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "date": "2026-10-02",
      "price": 86440.12,
      "score": 58.1,
      "regime": "Early Expansion",
      "valuation": 45.4,
      "trend": 70.9,
      "delta1d": 1.1,
      "delta7d": -2.4,
      "disagreement": true,
      "predictions": {
        "30":  { "pUp": 0.61, "baseRate": 0.58, "samples": 1240, "medianReturn": 0.05, "confidence": "High" },
        "90":  { "pUp": 0.64, "baseRate": 0.62, "samples": 1180, "medianReturn": 0.18, "confidence": "High" },
        "365": { "pUp": 0.71, "baseRate": 0.70, "samples": 950,  "medianReturn": 0.62, "confidence": "Medium" }
      }
    }
  ]
}
```

`regime` is one of: `Capitulation` (0–20), `Accumulation` (20–40), `Early Expansion` (40–60), `Mid Bull` (60–80), `Euphoria` (80–100).
`confidence` is `High` (≥ 500 samples), `Medium` (≥ 150) or `Low`.
`disagreement` is `true` when valuation and trend differ by more than 25 points.

## `coin_<SYMBOL>.json` — full detail for one coin (e.g. `coin_BTC.json`)

```json
{
  "symbol": "BTC",
  "name": "Bitcoin",
  "firstDate": "2010-07-17",
  "lastDate": "2026-10-02",
  "indicators": [
    { "key": "mayer", "name": "Mayer Multiple", "group": "valuation",
      "raw": 1.12, "unit": "×", "score": 52.3,
      "detail": "Price is 12% above its 200-day average" }
  ],
  "timeline": {
    "dates":     ["2010-07-17", "..."],
    "close":     [0.05, "..."],
    "score":     [null, "..."],
    "valuation": [null, "..."],
    "trend":     [null, "..."],
    "pUp30":     [null, "..."],
    "pUp90":     [null, "..."],
    "pUp365":    [null, "..."]
  },
  "backtest": {
    "90": {
      "from": "2013-01-01", "to": "2026-07-04", "n": 4933,
      "models": [
        { "key": "cycle",    "name": "Cycle score",          "hitRate": 0.66, "brier": 0.212, "brierSkill": 0.04 },
        { "key": "baseRate", "name": "Always up (base rate)", "hitRate": 0.63, "brier": 0.221, "brierSkill": 0.0 },
        { "key": "ma200",    "name": "200-day rule",          "hitRate": 0.64, "brier": 0.218, "brierSkill": 0.01 },
        { "key": "coinFlip", "name": "Coin flip",             "hitRate": 0.50, "brier": 0.250, "brierSkill": -0.13 }
      ],
      "calibration": [ { "bin": "0.6-0.7", "meanP": 0.65, "observed": 0.67, "n": 812 } ],
      "returnSpread": 0.21
    }
  },
  "buckets": [
    { "bucket": "50-60", "days": 1240,
      "upRate":       { "30": 0.61, "90": 0.64, "365": 0.71 },
      "medianReturn": { "30": 0.05, "90": 0.18, "365": 0.62 } }
  ]
}
```

All arrays in `timeline` have the same length as `dates`. `backtest` has keys `"30"`, `"90"`, `"365"`.

## `predictions_log.json` — the live track record (append-only)

```json
{
  "entries": [
    {
      "id": "BTC-90-2026-10-02",
      "coin": "BTC",
      "madeOn": "2026-10-02",
      "horizon": 90,
      "targetDate": "2026-12-31",
      "score": 58.1,
      "regime": "Early Expansion",
      "pUp": 0.64,
      "baseRate": 0.62,
      "priceAtPrediction": 86440.12,
      "status": "pending",
      "outcomePrice": null,
      "wentUp": null,
      "correct": null,
      "resolvedOn": null
    }
  ]
}
```

Rules: entries are **never edited or deleted**, except that the pipeline fills in the
`outcome*`, `wentUp`, `correct`, `resolvedOn` fields and sets `status` to `"resolved"`
once `targetDate` has passed. `correct` = (`pUp` > 0.5) == `wentUp`.
