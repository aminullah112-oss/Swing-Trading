# Backtest: trigger

Config: `{"min_score": 72, "trigger": "prior_high", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01", "cost_buy_bps": null, "cost_sell_bps": null, "participation_cap": null, "adv_cap": null}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 10233 | 27% | +0.04 (+0.00..+0.07) | 1.09 | -3.46 |
| Design period | 6459 | 26% | -0.01 (-0.04..+0.03) | 0.99 | -3.43 |
| Hold-out (from 2023-01-01) | 3774 | 29% | +0.10 (+0.04..+0.16) | 1.25 | -3.46 |
| Score: 72-79 | 2783 | 29% | +0.04 (-0.02..+0.10) | 1.11 | -2.95 |
| Score: 80-89 | 5024 | 26% | +0.05 (+0.01..+0.10) | 1.13 | -3.46 |
| Score: 90+ | 2426 | 27% | -0.01 (-0.06..+0.06) | 0.99 | -3.43 |
| Setup: BREAKOUT_CONT | 334 | 36% | +0.21 (-0.11..+0.54) | 1.32 | -1.89 |
| Setup: COMPRESSION | 110 | 32% | +0.02 (-0.33..+0.37) | 1.03 | -1.88 |
| Setup: PULLBACK_EMA20 | 5137 | 25% | +0.01 (-0.03..+0.05) | 1.02 | -3.46 |
| Setup: PULLBACK_EMA50 | 3137 | 27% | +0.01 (-0.03..+0.06) | 1.04 | -2.43 |
| Setup: TRENDING | 1515 | 32% | +0.14 (+0.03..+0.25) | 1.26 | -2.95 |
| Regime: bear | 1210 | 29% | +0.02 (-0.07..+0.10) | 1.05 | -3.46 |
| Regime: bull | 9023 | 27% | +0.04 (+0.00..+0.07) | 1.09 | -3.43 |
| Exit: ema20 | 9162 | 27% | -0.06 (-0.08..-0.04) | 0.83 | -3.26 |
| Exit: ema20_pending | 1 | 0% | -0.09 (n/a: 1 trade) | 0.0 | -0.09 |
| Exit: end_of_data | 17 | 88% | +2.20 (+1.20..+3.19) | 96.45 | -0.27 |
| Exit: gap_stop | 29 | 0% | -1.78 (-2.00..-1.57) | 0.0 | -3.46 |
| Exit: stop | 721 | 0% | -1.35 (-1.36..-1.34) | 0.0 | -2.62 |
| Exit: time | 303 | 100% | +6.23 (+5.81..+6.64) | None | 0.64 |
| Year: 2017 | 245 | 31% | +0.13 (-0.04..+0.30) | 1.36 | -1.52 |
| Year: 2018 | 973 | 22% | -0.19 (-0.26..-0.12) | 0.57 | -2.05 |
| Year: 2019 | 1099 | 23% | -0.12 (-0.18..-0.05) | 0.72 | -2.32 |
| Year: 2020 | 1045 | 31% | +0.24 (+0.12..+0.35) | 1.62 | -3.43 |
| Year: 2021 | 1918 | 29% | +0.07 (+0.00..+0.14) | 1.19 | -1.84 |
| Year: 2022 | 1179 | 24% | -0.11 (-0.18..-0.04) | 0.75 | -1.85 |
| Year: 2023 | 1295 | 34% | +0.47 (+0.33..+0.61) | 2.34 | -2.32 |
| Year: 2024 | 1209 | 27% | -0.02 (-0.11..+0.07) | 0.95 | -2.62 |
| Year: 2025 | 674 | 25% | -0.13 (-0.22..-0.03) | 0.7 | -3.01 |
| Year: 2026 | 596 | 24% | -0.17 (-0.28..-0.07) | 0.63 | -3.46 |

Portfolio: `{"accepted": 780, "rejected_by_limits": 9453, "final_equity": 335771.0, "total_return_pct": -40.6, "cagr_pct": -5.6, "max_drawdown_pct": -44.2, "longest_drawdown_days": 2178, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 31.4, "max_exposure_pct": 51.8, "time_in_cash_pct": 1.2, "avg_positions": 2.57}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 10.7, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.