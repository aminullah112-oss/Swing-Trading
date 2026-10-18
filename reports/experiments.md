# Pre-registered experiments (PREREG_v1)

Universe U159_v2 (159 symbols with data, survivorship bias present), data cutoff 2026-10-16, commit feec4c33d0, pre-registration `b54dc824b8ed`. Realistic execution model; Bonferroni family of 8.

**C0 retained: yes.** Candidates adopted for forward testing: none.

| ID | Change | Design net (CAGR / maxDD / Calmar) | P1 sample | P2 net edge vs C0 (CI of daily diff, %) | P3 yrs better | P4 | Hold-out | Result |
|---|---|---|---|---|---|---|---|---|
| C0 | control | 3.13% / -12.73% / Calmar 0.246 | — | — | — | — | — | control |
| H1 | relative-strength filter | 11.32% / -9.57% / Calmar 1.183 | 2022 tr / 111 mo | [0.0043, 0.06084] | 6/8 | 11.32 | FAILED | failed at hold-out |
| H2 | near 52-week high | 3.7% / -11.0% / Calmar 0.336 | 2836 tr / 111 mo | [-0.0205, 0.02788] | 5/8 | 3.7 | not opened | failed (P2_net_edge_vs_C0) |
| H3 | liquidity floor | 5.37% / -10.08% / Calmar 0.532 | 5163 tr / 111 mo | [-0.01003, 0.02689] | 7/8 | 5.37 | not opened | failed (P2_net_edge_vs_C0) |
| H4 | volatility cap | 5.38% / -14.53% / Calmar 0.371 | 4606 tr / 110 mo | [-0.0117, 0.03127] | 6/8 | 5.38 | not opened | failed (P2_net_edge_vs_C0) |
| H5 | higher score bar | 4.0% / -12.84% / Calmar 0.312 | 3659 tr / 111 mo | [-0.01117, 0.01886] | 4/8 | 4.0 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| H6 | bull-regime only | 5.28% / -14.84% / Calmar 0.356 | 4743 tr / 99 mo | [-0.01803, 0.03373] | 6/8 | 5.28 | not opened | failed (P2_net_edge_vs_C0) |
| H7 | smaller positions, more of them | 4.97% / -12.25% / Calmar 0.406 | 5483 tr / 111 mo | [-0.009, 0.02371] | 6/8 | 4.97 | not opened | failed (P2_net_edge_vs_C0) |
| H8 | shorter maximum hold | 4.69% / -9.73% / Calmar 0.482 | 6024 tr / 111 mo | [-0.01619, 0.03014] | 4/8 | 4.69 | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |

## Score predictiveness (design window)

no reliable evidence that the 0-100 score predicts R: it is a qualifier, not a conviction measure. Spearman [-0.035, -0.064, -0.004], tercile gap [0.174, -0.082, 0.401].

## C0 versus same-universe benchmarks (design window; net of costs for C0)

| Series | CAGR % | MaxDD % | Calmar | Sharpe | Sortino |
|---|---|---|---|---|---|
| C0 (net, realistic costs) | 3.13 | -12.73 | 0.246 | 0.46 | 0.629 |
| Equal-weight universe | 24.47 | -38.01 | 0.644 | 1.416 | 1.906 |
| Equal-weight universe, exposure-matched (33.0% invested, cash 0%) | 7.83 | -14.2 | 0.551 | 1.416 | 1.906 |
| Equal-weight universe, volatility-matched to C0 (7.44%) | 10.56 | -18.64 | 0.566 | 1.416 | 1.906 |
| Momentum-30 replica | 31.41 | -37.41 | 0.84 | 1.549 | 2.127 |
| Momentum-30 replica, exposure-matched (33.0% invested, cash 0%) | 9.88 | -13.9 | 0.711 | 1.549 | 2.127 |
| Momentum-30 replica, volatility-matched to C0 (7.44%) | 11.64 | -16.13 | 0.721 | 1.549 | 2.127 |
| Nifty 50 | 11.55 | -38.44 | 0.3 | 0.761 | 1.046 |
| Nifty 50, exposure-matched (33.0% invested, cash 0%) | 3.98 | -14.33 | 0.278 | 0.761 | 1.046 |
| Nifty 50, volatility-matched to C0 (7.44%) | 5.39 | -19.1 | 0.282 | 0.761 | 1.046 |

Hold-out (2025+) figures for C0 and the benchmarks are in the JSON as reference only; C0 was selected using data that includes this period.

Failed variants stay in this report and in reports/experiments/history/. Passing a pre-registered test is a reason for forward paper testing, not for live capital.