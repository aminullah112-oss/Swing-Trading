# Score diagnosis

Fixed reference configurations; see research.py docstring for caveats.

## Score diagnosis: baseline: next-open, ema20 exit, 40d

Design n=8812, hold-out n=5100.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [-0.018, -0.047, 0.008]
- hold-out: [-0.015, -0.043, 0.015]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.031, -0.111, 0.173]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 9 | -0.366 | 12 | -0.277 |
| rsi | 38-45 | 8 | 719 | -0.064 | 485 | -0.102 |
| rsi | 45-62 | 20 | 7254 | -0.023 | 4132 | +0.023 |
| rsi | 62-70 | 13 | 716 | -0.050 | 418 | +0.315 |
| rsi | 70-76 | 4 | 114 | +0.129 | 53 | +0.411 |
| volr | 0-0.7 | 3 | 1862 | -0.042 | 1098 | +0.006 |
| volr | 0.7-1.2 | 7 | 3544 | -0.039 | 2032 | +0.059 |
| volr | 1.2-1.8 | 13 | 1874 | +0.002 | 1126 | -0.033 |
| volr | 1.8+ | 20 | 1532 | -0.015 | 844 | +0.127 |
| nrising | 1 | 3 | 8812 | -0.027 | 5100 | +0.038 |
| near52 | 0 | 0 | 900 | -0.010 | 549 | +0.172 |
| near52 | 1 | 3 | 7912 | -0.029 | 4551 | +0.022 |
| setup | PULLBACK_EMA20 | 20 | 4069 | -0.059 | 2408 | +0.003 |
| setup | PULLBACK_EMA50 | 14 | 2932 | -0.022 | 1676 | -0.049 |
| setup | COMPRESSION | 12 | 58 | -0.085 | 95 | +0.324 |
| setup | BREAKOUT_CONT | 10 | 425 | -0.051 | 183 | +0.285 |
| setup | TRENDING | 6 | 1328 | +0.070 | 738 | +0.256 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.4, 0.3)
- volr: (0.8, 0.4)
- setup: (-0.5, -0.5)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.067, -0.105, -0.031]
- top minus bottom tercile avg R: [0.085, -0.075, 0.262]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.

## Score diagnosis: slow exit: next-open, chandelier(3 ATR), 120d

Design n=4403, hold-out n=2532.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [0.006, -0.028, 0.042]
- hold-out: [-0.006, -0.04, 0.036]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.033, -0.181, 0.24]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 9 | -0.634 | 9 | -0.712 |
| rsi | 38-45 | 8 | 447 | +0.038 | 277 | +0.187 |
| rsi | 45-62 | 20 | 3265 | +0.075 | 1879 | +0.178 |
| rsi | 62-70 | 13 | 587 | +0.010 | 325 | +0.488 |
| rsi | 70-76 | 4 | 95 | -0.312 | 42 | +0.643 |
| volr | 0-0.7 | 3 | 776 | +0.045 | 484 | +0.205 |
| volr | 0.7-1.2 | 7 | 1746 | +0.066 | 995 | +0.224 |
| volr | 1.2-1.8 | 13 | 1033 | +0.021 | 596 | +0.198 |
| volr | 1.8+ | 20 | 848 | +0.071 | 457 | +0.275 |
| nrising | 1 | 3 | 4403 | +0.053 | 2532 | +0.224 |
| near52 | 0 | 0 | 448 | +0.189 | 219 | +0.088 |
| near52 | 1 | 3 | 3955 | +0.038 | 2313 | +0.236 |
| setup | PULLBACK_EMA20 | 20 | 2144 | +0.050 | 1331 | +0.199 |
| setup | PULLBACK_EMA50 | 14 | 1133 | +0.060 | 615 | +0.115 |
| setup | COMPRESSION | 12 | 34 | +0.018 | 65 | +0.145 |
| setup | BREAKOUT_CONT | 10 | 293 | +0.002 | 132 | +0.511 |
| setup | TRENDING | 6 | 799 | +0.071 | 389 | +0.395 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.9, 0.1)
- volr: (0.4, 0.4)
- setup: (-0.1, -0.6)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.019, -0.057, 0.019]
- top minus bottom tercile avg R: [-0.149, -0.371, 0.068]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.
