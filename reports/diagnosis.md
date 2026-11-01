# Score diagnosis

Fixed reference configurations; see research.py docstring for caveats.

## Score diagnosis: baseline: next-open, ema20 exit, 40d

Design n=8846, hold-out n=5095.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [-0.018, -0.047, 0.009]
- hold-out: [-0.016, -0.041, 0.011]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.028, -0.112, 0.177]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 9 | -0.366 | 12 | -0.277 |
| rsi | 38-45 | 8 | 717 | -0.064 | 485 | -0.102 |
| rsi | 45-62 | 20 | 7277 | -0.025 | 4129 | +0.021 |
| rsi | 62-70 | 13 | 723 | -0.047 | 416 | +0.308 |
| rsi | 70-76 | 4 | 120 | +0.080 | 53 | +0.411 |
| volr | 0-0.7 | 3 | 1874 | -0.045 | 1098 | +0.006 |
| volr | 0.7-1.2 | 7 | 3551 | -0.042 | 2029 | +0.056 |
| volr | 1.2-1.8 | 13 | 1887 | +0.001 | 1125 | -0.036 |
| volr | 1.8+ | 20 | 1534 | -0.017 | 843 | +0.121 |
| nrising | 1 | 3 | 8846 | -0.029 | 5095 | +0.036 |
| near52 | 0 | 0 | 904 | -0.018 | 547 | +0.173 |
| near52 | 1 | 3 | 7942 | -0.030 | 4548 | +0.019 |
| setup | PULLBACK_EMA20 | 20 | 4073 | -0.063 | 2406 | +0.000 |
| setup | PULLBACK_EMA50 | 14 | 2943 | -0.022 | 1676 | -0.051 |
| setup | COMPRESSION | 12 | 60 | -0.086 | 95 | +0.324 |
| setup | BREAKOUT_CONT | 10 | 430 | -0.058 | 182 | +0.255 |
| setup | TRENDING | 6 | 1340 | +0.072 | 736 | +0.257 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.4, 0.3)
- volr: (0.8, 0.4)
- setup: (-0.5, -0.6)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.066, -0.107, -0.026]
- top minus bottom tercile avg R: [0.078, -0.081, 0.268]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.

## Score diagnosis: slow exit: next-open, chandelier(3 ATR), 120d

Design n=4431, hold-out n=2527.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [0.01, -0.025, 0.045]
- hold-out: [-0.005, -0.04, 0.032]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.036, -0.177, 0.277]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 9 | -0.634 | 9 | -0.712 |
| rsi | 38-45 | 8 | 449 | +0.043 | 277 | +0.180 |
| rsi | 45-62 | 20 | 3278 | +0.066 | 1877 | +0.173 |
| rsi | 62-70 | 13 | 594 | +0.018 | 322 | +0.482 |
| rsi | 70-76 | 4 | 101 | -0.344 | 42 | +0.643 |
| volr | 0-0.7 | 3 | 784 | +0.011 | 483 | +0.207 |
| volr | 0.7-1.2 | 7 | 1757 | +0.067 | 994 | +0.219 |
| volr | 1.2-1.8 | 13 | 1042 | +0.027 | 594 | +0.187 |
| volr | 1.8+ | 20 | 848 | +0.061 | 456 | +0.266 |
| nrising | 1 | 3 | 4431 | +0.046 | 2527 | +0.217 |
| near52 | 0 | 0 | 452 | +0.179 | 218 | +0.083 |
| near52 | 1 | 3 | 3979 | +0.031 | 2309 | +0.230 |
| setup | PULLBACK_EMA20 | 20 | 2147 | +0.043 | 1329 | +0.196 |
| setup | PULLBACK_EMA50 | 14 | 1140 | +0.053 | 615 | +0.106 |
| setup | COMPRESSION | 12 | 36 | +0.156 | 65 | +0.145 |
| setup | BREAKOUT_CONT | 10 | 299 | -0.018 | 130 | +0.478 |
| setup | TRENDING | 6 | 809 | +0.066 | 388 | +0.393 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.9, 0.1)
- volr: (0.4, 0.4)
- setup: (-0.2, -0.6)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.015, -0.053, 0.02]
- top minus bottom tercile avg R: [-0.149, -0.367, 0.086]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.
