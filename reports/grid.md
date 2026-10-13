# Exit/entry variant grid

Trials run: **12** (fixed in advance). Hold-out = entries from 2023-01-01. CIs are month-clustered bootstrap intervals (trades entered in the same month share market moves, so they are not independent), at Bonferroni-adjusted confidence for 12 trials (alpha = 0.05/12).

Gates: **G1** design avg R > 0 · **G2** hold-out adjusted CI lower bound > 0 · **G3** hold-out portfolio CAGR > 0.

| Variant | Trades/yr | Avg hold | Design n / avg R | Hold-out n / avg R | Hold-out adj. CI | Full PF | Full CAGR / maxDD | Hold-out portfolio CAGR / maxDD | G1 | G2 | G3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none/ema20/h40 | 1551 | 7.3 | 8866 / -0.024 | 5067 / 0.036 | [-0.129, 0.237] | 0.99 | -2.4% / -25.3% | -1.1% / -19.2% | ❌ | ❌ | ❌ |
| none/ema50/h40 | 879 | 13.8 | 5033 / 0.076 | 2853 / 0.24 | [-0.076, 0.635] | 1.26 | -0.6% / -21.2% | -1.1% / -13.8% | ✅ | ❌ | ❌ |
| none/ema50/h120 | 728 | 17.2 | 4230 / 0.147 | 2307 / 0.442 | [-0.026, 1.042] | 1.5 | 2.4% / -17.7% | 4.4% / -16.1% | ✅ | ❌ | ✅ |
| none/chandelier/h40 | 818 | 15.4 | 4674 / 0.043 | 2667 / 0.187 | [-0.126, 0.525] | 1.15 | 1.4% / -17.0% | 2.9% / -9.5% | ✅ | ❌ | ✅ |
| none/chandelier/h120 | 776 | 16.5 | 4448 / 0.053 | 2513 / 0.222 | [-0.114, 0.587] | 1.18 | 3.3% / -18.6% | 2.7% / -11.4% | ✅ | ❌ | ✅ |
| none/none/h120 | 349 | 43.1 | 2044 / 0.476 | 1090 / 1.204 | [0.169, 2.411] | 1.82 | 2.1% / -15.0% | 7.1% / -8.3% | ✅ | ✅ | ✅ |
| prior_high/ema20/h40 | 1147 | 8.9 | 6567 / 0.001 | 3738 / 0.098 | [-0.11, 0.332] | 1.09 | -4.5% / -33.8% | -6.2% / -22.0% | ✅ | ❌ | ❌ |
| prior_high/ema50/h40 | 687 | 16.5 | 3959 / 0.129 | 2210 / 0.367 | [0.0, 0.764] | 1.37 | 3.4% / -14.3% | 1.6% / -10.6% | ✅ | ✅ | ✅ |
| prior_high/ema50/h120 | 567 | 21.1 | 3310 / 0.22 | 1778 / 0.633 | [0.089, 1.291] | 1.65 | 6.3% / -12.5% | 6.7% / -15.7% | ✅ | ✅ | ✅ |
| prior_high/chandelier/h40 | 690 | 16.9 | 3948 / 0.048 | 2251 / 0.249 | [-0.098, 0.608] | 1.19 | 0.8% / -14.4% | 2.1% / -9.9% | ✅ | ❌ | ✅ |
| prior_high/chandelier/h120 | 660 | 18.0 | 3777 / 0.067 | 2142 / 0.285 | [-0.136, 0.683] | 1.23 | 2.0% / -15.0% | 3.5% / -11.8% | ✅ | ❌ | ✅ |
| prior_high/none/h120 | 291 | 50.3 | 1702 / 0.63 | 910 / 1.467 | [0.313, 2.618] | 1.93 | 1.9% / -15.8% | 7.6% / -9.0% | ✅ | ✅ | ✅ |

**Promising (all gates): ['none/none/h120', 'prior_high/ema50/h40', 'prior_high/ema50/h120', 'prior_high/none/h120']**

Nifty buy-and-hold since 2023-01-01: {"cagr_pct": 5.6, "max_drawdown_pct": -15.8}

_Survivorship bias flatters every row. Passing all gates would justify paper trading only._