# Backtest: trigger

Config: `{"min_score": 72, "trigger": "prior_high", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01", "cost_buy_bps": null, "cost_sell_bps": null, "participation_cap": null, "adv_cap": null}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 10257 | 27% | +0.04 (+0.01..+0.07) | 1.09 | -3.46 |
| Design period | 6488 | 26% | -0.00 (-0.04..+0.03) | 1.0 | -3.43 |
| Hold-out (from 2023-01-01) | 3769 | 29% | +0.10 (+0.04..+0.16) | 1.25 | -3.46 |
| Score: 72-79 | 2791 | 29% | +0.05 (-0.01..+0.11) | 1.11 | -2.95 |
| Score: 80-89 | 5031 | 26% | +0.05 (+0.00..+0.09) | 1.13 | -3.46 |
| Score: 90+ | 2435 | 27% | +0.00 (-0.06..+0.06) | 1.0 | -3.43 |
| Setup: BREAKOUT_CONT | 335 | 36% | +0.21 (-0.12..+0.53) | 1.31 | -1.89 |
| Setup: COMPRESSION | 110 | 32% | +0.02 (-0.33..+0.37) | 1.03 | -1.88 |
| Setup: PULLBACK_EMA20 | 5156 | 25% | +0.01 (-0.03..+0.04) | 1.02 | -3.46 |
| Setup: PULLBACK_EMA50 | 3154 | 27% | +0.01 (-0.03..+0.06) | 1.04 | -2.43 |
| Setup: TRENDING | 1502 | 33% | +0.15 (+0.04..+0.26) | 1.28 | -2.95 |
| Regime: bear | 1211 | 29% | +0.01 (-0.07..+0.10) | 1.03 | -3.46 |
| Regime: bull | 9046 | 27% | +0.04 (+0.01..+0.07) | 1.1 | -3.43 |
| Exit: ema20 | 9182 | 27% | -0.06 (-0.08..-0.04) | 0.83 | -3.26 |
| Exit: ema20_pending | 1 | 100% | +0.15 (n/a: 1 trade) | None | 0.15 |
| Exit: end_of_data | 18 | 72% | +1.85 (+0.89..+2.81) | 16.88 | -0.62 |
| Exit: gap_stop | 29 | 0% | -1.78 (-2.00..-1.57) | 0.0 | -3.46 |
| Exit: stop | 722 | 0% | -1.35 (-1.37..-1.34) | 0.0 | -2.62 |
| Exit: time | 305 | 100% | +6.21 (+5.79..+6.62) | None | 1.12 |
| Year: 2017 | 272 | 32% | +0.19 (+0.03..+0.36) | 1.62 | -1.52 |
| Year: 2018 | 973 | 22% | -0.19 (-0.26..-0.12) | 0.57 | -2.05 |
| Year: 2019 | 1095 | 23% | -0.12 (-0.18..-0.04) | 0.72 | -2.32 |
| Year: 2020 | 1045 | 31% | +0.23 (+0.12..+0.35) | 1.63 | -3.43 |
| Year: 2021 | 1921 | 29% | +0.07 (+0.00..+0.14) | 1.19 | -1.84 |
| Year: 2022 | 1182 | 24% | -0.11 (-0.19..-0.04) | 0.74 | -1.85 |
| Year: 2023 | 1295 | 34% | +0.47 (+0.33..+0.61) | 2.34 | -2.32 |
| Year: 2024 | 1208 | 27% | -0.02 (-0.11..+0.07) | 0.95 | -2.62 |
| Year: 2025 | 674 | 25% | -0.13 (-0.22..-0.03) | 0.7 | -3.01 |
| Year: 2026 | 592 | 24% | -0.18 (-0.29..-0.07) | 0.62 | -3.46 |

Portfolio: `{"accepted": 764, "rejected_by_limits": 9493, "final_equity": 417464.0, "total_return_pct": -26.1, "cagr_pct": -3.3, "max_drawdown_pct": -33.7, "longest_drawdown_days": 2171, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 31.9, "max_exposure_pct": 52.1, "time_in_cash_pct": 1.2, "avg_positions": 2.59}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 10.5, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.