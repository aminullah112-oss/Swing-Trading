# Score diagnosis

Fixed reference configurations; see research.py docstring for caveats.

## Score diagnosis: baseline: next-open, ema20 exit, 40d

Design n=8828, hold-out n=5003.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [-0.019, -0.046, 0.011]
- hold-out: [-0.013, -0.04, 0.016]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.029, -0.104, 0.168]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.373 | 12 | -0.277 |
| rsi | 38-45 | 8 | 720 | -0.060 | 477 | -0.102 |
| rsi | 45-62 | 20 | 7247 | -0.021 | 4054 | +0.016 |
| rsi | 62-70 | 13 | 738 | -0.045 | 408 | +0.289 |
| rsi | 70-76 | 4 | 113 | +0.124 | 52 | +0.407 |
| volr | 0-0.7 | 3 | 1872 | -0.038 | 1084 | +0.008 |
| volr | 0.7-1.2 | 7 | 3529 | -0.042 | 1985 | +0.046 |
| volr | 1.2-1.8 | 13 | 1883 | +0.012 | 1105 | -0.041 |
| volr | 1.8+ | 20 | 1544 | -0.012 | 829 | +0.120 |
| nrising | 1 | 3 | 8828 | -0.025 | 5003 | +0.031 |
| near52 | 0 | 0 | 898 | +0.006 | 540 | +0.157 |
| near52 | 1 | 3 | 7930 | -0.028 | 4463 | +0.015 |
| setup | PULLBACK_EMA20 | 20 | 4060 | -0.060 | 2367 | -0.004 |
| setup | PULLBACK_EMA50 | 14 | 2928 | -0.015 | 1644 | -0.054 |
| setup | COMPRESSION | 12 | 60 | -0.092 | 95 | +0.324 |
| setup | BREAKOUT_CONT | 10 | 434 | -0.035 | 177 | +0.246 |
| setup | TRENDING | 6 | 1346 | +0.069 | 720 | +0.246 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.4, 0.3)
- volr: (0.6, 0.4)
- setup: (-0.5, -0.5)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.074, -0.113, -0.036]
- top minus bottom tercile avg R: [0.106, -0.07, 0.31]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.

## Score diagnosis: slow exit: next-open, chandelier(3 ATR), 120d

Design n=4425, hold-out n=2478.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [0.008, -0.025, 0.041]
- hold-out: [-0.002, -0.035, 0.038]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.022, -0.192, 0.261]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.687 | 9 | -0.712 |
| rsi | 38-45 | 8 | 443 | +0.038 | 270 | +0.183 |
| rsi | 45-62 | 20 | 3271 | +0.079 | 1841 | +0.162 |
| rsi | 62-70 | 13 | 606 | +0.004 | 316 | +0.475 |
| rsi | 70-76 | 4 | 95 | -0.324 | 42 | +0.643 |
| volr | 0-0.7 | 3 | 788 | +0.030 | 474 | +0.192 |
| volr | 0.7-1.2 | 7 | 1739 | +0.074 | 975 | +0.202 |
| volr | 1.2-1.8 | 13 | 1037 | +0.031 | 579 | +0.199 |
| volr | 1.8+ | 20 | 861 | +0.064 | 450 | +0.257 |
| nrising | 1 | 3 | 4425 | +0.054 | 2478 | +0.209 |
| near52 | 0 | 0 | 444 | +0.176 | 215 | +0.018 |
| near52 | 1 | 3 | 3981 | +0.040 | 2263 | +0.228 |
| setup | PULLBACK_EMA20 | 20 | 2137 | +0.050 | 1306 | +0.180 |
| setup | PULLBACK_EMA50 | 14 | 1132 | +0.054 | 601 | +0.109 |
| setup | COMPRESSION | 12 | 37 | -0.020 | 65 | +0.145 |
| setup | BREAKOUT_CONT | 10 | 302 | +0.010 | 128 | +0.493 |
| setup | TRENDING | 6 | 817 | +0.084 | 378 | +0.385 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.9, 0.1)
- volr: (0.4, 0.8)
- setup: (-0.2, -0.6)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.019, -0.054, 0.018]
- top minus bottom tercile avg R: [-0.167, -0.365, 0.043]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.
