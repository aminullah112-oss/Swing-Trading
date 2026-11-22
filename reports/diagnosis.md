# Score diagnosis

Fixed reference configurations; see research.py docstring for caveats.

## Score diagnosis: baseline: next-open, ema20 exit, 40d

Design n=8718, hold-out n=5119.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [-0.016, -0.045, 0.01]
- hold-out: [-0.015, -0.043, 0.015]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.034, -0.107, 0.175]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 10 | -0.381 | 12 | -0.277 |
| rsi | 38-45 | 8 | 706 | -0.064 | 487 | -0.102 |
| rsi | 45-62 | 20 | 7176 | -0.024 | 4145 | +0.024 |
| rsi | 62-70 | 13 | 715 | -0.055 | 421 | +0.325 |
| rsi | 70-76 | 4 | 111 | +0.170 | 54 | +0.400 |
| volr | 0-0.7 | 3 | 1838 | -0.048 | 1106 | +0.004 |
| volr | 0.7-1.2 | 7 | 3510 | -0.040 | 2037 | +0.062 |
| volr | 1.2-1.8 | 13 | 1856 | +0.009 | 1128 | -0.035 |
| volr | 1.8+ | 20 | 1514 | -0.020 | 848 | +0.134 |
| nrising | 1 | 3 | 8718 | -0.028 | 5119 | +0.040 |
| near52 | 0 | 0 | 889 | -0.015 | 554 | +0.168 |
| near52 | 1 | 3 | 7829 | -0.029 | 4565 | +0.025 |
| setup | PULLBACK_EMA20 | 20 | 3997 | -0.062 | 2418 | +0.004 |
| setup | PULLBACK_EMA50 | 14 | 2908 | -0.022 | 1680 | -0.047 |
| setup | COMPRESSION | 12 | 57 | -0.086 | 95 | +0.324 |
| setup | BREAKOUT_CONT | 10 | 419 | -0.053 | 185 | +0.315 |
| setup | TRENDING | 6 | 1337 | +0.072 | 741 | +0.252 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.4, 0.3)
- volr: (0.8, 0.4)
- setup: (-0.5, -0.5)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.064, -0.103, -0.026]
- top minus bottom tercile avg R: [0.061, -0.092, 0.23]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.

## Score diagnosis: slow exit: next-open, chandelier(3 ATR), 120d

Design n=4375, hold-out n=2548.

**Does the live score predict R?** Spearman (point, month-clustered 95% CI):
- design: [0.013, -0.022, 0.048]
- hold-out: [-0.006, -0.04, 0.035]
- hold-out top-tercile minus bottom-tercile avg R (point, CI): [0.024, -0.198, 0.229]

**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.

| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |
|---|---|---|---|---|---|---|
| rsi | 0-38 | 0 | 9 | -0.634 | 9 | -0.712 |
| rsi | 38-45 | 8 | 441 | +0.048 | 278 | +0.197 |
| rsi | 45-62 | 20 | 3241 | +0.068 | 1890 | +0.182 |
| rsi | 62-70 | 13 | 592 | -0.003 | 328 | +0.481 |
| rsi | 70-76 | 4 | 92 | -0.320 | 43 | +0.624 |
| volr | 0-0.7 | 3 | 767 | +0.013 | 487 | +0.205 |
| volr | 0.7-1.2 | 7 | 1735 | +0.066 | 1002 | +0.225 |
| volr | 1.2-1.8 | 13 | 1032 | +0.023 | 599 | +0.207 |
| volr | 1.8+ | 20 | 841 | +0.065 | 460 | +0.277 |
| nrising | 1 | 3 | 4375 | +0.047 | 2548 | +0.226 |
| near52 | 0 | 0 | 444 | +0.164 | 223 | +0.071 |
| near52 | 1 | 3 | 3931 | +0.033 | 2325 | +0.241 |
| setup | PULLBACK_EMA20 | 20 | 2099 | +0.050 | 1338 | +0.196 |
| setup | PULLBACK_EMA50 | 14 | 1140 | +0.045 | 618 | +0.139 |
| setup | COMPRESSION | 12 | 33 | +0.037 | 65 | +0.145 |
| setup | BREAKOUT_CONT | 10 | 291 | -0.020 | 134 | +0.500 |
| setup | TRENDING | 6 | 812 | +0.064 | 393 | +0.385 |

Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:
- rsi: (0.9, 0.1)
- volr: (0.4, 0.8)
- setup: (0.0, -0.6)

**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:
- Spearman: [-0.021, -0.057, 0.019]
- top minus bottom tercile avg R: [-0.176, -0.378, 0.046]

Compare with the live score above. If the learned score's CI also spans 0, no component of the score carries a dependable signal and the ranking should be dropped rather than refitted.
