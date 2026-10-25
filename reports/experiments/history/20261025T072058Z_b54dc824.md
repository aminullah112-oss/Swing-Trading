# Pre-registered experiments (PREREG_v1)

Universe U159_v2 (159 symbols with data, survivorship bias present), data cutoff 2026-10-23, commit 3b1d452473, pre-registration `b54dc824b8ed`. Realistic execution model; Bonferroni family of 8.

**C0 retained: yes.** Candidates adopted for forward testing: none.

| ID | Change | Design net (CAGR / maxDD / Calmar) | P1 sample | P2 net edge vs C0 (CI of daily diff, %) | P3 yrs better | P4 | Hold-out | Result |
|---|---|---|---|---|---|---|---|---|
| C0 | control | 3.83% / -13.09% / Calmar 0.293 | — | — | — | — | — | control |
| H1 | relative-strength filter | 9.23% / -13.06% / Calmar 0.707 | 2025 tr / 110 mo | [-0.00739, 0.05181] | 7/8 | 9.23 | not opened | failed (P2_net_edge_vs_C0) |
| H2 | near 52-week high | 5.0% / -12.08% / Calmar 0.414 | 2831 tr / 110 mo | [-0.02006, 0.03041] | 4/8 | 5.0 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| H3 | liquidity floor | 2.79% / -16.23% / Calmar 0.172 | 5143 tr / 110 mo | [-0.02166, 0.01419] | 5/8 | 2.79 | not opened | failed (P2_net_edge_vs_C0) |
| H4 | volatility cap | 3.78% / -13.75% / Calmar 0.275 | 4584 tr / 109 mo | [-0.02287, 0.02273] | 2/8 | 3.78 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| H5 | higher score bar | 6.31% / -10.49% / Calmar 0.602 | 3643 tr / 110 mo | [-0.01054, 0.02821] | 5/8 | 6.31 | not opened | failed (P2_net_edge_vs_C0) |
| H6 | bull-regime only | 5.62% / -22.69% / Calmar 0.248 | 4704 tr / 98 mo | [-0.02327, 0.03302] | 4/8 | 5.62 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| H7 | smaller positions, more of them | 4.5% / -10.85% / Calmar 0.414 | 5461 tr / 110 mo | [-0.01516, 0.01791] | 4/8 | 4.5 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| H8 | shorter maximum hold | 3.7% / -10.04% / Calmar 0.368 | 6004 tr / 110 mo | [-0.02249, 0.02357] | 5/8 | 3.7 | not opened | failed (P2_net_edge_vs_C0) |

## Score predictiveness (design window)

no reliable evidence that the 0-100 score predicts R: it is a qualifier, not a conviction measure. Spearman [-0.033, -0.063, -0.004], tercile gap [0.179, -0.09, 0.394].

## C0 versus same-universe benchmarks (design window; net of costs for C0)

| Series | CAGR % | MaxDD % | Calmar | Sharpe | Sortino |
|---|---|---|---|---|---|
| C0 (net, realistic costs) | 3.83 | -13.09 | 0.293 | 0.539 | 0.75 |
| Equal-weight universe | 24.05 | -38.01 | 0.633 | 1.394 | 1.875 |
| Equal-weight universe, exposure-matched (32.5% invested, cash 0%) | 7.59 | -13.99 | 0.542 | 1.394 | 1.875 |
| Equal-weight universe, volatility-matched to C0 (7.67%) | 10.72 | -19.16 | 0.559 | 1.394 | 1.875 |
| Momentum-30 replica | 31.41 | -37.41 | 0.84 | 1.549 | 2.127 |
| Momentum-30 replica, exposure-matched (32.5% invested, cash 0%) | 9.73 | -13.7 | 0.71 | 1.549 | 2.127 |
| Momentum-30 replica, volatility-matched to C0 (7.67%) | 12.01 | -16.6 | 0.724 | 1.549 | 2.127 |
| Nifty 50 | 11.25 | -38.44 | 0.293 | 0.743 | 1.021 |
| Nifty 50, exposure-matched (32.5% invested, cash 0%) | 3.83 | -14.13 | 0.271 | 0.743 | 1.021 |
| Nifty 50, volatility-matched to C0 (7.67%) | 5.42 | -19.63 | 0.276 | 0.743 | 1.021 |

Hold-out (2025+) figures for C0 and the benchmarks are in the JSON as reference only; C0 was selected using data that includes this period.

Failed variants stay in this report and in reports/experiments/history/. Passing a pre-registered test is a reason for forward paper testing, not for live capital.