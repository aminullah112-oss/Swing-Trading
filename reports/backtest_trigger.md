# Backtest: trigger

Config: `{"min_score": 72, "trigger": "prior_high", "target_r": 0.0, "ema20_exit": true, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "oos_fraction": 0.4}`

| Slice | Trades | Win | Avg R (95% CI) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 10227 | 27% | +0.03 (+0.00..+0.06) | 1.08 | -3.46 |
| In-sample | 6136 | 26% | +0.00 (-0.03..+0.04) | 1.01 | -3.43 |
| Out-of-sample (from 2022-10-03) | 4091 | 28% | +0.07 (+0.02..+0.13) | 1.18 | -3.46 |
| Score: 72-79 | 2764 | 29% | +0.04 (-0.02..+0.10) | 1.11 | -2.95 |
| Score: 80-89 | 5036 | 26% | +0.05 (+0.00..+0.09) | 1.12 | -3.46 |
| Score: 90+ | 2427 | 26% | -0.01 (-0.07..+0.05) | 0.98 | -3.43 |
| Setup: BREAKOUT_CONT | 334 | 35% | +0.18 (-0.14..+0.50) | 1.27 | -1.89 |
| Setup: COMPRESSION | 112 | 31% | -0.01 (-0.35..+0.33) | 0.98 | -1.88 |
| Setup: PULLBACK_EMA20 | 5163 | 25% | +0.00 (-0.04..+0.04) | 1.01 | -3.46 |
| Setup: PULLBACK_EMA50 | 3122 | 27% | +0.01 (-0.04..+0.06) | 1.03 | -2.43 |
| Setup: TRENDING | 1496 | 33% | +0.14 (+0.03..+0.25) | 1.26 | -2.95 |
| Regime: bear | 1182 | 28% | +0.01 (-0.08..+0.09) | 1.01 | -3.46 |
| Regime: bull | 9045 | 27% | +0.04 (+0.00..+0.07) | 1.09 | -3.43 |
| Exit: ema20 | 9169 | 27% | -0.06 (-0.08..-0.04) | 0.82 | -3.26 |
| Exit: end_of_data | 4 | 75% | +4.59 (-3.82..+12.99) | 32.78 | -0.58 |
| Exit: gap_stop | 29 | 0% | -1.78 (-2.00..-1.57) | 0.0 | -3.46 |
| Exit: stop | 719 | 0% | -1.35 (-1.37..-1.34) | 0.0 | -2.62 |
| Exit: time | 306 | 100% | +6.20 (+5.79..+6.61) | None | 1.12 |
| Year: 2017 | 401 | 30% | +0.14 (-0.01..+0.29) | 1.37 | -2.12 |
| Year: 2018 | 949 | 22% | -0.19 (-0.26..-0.12) | 0.58 | -2.05 |
| Year: 2019 | 1081 | 23% | -0.11 (-0.18..-0.04) | 0.73 | -2.32 |
| Year: 2020 | 1028 | 31% | +0.22 (+0.11..+0.34) | 1.58 | -3.43 |
| Year: 2021 | 1904 | 29% | +0.07 (+0.00..+0.14) | 1.19 | -1.84 |
| Year: 2022 | 1176 | 24% | -0.11 (-0.18..-0.04) | 0.75 | -1.85 |
| Year: 2023 | 1274 | 33% | +0.46 (+0.32..+0.60) | 2.29 | -2.32 |
| Year: 2024 | 1191 | 27% | -0.02 (-0.11..+0.06) | 0.94 | -2.62 |
| Year: 2025 | 669 | 25% | -0.14 (-0.23..-0.04) | 0.68 | -3.01 |
| Year: 2026 | 554 | 23% | -0.23 (-0.34..-0.12) | 0.52 | -3.46 |

Portfolio: `{"accepted": 794, "rejected_by_limits": 9433, "final_equity": 342861.0, "total_return_pct": -39.3, "cagr_pct": -5.4, "max_drawdown_pct": -39.3, "longest_drawdown_days": 2211, "years": 8.99}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 9.3, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.