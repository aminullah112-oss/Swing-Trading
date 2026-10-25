# Exit/entry variant grid

Trials run: **12** (fixed in advance). Hold-out = entries from 2023-01-01. CIs are month-clustered bootstrap intervals (trades entered in the same month share market moves, so they are not independent), at Bonferroni-adjusted confidence for 12 trials (alpha = 0.05/12).

Gates: **G1** design avg R > 0 · **G2** hold-out adjusted CI lower bound > 0 · **G3** hold-out portfolio CAGR > 0.

| Variant | Trades/yr | Avg hold | Design n / avg R | Hold-out n / avg R | Hold-out adj. CI | Full PF | Full CAGR / maxDD | Hold-out portfolio CAGR / maxDD | G1 | G2 | G3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none/ema20/h40 | 1553 | 7.3 | 8871 / -0.025 | 5082 / 0.034 | [-0.13, 0.237] | 0.99 | -3.4% / -30.7% | -1.4% / -19.6% | ❌ | ❌ | ❌ |
| none/ema50/h40 | 881 | 13.7 | 5047 / 0.074 | 2860 / 0.236 | [-0.08, 0.633] | 1.25 | -0.1% / -19.3% | -1.7% / -15.2% | ✅ | ❌ | ❌ |
| none/ema50/h120 | 730 | 17.1 | 4242 / 0.144 | 2312 / 0.435 | [-0.033, 1.034] | 1.49 | 0.2% / -17.8% | 3.6% / -16.1% | ✅ | ❌ | ✅ |
| none/chandelier/h40 | 818 | 15.4 | 4671 / 0.045 | 2670 / 0.182 | [-0.134, 0.519] | 1.15 | 3.0% / -14.6% | 2.2% / -12.4% | ✅ | ❌ | ✅ |
| none/chandelier/h120 | 775 | 16.5 | 4447 / 0.054 | 2517 / 0.216 | [-0.118, 0.583] | 1.18 | 2.4% / -15.3% | 2.2% / -12.2% | ✅ | ❌ | ✅ |
| none/none/h120 | 350 | 42.9 | 2052 / 0.481 | 1092 / 1.181 | [0.142, 2.396] | 1.81 | 4.8% / -16.6% | 6.9% / -8.3% | ✅ | ✅ | ✅ |
| prior_high/ema20/h40 | 1150 | 8.9 | 6576 / -0.001 | 3744 / 0.097 | [-0.111, 0.33] | 1.09 | -6.2% / -44.7% | -6.5% / -23.1% | ❌ | ❌ | ❌ |
| prior_high/ema50/h40 | 688 | 16.5 | 3965 / 0.127 | 2210 / 0.364 | [-0.005, 0.762] | 1.36 | 4.2% / -12.7% | 1.2% / -11.5% | ✅ | ❌ | ✅ |
| prior_high/ema50/h120 | 568 | 21.0 | 3316 / 0.214 | 1778 / 0.627 | [0.084, 1.279] | 1.64 | 4.2% / -14.4% | 6.0% / -15.7% | ✅ | ✅ | ✅ |
| prior_high/chandelier/h40 | 692 | 16.9 | 3956 / 0.045 | 2250 / 0.246 | [-0.106, 0.608] | 1.18 | -0.4% / -15.0% | 0.9% / -17.5% | ✅ | ❌ | ✅ |
| prior_high/chandelier/h120 | 661 | 18.0 | 3785 / 0.064 | 2142 / 0.281 | [-0.145, 0.681] | 1.22 | 0.0% / -17.4% | 2.6% / -14.3% | ✅ | ❌ | ✅ |
| prior_high/none/h120 | 292 | 50.2 | 1710 / 0.631 | 911 / 1.444 | [0.262, 2.606] | 1.92 | 2.3% / -15.4% | 7.1% / -9.0% | ✅ | ✅ | ✅ |

**Promising (all gates): ['none/none/h120', 'prior_high/ema50/h120', 'prior_high/none/h120']**

Nifty buy-and-hold since 2023-01-01: {"cagr_pct": 5.9, "max_drawdown_pct": -15.8}

_Survivorship bias flatters every row. Passing all gates would justify paper trading only._