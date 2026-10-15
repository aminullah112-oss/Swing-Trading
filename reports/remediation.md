# Remediation matrix

Score now: **1.0/10**. Ceiling reachable by reruns and operator action alone: **1.5/10**. U1 excluded from the near-term ceiling: the frozen hold-out comparison shows C0 below momentum-30 and equal-weight on Calmar.

| Gate | Weight | State | Owner | Action | Depends on | Acceptance |
|---|---|---|---|---|---|---|
| B1 | 0.5 | blocked_defect | Engineering / operator (rerun workflow) | Run the Backtest workflow so reports are stamped with the current evidence_hash. | Workflow run; universe U159_v2 unchanged. | reports/provenance.json matches evidence_hash, is < 45 days old, and the live variant passes G1-G3. |
| U1 ⚠ | 1 | blocked_defect | Engineering / operator (rerun workflow) | Rerun the Backtest workflow, then judge the hold-out. Frozen numbers show C0 Calmar 0.42 against momentum-30 1.05 and equal-weight 0.83. | Fresh stamped benchmarks.json. | C0 hold-out Calmar >= every same-universe benchmark. On the frozen numbers it is not: do not expect these points. |
| B2 ⚠ | 1.5 | unverifiable | Operator attestation of a real-world fact | Build a point-in-time membership file (index reconstitution notices) and delisted-stock prices; set EDGE_PIT_UNIVERSE; rerun Backtest; then attest. | External data (NSE index notices, bhavcopy for delisted names) that this environment cannot fetch. | reports/pit_acceptance.json passes (coverage >= 95%, departed stocks with prices) AND the rerun passes the same gates AND attestations.json is set by the operator. |
| F1 | 1 | pending_time | Calendar time (cannot be accelerated) | Run the daily screen and ledger for months. No shortcut exists. | Signals arriving and resolving. | >= 100 closed evidence-eligible signals. |
| F2 | 1 | pending_time | Calendar time (cannot be accelerated) | Wait. The clock starts at the first evidence-eligible signal recorded under the fail-closed pipeline. | Calendar. | >= 182 days since the first eligible signal. |
| F3 ⚠ | 1.5 | pending_time | Calendar time (cannot be accelerated) | Accumulate forward data after F1/F2. | F1, F2. | Month-clustered 95% CI lower bound of forward expectancy (closed + open) > 0. |
| F4 ⚠ | 1 | pending_time | Calendar time (cannot be accelerated) | Accumulate forward data after F1/F2. | F1, F2, B1. | Forward CI upper bound >= backtest design-period average R. |
| E1 ⚠ | 1 | pending_time | Calendar time (cannot be accelerated) | Needs real fills, therefore a live trial, which needs explicit operator authorisation and every safety gate. Not available in paper mode. | Operator authorisation; micro-live prerequisites. | >= 30 real fills in live_fills.csv with slippage within 2x the model. |
| S1 | 0.5 | unverifiable | Operator attestation of a real-world fact | Needs a >= 10% Nifty drawdown to occur during the forward record, with the rules followed. Cannot be created or backdated. | Market event. | Operator attests market_stress_observed after it has actually happened. |
| O1 | 0.5 | passed | — | Run the Daily Stock Screen on a day the vendor has published the official bars; health must be OK/WARN with trusted data and consistent artefacts. | Vendor publishes daily bars; Yahoo reachable from Actions. | health OK/WARN, data_quality TRUSTED, no inconsistencies. |
| R1 | 0.5 | passed | — | Already within bounds. | — | risk/trade <= 1%, open risk <= 3%, position <= 25%. |

⚠ = critical gate. States: passed, failed (evidence says no), blocked_defect (we can fix by rerunning or repairing), pending_time, unverifiable (needs a human fact).