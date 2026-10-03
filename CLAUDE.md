# Crypto Cycle

A static dashboard for BTC, ETH, BNB, SOL, XRP, ADA and DOGE. It shows each coin's full price
history, a 0–100 cycle score, the chance the price is higher in 30, 90 and 365 days, and the
evidence for whether that works: a walk-forward backtest against baselines and a live,
append-only prediction log.

A Python pipeline runs once a day, downloads free public data, computes everything and writes
plain JSON. The website only reads that JSON. There is no server and no database.

```
free APIs ──► pipeline/fetch.py ──► pipeline/model.py ──► pipeline/run.py ──► web/data/*.json ──► web/index.html
                (data/raw/*.csv)     indicators, score,     JSON export,
                                     forecast, backtest     prediction log
```

## Where things are

| Path | What | Status (2026-10-03) |
|---|---|---|
| `pipeline/fetch.py` | Downloads history to `data/raw/` (BTC: price, hash rate, miner revenue); falls back to the saved file if an API fails | Done |
| `pipeline/check_data.py` | Reads `data/raw/` and checks all 7 assets (gaps, duplicates, empty, zero and stale prices); defines `ASSETS` | Done |
| `pipeline/model.py` | 8 indicators, percentile scoring, composite, bucket P(up) (method v1) | Done |
| `pipeline/backtest.py` | Pre-registered BTC backtest → `docs/results-btc-v1.md` | Done: **v1 failed** |
| `pipeline/live_log.py` | Appends daily v1 forecasts to `web/data/predictions_log.json` | Done; daily via `.github/workflows/daily-log.yml` |
| `pipeline/run.py` | Writes the dashboard JSON (`summary.json`, `coin_*.json`) | Not started |
| `tests/` | No-lookahead test, log append-only test | Done |
| `web/` | Dashboard (HTML/CSS/JS); only `web/data/predictions_log.json` exists | Not started |
| `data/raw/*.csv` | Committed raw daily history, one file per coin | Done |
| `docs/PLAN.md` | Milestones M0–M6 and who owns what. **Source of truth for scope.** | |
| `docs/data-contract.md` | JSON format between pipeline and website. **The only interface.** | |
| `docs/data-notes.md` | Coverage, source quirks, reviewed anomalies | |
| `docs/method-v1.md` | Pre-registered method and pass/fail test (tag `method-v1`). **Frozen.** | |
| `docs/results.md` | What the backtest found and what it means for the product | |
| `blueprint.html` | Design and method (indicators, scoring, prediction, validation) | |

## Commands

Run everything from the repo root. Modules import as `pipeline.*`, so use `-m`.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m pipeline.fetch             # downloads all 7 coins, rewrites data/raw/*.csv
python3 -m pipeline.check_data        # checks data/raw/*.csv (no download), exits 1 on a problem
python3 -m pipeline.backtest          # BTC backtest from the committed CSV → docs/results-btc-v1.md
python3 -m pipeline.live_log          # refetches, appends today's forecasts to the prediction log
python3 -m pytest tests -q
python3 -m http.server -d web 8000    # dashboard at http://localhost:8000 (file:// can't fetch JSON)
```

VS Code: `.vscode/launch.json` and `.vscode/tasks.json` wrap these same commands using the
`.venv` interpreter. Keep them in sync when a command changes.

`fetch` hits the network and **overwrites the committed CSVs**. Expect a `git diff` on
`data/raw/` afterwards (new days appended). That is normal; don't commit it by accident with
unrelated work.

## Rules that matter

- **No lookahead.** A value on day *t* may use only data up to and including day *t*.
  Percentiles are expanding (against the coin's own past), never over the full series.
  P(up) on day *t* uses only past days whose outcome was already known on *t*. This is what
  makes the backtest honest; break it and every number on the site is wrong. See the
  `cycle-model` skill.
- **The data contract is the interface.** The website reads only what `docs/data-contract.md`
  describes. A change to a JSON shape updates that file in the same commit, and the other
  track's owner is told first.
- **`predictions_log.json` is append-only.** Entries are never edited or deleted. The only
  allowed change is resolving a pending entry once its `targetDate` has passed.
- **Raw CSVs come only from `fetch.py`.** Never hand-edit `data/raw/*.csv`. If data looks
  wrong, fix the fetcher or record the finding in `docs/data-notes.md`.
- **Method v1 is frozen.** Never change a formula or parameter in `docs/method-v1.md` or the
  code that implements it to improve a result. A better method is a new pre-registered
  version (`method-v2.md`, its own tag) whose real test is the live log, because the
  backtest history has already been seen.
- **v1 failed its test** (`docs/results.md`). Don't present the score's P(up) as a forecast
  anywhere; the score is shown as a description of the cycle.
- **Report results honestly.** If the cycle score doesn't beat the baselines, the dashboard
  and docs say so. Don't tune parameters against the backtest until it looks good.
- **Not financial advice.** The disclaimer appears on every page and in `summary.json`.

## Code style

- Python 3, pandas + numpy. HTTP uses `requests` (via `download()` in `fetch.py`). Keep
  `requirements.txt` minimal.
- `fetch.py` and `check_data.py` are written in a beginner-friendly style with a comment on most
  lines; keep them that way when editing them. Other modules: docstring saying how to run it,
  short functions, module-level constants for thresholds, comments that explain *why*.
- Dates are UTC `YYYY-MM-DD`. Today's unfinished candle is always dropped; the last row is yesterday.
- Binance prices are USDT, not USD. Say so where it matters.
- In JSON output: `NaN` → `null`, probabilities 0–1, scores 0–100, returns as fractions (`0.18` = +18%).
- Web: plain HTML, CSS and JavaScript. No framework, no build step. Charts with TradingView
  Lightweight Charts. See the `web-dashboard` skill.

## Working conventions

- Two tracks: **Data** owns `pipeline/`, `tests/`, `docs/data-*`; **Web** owns `web/`, `.github/`.
- Commit messages start with the track: `data: add indicators`, `web: history chart`, `docs: …`.
- Reference issues with `closes #n`. Tasks are GitHub issues #1–#13, mirrored on the claude.ai sprint page
  (`sprint.html` is kept locally and gitignored, not committed).
- Direct push to `main`; `git pull` before `git push`. The plan says force push and branch deletion
  are blocked, but as of 2026-10-03 the repo ruleset targets tags only, so they aren't yet. Never force push.
- Never commit secrets, API keys or `.venv/`. All data sources are free and keyless.

## Skills in this repo

- `cycle-model`: indicators, expanding-percentile scoring, P(up), backtest, baselines, no-lookahead tests
- `web-dashboard`: the static site, reading the contract, charts, sample data, GitHub Pages and the daily workflow
- `data-check`: refresh and validate raw data, review anomalies, update `docs/data-notes.md`
