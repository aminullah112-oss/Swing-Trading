# Backtest: baseline

Config: `{"min_score": 72, "trigger": "none", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01", "cost_buy_bps": null, "cost_sell_bps": null, "participation_cap": null, "adv_cap": null}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 13860 | 29% | -0.00 (-0.02..+0.02) | 1.0 | -3.19 |
| Design period | 8753 | 29% | -0.02 (-0.05..+0.00) | 0.93 | -3.19 |
| Hold-out (from 2023-01-01) | 5107 | 29% | +0.04 (-0.01..+0.09) | 1.11 | -2.94 |
| Score: 72-79 | 3709 | 32% | -0.00 (-0.05..+0.04) | 1.0 | -2.94 |
| Score: 80-89 | 6525 | 28% | -0.00 (-0.04..+0.03) | 1.0 | -2.61 |
| Score: 90+ | 3626 | 28% | +0.00 (-0.04..+0.05) | 1.01 | -3.19 |
| Setup: BREAKOUT_CONT | 599 | 32% | +0.05 (-0.14..+0.24) | 1.08 | -2.61 |
| Setup: COMPRESSION | 152 | 33% | +0.17 (-0.14..+0.48) | 1.31 | -1.8 |
| Setup: PULLBACK_EMA20 | 6435 | 27% | -0.03 (-0.07..-0.00) | 0.9 | -3.19 |
| Setup: PULLBACK_EMA50 | 4611 | 29% | -0.03 (-0.07..+0.00) | 0.91 | -2.43 |
| Setup: TRENDING | 2063 | 32% | +0.15 (+0.06..+0.23) | 1.3 | -2.94 |
| Regime: bear | 1656 | 30% | -0.03 (-0.10..+0.03) | 0.91 | -2.94 |
| Regime: bull | 12204 | 29% | +0.00 (-0.02..+0.03) | 1.01 | -3.19 |
| Exit: ema20 | 12127 | 30% | -0.04 (-0.06..-0.02) | 0.87 | -2.94 |
| Exit: ema20_pending | 1 | 100% | +0.34 (n/a: 1 trade) | None | 0.34 |
| Exit: end_of_data | 18 | 78% | +1.99 (+1.03..+2.95) | 21.81 | -0.53 |
| Exit: gap_stop | 70 | 0% | -0.97 (-1.15..-0.79) | 0.0 | -3.19 |
| Exit: stop | 1329 | 0% | -1.11 (-1.12..-1.10) | 0.0 | -2.62 |
| Exit: time | 315 | 100% | +6.27 (+5.85..+6.68) | None | 1.05 |
| Year: 2017 | 362 | 35% | +0.13 (+0.00..+0.26) | 1.45 | -1.55 |
| Year: 2018 | 1363 | 25% | -0.18 (-0.23..-0.13) | 0.53 | -1.84 |
| Year: 2019 | 1492 | 26% | -0.11 (-0.17..-0.06) | 0.69 | -2.31 |
| Year: 2020 | 1400 | 33% | +0.17 (+0.09..+0.26) | 1.51 | -3.19 |
| Year: 2021 | 2526 | 30% | +0.04 (-0.02..+0.09) | 1.1 | -1.84 |
| Year: 2022 | 1610 | 28% | -0.10 (-0.16..-0.05) | 0.73 | -1.8 |
| Year: 2023 | 1705 | 33% | +0.33 (+0.22..+0.44) | 2.0 | -2.22 |
| Year: 2024 | 1631 | 29% | -0.06 (-0.12..+0.01) | 0.85 | -2.62 |
| Year: 2025 | 934 | 26% | -0.13 (-0.20..-0.06) | 0.66 | -2.94 |
| Year: 2026 | 837 | 26% | -0.17 (-0.25..-0.09) | 0.58 | -2.0 |

Portfolio: `{"accepted": 949, "rejected_by_limits": 12911, "final_equity": 421224.0, "total_return_pct": -25.4, "cagr_pct": -3.2, "max_drawdown_pct": -32.8, "longest_drawdown_days": 2171, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 30.0, "max_exposure_pct": 51.3, "time_in_cash_pct": 1.5, "avg_positions": 2.53}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 10.5, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.