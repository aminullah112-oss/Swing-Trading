# Regime breakdown of the live variant

Variant: slow-exit v4 (paper-trading candidate). Nifty regime measured at each signal date with causal EMA50/EMA200. Descriptive analysis: nothing in the scanner is gated on it. Intervals are month-clustered bootstrap, **not** corrected for multiple comparisons.

| Regime at signal | Trades | Months | Win | Avg R (95% CI) | PF |
|---|---|---|---|---|---|
| Uptrend (above EMA50 and EMA200) | 3263 | 80 | 27% | +0.331 (+0.094..+0.581) | 1.57 |
| Pullback in uptrend (below EMA50, above EMA200) | 1131 | 64 | 25% | +0.384 (-0.084..+0.905) | 1.71 |
| Bounce in weak market (above EMA50, below EMA200) | 104 | 12 | 30% | +0.272 (-0.128..+0.931) | 1.41 |
| Downtrend (below both) | 601 | 40 | 29% | +0.423 (+0.097..+0.783) | 1.85 |

**Downtrend minus all other regimes (avg R):** +0.080 (95% CI -0.369..+0.479). The interval spans 0: this data cannot tell whether downtrends are better or worse for the live rules.
- design period only: +0.338 (CI -0.114..+0.850)
- holdout period only: -0.374 (CI -1.149..+0.394)

**Today (2026-10-30): Downtrend (below both).** Few independent downtrend months exist in 10 years, so wide intervals are expected; a result spanning zero means "unknown", not "safe".