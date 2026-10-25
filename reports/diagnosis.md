# Score diagnosis

Fixed reference configurations; see research.py docstring for caveats.

## Score diagnosis: baseline: next-open, ema20 exit, 40d

Design n=8871, hold-out n=5082.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [-0.015, -0.04, 0.015]
- hold-out: [-0.017, -0.044, 0.012]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.024, -0.116, 0.174]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.373 | 12 | -0.277 |
| rsi | 38-45 | 8 | 722 | -0.062 | 485 | -0.102 |
| rsi | 45-62 | 20 | 7289 | -0.019 | 4118 | +0.018 |
| rsi | 62-70 | 13 | 734 | -0.061 | 414 | +0.309 |
| rsi | 70-76 | 4 | 116 | +0.102 | 53 | +0.411 |
| volr | 0-0.7 | 3 | 1870 | -0.048 | 1096 | +0.005 |
| volr | 0.7-1.2 | 7 | 3549 | -0.037 | 2025 | +0.055 |
| volr | 1.2-1.8 | 13 | 1898 | +0.011 | 1121 | -0.041 |
| volr | 1.8+ | 20 | 1554 | -0.012 | 840 | +0.120 |
| nrising | 1 | 3 | 8871 | -0.025 | 5082 | +0.034 |
| near52 | 0 | 0 | 900 | -0.006 | 546 | +0.173 |
| near52 | 1 | 3 | 7971 | -0.027 | 4536 | +0.017 |
| setup | PULLBACK_EMA20 | 20 | 4084 | -0.060 | 2400 | -0.004 |
| setup | PULLBACK_EMA50 | 14 | 2952 | -0.017 | 1673 | -0.052 |
| setup | COMPRESSION | 12 | 60 | +0.031 | 95 | +0.324 |
| setup | BREAKOUT_CONT | 10 | 433 | -0.070 | 180 | +0.261 |
| setup | TRENDING | 6 | 1342 | +0.077 | 734 | +0.257 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.4, 0.3)
- volr: (0.8, 0.4)
- setup: (-0.4, -0.5)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.062, -0.102, -0.02]
- top minus bottom tercile avg R: [0.074, -0.076, 0.245]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.

## Score diagnosis: slow exit: next-open, chandelier(3 ATR), 120d

Design n=4447, hold-out n=2517.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [0.013, -0.018, 0.044]
- hold-out: [-0.005, -0.038, 0.038]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.041, -0.173, 0.274]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.687 | 9 | -0.712 |
| rsi | 38-45 | 8 | 449 | +0.061 | 277 | +0.167 |
| rsi | 45-62 | 20 | 3284 | +0.082 | 1869 | +0.172 |
| rsi | 62-70 | 13 | 606 | -0.028 | 320 | +0.487 |
| rsi | 70-76 | 4 | 98 | -0.334 | 42 | +0.643 |
| volr | 0-0.7 | 3 | 778 | +0.034 | 481 | +0.209 |
| volr | 0.7-1.2 | 7 | 1748 | +0.073 | 991 | +0.219 |
| volr | 1.2-1.8 | 13 | 1051 | +0.031 | 591 | +0.182 |
| volr | 1.8+ | 20 | 870 | +0.062 | 454 | +0.262 |
| nrising | 1 | 3 | 4447 | +0.054 | 2517 | +0.216 |
| near52 | 0 | 0 | 450 | +0.197 | 218 | +0.083 |
| near52 | 1 | 3 | 3997 | +0.038 | 2299 | +0.229 |
| setup | PULLBACK_EMA20 | 20 | 2154 | +0.054 | 1325 | +0.195 |
| setup | PULLBACK_EMA50 | 14 | 1144 | +0.073 | 612 | +0.098 |
| setup | COMPRESSION | 12 | 36 | -0.016 | 65 | +0.145 |
| setup | BREAKOUT_CONT | 10 | 304 | -0.039 | 128 | +0.493 |
| setup | TRENDING | 6 | 809 | +0.067 | 387 | +0.394 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.9, 0.3)
- volr: (0.0, 0.4)
- setup: (0.2, -0.6)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.021, -0.056, 0.014]
- top minus bottom tercile avg R: [-0.134, -0.34, 0.12]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.
