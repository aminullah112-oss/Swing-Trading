# C0 baseline reproduction

Control C0 (`c0_hash` 5e7924a41b0ee220) reproduced from raw data. Universe U159_v2 (159 configured, 159 with data), data cutoff 2026-10-30, commit 5af68a6232.

Trades: 5099 · trades digest `33c0b89931e27926` (identical data and code give an identical digest).

| Slice | Trades | Win | Avg R | 95% CI (naive iid) | PF |
|---|---|---|---|---|---|
| All | 5099 | 0.266 | 0.353 | [np.float64(0.257), np.float64(0.448)] | 1.63 |
| Design (before 2023) | 3308 | 0.25 | 0.204 | [np.float64(0.108), np.float64(0.299)] | 1.36 |
| Hold-out (2023+) | 1791 | 0.295 | 0.628 | [np.float64(0.422), np.float64(0.833)] | 2.13 |

Portfolio, full period: `{"accepted": 321, "rejected_by_limits": 4778, "final_equity": 808391.0, "total_return_pct": 43.1, "cagr_pct": 4.1, "max_drawdown_pct": -14.2, "longest_drawdown_days": 772, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 34.1, "max_exposure_pct": 55.8, "time_in_cash_pct": 0.8, "avg_positions": 2.77}`

Portfolio, hold-out from a fresh start: `{"accepted": 141, "rejected_by_limits": 1650, "final_equity": 753765.0, "total_return_pct": 33.4, "cagr_pct": 7.8, "max_drawdown_pct": -14.8, "longest_drawdown_days": 598, "years": 3.82, "liquidity_limited_orders": 0, "avg_exposure_pct": 36.8, "max_exposure_pct": 56.6, "time_in_cash_pct": 0.3, "avg_positions": 2.78}`

**Reproduces the frozen baseline within tolerance.**