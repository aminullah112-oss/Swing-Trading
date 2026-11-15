# C0 baseline reproduction

Control C0 (`c0_hash` 5e7924a41b0ee220) reproduced from raw data. Universe U159_v2 (159 configured, 159 with data), data cutoff 2026-11-13, commit dba85c31d7.

Trades: 5073 · trades digest `b06d3a52421510c5` (identical data and code give an identical digest).

| Slice | Trades | Win | Avg R | 95% CI (naive iid) | PF |
|---|---|---|---|---|---|
| All | 5073 | 0.268 | 0.363 | [np.float64(0.267), np.float64(0.459)] | 1.65 |
| Design (before 2023) | 3274 | 0.253 | 0.212 | [np.float64(0.115), np.float64(0.308)] | 1.38 |
| Hold-out (2023+) | 1799 | 0.297 | 0.637 | [np.float64(0.432), np.float64(0.843)] | 2.15 |

Portfolio, full period: `{"accepted": 314, "rejected_by_limits": 4759, "final_equity": 806735.0, "total_return_pct": 42.8, "cagr_pct": 4.0, "max_drawdown_pct": -16.7, "longest_drawdown_days": 607, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 33.8, "max_exposure_pct": 57.0, "time_in_cash_pct": 0.8, "avg_positions": 2.77}`

Portfolio, hold-out from a fresh start: `{"accepted": 141, "rejected_by_limits": 1658, "final_equity": 749855.0, "total_return_pct": 32.7, "cagr_pct": 7.6, "max_drawdown_pct": -14.8, "longest_drawdown_days": 607, "years": 3.86, "liquidity_limited_orders": 0, "avg_exposure_pct": 36.3, "max_exposure_pct": 56.6, "time_in_cash_pct": 0.3, "avg_positions": 2.78}`

**Reproduces the frozen baseline within tolerance.**