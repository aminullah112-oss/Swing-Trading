# Backtest: trigger

Config: `{"min_score": 72, "trigger": "prior_high", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01", "cost_buy_bps": null, "cost_sell_bps": null, "participation_cap": null, "adv_cap": null}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 10288 | 27% | +0.04 (+0.00..+0.07) | 1.09 | -3.46 |
| Design period | 6524 | 26% | -0.00 (-0.04..+0.03) | 0.99 | -3.43 |
| Hold-out (from 2023-01-01) | 3764 | 29% | +0.10 (+0.04..+0.16) | 1.25 | -3.46 |
| Score: 72-79 | 2790 | 29% | +0.04 (-0.02..+0.10) | 1.09 | -2.95 |
| Score: 80-89 | 5048 | 26% | +0.05 (+0.00..+0.10) | 1.13 | -3.46 |
| Score: 90+ | 2450 | 27% | +0.00 (-0.06..+0.06) | 1.0 | -3.43 |
| Setup: BREAKOUT_CONT | 337 | 36% | +0.22 (-0.10..+0.54) | 1.32 | -1.89 |
| Setup: COMPRESSION | 111 | 32% | +0.02 (-0.33..+0.36) | 1.03 | -1.88 |
| Setup: PULLBACK_EMA20 | 5181 | 25% | +0.01 (-0.03..+0.04) | 1.02 | -3.46 |
| Setup: PULLBACK_EMA50 | 3153 | 27% | +0.02 (-0.03..+0.06) | 1.04 | -2.43 |
| Setup: TRENDING | 1506 | 32% | +0.13 (+0.03..+0.24) | 1.25 | -2.95 |
| Regime: bear | 1223 | 29% | +0.01 (-0.07..+0.09) | 1.03 | -3.46 |
| Regime: bull | 9065 | 27% | +0.04 (+0.00..+0.07) | 1.09 | -3.43 |
| Exit: ema20 | 9214 | 27% | -0.06 (-0.08..-0.04) | 0.83 | -3.26 |
| Exit: ema20_pending | 1 | 0% | -1.10 (n/a: 1 trade) | 0.0 | -1.11 |
| Exit: end_of_data | 15 | 87% | +1.63 (+0.95..+2.31) | 248.29 | -0.09 |
| Exit: gap_stop | 29 | 0% | -1.78 (-2.00..-1.57) | 0.0 | -3.46 |
| Exit: stop | 722 | 0% | -1.35 (-1.37..-1.34) | 0.0 | -2.62 |
| Exit: time | 307 | 100% | +6.21 (+5.80..+6.62) | None | 1.12 |
| Year: 2017 | 312 | 31% | +0.11 (-0.04..+0.27) | 1.32 | -1.63 |
| Year: 2018 | 968 | 22% | -0.18 (-0.25..-0.12) | 0.58 | -2.05 |
| Year: 2019 | 1096 | 23% | -0.11 (-0.18..-0.04) | 0.72 | -2.32 |
| Year: 2020 | 1046 | 31% | +0.24 (+0.12..+0.35) | 1.63 | -3.43 |
| Year: 2021 | 1919 | 29% | +0.07 (+0.00..+0.14) | 1.19 | -1.84 |
| Year: 2022 | 1183 | 24% | -0.11 (-0.19..-0.04) | 0.74 | -1.85 |
| Year: 2023 | 1296 | 34% | +0.47 (+0.33..+0.60) | 2.33 | -2.32 |
| Year: 2024 | 1208 | 27% | -0.02 (-0.11..+0.07) | 0.96 | -2.62 |
| Year: 2025 | 674 | 25% | -0.13 (-0.22..-0.03) | 0.7 | -3.01 |
| Year: 2026 | 586 | 24% | -0.20 (-0.30..-0.09) | 0.58 | -3.46 |

Portfolio: `{"accepted": 805, "rejected_by_limits": 9483, "final_equity": 308885.0, "total_return_pct": -45.3, "cagr_pct": -6.5, "max_drawdown_pct": -49.2, "longest_drawdown_days": 2169, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 31.8, "max_exposure_pct": 52.6, "time_in_cash_pct": 1.3, "avg_positions": 2.57}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 10.4, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.