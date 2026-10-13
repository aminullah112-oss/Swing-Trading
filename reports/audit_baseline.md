# Audit report and recorded baseline

Date 2026-10-13. Repository `aminullah112-oss/Swing-Trading`, branch `ccr-be6fe4f4-d4l1zo`.

## 1. Baseline recorded before any fix

| Item | Value |
|---|---|
| Commit audited | `f1ac90c` (last Backtest reports) |
| Tests at that commit | 91 passed |
| Strategy under audit | Control **C0** = `prior_high / ema50 / 120d`, score ≥ 72; `c0_hash 5e7924a41b0ee220` |
| Risk limits | 0.5% per trade, 25% position cap, 1.5% aggregate open risk (unchanged; pinned by tests) |
| Universe in use | `U159_v2` (159 symbols, hash `d02dc26765b272aa`) |
| Readiness | ≈ 1.5 / 10 (R1 0.5 + two further partial credits); live risk allowed 0% |
| C0 frozen results (reports committed at `f1ac90c`) | Hold-out CAGR 6.6%, max DD −15.7%, Calmar 0.42, Sharpe 0.79. Same-universe momentum-30: 24.1% / −23.0% / 1.05 / 1.36. Equal-weight universe: 17.1% / −20.7% / 0.83. Nifty 50: 5.8% / −15.8% / 0.36. Design period (to 2022): C0 5.7% / −8.5% / 0.67. |
| Grid row | design n 3310, avg R 0.22; hold-out n 1778, avg R 0.633, Bonferroni CI [0.089, 1.291]; full-period PF 1.65 |

These numbers are in `control/c0_frozen_baseline.json`. Raw-data reproduction needs Yahoo; it cannot run in this sandbox, so `c0_baseline.py` runs inside the Backtest workflow and compares against the frozen file with stated tolerances. C0's legacy-cost results on a synthetic fixture are pinned bit-for-bit in `tests/test_c0_control.py`.

## 2. Findings

Severity: **P0** can create an unsafe or false actionable signal or falsify readiness; **P1** weakens evidence; **P2** hygiene.

| # | Sev | Issue | Evidence | Root cause | Fix | Regression test | Status |
|---|---|---|---|---|---|---|---|
| A1 | P0 | Provisional 5-minute-derived bars could become **actionable** signals | Old `results.json`: "signals use provisional 2026-10-13 bars … for 159 symbols; official daily bar not published" (health H1c = WARN only) | Scanner substituted intraday-built bars when the daily bar was empty and only warned | `dataquality.py` + rewritten `screener.main()`: trust requires ≥ 95% official-bar coverage for the expected session, a current official Nifty bar and ≤ 2% critical errors; otherwise `stocks=[]`, `actionable=false`, previews carry `provisional=true`, a blocking check and no position | `test_scan_fail_closed.py::test_provisional_bars_never_produce_actionable_signals` and 7 more | Fixed |
| A2 | P0 | No integrity validation of vendor bars | No checks for duplicates, order, NaN, non-positive prices, OHLC consistency, zero volume, jumps, gaps | Scanner trusted the vendor frame | `validate_bars` / `assess` / quarantine per symbol; fail closed | `test_dataquality.py` (8 tests) | Fixed |
| A3 | P0 | Data lineage not recorded | Reports carried no vendor, retrieval time, session or cutoff | Not implemented | `vendor_metadata`, `expected_session`, `data_cutoff`, `data_quality` and a provenance block in `results.json` | `test_scan_fail_closed.py::test_official_current_data_yields_actionable_signals` | Fixed |
| B1 | P0 | Ledger had no real lifecycle | Statuses `pending/open/closed/expired/void` set in place; no expiry date; no history; no cancelled/rejected | Ad-hoc updates | Enforced transition table, `expires_on` from the exchange calendar, per-record history, `rejected` and `cancelled` | `test_lifecycle.py` (16 tests) | Fixed |
| B2 | P0 | Ingestion accepted anything in `results.json` | `add_signals` appended whatever was present, including provisional and stale signals; no replay protection | No ingestion contract | Idempotent by scan id and signal id; blocked when `actionable` is not true; older-cutoff scans refused; stale-dated, provisional, duplicate-symbol signals recorded as `rejected` with reasons | `test_lifecycle.py`, `test_intraday.py` | Fixed |
| B3 | P0 | No tamper-evident audit trail | `ledger.json` could be edited silently | Mutable JSON only | Hash-chained `events.jsonl`, replay of statuses, `reconcile()`, CI append-only check (`check_events.py`) | `test_lifecycle.py::test_event_chain_detects_tampering`, `test_lifecycle_is_logged_and_replay_matches_the_ledger` | Fixed (tamper-**evident** only: a writer with repository access could rewrite the whole file consistently) |
| B4 | P1 | Fill realism in forward paper | No partial fills, no gap-through-stop accounting, legacy flat costs | Backtest-grade simulation | Liquidity-capped partial fills, no-liquidity cancel, gap-loss-beyond-stop recorded, itemised cost model for forward results | `test_lifecycle.py` | Fixed |
| B5 | P1 | Legacy ledger records pre-date the gate | 13 pending records from the old pipeline | Flaw A1 | `migrate()` keeps them, flags `evidence_eligible=false`; excluded from F1/F2/F3 | `test_lifecycle.py::test_legacy_records…`, `test_consistency.py::test_legacy_signals_do_not_count…` | Fixed |
| C1 | P0 | Stale or mismatched reports earned readiness credit | Grid/benchmarks had no provenance; the universe changed 160 → 159 after they were produced | Readiness read files without checking origin | Provenance on scan, ledger, health, readiness; `reports/provenance.json` stamp (Backtest workflow only); B1/U1 earn nothing when evidence_hash, universe, age or file content ids disagree | `test_consistency.py` (16 tests) | Fixed. **Consequence:** until Backtest is rerun, B1 and U1 score 0 |
| C2 | P0 | Health could not express "data untrusted" | Three levels; provisional data was a WARN; readiness O1 passed on OK/WARN | Coarse model | Four states OK/WARN/DEGRADED/FAIL with a permission table; DEGRADED: no new entries, no ops credit; unknown status = FAIL | `test_consistency.py::test_health_*` | Fixed |
| C3 | P1 | Readiness blind to cross-artefact inconsistency | Health, ledger and results could come from different runs | No input identity | Content ids of inputs, consistency check, O1 blocked on mismatch | `test_consistency.py::test_inconsistent_artefacts…` | Fixed |
| C4 | P1 | B2 (survivorship-free) was attestation-only | `attestations.json` flag alone | Trusting a human flag | B2 now also needs `reports/pit_acceptance.json` to pass (coverage ≥ 95%, departed stocks with prices). A tightening: can only withhold credit | `test_consistency.py::test_b2_requires…`, `test_pit_and_leakage.py` | Fixed. B2 stays unearned (no PIT data exists here) |
| D1 | P0 | No pre-trade risk engine independent of signal code | Sizing in `risk.py`; no order-level checks | None existed | `riskgate.py`: per-trade risk, gap-stress loss, position cap, aggregate open risk, cash, liquidity, duplicates, stale/halted/circuit prices, broker health and reject/timeout breaker, reconciliation after restart, kill switch; every missing input rejects. Imports only `settings`, `json`, `math`, `os` (tested) | `test_riskgate.py` (39 tests) | Fixed |
| D2 | P0 | Live switch not enforced anywhere | n/a | n/a | `LIVE_EXECUTION_ENABLED = False` (not environment-overridable), `execution_guard.py` (no broker adapter; paper orders only recorded as simulated), shipped `kill_switch.json` engaged, health H14 FAILs if the flag were ever true | `test_riskgate.py::test_live_*`, `test_no_broker_or_network_code…` | Fixed |
| E1 | P1 | Universe count disagreement | Config 160, effective 157, current 159; the "agreed 156" appears nowhere | Undocumented edits (GUJARATGAS alias removed in #11) | Frozen, hash-pinned versions `U160_legacy`, `U159_v2`; manifest check; results never mixed across versions | `test_c0_control.py` | **Open**: the 156-stock list was not in the repository. Needs the owner to supply it |
| E2 | P1 | Backtest costs were flat and liquidity-free | 15 + 10 bps per side; no volume cap | Skeleton | Itemised statutory costs, slippage, 5% participation and 2% ADV caps; gross/cost/slippage decomposition; decisions use this model, C0's legacy numbers kept for continuity | `test_experiments.py`, `test_pit_and_leakage.py` | Fixed |
| E3 | P1 | Hold-out contaminated for C0 | C0 was picked as best of 12 variants with 2023+ visible | Process | Cannot be undone. Documented; new variants get a once-only hold-out (2025+) opened through a logged guard; C0 itself can only be validated forward | `test_experiments.py` | **Open by nature** |
| E4 | P1 | Survivorship bias | Universe is today's survivors | No delisted-price data available here | `pit.py` hook + `acceptance()`; every report labelled biased; B2 withheld | `test_pit_and_leakage.py` | **Open**: needs external data |
| E5 | P1 | No authoritative exchange holiday calendar | `market_holidays.json` empty | Hand-maintained | Calendar-aware expiry flags `needs_data` instead of guessing | `test_lifecycle.py::test_missing_entry_session…` | **Open**: needs a maintained calendar |
| E6 | P1 | No corporate-action feed | Splits/bonuses rely on Yahoo adjustment | None available | Jump heuristics quarantine suspect symbols (≥ 50% move errors; ≥ 30% in the last 5 bars errors) | `test_dataquality.py` | **Partly open**: heuristic only |
| F1 | P1 | No pre-registration or multiple-testing control for new ideas | Variants chosen after looking | Process | `experiments/PREREG_v1.json` pinned by SHA-256, committed before any experiment code; Bonferroni family of 8; `holdout_guard.py` | `test_experiments.py` | Fixed |
| G1 | P2 | Stale/duplicate scan outputs committed by two workflows | Scan and Backtest both commit to `main` | Shared files | Provenance + freshness limits; Backtest commits only reports, health, readiness and experiments | `test_consistency.py` | Mitigated |

## 3. What this audit could not verify
* Real-data behaviour of the new scanner, ledger and experiments: Yahoo and NSE are unreachable from this sandbox. Every real-data number requires the owner to trigger the **Daily Stock Screen** and **Backtest** workflows.
* That the vendor's adjusted prices equal exchange official closes.
* The cost constants in `settings.py` (statutory rates are assumptions dated 2026-10; check a contract note).
