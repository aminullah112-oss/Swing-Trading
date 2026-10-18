# Regime breakdown of the live variant

Variant: slow-exit v4 (paper-trading candidate). Nifty regime measured at each signal date with causal EMA50/EMA200. Descriptive analysis: nothing in the scanner is gated on it. Intervals are month-clustered bootstrap, **not** corrected for multiple comparisons.

| Regime at signal | Trades | Months | Win | Avg R (95% CI) | PF |
|---|---|---|---|---|---|
| Uptrend (above EMA50 and EMA200) | 3259 | 81 | 27% | +0.351 (+0.119..+0.596) | 1.61 |
| Pullback in uptrend (below EMA50, above EMA200) | 1121 | 64 | 25% | +0.382 (-0.083..+0.940) | 1.71 |
| Bounce in weak market (above EMA50, below EMA200) | 103 | 12 | 30% | +0.240 (-0.205..+0.907) | 1.37 |
| Downtrend (below both) | 588 | 40 | 29% | +0.434 (+0.080..+0.788) | 1.87 |

**Downtrend minus all other regimes (avg R):** +0.078 (95% CI -0.342..+0.503). The interval spans 0: this data cannot tell whether downtrends are better or worse for the live rules.
- design period only: +0.320 (CI -0.139..+0.823)
- holdout period only: -0.352 (CI -1.139..+0.452)

**Today (2026-10-16): Downtrend (below both).** Few independent downtrend months exist in 10 years, so wide intervals are expected; a result spanning zero means "unknown", not "safe".