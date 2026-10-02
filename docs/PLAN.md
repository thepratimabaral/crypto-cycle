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
| Python environment — `requirements.txt` | Sample data — `web/data/sample/*.json` |
| Data validation, 7 assets — `pipeline/check_data.py` | App shell: layout, tabs, price chart — `web/index.html` |
| Coverage and anomalies — `docs/data-notes.md` | |

**Exit gate:** Both tracks pushed to main; dashboard renders sample data.

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
- [ ] Fix problems found in review

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
| Commits | Prefix with track: `data: add indicators` · `web: history chart` |
| Pushing | Direct push to `main` · `git pull` before `git push` · force push and branch deletion blocked |
| Tracking | GitHub issues #1–#13 + Crypto Cycle Sprint page · `closes #n` in commit messages |
| Interface | `docs/data-contract.md` · agree changes with your teammate first |
| Excluded | Secrets, API keys, `.venv/` |
| Cadence | Daily 10-min sync · milestone review at each gate |
