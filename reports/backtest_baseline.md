# Backtest: baseline

Config: `{"min_score": 72, "trigger": "none", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01", "cost_buy_bps": null, "cost_sell_bps": null, "participation_cap": null, "adv_cap": null}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 13911 | 29% | -0.00 (-0.03..+0.02) | 0.99 | -3.19 |
| Design period | 8850 | 29% | -0.02 (-0.05..+0.00) | 0.93 | -3.19 |
| Hold-out (from 2023-01-01) | 5061 | 29% | +0.04 (-0.01..+0.08) | 1.09 | -2.94 |
| Score: 72-79 | 3704 | 32% | -0.01 (-0.05..+0.04) | 0.98 | -2.94 |
| Score: 80-89 | 6554 | 28% | -0.00 (-0.04..+0.04) | 1.0 | -2.61 |
| Score: 90+ | 3653 | 28% | -0.00 (-0.05..+0.04) | 0.99 | -3.19 |
| Setup: BREAKOUT_CONT | 611 | 32% | +0.04 (-0.15..+0.23) | 1.07 | -2.61 |
| Setup: COMPRESSION | 156 | 33% | +0.16 (-0.14..+0.46) | 1.3 | -1.8 |
| Setup: PULLBACK_EMA20 | 6465 | 27% | -0.04 (-0.07..-0.01) | 0.88 | -3.19 |
| Setup: PULLBACK_EMA50 | 4609 | 30% | -0.03 (-0.06..+0.01) | 0.91 | -2.43 |
| Setup: TRENDING | 2070 | 33% | +0.14 (+0.06..+0.23) | 1.29 | -2.94 |
| Regime: bear | 1644 | 30% | -0.04 (-0.11..+0.02) | 0.89 | -2.94 |
| Regime: bull | 12267 | 29% | +0.00 (-0.02..+0.03) | 1.01 | -3.19 |
| Exit: ema20 | 12169 | 30% | -0.04 (-0.06..-0.03) | 0.86 | -2.94 |
| Exit: ema20_pending | 1 | 100% | +0.20 (n/a: 1 trade) | None | 0.2 |
| Exit: end_of_data | 5 | 100% | +4.09 (-2.08..+10.27) | None | 0.14 |
| Exit: gap_stop | 68 | 0% | -0.97 (-1.15..-0.79) | 0.0 | -3.19 |
| Exit: stop | 1347 | 0% | -1.11 (-1.12..-1.10) | 0.0 | -2.62 |
| Exit: time | 321 | 100% | +6.27 (+5.86..+6.68) | None | 1.21 |
| Year: 2017 | 527 | 31% | +0.06 (-0.06..+0.18) | 1.18 | -2.12 |
| Year: 2018 | 1343 | 25% | -0.18 (-0.23..-0.13) | 0.54 | -1.84 |
| Year: 2019 | 1490 | 26% | -0.11 (-0.17..-0.06) | 0.69 | -2.31 |
| Year: 2020 | 1386 | 34% | +0.18 (+0.09..+0.27) | 1.52 | -3.19 |
| Year: 2021 | 2506 | 30% | +0.03 (-0.02..+0.09) | 1.1 | -1.84 |
| Year: 2022 | 1598 | 28% | -0.10 (-0.16..-0.05) | 0.73 | -1.8 |
| Year: 2023 | 1694 | 33% | +0.33 (+0.22..+0.44) | 1.99 | -2.22 |
| Year: 2024 | 1627 | 29% | -0.06 (-0.12..+0.01) | 0.85 | -2.62 |
| Year: 2025 | 934 | 26% | -0.13 (-0.20..-0.06) | 0.66 | -2.94 |
| Year: 2026 | 806 | 25% | -0.21 (-0.29..-0.13) | 0.49 | -2.0 |

Portfolio: `{"accepted": 949, "rejected_by_limits": 12962, "final_equity": 417823.0, "total_return_pct": -26.0, "cagr_pct": -3.3, "max_drawdown_pct": -27.4, "longest_drawdown_days": 2153, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 30.0, "max_exposure_pct": 51.0, "time_in_cash_pct": 1.5, "avg_positions": 2.53}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 9.6, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.