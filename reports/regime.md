# Regime breakdown of the live variant

Variant: slow-exit v4 (paper-trading candidate). Nifty regime measured at each signal date with causal EMA50/EMA200. Descriptive analysis: nothing in the scanner is gated on it. Intervals are month-clustered bootstrap, **not** corrected for multiple comparisons.

| Regime at signal | Trades | Months | Win | Avg R (95% CI) | PF |
|---|---|---|---|---|---|
| Uptrend (above EMA50 and EMA200) | 3279 | 81 | 27% | +0.345 (+0.116..+0.595) | 1.6 |
| Pullback in uptrend (below EMA50, above EMA200) | 1123 | 64 | 25% | +0.391 (-0.077..+0.952) | 1.73 |
| Bounce in weak market (above EMA50, below EMA200) | 101 | 12 | 31% | +0.276 (-0.187..+0.962) | 1.43 |
| Downtrend (below both) | 585 | 40 | 29% | +0.433 (+0.087..+0.789) | 1.87 |

**Downtrend minus all other regimes (avg R):** +0.077 (95% CI -0.350..+0.508). The interval spans 0: this data cannot tell whether downtrends are better or worse for the live rules.
- design period only: +0.309 (CI -0.147..+0.819)
- holdout period only: -0.340 (CI -1.124..+0.464)

**Today (2026-10-12): Downtrend (below both).** Few independent downtrend months exist in 10 years, so wide intervals are expected; a result spanning zero means "unknown", not "safe".