# Regime breakdown of the live variant

Variant: slow-exit v4 (paper-trading candidate). Nifty regime measured at each signal date with causal EMA50/EMA200. Descriptive analysis: nothing in the scanner is gated on it. Intervals are month-clustered bootstrap, **not** corrected for multiple comparisons.

| Regime at signal | Trades | Months | Win | Avg R (95% CI) | PF |
|---|---|---|---|---|---|
| Uptrend (above EMA50 and EMA200) | 3254 | 81 | 27% | +0.341 (+0.115..+0.578) | 1.59 |
| Pullback in uptrend (below EMA50, above EMA200) | 1104 | 64 | 25% | +0.382 (-0.076..+0.923) | 1.71 |
| Bounce in weak market (above EMA50, below EMA200) | 100 | 12 | 30% | +0.260 (-0.198..+0.931) | 1.4 |
| Downtrend (below both) | 584 | 40 | 29% | +0.440 (+0.090..+0.799) | 1.88 |

**Downtrend minus all other regimes (avg R):** +0.090 (95% CI -0.327..+0.518). The interval spans 0: this data cannot tell whether downtrends are better or worse for the live rules.
- design period only: +0.310 (CI -0.146..+0.819)
- holdout period only: -0.307 (CI -1.087..+0.489)

**Today (2026-10-12): Downtrend (below both).** Few independent downtrend months exist in 10 years, so wide intervals are expected; a result spanning zero means "unknown", not "safe".