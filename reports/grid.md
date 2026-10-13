# Exit/entry variant grid

Trials run: **12** (fixed in advance). Hold-out = entries from 2023-01-01. CIs are month-clustered bootstrap intervals (trades entered in the same month share market moves, so they are not independent), at Bonferroni-adjusted confidence for 12 trials (alpha = 0.05/12).

Gates: **G1** design avg R > 0 · **G2** hold-out adjusted CI lower bound > 0 · **G3** hold-out portfolio CAGR > 0.

| Variant | Trades/yr | Avg hold | Design n / avg R | Hold-out n / avg R | Hold-out adj. CI | Full PF | Full CAGR / maxDD | Hold-out portfolio CAGR / maxDD | G1 | G2 | G3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none/ema20/h40 | 1539 | 7.3 | 8828 / -0.025 | 5003 / 0.031 | [-0.132, 0.233] | 0.99 | -2.2% / -24.6% | -3.2% / -20.7% | ❌ | ❌ | ❌ |
| none/ema50/h40 | 873 | 13.8 | 5012 / 0.075 | 2821 / 0.229 | [-0.083, 0.621] | 1.25 | -0.4% / -19.9% | 0.5% / -10.0% | ✅ | ❌ | ✅ |
| none/ema50/h120 | 725 | 17.1 | 4213 / 0.147 | 2291 / 0.426 | [-0.038, 1.01] | 1.49 | 2.4% / -17.7% | 2.0% / -19.8% | ✅ | ❌ | ✅ |
| none/chandelier/h40 | 811 | 15.4 | 4651 / 0.043 | 2628 / 0.177 | [-0.13, 0.519] | 1.15 | 0.8% / -17.4% | 3.0% / -9.5% | ✅ | ❌ | ✅ |
| none/chandelier/h120 | 769 | 16.5 | 4426 / 0.053 | 2478 / 0.21 | [-0.117, 0.565] | 1.18 | 2.1% / -18.6% | 0.9% / -14.5% | ✅ | ❌ | ✅ |
| none/none/h120 | 347 | 43.0 | 2034 / 0.475 | 1081 / 1.167 | [0.161, 2.37] | 1.8 | 2.5% / -15.1% | 8.9% / -8.3% | ✅ | ✅ | ✅ |
| prior_high/ema20/h40 | 1138 | 8.9 | 6536 / -0.001 | 3689 / 0.091 | [-0.114, 0.323] | 1.08 | -5.3% / -38.5% | -6.6% / -23.3% | ❌ | ❌ | ❌ |
| prior_high/ema50/h40 | 682 | 16.5 | 3943 / 0.127 | 2185 / 0.354 | [-0.005, 0.739] | 1.36 | 2.9% / -13.9% | 1.6% / -10.6% | ✅ | ❌ | ✅ |
| prior_high/ema50/h120 | 564 | 21.0 | 3296 / 0.218 | 1764 / 0.613 | [0.085, 1.246] | 1.64 | 4.8% / -16.8% | 7.5% / -14.8% | ✅ | ✅ | ✅ |
| prior_high/chandelier/h40 | 684 | 16.9 | 3931 / 0.047 | 2217 / 0.237 | [-0.116, 0.594] | 1.18 | 1.6% / -13.3% | 2.4% / -12.2% | ✅ | ❌ | ✅ |
| prior_high/chandelier/h120 | 654 | 18.0 | 3760 / 0.067 | 2110 / 0.272 | [-0.144, 0.659] | 1.22 | 0.5% / -22.4% | 3.7% / -12.1% | ✅ | ❌ | ✅ |
| prior_high/none/h120 | 289 | 50.3 | 1693 / 0.628 | 899 / 1.432 | [0.285, 2.576] | 1.92 | 1.9% / -15.8% | 7.6% / -9.0% | ✅ | ✅ | ✅ |

**Promising (all gates): ['none/none/h120', 'prior_high/ema50/h120', 'prior_high/none/h120']**

Nifty buy-and-hold since 2023-01-01: {"cagr_pct": 5.6, "max_drawdown_pct": -15.8}

_Survivorship bias flatters every row. Passing all gates would justify paper trading only._