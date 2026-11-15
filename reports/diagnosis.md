# Score diagnosis

Fixed reference configurations; see research.py docstring for caveats.

## Score diagnosis: baseline: next-open, ema20 exit, 40d

Design n=8753, hold-out n=5107.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [-0.016, -0.045, 0.009]
- hold-out: [-0.015, -0.043, 0.015]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.033, -0.109, 0.175]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.381 | 12 | -0.277 |
| rsi | 38-45 | 8 | 719 | -0.061 | 485 | -0.102 |
| rsi | 45-62 | 20 | 7198 | -0.020 | 4137 | +0.025 |
| rsi | 62-70 | 13 | 716 | -0.050 | 419 | +0.321 |
| rsi | 70-76 | 4 | 110 | +0.179 | 54 | +0.393 |
| volr | 0-0.7 | 3 | 1856 | -0.045 | 1101 | +0.006 |
| volr | 0.7-1.2 | 7 | 3521 | -0.031 | 2034 | +0.062 |
| volr | 1.2-1.8 | 13 | 1853 | +0.007 | 1126 | -0.033 |
| volr | 1.8+ | 20 | 1523 | -0.020 | 846 | +0.131 |
| nrising | 1 | 3 | 8753 | -0.024 | 5107 | +0.040 |
| near52 | 0 | 0 | 889 | -0.016 | 550 | +0.171 |
| near52 | 1 | 3 | 7864 | -0.025 | 4557 | +0.024 |
| setup | PULLBACK_EMA20 | 20 | 4024 | -0.057 | 2411 | +0.004 |
| setup | PULLBACK_EMA50 | 14 | 2933 | -0.021 | 1678 | -0.047 |
| setup | COMPRESSION | 12 | 57 | -0.086 | 95 | +0.324 |
| setup | BREAKOUT_CONT | 10 | 416 | -0.061 | 183 | +0.303 |
| setup | TRENDING | 6 | 1323 | +0.086 | 740 | +0.253 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.4, 0.3)
- volr: (0.8, 0.4)
- setup: (-0.2, -0.5)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.067, -0.104, -0.029]
- top minus bottom tercile avg R: [0.066, -0.076, 0.212]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.

## Score diagnosis: slow exit: next-open, chandelier(3 ATR), 120d

Design n=4376, hold-out n=2537.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [0.011, -0.023, 0.046]
- hold-out: [-0.007, -0.041, 0.034]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.001, -0.231, 0.224]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 9 | -0.634 | 9 | -0.712 |
| rsi | 38-45 | 8 | 452 | +0.063 | 277 | +0.197 |
| rsi | 45-62 | 20 | 3237 | +0.078 | 1882 | +0.181 |
| rsi | 62-70 | 13 | 587 | +0.011 | 326 | +0.489 |
| rsi | 70-76 | 4 | 91 | -0.312 | 43 | +0.616 |
| volr | 0-0.7 | 3 | 775 | +0.016 | 485 | +0.207 |
| volr | 0.7-1.2 | 7 | 1732 | +0.084 | 998 | +0.224 |
| volr | 1.2-1.8 | 13 | 1027 | +0.025 | 596 | +0.208 |
| volr | 1.8+ | 20 | 842 | +0.080 | 458 | +0.275 |
| nrising | 1 | 3 | 4376 | +0.057 | 2537 | +0.226 |
| near52 | 0 | 0 | 440 | +0.173 | 220 | +0.077 |
| near52 | 1 | 3 | 3936 | +0.045 | 2317 | +0.241 |
| setup | PULLBACK_EMA20 | 20 | 2122 | +0.056 | 1331 | +0.198 |
| setup | PULLBACK_EMA50 | 14 | 1141 | +0.060 | 617 | +0.133 |
| setup | COMPRESSION | 12 | 33 | +0.037 | 65 | +0.145 |
| setup | BREAKOUT_CONT | 10 | 286 | -0.011 | 132 | +0.519 |
| setup | TRENDING | 6 | 794 | +0.083 | 392 | +0.386 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.9, 0.1)
- volr: (0.4, 0.8)
- setup: (-0.1, -0.6)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.015, -0.053, 0.026]
- top minus bottom tercile avg R: [-0.126, -0.334, 0.093]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.
