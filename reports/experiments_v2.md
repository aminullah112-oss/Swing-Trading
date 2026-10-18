# Pre-registered selection experiments (PREREG_v2)

Universe U159_v2 (159 symbols, survivorship bias present), data cutoff 2026-10-16, pre-registration `469617ab5554`. Realistic costs; Bonferroni over 13 tests. **C0 retained: yes.** Candidates: none.

| ID | Change | Design net (CAGR / maxDD / Calmar) | Trades / months | Passed via | Hold-out | Result |
|---|---|---|---|---|---|---|
| C0 | control | 3.13% / -12.73% / Calmar 0.246 | — | — | — | control |
| V2-1 | sector cap | 3.0% / -12.43% / Calmar 0.241 | 5483 / 111 | — | not opened | failed (P2_net_edge_vs_C0, P3_consistency) |
| V2-2 | preferred-tier stack | 9.54% / -12.92% / Calmar 0.738 | 816 / 98 | — | not opened | failed (P2_net_edge_vs_C0) |
| V2-3 | volatility-scaled risk | 4.24% / -10.93% / Calmar 0.388 | 5483 / 111 | risk route | FAILED | failed at hold-out |

## Already tested, failed, not retested

- admit same-day candidates in momentum-rank order (reports/benchmarks.md (H2)): failed: Calmar 0.21 design / 0.42 hold-out vs baseline 0.67 / 0.42; CI includes zero. Live default: display the rank only; allocation order stays C0's
- halve risk when the Nifty is below its EMA200 (reports/benchmarks.md (H3)): failed: Calmar 0.03 design / 0.29 hold-out; CI includes zero. Live default: off

Every run is kept in reports/experiments/history/. A pass is a reason for forward paper testing only.