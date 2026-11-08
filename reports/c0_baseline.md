# C0 baseline reproduction

Control C0 (`c0_hash` 5e7924a41b0ee220) reproduced from raw data. Universe U159_v2 (159 configured, 159 with data), data cutoff 2026-11-06, commit b1ea309cf7.

Trades: 5083 · trades digest `368edb94eb5b403d` (identical data and code give an identical digest).

| Slice | Trades | Win | Avg R | 95% CI (naive iid) | PF |
|---|---|---|---|---|---|
| All | 5083 | 0.268 | 0.358 | [np.float64(0.262), np.float64(0.454)] | 1.64 |
| Design (before 2023) | 3291 | 0.251 | 0.207 | [np.float64(0.111), np.float64(0.303)] | 1.37 |
| Hold-out (2023+) | 1792 | 0.298 | 0.635 | [np.float64(0.43), np.float64(0.841)] | 2.15 |

Portfolio, full period: `{"accepted": 301, "rejected_by_limits": 4782, "final_equity": 830905.0, "total_return_pct": 47.1, "cagr_pct": 4.4, "max_drawdown_pct": -16.1, "longest_drawdown_days": 603, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 33.9, "max_exposure_pct": 53.7, "time_in_cash_pct": 0.9, "avg_positions": 2.79}`

Portfolio, hold-out from a fresh start: `{"accepted": 141, "rejected_by_limits": 1651, "final_equity": 745806.0, "total_return_pct": 32.0, "cagr_pct": 7.5, "max_drawdown_pct": -15.7, "longest_drawdown_days": 603, "years": 3.84, "liquidity_limited_orders": 0, "avg_exposure_pct": 36.6, "max_exposure_pct": 56.6, "time_in_cash_pct": 0.1, "avg_positions": 2.77}`

**Reproduces the frozen baseline within tolerance.**