# Backtest: trigger

Config: `{"min_score": 72, "trigger": "prior_high", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01"}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 10204 | 27% | +0.03 (+0.00..+0.07) | 1.08 | -3.46 |
| Design period | 6516 | 26% | +0.00 (-0.03..+0.04) | 1.0 | -3.43 |
| Hold-out (from 2023-01-01) | 3688 | 28% | +0.09 (+0.03..+0.15) | 1.22 | -3.46 |
| Score: 72-79 | 2761 | 29% | +0.04 (-0.02..+0.10) | 1.11 | -2.95 |
| Score: 80-89 | 5018 | 26% | +0.05 (+0.00..+0.09) | 1.12 | -3.46 |
| Score: 90+ | 2425 | 27% | -0.01 (-0.07..+0.05) | 0.98 | -3.43 |
| Setup: BREAKOUT_CONT | 330 | 36% | +0.20 (-0.13..+0.52) | 1.29 | -1.89 |
| Setup: COMPRESSION | 112 | 31% | -0.01 (-0.35..+0.33) | 0.98 | -1.88 |
| Setup: PULLBACK_EMA20 | 5150 | 25% | +0.00 (-0.04..+0.04) | 1.01 | -3.46 |
| Setup: PULLBACK_EMA50 | 3120 | 27% | +0.01 (-0.04..+0.06) | 1.04 | -2.43 |
| Setup: TRENDING | 1492 | 33% | +0.15 (+0.04..+0.26) | 1.27 | -2.95 |
| Regime: bear | 1180 | 29% | +0.00 (-0.08..+0.09) | 1.01 | -3.46 |
| Regime: bull | 9024 | 27% | +0.04 (+0.00..+0.07) | 1.09 | -3.43 |
| Exit: ema20 | 9148 | 27% | -0.06 (-0.08..-0.04) | 0.82 | -3.26 |
| Exit: end_of_data | 4 | 100% | +4.71 (-3.56..+12.99) | None | 0.01 |
| Exit: gap_stop | 29 | 0% | -1.78 (-2.00..-1.57) | 0.0 | -3.46 |
| Exit: stop | 716 | 0% | -1.35 (-1.37..-1.34) | 0.0 | -2.62 |
| Exit: time | 307 | 100% | +6.21 (+5.80..+6.62) | None | 1.12 |
| Year: 2017 | 395 | 30% | +0.14 (-0.02..+0.29) | 1.37 | -2.12 |
| Year: 2018 | 940 | 22% | -0.19 (-0.26..-0.12) | 0.57 | -2.05 |
| Year: 2019 | 1078 | 23% | -0.11 (-0.18..-0.04) | 0.73 | -2.32 |
| Year: 2020 | 1027 | 31% | +0.23 (+0.11..+0.34) | 1.6 | -3.43 |
| Year: 2021 | 1900 | 29% | +0.07 (+0.01..+0.14) | 1.2 | -1.84 |
| Year: 2022 | 1176 | 24% | -0.11 (-0.18..-0.03) | 0.75 | -1.85 |
| Year: 2023 | 1277 | 33% | +0.46 (+0.32..+0.59) | 2.29 | -2.32 |
| Year: 2024 | 1190 | 27% | -0.02 (-0.11..+0.06) | 0.95 | -2.62 |
| Year: 2025 | 669 | 25% | -0.14 (-0.23..-0.04) | 0.68 | -3.01 |
| Year: 2026 | 552 | 23% | -0.23 (-0.34..-0.12) | 0.52 | -3.46 |

Portfolio: `{"accepted": 774, "rejected_by_limits": 9430, "final_equity": 372575.0, "total_return_pct": -34.1, "cagr_pct": -4.5, "max_drawdown_pct": -34.1, "longest_drawdown_days": 2211, "years": 8.99}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 9.1, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.