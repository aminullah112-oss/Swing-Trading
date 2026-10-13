# Backtest: baseline

Config: `{"min_score": 72, "trigger": "none", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01"}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 13933 | 29% | -0.00 (-0.03..+0.02) | 0.99 | -3.19 |
| Design period | 8866 | 29% | -0.02 (-0.05..+0.00) | 0.93 | -3.19 |
| Hold-out (from 2023-01-01) | 5067 | 29% | +0.04 (-0.01..+0.08) | 1.09 | -2.94 |
| Score: 72-79 | 3721 | 32% | -0.00 (-0.04..+0.04) | 1.0 | -2.94 |
| Score: 80-89 | 6562 | 28% | -0.00 (-0.04..+0.03) | 0.99 | -2.61 |
| Score: 90+ | 3650 | 28% | -0.00 (-0.05..+0.04) | 0.99 | -3.19 |
| Setup: BREAKOUT_CONT | 614 | 32% | +0.04 (-0.15..+0.23) | 1.06 | -2.61 |
| Setup: COMPRESSION | 155 | 33% | +0.16 (-0.14..+0.46) | 1.3 | -1.8 |
| Setup: PULLBACK_EMA20 | 6468 | 27% | -0.04 (-0.07..-0.01) | 0.88 | -3.19 |
| Setup: PULLBACK_EMA50 | 4609 | 30% | -0.03 (-0.06..+0.01) | 0.91 | -2.43 |
| Setup: TRENDING | 2087 | 32% | +0.14 (+0.06..+0.23) | 1.3 | -2.94 |
| Regime: bear | 1626 | 30% | -0.04 (-0.11..+0.02) | 0.89 | -2.94 |
| Regime: bull | 12307 | 29% | +0.00 (-0.02..+0.03) | 1.01 | -3.19 |
| Exit: ema20 | 12190 | 30% | -0.04 (-0.06..-0.03) | 0.86 | -2.94 |
| Exit: end_of_data | 5 | 100% | +3.93 (-2.72..+10.57) | None | 0.11 |
| Exit: gap_stop | 70 | 0% | -1.00 (-1.17..-0.82) | 0.0 | -3.19 |
| Exit: stop | 1346 | 0% | -1.11 (-1.13..-1.10) | 0.0 | -2.62 |
| Exit: time | 322 | 100% | +6.27 (+5.86..+6.68) | None | 1.21 |
| Year: 2017 | 537 | 31% | +0.06 (-0.05..+0.18) | 1.18 | -2.12 |
| Year: 2018 | 1332 | 25% | -0.19 (-0.24..-0.14) | 0.53 | -1.84 |
| Year: 2019 | 1473 | 26% | -0.11 (-0.17..-0.06) | 0.69 | -2.31 |
| Year: 2020 | 1388 | 33% | +0.18 (+0.09..+0.27) | 1.51 | -3.19 |
| Year: 2021 | 2526 | 30% | +0.04 (-0.02..+0.09) | 1.1 | -1.84 |
| Year: 2022 | 1610 | 28% | -0.10 (-0.16..-0.05) | 0.73 | -1.8 |
| Year: 2023 | 1705 | 33% | +0.33 (+0.22..+0.44) | 2.0 | -2.22 |
| Year: 2024 | 1631 | 29% | -0.06 (-0.12..+0.01) | 0.85 | -2.62 |
| Year: 2025 | 934 | 26% | -0.13 (-0.20..-0.06) | 0.66 | -2.94 |
| Year: 2026 | 797 | 25% | -0.21 (-0.29..-0.13) | 0.5 | -2.0 |

Portfolio: `{"accepted": 917, "rejected_by_limits": 13016, "final_equity": 452312.0, "total_return_pct": -19.9, "cagr_pct": -2.4, "max_drawdown_pct": -25.3, "longest_drawdown_days": 2207, "years": 8.99}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 9.1, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.