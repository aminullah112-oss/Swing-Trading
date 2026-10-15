# Survivorship bias: the data that is still missing (gate B2)

Every backtest uses today's 160 names. Stocks that were in the universe, fell hard and left it are absent, so the history is
flattering by an unknown amount. `robustness.py` (R-SURV) shows how much hidden delisting risk the result can absorb; it does not fix
the problem. Fixing it needs two datasets that cannot be fetched from the sandbox.

## 1. Membership file (point-in-time universe)

CSV `universe/pit_membership.csv`, columns `symbol,start,end` (YYYY-MM-DD, blank `end` = still a member), one row per membership span:

```
symbol,start,end
RELIANCE,2014-01-01,
JPASSOCIAT,2014-01-01,2017-09-29
```

Source: NSE index reconstitution notices (semi-annual, March and September) for the index the universe was drawn from. Use the same
selection rule you used for today's 160 (index, size band, liquidity floor) and apply it as of each past date. Do not back-fill with
today's list.

## 2. Prices for the departed names

OHLCV for every symbol in the file for its whole membership span, including the final sessions before delisting or suspension.
NSE bhavcopy archives (`sec_bhavdata_full_*.csv`) cover this; Yahoo usually does not. Prices must be split/bonus adjusted the same
way as the current history. Where a stock was suspended or delisted at a loss, record the last tradable price: do not drop the trade.

## 3. Acceptance

```
EDGE_PIT_UNIVERSE=universe/pit_membership.csv python pit_report.py --years 12
```

`pit.acceptance()` requires departed names to exist in the file AND to have prices, and price coverage of member-months of at least
95%. Only if it passes may `attestations.json` carry the survivorship attestation, and only then does B2 earn credit. The backtests
then drop signals on dates the stock was not a member (`pit.is_member`). Re-run the Backtest workflow; compare C0 before and after.
The drop in CAGR is the survivorship bias.

## Rough effort

A few days of data work for a careful job, most of it on reconstitution history and delisted-price gaps. If this is not worth doing,
the honest conclusion stays: backtest results are an optimistic upper bound.
