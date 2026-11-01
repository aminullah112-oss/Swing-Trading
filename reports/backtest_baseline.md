# Backtest: baseline

Config: `{"min_score": 72, "trigger": "none", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01", "cost_buy_bps": null, "cost_sell_bps": null, "participation_cap": null, "adv_cap": null}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 13941 | 29% | -0.01 (-0.03..+0.02) | 0.99 | -3.19 |
| Design period | 8846 | 29% | -0.03 (-0.06..-0.00) | 0.92 | -3.19 |
| Hold-out (from 2023-01-01) | 5095 | 29% | +0.04 (-0.01..+0.08) | 1.09 | -2.94 |
| Score: 72-79 | 3726 | 32% | -0.01 (-0.05..+0.04) | 0.98 | -2.94 |
| Score: 80-89 | 6555 | 28% | -0.01 (-0.04..+0.03) | 0.98 | -2.61 |
| Score: 90+ | 3660 | 28% | -0.00 (-0.05..+0.05) | 1.0 | -3.19 |
| Setup: BREAKOUT_CONT | 612 | 32% | +0.04 (-0.16..+0.23) | 1.06 | -2.61 |
| Setup: COMPRESSION | 155 | 33% | +0.17 (-0.14..+0.47) | 1.31 | -1.8 |
| Setup: PULLBACK_EMA20 | 6479 | 27% | -0.04 (-0.07..-0.01) | 0.88 | -3.19 |
| Setup: PULLBACK_EMA50 | 4619 | 30% | -0.03 (-0.07..+0.00) | 0.9 | -2.43 |
| Setup: TRENDING | 2076 | 32% | +0.14 (+0.05..+0.22) | 1.29 | -2.94 |
| Regime: bear | 1668 | 30% | -0.04 (-0.10..+0.02) | 0.89 | -2.94 |
| Regime: bull | 12273 | 29% | -0.00 (-0.03..+0.03) | 1.0 | -3.19 |
| Exit: ema20 | 12191 | 30% | -0.04 (-0.06..-0.03) | 0.86 | -2.94 |
| Exit: ema20_pending | 1 | 100% | +0.32 (n/a: 1 trade) | None | 0.32 |
| Exit: end_of_data | 14 | 64% | +0.76 (-0.02..+1.55) | 8.3 | -0.56 |
| Exit: gap_stop | 70 | 0% | -0.98 (-1.16..-0.81) | 0.0 | -3.19 |
| Exit: stop | 1347 | 0% | -1.11 (-1.13..-1.10) | 0.0 | -2.62 |
| Exit: time | 318 | 100% | +6.25 (+5.83..+6.66) | None | 1.21 |
| Year: 2017 | 462 | 31% | -0.00 (-0.11..+0.11) | 0.99 | -1.64 |
| Year: 2018 | 1356 | 25% | -0.18 (-0.23..-0.13) | 0.54 | -1.84 |
| Year: 2019 | 1492 | 26% | -0.12 (-0.17..-0.06) | 0.69 | -2.31 |
| Year: 2020 | 1400 | 33% | +0.17 (+0.09..+0.26) | 1.51 | -3.19 |
| Year: 2021 | 2526 | 30% | +0.04 (-0.02..+0.09) | 1.1 | -1.84 |
| Year: 2022 | 1610 | 28% | -0.10 (-0.16..-0.05) | 0.73 | -1.8 |
| Year: 2023 | 1705 | 33% | +0.33 (+0.22..+0.44) | 2.0 | -2.22 |
| Year: 2024 | 1631 | 29% | -0.06 (-0.12..+0.01) | 0.85 | -2.62 |
| Year: 2025 | 934 | 26% | -0.13 (-0.20..-0.06) | 0.66 | -2.94 |
| Year: 2026 | 825 | 25% | -0.20 (-0.28..-0.13) | 0.51 | -2.0 |

Portfolio: `{"accepted": 938, "rejected_by_limits": 13003, "final_equity": 464237.0, "total_return_pct": -17.8, "cagr_pct": -2.2, "max_drawdown_pct": -27.4, "longest_drawdown_days": 1500, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 30.3, "max_exposure_pct": 50.7, "time_in_cash_pct": 1.4, "avg_positions": 2.54}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 9.2, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.