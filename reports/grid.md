# Exit/entry variant grid

Trials run: **12** (fixed in advance). Hold-out = entries from 2023-01-01. CIs are month-clustered bootstrap intervals (trades entered in the same month share market moves, so they are not independent), at Bonferroni-adjusted confidence for 12 trials (alpha = 0.05/12).

Gates: **G1** design avg R > 0 · **G2** hold-out adjusted CI lower bound > 0 · **G3** hold-out portfolio CAGR > 0.

| Variant | Trades/yr | Avg hold | Design n / avg R | Hold-out n / avg R | Hold-out adj. CI | Full PF | Full CAGR / maxDD | Hold-out portfolio CAGR / maxDD | G1 | G2 | G3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none/ema20/h40 | 1537 | 7.3 | 8808 / -0.025 | 5000 / 0.031 | [-0.131, 0.234] | 0.99 | -4.0% / -30.8% | -3.2% / -20.7% | ❌ | ❌ | ❌ |
| none/ema50/h40 | 871 | 13.8 | 5003 / 0.076 | 2818 / 0.231 | [-0.083, 0.624] | 1.25 | -0.4% / -19.9% | 0.4% / -10.2% | ✅ | ❌ | ✅ |
| none/ema50/h120 | 723 | 17.1 | 4204 / 0.148 | 2289 / 0.427 | [-0.038, 1.01] | 1.49 | 1.4% / -16.8% | 2.6% / -18.0% | ✅ | ❌ | ✅ |
| none/chandelier/h40 | 810 | 15.4 | 4644 / 0.043 | 2625 / 0.177 | [-0.13, 0.521] | 1.15 | 0.8% / -17.4% | 3.0% / -9.5% | ✅ | ❌ | ✅ |
| none/chandelier/h120 | 768 | 16.5 | 4419 / 0.053 | 2475 / 0.21 | [-0.117, 0.566] | 1.18 | 2.1% / -18.6% | 0.9% / -14.5% | ✅ | ❌ | ✅ |
| none/none/h120 | 347 | 43.0 | 2031 / 0.478 | 1079 / 1.171 | [0.163, 2.378] | 1.81 | 1.8% / -15.1% | 7.0% / -8.3% | ✅ | ✅ | ✅ |
| prior_high/ema20/h40 | 1136 | 8.9 | 6516 / 0.001 | 3688 / 0.091 | [-0.114, 0.323] | 1.08 | -4.5% / -34.1% | -6.6% / -23.3% | ✅ | ❌ | ❌ |
| prior_high/ema50/h40 | 680 | 16.5 | 3928 / 0.13 | 2182 / 0.357 | [-0.005, 0.744] | 1.36 | 2.9% / -14.3% | 1.6% / -10.6% | ✅ | ❌ | ✅ |
| prior_high/ema50/h120 | 562 | 21.0 | 3280 / 0.223 | 1762 / 0.614 | [0.086, 1.247] | 1.64 | 3.5% / -16.8% | 7.5% / -14.8% | ✅ | ✅ | ✅ |
| prior_high/chandelier/h40 | 683 | 16.9 | 3923 / 0.047 | 2213 / 0.239 | [-0.114, 0.596] | 1.18 | 0.2% / -16.2% | 2.4% / -12.2% | ✅ | ❌ | ✅ |
| prior_high/chandelier/h120 | 653 | 18.0 | 3752 / 0.068 | 2106 / 0.274 | [-0.143, 0.66] | 1.22 | 0.1% / -27.1% | 3.7% / -12.1% | ✅ | ❌ | ✅ |
| prior_high/none/h120 | 288 | 50.4 | 1685 / 0.64 | 897 / 1.438 | [0.289, 2.581] | 1.93 | 1.8% / -18.5% | 7.6% / -9.0% | ✅ | ✅ | ✅ |

**Promising (all gates): ['none/none/h120', 'prior_high/ema50/h120', 'prior_high/none/h120']**

Nifty buy-and-hold since 2023-01-01: {"cagr_pct": 5.6, "max_drawdown_pct": -15.8}

_Survivorship bias flatters every row. Passing all gates would justify paper trading only._