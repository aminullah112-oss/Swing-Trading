# Regime breakdown of the live variant

Variant: slow-exit v4 (paper-trading candidate). Nifty regime measured at each signal date with causal EMA50/EMA200. Descriptive analysis: nothing in the scanner is gated on it. Intervals are month-clustered bootstrap, **not** corrected for multiple comparisons.

| Regime at signal | Trades | Months | Win | Avg R (95% CI) | PF |
|---|---|---|---|---|---|
| Uptrend (above EMA50 and EMA200) | 3222 | 80 | 27% | +0.332 (+0.086..+0.595) | 1.57 |
| Pullback in uptrend (below EMA50, above EMA200) | 1155 | 64 | 25% | +0.387 (-0.067..+0.936) | 1.72 |
| Bounce in weak market (above EMA50, below EMA200) | 104 | 13 | 31% | +0.292 (-0.125..+1.036) | 1.45 |
| Downtrend (below both) | 594 | 39 | 29% | +0.446 (+0.106..+0.790) | 1.89 |

**Downtrend minus all other regimes (avg R):** +0.101 (95% CI -0.333..+0.516). The interval spans 0: this data cannot tell whether downtrends are better or worse for the live rules.
- design period only: +0.295 (CI -0.160..+0.779)
- holdout period only: -0.255 (CI -1.024..+0.528)

**Today (2026-11-20): Pullback in uptrend (below EMA50, above EMA200).** Few independent downtrend months exist in 10 years, so wide intervals are expected; a result spanning zero means "unknown", not "safe".