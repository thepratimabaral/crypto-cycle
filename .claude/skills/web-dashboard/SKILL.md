---
name: web-dashboard
description: The Crypto Cycle website in web/, a static HTML/CSS/JS dashboard that reads web/data/*.json, plus its hosting on GitHub Pages and the daily GitHub Actions workflow. Use when building or changing a dashboard section, chart, sample data file, the way the site reads the data contract, the deploy, or .github/workflows/daily.yml. Triggers on "dashboard", "web/index.html", "chart", "Lightweight Charts", "log scale", "forecast card", "track record", "calibration chart", "live log", "sample data", "GitHub Pages", "daily workflow", "cron", "mobile".
---

# Web dashboard

Plain HTML, CSS and JavaScript in `web/`. No framework, no bundler, no build step: the
files in `web/` are exactly what gets hosted. The site only reads JSON; it never computes a
score or a probability itself.

## Files

```
web/
├── index.html                 the dashboard (CSS and JS inline or in web/*.css, web/*.js)
└── data/
    ├── summary.json           all coins, current state         (written by the pipeline)
    ├── coin_<SYMBOL>.json     full timeline, indicators, backtest, buckets
    ├── predictions_log.json   live, append-only track record
    └── sample/                hand-made copies with the same shape, used until M2
```

Serve locally with `python3 -m http.server -d web 8000`. Opening `index.html` from disk
fails because `fetch()` doesn't work over `file://`.

## Reading the data

`docs/data-contract.md` is the only spec. Read field names from it, not from memory. If you
need a field that isn't there, the change goes into the contract first and the data track
owner agrees it.

- Keep the data location in one constant (`const DATA = "data/"` vs `"data/sample/"`) so the
  M2 switch from sample to real data is a one-line change.
- Load `summary.json` first for the home view; load `coin_<SYMBOL>.json` lazily when a tab
  opens. BTC's file is the largest (~16 years of daily arrays).
- `null` is normal (early history, short-history coins, unresolved log entries). Render it as
  "—" or leave a chart gap; never as 0 and never as `NaN%`.
- Formats: probabilities 0–1 → show as `64%`; returns are fractions → `+18%`; scores 0–100
  with one decimal at most; dates are UTC `YYYY-MM-DD`.
- Show `samples` and `confidence` next to every forecast. Low-confidence forecasts (SOL,
  DOGE) must look less certain, not identical to BTC's.

## Sections (from blueprint.html §09)

| Section | Data |
|---|---|
| Coin tabs | BTC · ETH · BNB · SOL · XRP · ADA · DOGE (`summary.coins[]`) |
| Today | score, regime, valuation vs trend, delta1d/7d, `disagreement` flag, Fear & Greed |
| Forecast cards | `predictions["30"/"90"/"365"]`: pUp vs baseRate, samples, medianReturn, confidence |
| History chart | `timeline.close` on a **log** price scale; `timeline.score` in a pane below on the same time axis |
| Indicators | `indicators[]`: name, raw + unit, 0–100 score, `detail` sentence |
| Track record | `backtest[N].models[]` table, `calibration` chart (diagonal = perfect), `buckets[]` table |
| Live log | `predictions_log.entries` for the coin: pending / ✓ / ✗, running hit rate on resolved entries |

The disclaimer (`summary.disclaimer`) appears on every view. If the cycle model doesn't beat
the baselines, the track record shows that plainly; never hide or soften a losing row.

Regime colour order runs Capitulation → Accumulation → Early Expansion → Mid Bull → Euphoria;
keep the same colours everywhere the regime appears (badge, score pane bands, log entries).

## Charts

TradingView Lightweight Charts, loaded from a pinned CDN version (e.g. unpkg with an exact
version number, never `@latest`). Use it for price and score. Small tables and the
calibration plot can be plain HTML or inline SVG; don't add a second charting library for one
chart.

- Price: `priceScaleId` with `mode: LogarithmicMode`. Early BTC is $0.07; linear scale is useless.
- Score pane: fixed 0–100 range with faint regime bands at 20/40/60/80.
- Convert `dates[]` + value arrays to `{time, value}` and drop `null` points for line series.

## Responsive

Must work at phone width (M6 includes mobile QA): single column under ~640px, tabs scroll
horizontally rather than wrap into several rows, charts resize with the container
(`ResizeObserver` → `chart.resize`), tables scroll inside their own box, not the page.

## Daily workflow (`.github/workflows/daily.yml`, M4)

- `schedule` cron once a day after 00:00 UTC (e.g. `15 1 * * *`) plus `workflow_dispatch`.
- `actions/setup-python` with a pinned version, `pip install -r requirements.txt`,
  `python -m pipeline.run`.
- Commit `data/raw/` and `web/data/` back to `main` only if they changed, with a
  `data: daily update YYYY-MM-DD` message. Needs `permissions: contents: write`.
- The committed log is the tamper-evident record, so the workflow must never rewrite history.
- No secrets are needed; all data sources are keyless.

## Hosting (M6)

GitHub Pages serving the `web/` folder (Pages action uploading `web/` as the artifact). The
site is static, so every page works from relative paths; don't hard-code the domain.
Deploying needs the repo owner's approval; ask before enabling Pages or changing repo settings.
