# C0 baseline reproduction

Control C0 (`c0_hash` 5e7924a41b0ee220) reproduced from raw data. Universe U159_v2 (159 configured, 158 with data), data cutoff 2026-10-16, commit feec4c33d0.

Trades: 5071 · trades digest `8683d3288fe82da7` (identical data and code give an identical digest).

| Slice | Trades | Win | Avg R | 95% CI (naive iid) | PF |
|---|---|---|---|---|---|
| All | 5071 | 0.266 | 0.365 | [np.float64(0.269), np.float64(0.461)] | 1.65 |
| Design (before 2023) | 3295 | 0.251 | 0.223 | [np.float64(0.126), np.float64(0.319)] | 1.4 |
| Hold-out (2023+) | 1776 | 0.295 | 0.63 | [np.float64(0.422), np.float64(0.837)] | 2.14 |

Portfolio, full period: `{"accepted": 321, "rejected_by_limits": 4750, "final_equity": 835274.0, "total_return_pct": 47.8, "cagr_pct": 4.4, "max_drawdown_pct": -13.9, "longest_drawdown_days": 589, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 34.0, "max_exposure_pct": 56.6, "time_in_cash_pct": 0.9, "avg_positions": 2.78}`

Portfolio, hold-out from a fresh start: `{"accepted": 139, "rejected_by_limits": 1637, "final_equity": 737608.0, "total_return_pct": 30.6, "cagr_pct": 7.3, "max_drawdown_pct": -14.8, "longest_drawdown_days": 589, "years": 3.79, "liquidity_limited_orders": 0, "avg_exposure_pct": 36.8, "max_exposure_pct": 56.6, "time_in_cash_pct": 0.3, "avg_positions": 2.78}`

**Reproduces the frozen baseline within tolerance.**