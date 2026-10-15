# Readiness scorecard: 1.0/10 — PAPER ONLY

Generated 2026-10-15T17:24:35+00:00. Live risk allowed: **0.0%** per trade.

| Gate | Points | Status | Value / detail |
|---|---|---|---|
| B1 Live variant passes the pre-registered backtest gates | 0/0.5 | ♻️ stale evidence | STALE EVIDENCE, no credit: report has no provenance block (produced before provenance existed): rerun it (rerun the Backtest workflow) |
| U1 Beats buy-and-hold of the same universe AND a momentum-30 replica per unit of drawdown (hold-out) **(critical)** | 0/1 | ♻️ stale evidence | STALE EVIDENCE, no credit: report has no provenance block (produced before provenance existed): rerun it |
| B2 Survivorship-free backtest passes the same gates (attested) **(critical)** | 0/1.5 | 🖐 not attested | survivorship bias remains: no point-in-time universe tested (attestations.json: survivorship_free_backtest_passed also required) |
| F1 At least 100 closed forward signals | 0/1 | ❌ fail | 0 — 1 legacy closed signal(s) excluded |
| F2 At least 182 days of forward record | 0/1 | ❌ fail | 1 |
| F3 Forward expectancy (closed + open) has a 95% CI lower bound above 0 **(critical)** | 0/1.5 | ⏳ not enough data | needs 100+ closed signals and 182+ days first (have 0, 1) |
| F4 Forward expectancy is not clearly below the backtest design-period figure **(critical)** | 0/1 | ⏳ not enough data | needs 100+ closed signals and 182+ days first (have 0, 1) |
| E1 At least 30 live fills with slippage within 2x the model **(critical)** | 0/1 | ⏳ not enough data | {'n_entries': 0, 'n_exits': 0, 'entry_slip_bps': None, 'exit_slip_bps': None} |
| S1 Forward record includes a >=10% Nifty drawdown, rules followed (attested) | 0/0.5 | 🖐 not attested | attestations.json: market_stress_observed |
| O1 Operations healthy: no health FAIL and no data lag | 0.5/0.5 | ✅ pass | WARN |
| R1 Risk limits within safe bounds (risk/trade <= 1%, open risk <= 3%, position <= 25%) | 0.5/0.5 | ✅ pass | {'capital': 565000.0, 'risk_pct': 0.5, 'max_pos_pct': 25.0, 'max_open_risk_pct': 1.5, 'max_per_sector': 2} |

Why not higher: capital not confirmed in attestations.json

Points come only from verified evidence. Gates marked "not attested" need a human to set the flag in `attestations.json` once it is true.