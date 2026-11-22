# C0 baseline reproduction

Control C0 (`c0_hash` 5e7924a41b0ee220) reproduced from raw data. Universe U159_v2 (159 configured, 159 with data), data cutoff 2026-11-20, commit 59d8498514.

Trades: 5075 · trades digest `b5caa2b2f0c5290a` (identical data and code give an identical digest).

| Slice | Trades | Win | Avg R | 95% CI (naive iid) | PF |
|---|---|---|---|---|---|
| All | 5075 | 0.267 | 0.357 | [np.float64(0.261), np.float64(0.453)] | 1.64 |
| Design (before 2023) | 3272 | 0.251 | 0.202 | [np.float64(0.105), np.float64(0.298)] | 1.36 |
| Hold-out (2023+) | 1803 | 0.297 | 0.639 | [np.float64(0.434), np.float64(0.844)] | 2.16 |

Portfolio, full period: `{"accepted": 302, "rejected_by_limits": 4773, "final_equity": 836811.0, "total_return_pct": 48.1, "cagr_pct": 4.5, "max_drawdown_pct": -16.2, "longest_drawdown_days": 1006, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 34.4, "max_exposure_pct": 56.4, "time_in_cash_pct": 0.8, "avg_positions": 2.78}`

Portfolio, hold-out from a fresh start: `{"accepted": 142, "rejected_by_limits": 1661, "final_equity": 739780.0, "total_return_pct": 30.9, "cagr_pct": 7.2, "max_drawdown_pct": -14.8, "longest_drawdown_days": 612, "years": 3.88, "liquidity_limited_orders": 0, "avg_exposure_pct": 36.3, "max_exposure_pct": 56.6, "time_in_cash_pct": 0.3, "avg_positions": 2.78}`

**Reproduces the frozen baseline within tolerance.**