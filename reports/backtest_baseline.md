# Backtest: baseline

Config: `{"min_score": 72, "trigger": "none", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01", "cost_buy_bps": null, "cost_sell_bps": null, "participation_cap": null, "adv_cap": null}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 13953 | 29% | -0.00 (-0.03..+0.02) | 0.99 | -3.19 |
| Design period | 8871 | 29% | -0.03 (-0.05..+0.00) | 0.93 | -3.19 |
| Hold-out (from 2023-01-01) | 5082 | 29% | +0.03 (-0.01..+0.08) | 1.09 | -2.94 |
| Score: 72-79 | 3718 | 31% | -0.01 (-0.05..+0.04) | 0.98 | -2.94 |
| Score: 80-89 | 6568 | 28% | -0.01 (-0.04..+0.03) | 0.99 | -2.61 |
| Score: 90+ | 3667 | 28% | +0.00 (-0.04..+0.05) | 1.01 | -3.19 |
| Setup: BREAKOUT_CONT | 613 | 32% | +0.03 (-0.16..+0.22) | 1.04 | -2.61 |
| Setup: COMPRESSION | 155 | 33% | +0.21 (-0.10..+0.53) | 1.39 | -1.8 |
| Setup: PULLBACK_EMA20 | 6484 | 27% | -0.04 (-0.07..-0.01) | 0.88 | -3.19 |
| Setup: PULLBACK_EMA50 | 4625 | 30% | -0.03 (-0.06..+0.01) | 0.91 | -2.43 |
| Setup: TRENDING | 2076 | 32% | +0.14 (+0.06..+0.23) | 1.29 | -2.94 |
| Regime: bear | 1653 | 30% | -0.05 (-0.11..+0.01) | 0.87 | -2.94 |
| Regime: bull | 12300 | 29% | +0.00 (-0.02..+0.03) | 1.01 | -3.19 |
| Exit: ema20 | 12213 | 30% | -0.04 (-0.06..-0.02) | 0.86 | -2.94 |
| Exit: ema20_pending | 1 | 0% | -0.35 (n/a: 1 trade) | 0.0 | -0.35 |
| Exit: end_of_data | 2 | 50% | -0.10 (-0.87..+0.66) | 0.59 | -0.49 |
| Exit: gap_stop | 70 | 0% | -0.98 (-1.16..-0.81) | 0.0 | -3.19 |
| Exit: stop | 1347 | 0% | -1.11 (-1.12..-1.10) | 0.0 | -2.62 |
| Exit: time | 320 | 100% | +6.29 (+5.87..+6.70) | None | 1.21 |
| Year: 2017 | 490 | 30% | +0.07 (-0.06..+0.19) | 1.2 | -1.52 |
| Year: 2018 | 1354 | 25% | -0.18 (-0.23..-0.13) | 0.53 | -1.84 |
| Year: 2019 | 1491 | 26% | -0.11 (-0.17..-0.06) | 0.69 | -2.31 |
| Year: 2020 | 1400 | 33% | +0.17 (+0.09..+0.26) | 1.51 | -3.19 |
| Year: 2021 | 2526 | 30% | +0.04 (-0.02..+0.09) | 1.1 | -1.84 |
| Year: 2022 | 1610 | 28% | -0.10 (-0.16..-0.05) | 0.73 | -1.8 |
| Year: 2023 | 1705 | 33% | +0.33 (+0.22..+0.44) | 2.0 | -2.22 |
| Year: 2024 | 1631 | 29% | -0.06 (-0.12..+0.01) | 0.85 | -2.62 |
| Year: 2025 | 934 | 26% | -0.13 (-0.20..-0.06) | 0.66 | -2.94 |
| Year: 2026 | 812 | 25% | -0.22 (-0.29..-0.14) | 0.48 | -2.0 |

Portfolio: `{"accepted": 958, "rejected_by_limits": 12995, "final_equity": 415168.0, "total_return_pct": -26.5, "cagr_pct": -3.4, "max_drawdown_pct": -30.7, "longest_drawdown_days": 2157, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 29.8, "max_exposure_pct": 50.5, "time_in_cash_pct": 1.7, "avg_positions": 2.53}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 9.1, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.