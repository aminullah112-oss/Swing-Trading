# Final report: EDGE PROTOCOL evidence programme

Date 2026-10-13 · branch `ccr-be6fe4f4-d4l1zo` · control **C0** (`prior_high/ema50/120d`, score ≥ 72, `c0_hash 5e7924a41b0ee220`) · universe **U159_v2**

## 1. Executive summary

**The verified readiness score is 0.5 / 10, not 7.** It was ≈ 1.5 before this work. The drop is the system correctly refusing credit it could not justify:

* the existing backtest reports carry no provenance and were produced before the cost model, universe and gating changed, so B1 and U1 now earn nothing until the Backtest workflow is rerun and stamped;
* the `results.json` on disk came from the old scanner (no data-quality verdict, and it used provisional 5-minute-derived bars), so health is DEGRADED and O1 earns nothing;
* only R1 (risk limits within bounds, 0.5 points) is currently earned.

**What reruns can recover:** B1 (0.5, only if C0 still passes its pre-registered gates on fresh data) and O1 (0.5, on a day the vendor has published official bars and the scan is TRUSTED). That is a ceiling of **1.5 / 10** from reruns and operator action alone. U1 (1.0, critical) is excluded from that ceiling because the frozen hold-out numbers show C0 losing to both same-universe benchmarks.

**Why 7 / 10 is not legitimately reachable now.** Eight of eleven gates cannot be satisfied by engineering:

| Gate | Points | Why it cannot be earned today |
|---|---|---|
| B2 survivorship-free backtest | 1.5 | Needs point-in-time membership and delisted-stock prices; none exist here |
| F1 100 closed forward signals | 1.0 | Needs time; the clock starts at the first evidence-eligible signal |
| F2 182 days of forward record | 1.0 | Calendar |
| F3 forward CI lower bound > 0 | 1.5 | Needs F1/F2 and a real edge |
| F4 forward not below design figure | 1.0 | Needs F1/F2 |
| E1 30 live fills | 1.0 | Needs a live trial, which needs your separate authorisation |
| S1 ≥ 10% Nifty drawdown handled | 0.5 | Needs a market event; cannot be created or backdated |
| U1 beats same-universe benchmarks | 1.0 | Evidence currently says no |

The arithmetic: 7.0 needs, at minimum, B1 + U1 + F1–F4 + O1 + R1 (0.5+1+1+1+1.5+1+0.5+0.5 = 7.0), which means a pre-registered rerun in which C0 beats momentum-30 and equal-weight on hold-out Calmar, **and** ≥ 100 closed forward signals over ≥ 182 days whose clustered CI lower bound is above zero. The earliest that forward clock can finish is mid-April 2027 (182 days from the next trusted scan), and only if the evidence supports it. Nothing in the repository can make that happen sooner, and I did not bend any weight, threshold, date or attestation to try.

**What was achieved instead:** the system can no longer turn bad data into an actionable signal, can no longer award credit from stale or unverified evidence, keeps a tamper-evident record of every signal, has an order-level risk gate and a hard-disabled live switch, and has a pre-registered, hash-pinned experiment programme with a once-only hold-out. Those are the preconditions for a score that means something. They are not an edge.

## 2. Initial versus final verified score

| Gate (weight) | Before | After (today) | State | Evidence |
|---|---|---|---|---|
| B1 (0.5) | credited from unstamped reports | **0** | blocked_defect | No provenance block: rerun Backtest |
| U1 (1.0, critical) | credited/partial | **0** | blocked_defect, and expected to fail | Frozen hold-out Calmar 0.42 vs momentum-30 1.05, equal-weight 0.83 |
| B2 (1.5, critical) | 0 | 0 | unverifiable | No PIT universe; attestation unset; objective PIT test now also required |
| F1 (1.0) | 0 | 0 | pending_time | 0 of 100 eligible closed signals (legacy records excluded) |
| F2 (1.0) | 0 | 0 | pending_time | 0 of 182 days |
| F3 (1.5, critical) | 0 | 0 | pending_time | Insufficient data |
| F4 (1.0, critical) | 0 | 0 | pending_time | Insufficient data |
| E1 (1.0, critical) | 0 | 0 | pending_time | No live fills; live trading disabled |
| S1 (0.5) | 0 | 0 | unverifiable | Attestation unset |
| O1 (0.5) | credited on OK/WARN health | **0** | blocked_defect | Health DEGRADED: scan predates the fail-closed gate |
| R1 (0.5) | 0.5 | **0.5** | passed | 0.5% / 1.5% / 25% within bounds |
| **Total (10)** | ≈ 1.5 | **0.5** | PAPER ONLY | `readiness.json`, `reports/readiness.md` |

Weights, thresholds (100 signals, 182 days, 30 fills) and attestations are unchanged and pinned by tests (`test_gate_weights_are_unchanged`). The one criterion change is a tightening: B2 additionally needs the machine-checked PIT acceptance, so it can only withhold credit.

## 3. P0 / P1 / P2

Full table with evidence, root cause, fix and regression test: `reports/audit_baseline.md`.

* **P0, fixed:** provisional bars actionable (A1); no bar validation (A2); no lineage (A3); ledger lifecycle, ingestion and audit trail (B1–B3); stale evidence earning credit and coarse health (C1, C2); no independent risk gate and no live-switch enforcement (D1, D2).
* **P1, fixed:** partial fills/gap accounting (B4); legacy records (B5); cross-artefact consistency (C3); B2 objective test (C4); costs and liquidity model (E2); pre-registration (F1).
* **P1, open:** the "agreed 156-stock" list is nowhere in the repository (E1); C0's hold-out is contaminated by its own selection (E3); survivorship bias (E4); no authoritative holiday calendar (E5); corporate actions detected by heuristic only (E6).
* **P2, mitigated:** two workflows committing to `main` (G1).

## 4. Files changed

New: `settings.py`, `universe.py` + `universe/*`, `provenance.py`, `control/*`, `c0_baseline.py`, `dataquality.py`, `events.py`, `check_events.py`, `riskgate.py`, `execution_guard.py`, `kill_switch.json`, `prereg.py`, `experiments/PREREG_v1.{json,sha256}`, `holdout_guard.py`, `metrics.py`, `experiments.py`, `pit_report.py`, `stamp_reports.py`, `forward_report.py`, `remediation.py`, `docs/OPERATOR_CHECKLIST.md`, `reports/audit_baseline.md`, this report, and 11 new test modules. Modified: `screener.py`, `ledger.py`, `paper.py`, `health.py`, `readiness.py`, `backtest.py` (optional itemised costs and liquidity caps; legacy results proven bit-identical), `analysis.py`, `pit.py`, `strategy.py` (adds `realistic_config()`; C0 identity unchanged), three workflows.

## 5. Tests run

**224 passed** (`python -m pytest -q tests`, 2 minutes). At the start of the programme: 91 passed. New coverage: data-quality and fail-closed scan, ledger lifecycle/expiry/replay/reconcile, event-chain tamper detection, health states and readiness consistency, stale-evidence blocking, risk-gate controls and structural independence (import scan, no broker code), pre-registration pinning, once-only hold-out, experiment runner pass/fail paths, look-ahead and hold-out isolation, same-bar fills, stop/target ambiguity, gap-through-stop, liquidity caps, PIT acceptance, C0 regression (pinned hash and trade digest), and an end-to-end pipeline smoke test.

**Not run:** anything against real market data. Yahoo and NSE are unreachable from this environment, so the new scanner, the C0 raw-data reproduction, the benchmarks, the eight experiments and the PIT test have only run on synthetic fixtures. The workflow files that perform those runs were edited but have not been executed on GitHub; I have not seen a workflow result for them.

## 6. C0 versus benchmarks (frozen reports, legacy costs, today's survivors)

Reproducible with `python benchmarks.py` and `python c0_baseline.py` (both run inside the Backtest workflow; digest-pinned on synthetic data).

| Hold-out (2023+) | CAGR % | Max DD % | Calmar | Sharpe |
|---|---|---|---|---|
| **C0** | 6.6 | −15.7 | 0.42 | 0.79 |
| Momentum-30 replica | 24.1 | −23.0 | 1.05 | 1.36 |
| Equal-weight universe | 17.1 | −20.7 | 0.83 | 1.17 |
| Nifty 50 | 5.8 | −15.8 | 0.36 | 0.52 |

Design period (to 2022): C0 5.7 / −8.5 / Calmar 0.67 against momentum-30 22.6 / −37.4 / 0.60. Reading: C0 earns roughly Nifty-like returns with Nifty-like drawdown, and about a quarter of the same-universe momentum return. A lower drawdown than momentum is not an advantage when the return is a quarter of it; a trader could hold less momentum. Exposure-matched and volatility-matched comparisons are implemented (`metrics.py`, `experiments.py`) and will appear in `reports/experiments.md` after the Backtest run. I have no evidence yet that C0 has an edge over simple momentum.

## 7. Experiments

Pre-registered before any experiment code or result existed (`experiments/PREREG_v1.json`, SHA-256 `b54dc824…`, committed separately ahead of the runner): H1 relative strength, H2 near 52-week high, H3 liquidity floor, H4 volatility cap, H5 score ≥ 80, H6 bull regime only, H7 0.25% risk × up to 6 positions, H8 60-day maximum hold. Bonferroni family of 8 (α = 0.00625 each). Acceptance: ≥ 100 trades over ≥ 40 months, a clustered CI on the paired net daily return difference versus C0 above zero, beating C0 in ≥ 5 of 8 yearly blocks, positive net CAGR; the hold-out (2025+) opens once, only for variants that pass, and is logged before any number is computed.

**Results: none yet.** Passed: none. Failed: none. Not-yet-run: all eight. The runner keeps every run in `reports/experiments/history/`, so a failure cannot be quietly removed. Expectation, stated so it can be judged afterwards: most or all will fail; C0 is retained unless one passes everything. Score predictiveness is a diagnostic; the earlier diagnosis already found the 0–100 score does not rank trades.

## 8. Data and survivorship limitations

* Universe is today's survivors; no delisted-stock prices. All absolute backtest numbers are optimistic. Comparisons against the same universe share the bias, which is why they are the only fair test.
* 159 symbols are in use; the original 160 included one unresolvable alias. The "agreed 156" is unidentified.
* Adjusted prices come from Yahoo; revisions can shift history. No corporate-action feed. The holiday calendar is hand-maintained and empty.
* Daily bars only. Stop-versus-target order inside a bar is assumed (stop first). Circuit limits and halts are not modelled in the backtest.
* Cost constants are assumptions dated 2026-10.

## 9. Forward-validation requirements and waiting periods

Every signal, including expired, rejected and not-taken ones, is recorded with a reason in a hash-chained log. All fills are simulated and labelled so. The 13 pre-existing records are kept and will be flagged `evidence_eligible=false` on the next ledger run, which excludes them from every gate. The gates need ≥ 100 closed eligible signals **and** ≥ 182 days (earliest finish mid-April 2027), then a clustered CI lower bound above zero. Fewer than that says almost nothing about edge. Reasonable expectation: C0 produced 3,310 design-period trades (to 2022) in backtest, so volume should not be the binding constraint; calendar time is.

## 10. Live-trading blockers and risk-control audit

| Control | Where | Status |
|---|---|---|
| Live execution off | `settings.LIVE_EXECUTION_ENABLED = False`, not env-overridable; H14 FAILs if true; no broker adapter exists | Enforced and tested |
| Kill switch | `kill_switch.json` engaged; missing or unreadable = engaged | Enforced and tested |
| Per-trade risk 0.5%, position 25%, open risk 1.5% | `riskgate.py`, `settings.py` | Enforced and tested; not raised |
| Gap stress loss ≤ 2× per-trade limit | `riskgate.py` | Enforced and tested |
| Cash, liquidity (5% volume, 2% ADV), duplicates, positions already open | `riskgate.py` | Enforced and tested |
| Stale quotes, halts, circuit proximity, market closed | `riskgate.py` | Enforced and tested; needs a live feed to supply them |
| Broker disconnect, heartbeat, reject/timeout breaker, restart reconciliation | `riskgate.py` | Logic tested; no broker exists to supply state |
| Independence from signal code | AST test on imports | Tested |
| Uncertainty blocks entries | Missing/malformed input rejects | Tested |

**Blockers to any live trial:** score and tier gates unmet (live risk allowed is 0%); capital not confirmed in `attestations.json`; no broker adapter or order-state recovery; no sector/correlation map (concentration is limited only by the aggregate risk cap); no authoritative holiday calendar or corporate-action feed; survivorship-biased evidence; no forward record; your explicit written approval. The system stays paper-only.

## 11. Next steps

| # | Step | Owner | Depends on | Acceptance |
|---|---|---|---|---|
| 1 | Trigger **Daily Stock Screen** after 16:30 IST on a trading day | You | Vendor has published bars | Run completes; `data_quality.status` TRUSTED, or UNTRUSTED with reasons; ledger reconciles; events.jsonl verifies |
| 2 | Trigger **Backtest** (runs C0 reproduction, benchmarks, 8 experiments, PIT test, stamping) | You | Step 1 not required | `reports/provenance.json` present; `c0_baseline.md` reports no drift; `experiments.md` shows every hypothesis |
| 3 | Send me the run results to read | You | 1–2 | I report actual figures and update this report; nothing here assumes the outcome |
| 4 | Supply the "agreed 156" list, or confirm U159_v2 | You | — | Universe versioned; no mixing of results |
| 5 | Maintain `market_holidays.json` | You | NSE circulars | Calendar-driven expiry shows no `needs_data` |
| 6 | Build a PIT membership file with delisted prices | You / data vendor | NSE notices, bhavcopy | `pit_acceptance.json` passes (≥ 95% coverage, departed names priced) |
| 7 | Let the paper record run | Time | 1 | ≥ 100 closed eligible signals and ≥ 182 days |
| 8 | Decide on a live trial only after gates pass | You | 1–7, plus a broker adapter and risk review | Separate written approval; no code path to a real order exists until then |

## 12. Questions only you can answer
* Which 156 stocks were agreed? The repository never contained that list.
* Is INR 565,000 the capital you will actually trade? It is unconfirmed and drives sizing.
