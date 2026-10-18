# Score diagnosis

Fixed reference configurations; see research.py docstring for caveats.

## Score diagnosis: baseline: next-open, ema20 exit, 40d

Design n=8850, hold-out n=5061.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [-0.02, -0.045, 0.01]
- hold-out: [-0.017, -0.044, 0.012]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.026, -0.109, 0.175]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.373 | 12 | -0.277 |
| rsi | 38-45 | 8 | 719 | -0.064 | 483 | -0.104 |
| rsi | 45-62 | 20 | 7279 | -0.020 | 4101 | +0.019 |
| rsi | 62-70 | 13 | 728 | -0.046 | 412 | +0.313 |
| rsi | 70-76 | 4 | 114 | +0.118 | 53 | +0.411 |
| volr | 0-0.7 | 3 | 1881 | -0.044 | 1093 | +0.007 |
| volr | 0.7-1.2 | 7 | 3532 | -0.038 | 2014 | +0.056 |
| volr | 1.2-1.8 | 13 | 1890 | +0.009 | 1116 | -0.041 |
| volr | 1.8+ | 20 | 1547 | -0.012 | 838 | +0.120 |
| nrising | 1 | 3 | 8850 | -0.024 | 5061 | +0.035 |
| near52 | 0 | 0 | 893 | +0.001 | 544 | +0.175 |
| near52 | 1 | 3 | 7957 | -0.027 | 4517 | +0.018 |
| setup | PULLBACK_EMA20 | 20 | 4072 | -0.061 | 2393 | -0.002 |
| setup | PULLBACK_EMA50 | 14 | 2947 | -0.016 | 1662 | -0.050 |
| setup | COMPRESSION | 12 | 61 | -0.094 | 95 | +0.324 |
| setup | BREAKOUT_CONT | 10 | 432 | -0.050 | 179 | +0.265 |
| setup | TRENDING | 6 | 1338 | +0.081 | 732 | +0.252 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.4, 0.3)
- volr: (0.8, 0.4)
- setup: (-0.5, -0.5)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.066, -0.106, -0.026]
- top minus bottom tercile avg R: [0.084, -0.075, 0.263]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.

## Score diagnosis: slow exit: next-open, chandelier(3 ATR), 120d

Design n=4431, hold-out n=2508.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [0.011, -0.021, 0.043]
- hold-out: [-0.006, -0.039, 0.036]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.043, -0.167, 0.273]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.687 | 9 | -0.712 |
| rsi | 38-45 | 8 | 446 | +0.072 | 275 | +0.163 |
| rsi | 45-62 | 20 | 3280 | +0.075 | 1863 | +0.177 |
| rsi | 62-70 | 13 | 599 | +0.010 | 319 | +0.490 |
| rsi | 70-76 | 4 | 96 | -0.331 | 42 | +0.643 |
| volr | 0-0.7 | 3 | 792 | +0.014 | 480 | +0.216 |
| volr | 0.7-1.2 | 7 | 1740 | +0.071 | 985 | +0.226 |
| volr | 1.2-1.8 | 13 | 1043 | +0.038 | 590 | +0.174 |
| volr | 1.8+ | 20 | 856 | +0.082 | 453 | +0.271 |
| nrising | 1 | 3 | 4431 | +0.055 | 2508 | +0.220 |
| near52 | 0 | 0 | 441 | +0.179 | 217 | +0.090 |
| near52 | 1 | 3 | 3990 | +0.042 | 2291 | +0.232 |
| setup | PULLBACK_EMA20 | 20 | 2141 | +0.058 | 1321 | +0.199 |
| setup | PULLBACK_EMA50 | 14 | 1143 | +0.049 | 608 | +0.102 |
| setup | COMPRESSION | 12 | 37 | -0.023 | 65 | +0.145 |
| setup | BREAKOUT_CONT | 10 | 300 | -0.004 | 128 | +0.493 |
| setup | TRENDING | 6 | 810 | +0.082 | 386 | +0.397 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.9, 0.3)
- volr: (0.8, 0.4)
- setup: (-0.1, -0.6)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.015, -0.05, 0.021]
- top minus bottom tercile avg R: [-0.135, -0.37, 0.101]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.
