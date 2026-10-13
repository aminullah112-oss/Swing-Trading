# Exit/entry variant grid

Trials run: **12** (fixed in advance). Hold-out = entries from 2023-01-01. CIs are month-clustered bootstrap intervals (trades entered in the same month share market moves, so they are not independent), at Bonferroni-adjusted confidence for 12 trials (alpha = 0.05/12).

Gates: **G1** design avg R > 0 · **G2** hold-out adjusted CI lower bound > 0 · **G3** hold-out portfolio CAGR > 0.

| Variant | Trades/yr | Avg hold | Design n / avg R | Hold-out n / avg R | Hold-out adj. CI | Full PF | Full CAGR / maxDD | Hold-out portfolio CAGR / maxDD | G1 | G2 | G3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none/ema20/h40 | 1539 | 7.3 | 8828 / -0.025 | 5003 / 0.031 | [-0.132, 0.233] | 0.99 | -2.2% / -24.6% | -3.3% / -20.7% | ❌ | ❌ | ❌ |
| none/ema50/h40 | 873 | 13.8 | 5012 / 0.075 | 2820 / 0.23 | [-0.084, 0.623] | 1.25 | -0.5% / -20.2% | 0.2% / -10.4% | ✅ | ❌ | ✅ |
| none/ema50/h120 | 725 | 17.1 | 4213 / 0.147 | 2291 / 0.425 | [-0.039, 1.01] | 1.49 | 2.3% / -17.7% | 1.8% / -20.1% | ✅ | ❌ | ✅ |
| none/chandelier/h40 | 811 | 15.4 | 4650 / 0.044 | 2628 / 0.177 | [-0.13, 0.519] | 1.15 | 0.8% / -17.4% | 2.7% / -9.9% | ✅ | ❌ | ✅ |
| none/chandelier/h120 | 769 | 16.5 | 4425 / 0.054 | 2478 / 0.209 | [-0.118, 0.564] | 1.18 | 2.2% / -18.6% | 0.9% / -14.5% | ✅ | ❌ | ✅ |
| none/none/h120 | 347 | 43.0 | 2034 / 0.475 | 1081 / 1.167 | [0.161, 2.371] | 1.8 | 2.6% / -15.1% | 9.0% / -8.3% | ✅ | ✅ | ✅ |
| prior_high/ema20/h40 | 1137 | 8.9 | 6533 / -0.001 | 3689 / 0.091 | [-0.114, 0.323] | 1.08 | -5.4% / -39.2% | -6.6% / -23.3% | ❌ | ❌ | ❌ |
| prior_high/ema50/h40 | 682 | 16.5 | 3939 / 0.127 | 2183 / 0.355 | [-0.005, 0.743] | 1.36 | 3.6% / -14.4% | 1.6% / -12.7% | ✅ | ❌ | ✅ |
| prior_high/ema50/h120 | 563 | 21.0 | 3293 / 0.219 | 1764 / 0.611 | [0.084, 1.246] | 1.63 | 3.8% / -16.6% | 7.2% / -14.8% | ✅ | ✅ | ✅ |
| prior_high/chandelier/h40 | 685 | 16.9 | 3930 / 0.048 | 2215 / 0.238 | [-0.115, 0.595] | 1.18 | -0.8% / -17.3% | 0.2% / -12.0% | ✅ | ❌ | ✅ |
| prior_high/chandelier/h120 | 654 | 18.0 | 3758 / 0.069 | 2109 / 0.272 | [-0.142, 0.66] | 1.22 | -1.1% / -24.9% | 3.4% / -12.1% | ✅ | ❌ | ✅ |
| prior_high/none/h120 | 289 | 50.2 | 1694 / 0.63 | 899 / 1.432 | [0.287, 2.576] | 1.92 | 1.9% / -15.8% | 7.6% / -9.0% | ✅ | ✅ | ✅ |

**Promising (all gates): ['none/none/h120', 'prior_high/ema50/h120', 'prior_high/none/h120']**

Nifty buy-and-hold since 2023-01-01: {"cagr_pct": 6.1, "max_drawdown_pct": -15.8}

_Survivorship bias flatters every row. Passing all gates would justify paper trading only._