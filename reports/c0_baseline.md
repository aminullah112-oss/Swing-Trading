# C0 baseline reproduction

Control C0 (`c0_hash` 5e7924a41b0ee220) reproduced from raw data. Universe U159_v2 (159 configured, 159 with data), data cutoff 2026-10-23, commit 3b1d452473.

Trades: 5094 · trades digest `16905339bff19a4d` (identical data and code give an identical digest).

| Slice | Trades | Win | Avg R | 95% CI (naive iid) | PF |
|---|---|---|---|---|---|
| All | 5094 | 0.266 | 0.358 | [np.float64(0.263), np.float64(0.454)] | 1.64 |
| Design (before 2023) | 3316 | 0.25 | 0.214 | [np.float64(0.118), np.float64(0.31)] | 1.38 |
| Hold-out (2023+) | 1778 | 0.295 | 0.627 | [np.float64(0.42), np.float64(0.834)] | 2.13 |

Portfolio, full period: `{"accepted": 303, "rejected_by_limits": 4791, "final_equity": 817245.0, "total_return_pct": 44.6, "cagr_pct": 4.2, "max_drawdown_pct": -14.4, "longest_drawdown_days": 528, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 34.8, "max_exposure_pct": 56.2, "time_in_cash_pct": 0.6, "avg_positions": 2.78}`

Portfolio, hold-out from a fresh start: `{"accepted": 140, "rejected_by_limits": 1638, "final_equity": 706249.0, "total_return_pct": 25.0, "cagr_pct": 6.0, "max_drawdown_pct": -15.7, "longest_drawdown_days": 593, "years": 3.81, "liquidity_limited_orders": 0, "avg_exposure_pct": 36.6, "max_exposure_pct": 56.6, "time_in_cash_pct": 0.1, "avg_positions": 2.77}`

**Reproduces the frozen baseline within tolerance.**