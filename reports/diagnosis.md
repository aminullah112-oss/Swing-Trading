# Score diagnosis

Fixed reference configurations; see research.py docstring for caveats.

## Score diagnosis: baseline: next-open, ema20 exit, 40d

Design n=8808, hold-out n=5000.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [-0.02, -0.046, 0.011]
- hold-out: [-0.013, -0.04, 0.015]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.029, -0.104, 0.168]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.373 | 12 | -0.277 |
| rsi | 38-45 | 8 | 720 | -0.060 | 477 | -0.102 |
| rsi | 45-62 | 20 | 7229 | -0.021 | 4051 | +0.017 |
| rsi | 62-70 | 13 | 736 | -0.045 | 408 | +0.289 |
| rsi | 70-76 | 4 | 113 | +0.124 | 52 | +0.407 |
| volr | 0-0.7 | 3 | 1867 | -0.038 | 1082 | +0.009 |
| volr | 0.7-1.2 | 7 | 3522 | -0.041 | 1984 | +0.046 |
| volr | 1.2-1.8 | 13 | 1879 | +0.011 | 1105 | -0.042 |
| volr | 1.8+ | 20 | 1540 | -0.016 | 829 | +0.120 |
| nrising | 1 | 3 | 8808 | -0.025 | 5000 | +0.031 |
| near52 | 0 | 0 | 895 | -0.002 | 540 | +0.158 |
| near52 | 1 | 3 | 7913 | -0.027 | 4460 | +0.015 |
| setup | PULLBACK_EMA20 | 20 | 4051 | -0.060 | 2366 | -0.004 |
| setup | PULLBACK_EMA50 | 14 | 2923 | -0.015 | 1644 | -0.054 |
| setup | COMPRESSION | 12 | 60 | -0.092 | 95 | +0.324 |
| setup | BREAKOUT_CONT | 10 | 429 | -0.048 | 177 | +0.246 |
| setup | TRENDING | 6 | 1345 | +0.071 | 718 | +0.247 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.4, 0.3)
- volr: (0.6, 0.4)
- setup: (-0.5, -0.6)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.068, -0.108, -0.028]
- top minus bottom tercile avg R: [0.078, -0.087, 0.281]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.

## Score diagnosis: slow exit: next-open, chandelier(3 ATR), 120d

Design n=4419, hold-out n=2475.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [0.007, -0.025, 0.04]
- hold-out: [-0.001, -0.033, 0.038]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.025, -0.189, 0.265]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.687 | 9 | -0.712 |
| rsi | 38-45 | 8 | 443 | +0.038 | 270 | +0.179 |
| rsi | 45-62 | 20 | 3268 | +0.077 | 1839 | +0.164 |
| rsi | 62-70 | 13 | 603 | +0.006 | 315 | +0.477 |
| rsi | 70-76 | 4 | 95 | -0.324 | 42 | +0.643 |
| volr | 0-0.7 | 3 | 787 | +0.031 | 473 | +0.198 |
| volr | 0.7-1.2 | 7 | 1736 | +0.074 | 973 | +0.203 |
| volr | 1.2-1.8 | 13 | 1037 | +0.031 | 579 | +0.198 |
| volr | 1.8+ | 20 | 859 | +0.058 | 450 | +0.254 |
| nrising | 1 | 3 | 4419 | +0.053 | 2475 | +0.210 |
| near52 | 0 | 0 | 442 | +0.160 | 215 | +0.018 |
| near52 | 1 | 3 | 3977 | +0.041 | 2260 | +0.228 |
| setup | PULLBACK_EMA20 | 20 | 2134 | +0.048 | 1306 | +0.182 |
| setup | PULLBACK_EMA50 | 14 | 1132 | +0.054 | 601 | +0.107 |
| setup | COMPRESSION | 12 | 37 | -0.020 | 65 | +0.145 |
| setup | BREAKOUT_CONT | 10 | 300 | -0.008 | 128 | +0.493 |
| setup | TRENDING | 6 | 816 | +0.092 | 375 | +0.389 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.9, 0.1)
- volr: (0.0, 0.4)
- setup: (-0.2, -0.6)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.015, -0.049, 0.018]
- top minus bottom tercile avg R: [-0.185, -0.392, 0.04]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.
