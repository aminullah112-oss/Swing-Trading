# Backtest: trigger

Config: `{"min_score": 72, "trigger": "prior_high", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01"}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 10305 | 27% | +0.04 (+0.01..+0.07) | 1.09 | -3.46 |
| Design period | 6567 | 26% | +0.00 (-0.03..+0.04) | 1.0 | -3.43 |
| Hold-out (from 2023-01-01) | 3738 | 28% | +0.10 (+0.04..+0.16) | 1.24 | -3.46 |
| Score: 72-79 | 2795 | 29% | +0.05 (-0.01..+0.11) | 1.12 | -2.95 |
| Score: 80-89 | 5073 | 26% | +0.05 (+0.00..+0.10) | 1.13 | -3.46 |
| Score: 90+ | 2437 | 27% | -0.01 (-0.07..+0.05) | 0.98 | -3.43 |
| Setup: BREAKOUT_CONT | 338 | 36% | +0.18 (-0.14..+0.50) | 1.27 | -1.89 |
| Setup: COMPRESSION | 112 | 31% | -0.01 (-0.35..+0.33) | 0.98 | -1.88 |
| Setup: PULLBACK_EMA20 | 5186 | 25% | +0.00 (-0.03..+0.04) | 1.01 | -3.46 |
| Setup: PULLBACK_EMA50 | 3157 | 27% | +0.02 (-0.03..+0.07) | 1.05 | -2.43 |
| Setup: TRENDING | 1512 | 33% | +0.15 (+0.04..+0.26) | 1.29 | -2.95 |
| Regime: bear | 1188 | 29% | +0.00 (-0.09..+0.09) | 1.0 | -3.46 |
| Regime: bull | 9117 | 27% | +0.04 (+0.01..+0.07) | 1.1 | -3.43 |
| Exit: ema20 | 9235 | 27% | -0.06 (-0.08..-0.04) | 0.82 | -3.26 |
| Exit: ema20_pending | 1 | 0% | -0.31 (n/a: 1 trade) | 0.0 | -0.31 |
| Exit: end_of_data | 4 | 100% | +4.71 (-3.56..+12.99) | None | 0.01 |
| Exit: gap_stop | 29 | 0% | -1.78 (-2.00..-1.57) | 0.0 | -3.46 |
| Exit: stop | 724 | 0% | -1.35 (-1.36..-1.34) | 0.0 | -2.62 |
| Exit: time | 312 | 100% | +6.20 (+5.79..+6.61) | None | 1.12 |
| Year: 2017 | 401 | 30% | +0.14 (-0.01..+0.29) | 1.38 | -2.12 |
| Year: 2018 | 948 | 22% | -0.19 (-0.26..-0.12) | 0.58 | -2.05 |
| Year: 2019 | 1079 | 23% | -0.11 (-0.18..-0.04) | 0.73 | -2.32 |
| Year: 2020 | 1037 | 31% | +0.24 (+0.12..+0.35) | 1.63 | -3.43 |
| Year: 2021 | 1920 | 29% | +0.07 (+0.00..+0.14) | 1.19 | -1.84 |
| Year: 2022 | 1182 | 24% | -0.11 (-0.19..-0.04) | 0.74 | -1.85 |
| Year: 2023 | 1294 | 34% | +0.47 (+0.33..+0.61) | 2.34 | -2.32 |
| Year: 2024 | 1210 | 27% | -0.02 (-0.11..+0.07) | 0.95 | -2.62 |
| Year: 2025 | 674 | 25% | -0.13 (-0.22..-0.03) | 0.7 | -3.01 |
| Year: 2026 | 560 | 23% | -0.23 (-0.34..-0.12) | 0.52 | -3.46 |

Portfolio: `{"accepted": 794, "rejected_by_limits": 9511, "final_equity": 374402.0, "total_return_pct": -33.7, "cagr_pct": -4.5, "max_drawdown_pct": -33.8, "longest_drawdown_days": 2211, "years": 8.99}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 9.1, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.