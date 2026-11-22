# Exit/entry variant grid

Trials run: **12** (fixed in advance). Hold-out = entries from 2023-01-01. CIs are month-clustered bootstrap intervals (trades entered in the same month share market moves, so they are not independent), at Bonferroni-adjusted confidence for 12 trials (alpha = 0.05/12).

Gates: **G1** design avg R > 0 · **G2** hold-out adjusted CI lower bound > 0 · **G3** hold-out portfolio CAGR > 0.

| Variant | Trades/yr | Avg hold | Design n / avg R | Hold-out n / avg R | Hold-out adj. CI | Full PF | Full CAGR / maxDD | Hold-out portfolio CAGR / maxDD | G1 | G2 | G3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none/ema20/h40 | 1538 | 7.3 | 8718 / -0.028 | 5119 / 0.04 | [-0.114, 0.238] | 0.99 | -4.0% / -36.1% | 0.3% / -18.6% | ❌ | ❌ | ✅ |
| none/ema50/h40 | 873 | 13.7 | 4959 / 0.071 | 2891 / 0.244 | [-0.046, 0.635] | 1.26 | 2.5% / -20.7% | -1.9% / -15.4% | ✅ | ❌ | ❌ |
| none/ema50/h120 | 724 | 17.1 | 4171 / 0.137 | 2340 / 0.447 | [-0.01, 1.056] | 1.5 | 0.5% / -19.4% | 0.9% / -22.6% | ✅ | ❌ | ✅ |
| none/chandelier/h40 | 811 | 15.4 | 4597 / 0.039 | 2701 / 0.193 | [-0.13, 0.541] | 1.16 | 1.5% / -19.1% | 3.6% / -12.3% | ✅ | ❌ | ✅ |
| none/chandelier/h120 | 770 | 16.4 | 4375 / 0.047 | 2548 / 0.226 | [-0.133, 0.614] | 1.18 | 2.6% / -13.8% | 3.5% / -11.4% | ✅ | ❌ | ✅ |
| none/none/h120 | 348 | 42.8 | 2013 / 0.459 | 1113 / 1.209 | [0.129, 2.351] | 1.82 | 2.7% / -21.0% | 7.6% / -8.3% | ✅ | ✅ | ✅ |
| prior_high/ema20/h40 | 1138 | 8.9 | 6459 / -0.005 | 3774 / 0.104 | [-0.088, 0.349] | 1.09 | -5.6% / -44.2% | -5.2% / -23.0% | ❌ | ❌ | ❌ |
| prior_high/ema50/h40 | 681 | 16.5 | 3890 / 0.12 | 2239 / 0.371 | [-0.022, 0.782] | 1.36 | 4.6% / -13.8% | 3.3% / -12.4% | ✅ | ❌ | ✅ |
| prior_high/ema50/h120 | 564 | 20.9 | 3272 / 0.202 | 1803 / 0.639 | [0.09, 1.25] | 1.64 | 4.5% / -16.2% | 7.2% / -14.8% | ✅ | ✅ | ✅ |
| prior_high/chandelier/h40 | 685 | 16.8 | 3886 / 0.041 | 2276 / 0.257 | [-0.1, 0.606] | 1.19 | -1.7% / -21.6% | 4.0% / -10.5% | ✅ | ❌ | ✅ |
| prior_high/chandelier/h120 | 655 | 18.0 | 3720 / 0.058 | 2168 / 0.292 | [-0.06, 0.638] | 1.22 | 3.3% / -12.3% | 1.8% / -17.3% | ✅ | ❌ | ✅ |
| prior_high/none/h120 | 291 | 49.8 | 1690 / 0.589 | 929 / 1.477 | [0.471, 2.636] | 1.91 | 4.7% / -13.7% | 8.3% / -9.0% | ✅ | ✅ | ✅ |

**Promising (all gates): ['none/none/h120', 'prior_high/ema50/h120', 'prior_high/none/h120']**

Nifty buy-and-hold since 2023-01-01: {"cagr_pct": 9.4, "max_drawdown_pct": -15.8}

_Survivorship bias flatters every row. Passing all gates would justify paper trading only._