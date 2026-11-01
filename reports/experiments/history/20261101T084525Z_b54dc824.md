# Pre-registered experiments (PREREG_v1)

Universe U159_v2 (159 symbols with data, survivorship bias present), data cutoff 2026-10-30, commit 5af68a6232, pre-registration `b54dc824b8ed`. Realistic execution model; Bonferroni family of 8.

**C0 retained: yes.** Candidates adopted for forward testing: none.

| ID | Change | Design net (CAGR / maxDD / Calmar) | P1 sample | P2 net edge vs C0 (CI of daily diff, %) | P3 yrs better | P4 | Hold-out | Result |
|---|---|---|---|---|---|---|---|---|
| C0 | control | 6.22% / -12.79% / Calmar 0.486 | — | — | — | — | — | control |
| H1 | relative-strength filter | 9.83% / -10.94% / Calmar 0.898 | 2023 tr / 110 mo | [-0.01065, 0.03842] | 5/8 | 9.83 | not opened | failed (P2_net_edge_vs_C0) |
| H2 | near 52-week high | 4.68% / -11.49% / Calmar 0.407 | 2829 tr / 110 mo | [-0.02582, 0.01458] | 3/8 | 4.68 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| H3 | liquidity floor | 2.54% / -15.23% / Calmar 0.167 | 5134 tr / 110 mo | [-0.03347, 0.00451] | 1/8 | 2.54 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| H4 | volatility cap | 5.09% / -14.44% / Calmar 0.352 | 4576 tr / 109 mo | [-0.02385, 0.0173] | 2/8 | 5.09 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| H5 | higher score bar | 7.48% / -10.61% / Calmar 0.705 | 3640 tr / 110 mo | [-0.01325, 0.02466] | 4/8 | 7.48 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| H6 | bull-regime only | 7.6% / -16.37% / Calmar 0.464 | 4708 tr / 98 mo | [-0.02037, 0.02604] | 4/8 | 7.6 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| H7 | smaller positions, more of them | 5.3% / -12.77% / Calmar 0.415 | 5451 tr / 110 mo | [-0.02205, 0.01292] | 4/8 | 5.3 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| H8 | shorter maximum hold | 4.55% / -14.9% / Calmar 0.305 | 5994 tr / 110 mo | [-0.02559, 0.01373] | 5/8 | 4.55 | not opened | failed (P2_net_edge_vs_C0) |

## Score predictiveness (design window)

no reliable evidence that the 0-100 score predicts R: it is a qualifier, not a conviction measure. Spearman [-0.035, -0.063, -0.005], tercile gap [0.163, -0.105, 0.375].

## C0 versus same-universe benchmarks (design window; net of costs for C0)

| Series | CAGR % | MaxDD % | Calmar | Sharpe | Sortino |
|---|---|---|---|---|---|
| C0 (net, realistic costs) | 6.22 | -12.79 | 0.486 | 0.845 | 1.186 |
| Equal-weight universe | 23.87 | -38.01 | 0.628 | 1.385 | 1.863 |
| Equal-weight universe, exposure-matched (34.1% invested, cash 0%) | 7.92 | -14.64 | 0.541 | 1.385 | 1.863 |
| Equal-weight universe, volatility-matched to C0 (7.64%) | 10.6 | -19.09 | 0.555 | 1.385 | 1.863 |
| Momentum-30 replica | 31.41 | -37.41 | 0.84 | 1.549 | 2.127 |
| Momentum-30 replica, exposure-matched (34.1% invested, cash 0%) | 10.22 | -14.33 | 0.713 | 1.549 | 2.127 |
| Momentum-30 replica, volatility-matched to C0 (7.64%) | 11.96 | -16.54 | 0.723 | 1.549 | 2.127 |
| Nifty 50 | 11.02 | -38.44 | 0.287 | 0.73 | 1.003 |
| Nifty 50, exposure-matched (34.1% invested, cash 0%) | 3.94 | -14.78 | 0.267 | 0.73 | 1.003 |
| Nifty 50, volatility-matched to C0 (7.64%) | 5.29 | -19.55 | 0.271 | 0.73 | 1.003 |

Hold-out (2025+) figures for C0 and the benchmarks are in the JSON as reference only; C0 was selected using data that includes this period.

Failed variants stay in this report and in reports/experiments/history/. Passing a pre-registered test is a reason for forward paper testing, not for live capital.