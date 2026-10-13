# Universe / survivorship check

Equal-weight buy-and-hold of the 159 stocks in today's universe (daily rebalanced, no costs) versus the Nifty.
The gap is an **upper bound** on survivorship effects: it also contains real size/style differences (this list is mid-cap heavy).

| Period | Universe CAGR / maxDD | Nifty CAGR / maxDD | Universe excess CAGR |
|---|---|---|---|
| Full history | 19.8% / -38.0% | 10.1% / -38.4% | 9.7 pts |
| Hold-out (from 2023-01-01) | 17.1% / -20.7% | 5.8% / -15.8% | 11.3 pts |

**Do the passing variants beat what the universe alone delivered?** Hold-out portfolio CAGR vs Nifty, next to the universe excess above. Note the strategy portfolio holds at most ~3 positions at 0.5% risk, so it is rarely more than half invested; compare drawdown as well.

| Variant | Hold-out portfolio CAGR | Excess over Nifty | Beats universe excess? |
|---|---|---|---|
| none/none/h120 | 7.1% | 1.3 pts | no |
| prior_high/ema50/h40 | 1.6% | -4.2 pts | no |
| prior_high/ema50/h120 | 6.7% | 0.9 pts | no |
| prior_high/none/h120 | 7.6% | 1.8 pts | no |

Reading it: if the universe alone beat the Nifty by about as much as a passing variant did, the variant has shown no edge beyond "these stocks went up". Beating it does not prove the edge is real: data without delisted names can still flatter every row.