# Amendments log

Changes to the research machinery that were made after PREREG_v1/v2 were written. None of them was made after seeing a result on real data:
the Backtest workflow has not produced stamped v1/v2/v3 results yet. They are logged so nobody has to take that on trust.

## 2026-10-15: independent code review (PREREG_v3 written the same day)

A reviewer with no stake in the code read the backtester and the new robustness module. Findings and what was done:

| # | Finding | Direction of bias | Action |
|---|---|---|---|
| F1 | Backtest sized positions and measured R from the signal-close stop distance. The live screener sizes from the buy-stop (higher), so the backtest took about 1.26x the intended risk (measured on reports/trades_trigger.csv: mean (entry-stop)/plan_risk 1.26) | Flattering | New `Config.risk_basis='entry'`, used by `strategy.research_config()` for every experiment and the robustness battery. Legacy `backtest_config()` is unchanged so the frozen C0 baseline still reproduces; its numbers carry this bias and are labelled as such |
| F2 | Nifty is a price index, stocks are dividend-adjusted | Flattering to C0 | 1.3%/yr dividend yield added back in R-BENCH (assumption stated in the report) |
| F3 | Selection bias: C0 was chosen from a 12-variant grid on data including 2023+ | Flattering | The 12 grid trials are counted in the multiple-testing family (n_tests 17 -> 29). The in-sample selection effect itself is not removable and is a stated limit |
| F4 | Month clusters understate dependence of overlapping trades | Flattering | Quarter clusters for R-CI and R-BENCH. PREREG_v1/v2 keep their registered month clusters |
| F5 | Monte Carlo block (21 days) shorter than holding periods; R-HO compared a 2-year drawdown with a 10-year p95 | Flattering | Block 63 days; R-HO uses paths as short as the hold-out |
| F6 | "Design" numbers used post-design prices when late-2024 trades exited in 2025 | Leak | `experiments.design_view()` truncates the data at design_end for the design window in v1, v2 and v3 |
| F7 | Survivorship haircut modelled delistings only | Flattering | Added uniform R-haircut (inclusion bias); both must pass |
| F8 | Weak gates (R-EXEC passes at +0.1% CAGR; random-miss optimistic; R-NULL-A easy) | Flattering | Harsh case must keep half of base CAGR; added a gap-up-miss scenario; R-NULL-A flagged as easy, verdict needs both nulls |
| F9 | Entries were sized on the same day's closing equity | Small, favourable | `Config.sizing_equity='prior_day'` in `research_config` |

Not changed, and why:
- The forward paper ledger keeps `realistic_config` (R measured from the signal-close stop). Its INR results are unaffected by the R unit, and changing a live record's definition mid-stream would break its hash-chained history. Treat ledger R as relative to the signal-close stop distance.
- PREREG_v1/v2 files are untouched (their hashes still verify). Their "realistic execution model" now resolves to `research_config`; this log is the record of that.
- The frozen C0 baseline (`control/`) is still the legacy definition so reproduction can be checked. It is optimistic by the F1 amount.
