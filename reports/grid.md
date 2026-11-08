# Exit/entry variant grid

Trials run: **12** (fixed in advance). Hold-out = entries from 2023-01-01. CIs are month-clustered bootstrap intervals (trades entered in the same month share market moves, so they are not independent), at Bonferroni-adjusted confidence for 12 trials (alpha = 0.05/12).

Gates: **G1** design avg R > 0 · **G2** hold-out adjusted CI lower bound > 0 · **G3** hold-out portfolio CAGR > 0.

| Variant | Trades/yr | Avg hold | Design n / avg R | Hold-out n / avg R | Hold-out adj. CI | Full PF | Full CAGR / maxDD | Hold-out portfolio CAGR / maxDD | G1 | G2 | G3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none/ema20/h40 | 1547 | 7.3 | 8812 / -0.027 | 5100 / 0.038 | [-0.117, 0.235] | 0.99 | -2.6% / -26.1% | -0.4% / -19.4% | ❌ | ❌ | ❌ |
| none/ema50/h40 | 878 | 13.7 | 5018 / 0.071 | 2877 / 0.242 | [-0.048, 0.634] | 1.25 | 1.4% / -19.3% | -1.3% / -15.3% | ✅ | ❌ | ❌ |
| none/ema50/h120 | 727 | 17.1 | 4206 / 0.14 | 2327 / 0.444 | [-0.019, 1.052] | 1.5 | 0.1% / -17.4% | 4.1% / -15.2% | ✅ | ❌ | ✅ |
| none/chandelier/h40 | 814 | 15.4 | 4631 / 0.043 | 2685 / 0.19 | [-0.133, 0.53] | 1.16 | 3.2% / -13.9% | 3.0% / -12.3% | ✅ | ❌ | ✅ |
| none/chandelier/h120 | 771 | 16.5 | 4403 / 0.053 | 2532 / 0.224 | [-0.134, 0.606] | 1.19 | 3.9% / -11.6% | 3.2% / -11.4% | ✅ | ❌ | ✅ |
| none/none/h120 | 347 | 43.1 | 2020 / 0.472 | 1101 / 1.212 | [0.128, 2.406] | 1.83 | 2.3% / -15.0% | 7.7% / -8.3% | ✅ | ✅ | ✅ |
| prior_high/ema20/h40 | 1144 | 8.9 | 6524 / -0.004 | 3764 / 0.101 | [-0.094, 0.347] | 1.09 | -6.5% / -49.2% | -5.2% / -22.4% | ❌ | ❌ | ❌ |
| prior_high/ema50/h40 | 684 | 16.5 | 3927 / 0.122 | 2227 / 0.369 | [-0.027, 0.78] | 1.36 | 4.5% / -13.3% | 2.2% / -12.4% | ✅ | ❌ | ✅ |
| prior_high/ema50/h120 | 565 | 21.0 | 3291 / 0.207 | 1792 / 0.635 | [0.086, 1.256] | 1.64 | 4.4% / -16.1% | 7.5% / -15.7% | ✅ | ✅ | ✅ |
| prior_high/chandelier/h40 | 687 | 16.9 | 3910 / 0.045 | 2267 / 0.251 | [-0.108, 0.6] | 1.19 | 1.1% / -16.5% | 2.5% / -14.9% | ✅ | ❌ | ✅ |
| prior_high/chandelier/h120 | 656 | 18.0 | 3741 / 0.064 | 2157 / 0.288 | [-0.074, 0.642] | 1.23 | 1.6% / -15.7% | 1.2% / -17.3% | ✅ | ❌ | ✅ |
| prior_high/none/h120 | 289 | 50.4 | 1681 / 0.625 | 920 / 1.477 | [0.475, 2.637] | 1.94 | 1.8% / -18.9% | 8.2% / -9.0% | ✅ | ✅ | ✅ |

**Promising (all gates): ['none/none/h120', 'prior_high/ema50/h120', 'prior_high/none/h120']**

Nifty buy-and-hold since 2023-01-01: {"cagr_pct": 8.6, "max_drawdown_pct": -15.8}

_Survivorship bias flatters every row. Passing all gates would justify paper trading only._