# Regime breakdown of the live variant

Variant: slow-exit v4 (paper-trading candidate). Nifty regime measured at each signal date with causal EMA50/EMA200. Descriptive analysis: nothing in the scanner is gated on it. Intervals are month-clustered bootstrap, **not** corrected for multiple comparisons.

| Regime at signal | Trades | Months | Win | Avg R (95% CI) | PF |
|---|---|---|---|---|---|
| Uptrend (above EMA50 and EMA200) | 3242 | 80 | 27% | +0.337 (+0.100..+0.585) | 1.59 |
| Pullback in uptrend (below EMA50, above EMA200) | 1133 | 65 | 25% | +0.383 (-0.056..+0.956) | 1.71 |
| Bounce in weak market (above EMA50, below EMA200) | 104 | 13 | 31% | +0.284 (-0.125..+0.973) | 1.44 |
| Downtrend (below both) | 604 | 40 | 30% | +0.439 (+0.111..+0.790) | 1.88 |

**Downtrend minus all other regimes (avg R):** +0.091 (95% CI -0.320..+0.499). The interval spans 0: this data cannot tell whether downtrends are better or worse for the live rules.
- design period only: +0.319 (CI -0.133..+0.834)
- holdout period only: -0.317 (CI -1.068..+0.466)

**Today (2026-11-06): Pullback in uptrend (below EMA50, above EMA200).** Few independent downtrend months exist in 10 years, so wide intervals are expected; a result spanning zero means "unknown", not "safe".