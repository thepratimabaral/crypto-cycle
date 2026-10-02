# Version 1 build plan

**Scope:** full price history, cycle score, 30/90/365-day forecasts, walk-forward backtest against
baselines, live prediction log, and a public dashboard for BTC, ETH, BNB, SOL, XRP, ADA and DOGE.

| Track | Owns | Paths |
|---|---|---|
| **Data** | Ingestion, indicators, scoring, forecasting, backtest, prediction log | `pipeline/` `tests/` `docs/data-*` |
| **Web** | Dashboard, charts, repository, CI/CD, hosting | `web/` `.github/` |
| **Joint** | Kickoff, validation, release | — |

The tracks share one interface: [`data-contract.md`](data-contract.md).

---

## M0 · Kickoff (Joint)
- [ ] Create repository, push initial commit, add collaborator
- [ ] Protect `main`, create labels and project board
- [ ] Review and approve data contract — `docs/data-contract.md`

**Exit gate:** Both owners have cloned the repo; data contract approved.

## M1 · Foundations
**Handoff:** Web builds against sample data until M2.

| Data | Web |
|---|---|
| Python environment — `requirements.txt` | Issues for every v1 task |
| Data validation, 7 assets — `pipeline/check_data.py` | Sample data — `web/data/sample/*.json` |
| Coverage and anomalies — `docs/data-notes.md` | App shell: layout, tabs, price chart — `web/index.html` |

**Exit gate:** Both PRs merged; dashboard renders sample data.

## M2 · Cycle score
**Handoff:** Data → Web: `summary.json`, `coin_*.json`.

| Data | Web |
|---|---|
| 8 indicators — `pipeline/model.py` | Current-state panel |
| Expanding-percentile scoring + no-lookahead test — `tests/test_model.py` | Indicator table |
| Composite, regimes, JSON export — `pipeline/run.py` | History chart: log price + score pane |
| | Switch from sample to pipeline output |

**Exit gate:** Real scores and full history for all 7 assets.

## M3 · Forecast & backtest
**Handoff:** Data → Web: predictions, backtest, buckets in `coin_*.json`.

| Data | Web |
|---|---|
| Walk-forward P(up), 30/90/365 days | Forecast cards |
| Baselines: coin flip, base rate, 200-DMA, valuation-only, trend-only | Model vs baseline table |
| Hit rate, Brier, skill, calibration, bucket table | Calibration chart and bucket table |

**Exit gate:** Backtest visible for all assets at all horizons.

## M4 · Live tracking
**Handoff:** Data → Web: `predictions_log.json`.

| Data | Web |
|---|---|
| Append-only prediction log with resolver | Prediction log view with running hit rate |
| Immutability test — `tests/test_log.py` | Daily workflow — `.github/workflows/daily.yml` |

**Exit gate:** Scheduled workflow green; first log entries committed.

## M5 · Validation (Joint)
- [ ] Results review across assets and horizons — `docs/results.md`
- [ ] Manual spot-check: 3 dates per asset
- [ ] Resolve issues found in review

**Exit gate:** Results documented; no open blocking bugs.

## M6 · Release
| Data | Web |
|---|---|
| README and methodology copy | Deploy to GitHub Pages; mobile QA |

- [ ] **Joint:** release review and `v1.0` tag

**Exit gate:** v1.0 tagged and live.

---

## Conventions
| | |
|---|---|
| Branches | `data/<topic>` · `web/<topic>` |
| Merging | PR only · 1 approval from the other track · `main` protected |
| Tracking | One issue per task · labels `data` `web` `M0`–`M6` · `Closes #n` in PR |
| Interface | `docs/data-contract.md` · changes need both approvals |
| Excluded | Secrets, API keys, `data/raw/` |
| Cadence | Daily 10-min sync · milestone review at each gate |
