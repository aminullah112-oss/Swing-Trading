# Regime breakdown of the live variant

Variant: slow-exit v4 (paper-trading candidate). Nifty regime measured at each signal date with causal EMA50/EMA200. Descriptive analysis: nothing in the scanner is gated on it. Intervals are month-clustered bootstrap, **not** corrected for multiple comparisons.

| Regime at signal | Trades | Months | Win | Avg R (95% CI) | PF |
|---|---|---|---|---|---|
| Uptrend (above EMA50 and EMA200) | 3268 | 81 | 27% | +0.343 (+0.110..+0.582) | 1.59 |
| Pullback in uptrend (below EMA50, above EMA200) | 1131 | 64 | 25% | +0.383 (-0.070..+0.929) | 1.71 |
| Bounce in weak market (above EMA50, below EMA200) | 103 | 12 | 30% | +0.217 (-0.249..+0.931) | 1.33 |
| Downtrend (below both) | 592 | 40 | 29% | +0.418 (+0.072..+0.772) | 1.82 |

**Downtrend minus all other regimes (avg R):** +0.067 (95% CI -0.355..+0.495). The interval spans 0: this data cannot tell whether downtrends are better or worse for the live rules.
- design period only: +0.313 (CI -0.139..+0.828)
- holdout period only: -0.374 (CI -1.157..+0.430)

**Today (2026-10-23): Downtrend (below both).** Few independent downtrend months exist in 10 years, so wide intervals are expected; a result spanning zero means "unknown", not "safe".