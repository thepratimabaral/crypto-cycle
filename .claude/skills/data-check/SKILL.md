---
name: data-check
description: Refresh and validate the Crypto Cycle raw data. Runs pipeline/check_data.py, reads its blocking problems and warnings, decides whether each anomaly is real or a data error, and updates docs/data-notes.md and data/raw/README.md. Use when asked to refresh data, check data quality, investigate a price spike or gap, add a coin or data source, or when check_data fails. Triggers on "check data", "refresh data", "data quality", "missing days", "stale", "outlier", "spike", "anomaly", "data notes", "add a coin", "new source", "fetch failed".
---

# Data check

## 1. Run it

```bash
python3 -m pipeline.check_data
```

It refetches all 7 coins and **rewrites `data/raw/*.csv`**. If an API fails it prints
`! SYMBOL: fetch failed (...); using cached data` and checks the committed copy instead. It
ends with `RESULT: PASS` or `RESULT: FAIL` (exit code 1).

## 2. Read the output

Blocking (must be fixed before the pipeline can be trusted):

| Message | Usual cause | What to do |
|---|---|---|
| `N missing days` | Source gap or pagination bug in `binance_daily` | Fix the fetcher; don't patch the CSV |
| `N duplicate dates` | Overlapping pages or a timezone shift | Fix the fetcher's dedup / normalisation |
| `zero/negative prices` | Source placeholder values (BTC before 2010-08-18 is 0) | Filter in the fetcher |
| `empty values in close` | Forward-fill didn't cover the start | Check the first rows the source returns |
| `last row is N days old` | API down and cache used, or source lagging | Rerun later; if persistent, check the endpoint |

Warnings (review, then record):

- `daily moves over 60%`: look up the date. A real event (court ruling, listing, social-media
  spike) → keep and record it. A bad print (one day spikes and reverts, other sources disagree)
  → fix at the fetcher level, never by editing the CSV.
- `price unchanged for N days`: expected in BTC 2010–2012 (thin market). Anywhere else it
  usually means forward-filled missing data from the source.

Already-reviewed anomalies are listed in `docs/data-notes.md` → "Anomalies reviewed". Don't
re-investigate those; only new ones.

## 3. Record it

Update `docs/data-notes.md`:

- The "Checked with … on YYYY-MM-DD. Result: PASS/FAIL" line.
- The coverage table (last day and day counts) if you are recording a snapshot.
- New rows in "Anomalies reviewed": asset, finding, verdict with the reason.
- "Impact on the model" if coverage changes what indicators a coin can have
  (the 200-week MA needs 1,400 days; percentiles need 365 days of indicator values).

## 4. Commit

Raw data and notes go in one commit, separate from code changes:

```
data: refresh raw data to YYYY-MM-DD
```

Add `closes #n` if it finishes an issue. Before committing, `git diff --stat data/raw/` should
show only appended rows. A large rewrite of old rows means the source changed history; look
at it and note it in `data-notes.md` before committing.

## Adding a coin or source

- A Binance coin: add `"SYM": "SYMUSDT"` to `ASSETS` in `pipeline/check_data.py` (and to the
  pipeline's coin list once `run.py` exists), run the check, add a row to the coverage table
  in `docs/data-notes.md` and the file table in `data/raw/README.md`.
- A new source: free and keyless only (CoinGecko free tier is 365 days and CryptoCompare needs
  a key; both were rejected). Use `get_json()` from `fetch.py` so retries and the certifi CA
  bundle apply. Document the exact endpoint, units and history start in `data/raw/README.md`.
- History starts at the Binance listing, not the coin's launch. Prices are USDT, not USD.
