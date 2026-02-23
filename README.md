# HolderLens

## What is HolderLens?

HolderLens is a tool that analyzes Polymarket prediction markets by examining the positions of top holders and their historical profitability. By weighting holder positions against their all-time PnL, HolderLens surfaces where "smart money" is leaning on any given market.

---

## How it works

1. You paste a Polymarket event URL
2. HolderLens fetches the top 50 holders for that market
3. It filters out holders with less than 100 shares (noise reduction)
4. It fetches the all-time PnL for each holder
5. It calculates a position-weighted PnL for both YES and NO sides
6. It tells you which side the historically profitable traders are on

The core signal is the **weighted PnL formula**:

```
Weighted PnL = Σ(PnL_i × Amount_i) / Σ(Amount_i)
```

A holder with 10,000 shares influences the signal more than a holder with 200 shares. This ensures the signal reflects conviction, not just headcount.

---

## Interface

HolderLens comes with two ways to run it:

## Command Line

Runmain.py directly and interact through the terminal. Paste a URL, pick a market by number, and results are printed to the console.

## Streamlit UI

Runstreamlit run app.py for a browser-based interface. The UI guides you through the same steps with dropdowns, progress bars, and formatted results. Only YES/NO binary markets are supported — sports markets or any market with more than two outcomes will not produce reliable signals.

---

## Usage

```
Please enter the Polymarket URL: https://polymarket.com/event/will-x-happen

==================================================
Available markets:
  1. Will X happen by March?
  2. Will X happen by June?
==================================================
Pick a market (enter number): 1

==================================================
Market: Will X happen by March?
==================================================
Found 30 YES holders and 20 NO holders

==================================================
SMART MONEY SIGNAL
==================================================
Weighted PnL - YES holders: $  124500.00
Weighted PnL - NO holders:  $   43200.00
==================================================
Smart money leans YES
==================================================
```

---

## Limitations

- Only looks at the **top 50 holders** per market
- PnL is **all-time** across all markets, not specific to this market
- A high PnL holder on the wrong side will still influence the signal
- Low liquidity markets may not have enough holders above the 100 share threshold to produce a meaningful signal
- Only binary markets are supported

---

## Data Sources

- [Gamma API](https://gamma-api.polymarket.com) — market and event metadata
- [Data API](https://data-api.polymarket.com) — holder positions and leaderboard PnL

---

## Disclaimer

HolderLens is for informational purposes only. Nothing here is financial advice. Prediction markets are risky and past PnL of holders does not guarantee future performance.
