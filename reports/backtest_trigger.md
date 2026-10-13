# Backtest: trigger

Config: `{"min_score": 72, "trigger": "prior_high", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01"}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 10222 | 27% | +0.03 (+0.00..+0.06) | 1.08 | -3.46 |
| Design period | 6533 | 26% | -0.00 (-0.04..+0.03) | 1.0 | -3.43 |
| Hold-out (from 2023-01-01) | 3689 | 28% | +0.09 (+0.03..+0.15) | 1.22 | -3.46 |
| Score: 72-79 | 2764 | 29% | +0.04 (-0.02..+0.10) | 1.1 | -2.95 |
| Score: 80-89 | 5037 | 26% | +0.05 (+0.00..+0.09) | 1.12 | -3.46 |
| Score: 90+ | 2421 | 26% | -0.01 (-0.07..+0.05) | 0.98 | -3.43 |
| Setup: BREAKOUT_CONT | 335 | 36% | +0.20 (-0.12..+0.52) | 1.3 | -1.89 |
| Setup: COMPRESSION | 113 | 32% | +0.02 (-0.33..+0.36) | 1.03 | -1.88 |
| Setup: PULLBACK_EMA20 | 5152 | 25% | +0.00 (-0.04..+0.04) | 1.01 | -3.46 |
| Setup: PULLBACK_EMA50 | 3128 | 27% | +0.01 (-0.03..+0.06) | 1.04 | -2.43 |
| Setup: TRENDING | 1494 | 33% | +0.14 (+0.03..+0.24) | 1.25 | -2.95 |
| Regime: bear | 1180 | 29% | +0.00 (-0.09..+0.09) | 1.0 | -3.46 |
| Regime: bull | 9042 | 27% | +0.04 (+0.00..+0.07) | 1.09 | -3.43 |
| Exit: ema20 | 9166 | 27% | -0.06 (-0.08..-0.04) | 0.82 | -3.26 |
| Exit: end_of_data | 4 | 75% | +4.59 (-3.82..+12.99) | 32.78 | -0.58 |
| Exit: gap_stop | 29 | 0% | -1.78 (-2.00..-1.57) | 0.0 | -3.46 |
| Exit: stop | 718 | 0% | -1.35 (-1.37..-1.34) | 0.0 | -2.62 |
| Exit: time | 305 | 100% | +6.20 (+5.79..+6.62) | None | 1.12 |
| Year: 2017 | 402 | 30% | +0.14 (-0.01..+0.29) | 1.37 | -2.12 |
| Year: 2018 | 949 | 22% | -0.19 (-0.26..-0.12) | 0.57 | -2.05 |
| Year: 2019 | 1080 | 23% | -0.11 (-0.18..-0.04) | 0.73 | -2.32 |
| Year: 2020 | 1027 | 31% | +0.22 (+0.11..+0.34) | 1.59 | -3.43 |
| Year: 2021 | 1899 | 29% | +0.07 (+0.01..+0.14) | 1.21 | -1.84 |
| Year: 2022 | 1176 | 24% | -0.11 (-0.19..-0.04) | 0.75 | -1.85 |
| Year: 2023 | 1276 | 33% | +0.46 (+0.32..+0.59) | 2.29 | -2.32 |
| Year: 2024 | 1190 | 27% | -0.02 (-0.11..+0.06) | 0.94 | -2.62 |
| Year: 2025 | 669 | 25% | -0.14 (-0.23..-0.04) | 0.68 | -3.01 |
| Year: 2026 | 554 | 23% | -0.23 (-0.34..-0.12) | 0.52 | -3.46 |

Portfolio: `{"accepted": 774, "rejected_by_limits": 9448, "final_equity": 343725.0, "total_return_pct": -39.2, "cagr_pct": -5.4, "max_drawdown_pct": -39.2, "longest_drawdown_days": 2211, "years": 8.99}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 9.3, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.