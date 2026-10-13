# Score diagnosis

Fixed reference configurations; see research.py docstring for caveats.

## Score diagnosis: baseline: next-open, ema20 exit, 40d

Design n=8866, hold-out n=5067.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [-0.019, -0.046, 0.011]
- hold-out: [-0.017, -0.044, 0.013]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.025, -0.115, 0.175]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.373 | 12 | -0.277 |
| rsi | 38-45 | 8 | 723 | -0.060 | 484 | -0.103 |
| rsi | 45-62 | 20 | 7279 | -0.020 | 4105 | +0.020 |
| rsi | 62-70 | 13 | 741 | -0.047 | 413 | +0.311 |
| rsi | 70-76 | 4 | 113 | +0.124 | 53 | +0.411 |
| volr | 0-0.7 | 3 | 1879 | -0.037 | 1092 | +0.007 |
| volr | 0.7-1.2 | 7 | 3546 | -0.040 | 2017 | +0.059 |
| volr | 1.2-1.8 | 13 | 1892 | +0.011 | 1119 | -0.042 |
| volr | 1.8+ | 20 | 1549 | -0.012 | 839 | +0.120 |
| nrising | 1 | 3 | 8866 | -0.024 | 5067 | +0.036 |
| near52 | 0 | 0 | 909 | +0.007 | 545 | +0.177 |
| near52 | 1 | 3 | 7957 | -0.027 | 4522 | +0.019 |
| setup | PULLBACK_EMA20 | 20 | 4076 | -0.060 | 2392 | -0.001 |
| setup | PULLBACK_EMA50 | 14 | 2942 | -0.016 | 1667 | -0.050 |
| setup | COMPRESSION | 12 | 60 | -0.092 | 95 | +0.324 |
| setup | BREAKOUT_CONT | 10 | 436 | -0.040 | 179 | +0.265 |
| setup | TRENDING | 6 | 1352 | +0.077 | 734 | +0.259 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.4, 0.3)
- volr: (0.6, 0.4)
- setup: (-0.5, -0.5)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.066, -0.106, -0.028]
- top minus bottom tercile avg R: [0.095, -0.072, 0.3]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.

## Score diagnosis: slow exit: next-open, chandelier(3 ATR), 120d

Design n=4449, hold-out n=2513.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [0.007, -0.024, 0.041]
- hold-out: [-0.005, -0.038, 0.038]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.043, -0.169, 0.28]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.687 | 9 | -0.712 |
| rsi | 38-45 | 8 | 447 | +0.054 | 276 | +0.179 |
| rsi | 45-62 | 20 | 3287 | +0.077 | 1866 | +0.178 |
| rsi | 62-70 | 13 | 610 | -0.002 | 320 | +0.487 |
| rsi | 70-76 | 4 | 95 | -0.324 | 42 | +0.643 |
| volr | 0-0.7 | 3 | 788 | +0.030 | 481 | +0.218 |
| volr | 0.7-1.2 | 7 | 1752 | +0.072 | 989 | +0.225 |
| volr | 1.2-1.8 | 13 | 1044 | +0.024 | 589 | +0.185 |
| volr | 1.8+ | 20 | 865 | +0.073 | 454 | +0.265 |
| nrising | 1 | 3 | 4449 | +0.053 | 2513 | +0.222 |
| near52 | 0 | 0 | 453 | +0.187 | 218 | +0.087 |
| near52 | 1 | 3 | 3996 | +0.038 | 2295 | +0.234 |
| setup | PULLBACK_EMA20 | 20 | 2148 | +0.047 | 1323 | +0.202 |
| setup | PULLBACK_EMA50 | 14 | 1139 | +0.062 | 610 | +0.106 |
| setup | COMPRESSION | 12 | 37 | -0.020 | 65 | +0.145 |
| setup | BREAKOUT_CONT | 10 | 304 | +0.002 | 128 | +0.493 |
| setup | TRENDING | 6 | 821 | +0.080 | 387 | +0.394 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.9, 0.1)
- volr: (0.4, 0.4)
- setup: (-0.2, -0.6)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.021, -0.055, 0.014]
- top minus bottom tercile avg R: [-0.172, -0.345, 0.031]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.
