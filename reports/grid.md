# Exit/entry variant grid

Trials run: **12** (fixed in advance). Hold-out = entries from 2023-01-01. CIs are month-clustered bootstrap intervals (trades entered in the same month share market moves, so they are not independent), at Bonferroni-adjusted confidence for 12 trials (alpha = 0.05/12).

Gates: **G1** design avg R > 0 · **G2** hold-out adjusted CI lower bound > 0 · **G3** hold-out portfolio CAGR > 0.

| Variant | Trades/yr | Avg hold | Design n / avg R | Hold-out n / avg R | Hold-out adj. CI | Full PF | Full CAGR / maxDD | Hold-out portfolio CAGR / maxDD | G1 | G2 | G3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none/ema20/h40 | 1542 | 7.3 | 8753 / -0.024 | 5107 / 0.04 | [-0.114, 0.238] | 1.0 | -3.2% / -32.8% | 0.3% / -18.6% | ❌ | ❌ | ✅ |
| none/ema50/h40 | 874 | 13.7 | 4981 / 0.079 | 2881 / 0.246 | [-0.045, 0.64] | 1.27 | 0.8% / -18.9% | -1.7% / -15.1% | ✅ | ❌ | ❌ |
| none/ema50/h120 | 723 | 17.2 | 4171 / 0.149 | 2332 / 0.447 | [-0.013, 1.058] | 1.52 | 0.5% / -22.2% | 1.1% / -22.3% | ✅ | ❌ | ✅ |
| none/chandelier/h40 | 811 | 15.4 | 4605 / 0.047 | 2690 / 0.193 | [-0.13, 0.535] | 1.16 | 2.2% / -13.1% | 3.6% / -12.3% | ✅ | ❌ | ✅ |
| none/chandelier/h120 | 769 | 16.5 | 4376 / 0.057 | 2537 / 0.226 | [-0.132, 0.611] | 1.19 | 4.9% / -11.5% | 3.5% / -11.4% | ✅ | ❌ | ✅ |
| none/none/h120 | 345 | 43.3 | 1996 / 0.488 | 1105 / 1.216 | [0.133, 2.402] | 1.84 | 2.6% / -20.6% | 7.6% / -8.3% | ✅ | ✅ | ✅ |
| prior_high/ema20/h40 | 1141 | 8.9 | 6488 / -0.002 | 3769 / 0.103 | [-0.09, 0.349] | 1.09 | -3.3% / -33.7% | -4.9% / -23.0% | ❌ | ❌ | ❌ |
| prior_high/ema50/h40 | 683 | 16.5 | 3907 / 0.126 | 2233 / 0.372 | [-0.022, 0.783] | 1.37 | 4.3% / -15.1% | 3.0% / -12.4% | ✅ | ❌ | ✅ |
| prior_high/ema50/h120 | 564 | 21.0 | 3274 / 0.212 | 1799 / 0.637 | [0.091, 1.251] | 1.65 | 4.0% / -16.7% | 7.6% / -14.8% | ✅ | ✅ | ✅ |
| prior_high/chandelier/h40 | 686 | 16.9 | 3897 / 0.047 | 2271 / 0.255 | [-0.103, 0.603] | 1.19 | 2.1% / -13.4% | 4.0% / -10.5% | ✅ | ❌ | ✅ |
| prior_high/chandelier/h120 | 655 | 18.0 | 3731 / 0.063 | 2161 / 0.291 | [-0.064, 0.641] | 1.23 | 0.7% / -22.1% | 1.8% / -17.3% | ✅ | ❌ | ✅ |
| prior_high/none/h120 | 289 | 50.2 | 1677 / 0.623 | 925 / 1.478 | [0.48, 2.63] | 1.94 | 4.7% / -13.7% | 8.3% / -9.0% | ✅ | ✅ | ✅ |

**Promising (all gates): ['none/none/h120', 'prior_high/ema50/h120', 'prior_high/none/h120']**

Nifty buy-and-hold since 2023-01-01: {"cagr_pct": 8.7, "max_drawdown_pct": -15.8}

_Survivorship bias flatters every row. Passing all gates would justify paper trading only._