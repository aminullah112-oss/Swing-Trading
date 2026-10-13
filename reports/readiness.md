# Readiness scorecard: 1.0/10 — PAPER ONLY

Generated 2026-10-13T19:43:21+00:00. Live risk allowed: **0.0%** per trade.

| Gate | Points | Status | Value / detail |
|---|---|---|---|
| B1 Live variant passes the pre-registered backtest gates | 0.5/0.5 | ✅ pass | G1/G2/G3 = True/True/True — variant prior_high/ema50/h120 |
| U1 Beats buy-and-hold of the same universe per unit of drawdown (hold-out) **(critical)** | 0/1 | ❌ fail | strategy 0.51 vs universe 0.83 — hold-out CAGR 7.5% / DD -14.8% vs universe 17.1% / -20.5% |
| B2 Survivorship-free backtest passes the same gates (attested) **(critical)** | 0/1.5 | 🖐 not attested | attestations.json: survivorship_free_backtest_passed |
| F1 At least 100 closed forward signals | 0/1 | ❌ fail | 0 |
| F2 At least 182 days of forward record | 0/1 | ❌ fail | 0 |
| F3 Forward expectancy (closed + open) has a 95% CI lower bound above 0 **(critical)** | 0/1.5 | ⏳ not enough data | needs 100+ closed signals and 182+ days first (have 0, 0) |
| F4 Forward expectancy is not clearly below the backtest design-period figure **(critical)** | 0/1 | ⏳ not enough data | needs 100+ closed signals and 182+ days first (have 0, 0) |
| E1 At least 30 live fills with slippage within 2x the model **(critical)** | 0/1 | ⏳ not enough data | {'n_entries': 0, 'n_exits': 0, 'entry_slip_bps': None, 'exit_slip_bps': None} |
| S1 Forward record includes a >=10% Nifty drawdown, rules followed (attested) | 0/0.5 | 🖐 not attested | attestations.json: market_stress_observed |
| O1 Operations healthy: no health FAIL and no data lag | 0/0.5 | ❌ fail | WARN — market data is behind the expected session; a system that buys the session after a signal cannot be traded on stale bars |
| R1 Risk limits within safe bounds (risk/trade <= 1%, open risk <= 3%, position <= 25%) | 0.5/0.5 | ✅ pass | {'capital': 565000.0, 'risk_pct': 0.5, 'max_pos_pct': 25.0, 'max_open_risk_pct': 1.5} |

Why not higher: capital not confirmed in attestations.json

Points come only from verified evidence. Gates marked "not attested" need a human to set the flag in `attestations.json` once it is true.