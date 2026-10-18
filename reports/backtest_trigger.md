# Backtest: trigger

Config: `{"min_score": 72, "trigger": "prior_high", "target_r": 0.0, "exit_mode": "ema20", "trail_k": 3.0, "max_hold": 40, "slippage_bps": 10.0, "cost_bps": 15.0, "capital": 565000, "risk_pct": 0.005, "max_pos_pct": 0.25, "max_open_risk": 0.015, "split_date": "2023-01-01", "cost_buy_bps": null, "cost_sell_bps": null, "participation_cap": null, "adv_cap": null}`

| Slice | Trades | Win | Avg R (naive iid 95% CI, too narrow: trades cluster by date) | PF | Worst R |
|---|---|---|---|---|---|
| ALL | 10274 | 27% | +0.04 (+0.01..+0.07) | 1.09 | -3.46 |
| Design period | 6542 | 26% | +0.00 (-0.03..+0.04) | 1.01 | -3.43 |
| Hold-out (from 2023-01-01) | 3732 | 28% | +0.10 (+0.04..+0.16) | 1.24 | -3.46 |
| Score: 72-79 | 2780 | 29% | +0.05 (-0.01..+0.11) | 1.12 | -2.95 |
| Score: 80-89 | 5069 | 26% | +0.05 (+0.01..+0.10) | 1.14 | -3.46 |
| Score: 90+ | 2425 | 26% | -0.01 (-0.07..+0.05) | 0.98 | -3.43 |
| Setup: BREAKOUT_CONT | 333 | 36% | +0.20 (-0.13..+0.52) | 1.3 | -1.89 |
| Setup: COMPRESSION | 113 | 32% | +0.01 (-0.33..+0.36) | 1.02 | -1.88 |
| Setup: PULLBACK_EMA20 | 5174 | 25% | +0.01 (-0.03..+0.05) | 1.02 | -3.46 |
| Setup: PULLBACK_EMA50 | 3150 | 27% | +0.01 (-0.03..+0.06) | 1.04 | -2.43 |
| Setup: TRENDING | 1504 | 33% | +0.15 (+0.04..+0.26) | 1.28 | -2.95 |
| Regime: bear | 1200 | 29% | -0.00 (-0.09..+0.08) | 1.0 | -3.46 |
| Regime: bull | 9074 | 27% | +0.04 (+0.01..+0.08) | 1.1 | -3.43 |
| Exit: ema20 | 9210 | 27% | -0.06 (-0.08..-0.04) | 0.82 | -3.26 |
| Exit: ema20_pending | 1 | 0% | -0.08 (n/a: 1 trade) | 0.0 | -0.08 |
| Exit: end_of_data | 4 | 100% | +4.91 (-2.69..+12.52) | None | 0.66 |
| Exit: gap_stop | 28 | 0% | -1.79 (-2.02..-1.56) | 0.0 | -3.46 |
| Exit: stop | 719 | 0% | -1.35 (-1.36..-1.34) | 0.0 | -2.62 |
| Exit: time | 312 | 100% | +6.21 (+5.80..+6.62) | None | 1.12 |
| Year: 2017 | 388 | 30% | +0.17 (+0.01..+0.33) | 1.47 | -2.12 |
| Year: 2018 | 956 | 22% | -0.18 (-0.25..-0.11) | 0.59 | -2.05 |
| Year: 2019 | 1093 | 23% | -0.11 (-0.18..-0.04) | 0.73 | -2.32 |
| Year: 2020 | 1034 | 31% | +0.24 (+0.12..+0.35) | 1.64 | -3.43 |
| Year: 2021 | 1900 | 28% | +0.07 (+0.00..+0.13) | 1.18 | -1.84 |
| Year: 2022 | 1171 | 24% | -0.11 (-0.18..-0.03) | 0.75 | -1.85 |
| Year: 2023 | 1285 | 34% | +0.47 (+0.33..+0.61) | 2.34 | -2.32 |
| Year: 2024 | 1207 | 27% | -0.02 (-0.11..+0.07) | 0.95 | -2.62 |
| Year: 2025 | 674 | 25% | -0.13 (-0.22..-0.03) | 0.7 | -3.01 |
| Year: 2026 | 566 | 23% | -0.23 (-0.34..-0.12) | 0.52 | -3.46 |

Portfolio: `{"accepted": 781, "rejected_by_limits": 9493, "final_equity": 369471.0, "total_return_pct": -34.6, "cagr_pct": -4.6, "max_drawdown_pct": -36.8, "longest_drawdown_days": 2212, "years": 8.99, "liquidity_limited_orders": 0, "avg_exposure_pct": 32.0, "max_exposure_pct": 52.1, "time_in_cash_pct": 1.2, "avg_positions": 2.59}`
Benchmark (Nifty buy&hold): `{"cagr_pct": 9.6, "max_drawdown_pct": -38.4}`

**Limitations:** survivorship bias (today's universe), StockEdge flag not testable, daily bars only (stop assumed first if stop and target share a bar), Yahoo data. Treat as an optimistic upper bound; an edge that fails here is unlikely to exist, one that passes is not yet proven.