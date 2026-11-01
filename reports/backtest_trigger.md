# Backtest: trigger

Config: `{"min_score": 72, "trigger": "prior_high", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01", "cost_buy_bps": null, "cost_sell_bps": null, "participation_cap": null, "adv_cap": null}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 10303 | 27% | +0.03 (+0.00..+0.06) | 1.08 | -3.46 |
| Design period | 6544 | 26% | -0.01 (-0.04..+0.03) | 0.99 | -3.43 |
| Hold-out (from 2023-01-01) | 3759 | 28% | +0.10 (+0.04..+0.16) | 1.24 | -3.46 |
| Score: 72-79 | 2797 | 29% | +0.04 (-0.02..+0.10) | 1.1 | -2.95 |
| Score: 80-89 | 5059 | 26% | +0.05 (+0.00..+0.09) | 1.12 | -3.46 |
| Score: 90+ | 2447 | 27% | -0.01 (-0.06..+0.05) | 0.99 | -3.43 |
| Setup: BREAKOUT_CONT | 337 | 35% | +0.18 (-0.14..+0.50) | 1.27 | -1.89 |
| Setup: COMPRESSION | 113 | 32% | +0.01 (-0.33..+0.36) | 1.02 | -1.88 |
| Setup: PULLBACK_EMA20 | 5189 | 25% | +0.01 (-0.03..+0.04) | 1.01 | -3.46 |
| Setup: PULLBACK_EMA50 | 3157 | 27% | +0.01 (-0.04..+0.06) | 1.03 | -2.43 |
| Setup: TRENDING | 1507 | 33% | +0.14 (+0.04..+0.25) | 1.27 | -2.95 |
| Regime: bear | 1221 | 29% | +0.00 (-0.08..+0.09) | 1.01 | -3.46 |
| Regime: bull | 9082 | 27% | +0.04 (+0.00..+0.07) | 1.09 | -3.43 |
| Exit: ema20 | 9227 | 27% | -0.06 (-0.08..-0.04) | 0.83 | -3.26 |
| Exit: ema20_pending | 1 | 0% | -0.15 (n/a: 1 trade) | 0.0 | -0.15 |
| Exit: end_of_data | 14 | 57% | +0.59 (-0.14..+1.32) | 4.69 | -0.7 |
| Exit: gap_stop | 29 | 0% | -1.78 (-2.00..-1.57) | 0.0 | -3.46 |
| Exit: stop | 725 | 0% | -1.35 (-1.36..-1.34) | 0.0 | -2.62 |
| Exit: time | 307 | 100% | +6.20 (+5.79..+6.62) | None | 1.12 |
| Year: 2017 | 339 | 29% | +0.06 (-0.09..+0.20) | 1.14 | -1.64 |
| Year: 2018 | 964 | 22% | -0.18 (-0.25..-0.11) | 0.59 | -2.05 |
| Year: 2019 | 1095 | 23% | -0.11 (-0.18..-0.04) | 0.73 | -2.32 |
| Year: 2020 | 1045 | 31% | +0.24 (+0.12..+0.35) | 1.63 | -3.43 |
| Year: 2021 | 1919 | 29% | +0.07 (+0.00..+0.14) | 1.19 | -1.84 |
| Year: 2022 | 1182 | 24% | -0.11 (-0.19..-0.04) | 0.74 | -1.85 |
| Year: 2023 | 1296 | 34% | +0.47 (+0.33..+0.60) | 2.33 | -2.32 |
| Year: 2024 | 1208 | 27% | -0.02 (-0.11..+0.07) | 0.95 | -2.62 |
| Year: 2025 | 674 | 25% | -0.13 (-0.22..-0.03) | 0.7 | -3.01 |
| Year: 2026 | 581 | 24% | -0.22 (-0.33..-0.12) | 0.54 | -3.46 |

Portfolio: `{"accepted": 808, "rejected_by_limits": 9495, "final_equity": 290147.0, "total_return_pct": -48.6, "cagr_pct": -7.1, "max_drawdown_pct": -51.0, "longest_drawdown_days": 2176, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 31.6, "max_exposure_pct": 52.1, "time_in_cash_pct": 1.1, "avg_positions": 2.57}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 9.2, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.