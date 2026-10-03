# Crypto Cycle

A dashboard for BTC and the top coins. It shows each coin's full price history, a 0–100 cycle
score, the chance the price is higher in 30, 90 and 365 days, and a backtest plus a live log
that show whether those predictions actually work.

- Design and method: open [`blueprint.html`](blueprint.html) in a browser
- Who does what, day by day: [`docs/PLAN.md`](docs/PLAN.md)
- JSON format between the pipeline and the website: [`docs/data-contract.md`](docs/data-contract.md)

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 pipeline/fetch.py        # download price history to data/raw/
python3 pipeline/check_data.py   # check the data: PASS / FAIL
python3 -m http.server -d web 8000   # then open http://localhost:8000
```

## Data sources (free, no API key)

- BTC daily price: blockchain.info charts API
- ETH, BNB, SOL, XRP, ADA, DOGE daily prices: Binance public market-data API
- Fear & Greed Index: alternative.me

## Disclaimer

Not financial advice. Historical indicators can fail, and past cycles don't guarantee future results.
