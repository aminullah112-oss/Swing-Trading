# Exit/entry variant grid

Trials run: **12** (fixed in advance). Hold-out = entries from 2023-01-01. CIs are month-clustered bootstrap intervals (trades entered in the same month share market moves, so they are not independent), at Bonferroni-adjusted confidence for 12 trials (alpha = 0.05/12).

Gates: **G1** design avg R > 0 · **G2** hold-out adjusted CI lower bound > 0 · **G3** hold-out portfolio CAGR > 0.

| Variant | Trades/yr | Avg hold | Design n / avg R | Hold-out n / avg R | Hold-out adj. CI | Full PF | Full CAGR / maxDD | Hold-out portfolio CAGR / maxDD | G1 | G2 | G3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none/ema20/h40 | 1551 | 7.3 | 8846 / -0.029 | 5095 / 0.036 | [-0.123, 0.246] | 0.99 | -2.2% / -27.4% | -1.2% / -22.0% | ❌ | ❌ | ❌ |
| none/ema50/h40 | 880 | 13.7 | 5038 / 0.068 | 2871 / 0.238 | [-0.088, 0.62] | 1.25 | 2.0% / -16.8% | -1.5% / -15.3% | ✅ | ❌ | ❌ |
| none/ema50/h120 | 729 | 17.1 | 4234 / 0.133 | 2323 / 0.439 | [-0.033, 1.034] | 1.48 | -1.9% / -22.5% | 3.3% / -13.3% | ✅ | ❌ | ✅ |
| none/chandelier/h40 | 816 | 15.4 | 4657 / 0.038 | 2681 / 0.184 | [-0.129, 0.532] | 1.15 | 1.1% / -16.5% | 2.7% / -12.3% | ✅ | ❌ | ✅ |
| none/chandelier/h120 | 774 | 16.5 | 4431 / 0.046 | 2527 / 0.217 | [-0.125, 0.577] | 1.18 | 3.6% / -11.8% | 2.5% / -12.2% | ✅ | ❌ | ✅ |
| none/none/h120 | 350 | 42.8 | 2048 / 0.459 | 1098 / 1.198 | [0.104, 2.309] | 1.81 | 2.6% / -16.2% | 7.4% / -8.3% | ✅ | ✅ | ✅ |
| prior_high/ema20/h40 | 1146 | 8.9 | 6544 / -0.005 | 3759 / 0.098 | [-0.105, 0.316] | 1.08 | -7.1% / -51.0% | -5.4% / -22.4% | ❌ | ❌ | ❌ |
| prior_high/ema50/h40 | 687 | 16.4 | 3953 / 0.119 | 2223 / 0.364 | [0.017, 0.772] | 1.35 | 2.4% / -20.0% | 1.6% / -11.4% | ✅ | ✅ | ✅ |
| prior_high/ema50/h120 | 567 | 20.9 | 3308 / 0.204 | 1791 / 0.628 | [0.102, 1.275] | 1.63 | 4.1% / -14.2% | 7.8% / -14.8% | ✅ | ✅ | ✅ |
| prior_high/chandelier/h40 | 690 | 16.8 | 3936 / 0.039 | 2262 / 0.246 | [-0.109, 0.571] | 1.18 | 0.5% / -16.1% | 1.3% / -17.5% | ✅ | ❌ | ✅ |
| prior_high/chandelier/h120 | 658 | 18.0 | 3763 / 0.058 | 2153 / 0.281 | [-0.087, 0.668] | 1.21 | 1.0% / -18.7% | 3.3% / -14.3% | ✅ | ❌ | ✅ |
| prior_high/none/h120 | 291 | 50.1 | 1701 / 0.619 | 917 / 1.462 | [0.308, 2.627] | 1.92 | 5.1% / -13.7% | 7.8% / -9.0% | ✅ | ✅ | ✅ |

**Promising (all gates): ['none/none/h120', 'prior_high/ema50/h40', 'prior_high/ema50/h120', 'prior_high/none/h120']**

Nifty buy-and-hold since 2023-01-01: {"cagr_pct": 6.4, "max_drawdown_pct": -15.8}

_Survivorship bias flatters every row. Passing all gates would justify paper trading only._