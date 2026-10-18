# Exit/entry variant grid

Trials run: **12** (fixed in advance). Hold-out = entries from 2023-01-01. CIs are month-clustered bootstrap intervals (trades entered in the same month share market moves, so they are not independent), at Bonferroni-adjusted confidence for 12 trials (alpha = 0.05/12).

Gates: **G1** design avg R > 0 · **G2** hold-out adjusted CI lower bound > 0 · **G3** hold-out portfolio CAGR > 0.

| Variant | Trades/yr | Avg hold | Design n / avg R | Hold-out n / avg R | Hold-out adj. CI | Full PF | Full CAGR / maxDD | Hold-out portfolio CAGR / maxDD | G1 | G2 | G3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none/ema20/h40 | 1547 | 7.3 | 8850 / -0.024 | 5061 / 0.035 | [-0.129, 0.235] | 0.99 | -3.3% / -27.4% | -2.9% / -24.2% | ❌ | ❌ | ❌ |
| none/ema50/h40 | 876 | 13.8 | 5020 / 0.075 | 2852 / 0.239 | [-0.077, 0.628] | 1.26 | 2.2% / -19.9% | -1.4% / -14.4% | ✅ | ❌ | ❌ |
| none/ema50/h120 | 725 | 17.2 | 4216 / 0.149 | 2307 / 0.438 | [-0.029, 1.035] | 1.5 | 0.2% / -17.9% | 3.8% / -16.1% | ✅ | ❌ | ✅ |
| none/chandelier/h40 | 814 | 15.4 | 4659 / 0.045 | 2662 / 0.186 | [-0.127, 0.52] | 1.16 | 2.9% / -17.1% | 2.5% / -10.3% | ✅ | ❌ | ✅ |
| none/chandelier/h120 | 772 | 16.5 | 4431 / 0.055 | 2508 / 0.22 | [-0.114, 0.583] | 1.19 | 3.6% / -14.6% | 2.6% / -11.4% | ✅ | ❌ | ✅ |
| none/none/h120 | 347 | 43.2 | 2032 / 0.494 | 1089 / 1.197 | [0.163, 2.405] | 1.83 | 4.0% / -15.0% | 7.1% / -8.3% | ✅ | ✅ | ✅ |
| prior_high/ema20/h40 | 1143 | 8.9 | 6542 / 0.003 | 3732 / 0.097 | [-0.11, 0.327] | 1.09 | -4.6% / -36.8% | -5.5% / -20.1% | ✅ | ❌ | ❌ |
| prior_high/ema50/h40 | 683 | 16.5 | 3939 / 0.131 | 2205 / 0.367 | [0.001, 0.763] | 1.37 | 4.3% / -14.8% | 1.4% / -11.1% | ✅ | ✅ | ✅ |
| prior_high/ema50/h120 | 564 | 21.1 | 3295 / 0.223 | 1776 / 0.63 | [0.088, 1.284] | 1.65 | 4.4% / -13.9% | 7.3% / -14.8% | ✅ | ✅ | ✅ |
| prior_high/chandelier/h40 | 686 | 16.9 | 3927 / 0.05 | 2244 / 0.25 | [-0.097, 0.608] | 1.19 | -0.7% / -23.2% | 1.2% / -16.5% | ✅ | ❌ | ✅ |
| prior_high/chandelier/h120 | 655 | 18.1 | 3755 / 0.071 | 2136 / 0.285 | [-0.132, 0.681] | 1.23 | 0.8% / -16.9% | 3.3% / -11.8% | ✅ | ❌ | ✅ |
| prior_high/none/h120 | 289 | 50.5 | 1689 / 0.651 | 909 / 1.46 | [0.31, 2.614] | 1.95 | 4.2% / -12.8% | 7.7% / -9.0% | ✅ | ✅ | ✅ |

**Promising (all gates): ['none/none/h120', 'prior_high/ema50/h40', 'prior_high/ema50/h120', 'prior_high/none/h120']**

Nifty buy-and-hold since 2023-01-01: {"cagr_pct": 6.6, "max_drawdown_pct": -15.8}

_Survivorship bias flatters every row. Passing all gates would justify paper trading only._