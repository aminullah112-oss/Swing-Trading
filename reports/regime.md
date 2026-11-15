# Regime breakdown of the live variant

Variant: slow-exit v4 (paper-trading candidate). Nifty regime measured at each signal date with causal EMA50/EMA200. Descriptive analysis: nothing in the scanner is gated on it. Intervals are month-clustered bootstrap, **not** corrected for multiple comparisons.

| Regime at signal | Trades | Months | Win | Avg R (95% CI) | PF |
|---|---|---|---|---|---|
| Uptrend (above EMA50 and EMA200) | 3202 | 80 | 27% | +0.338 (+0.105..+0.588) | 1.59 |
| Pullback in uptrend (below EMA50, above EMA200) | 1173 | 65 | 26% | +0.401 (-0.023..+0.962) | 1.75 |
| Bounce in weak market (above EMA50, below EMA200) | 104 | 13 | 31% | +0.310 (-0.106..+1.036) | 1.48 |
| Downtrend (below both) | 594 | 39 | 29% | +0.427 (+0.092..+0.773) | 1.85 |

**Downtrend minus all other regimes (avg R):** +0.073 (95% CI -0.338..+0.494). The interval spans 0: this data cannot tell whether downtrends are better or worse for the live rules.
- design period only: +0.267 (CI -0.179..+0.768)
- holdout period only: -0.280 (CI -1.045..+0.499)

**Today (2026-11-13): Pullback in uptrend (below EMA50, above EMA200).** Few independent downtrend months exist in 10 years, so wide intervals are expected; a result spanning zero means "unknown", not "safe".