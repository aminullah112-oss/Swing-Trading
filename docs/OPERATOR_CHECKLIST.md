# Daily operator checklist (paper-only)

Live trading is disabled in code (`settings.LIVE_EXECUTION_ENABLED = False`) and `kill_switch.json` ships engaged. Nothing below places a real order.

**This is now automated.** The Daily Stock Screen runs `pretrade.py`, which applies steps 1-6 below and writes `reports/pretrade.md`: verdict GO or NO-GO, every blocking reason, and the signals that survive the risk limits with buy-stop, stop, shares and validity date. Read that file; use the list below only to understand a NO-GO. Still manual: step 7 (holidays) and any decision to go beyond paper.

## After the Daily Stock Screen run (after 16:30 IST, once the vendor has published the day's bars)
1. **Run status.** Open the run. Red is acceptable and informative; silence is not.
2. **`results.json` → `data_quality.status`.** `TRUSTED` or `UNTRUSTED`. If `UNTRUSTED`, read `reasons`. There are **no actionable signals**; `preview` entries are labelled provisional and are not entries. Rerun later after the official bars exist. Do not trade from a preview.
2b. **NSE cross-check (health H15).** `ok` means Yahoo's closes matched NSE's own file. `unavailable` means NSE did not serve the file to the runner (the scan still runs, unverified). Mismatched symbols are quarantined; if more than 5% disagree the whole scan is UNTRUSTED.
3. **`health.json` status.** `OK`/`WARN` allow new entries; `DEGRADED` allows none (existing positions still follow their exit rules); `FAIL` stops everything. Check H10 (data), H11 (ledger reconciliation), H12 (event-log chain), H14 (live switch off).
4. **`reports/readiness.md`.** Score and mode. Anything but PAPER ONLY needs the owner's separate written approval.
5. **`reports/forward.md`.** Count of signals by fate, reasons for signals not taken, event-log verification.
6. **Ledger.** `reconciliation.ok` should be true. `needs_data` or `overdue_pending` means a bar for the permitted entry session is missing: check `market_holidays.json` and the vendor, then rerun. Never edit `ledger.json` or `events.jsonl` by hand (CI rejects non-append changes to the log).
7. **Holidays.** If an exchange holiday is not in `market_holidays.json`, add it before the next run.

## Event calendar (new, manual input)
* Keep `event_calendar.json` current: earnings dates, ex-dates, splits/bonuses and the ASM/GSM list. A known event within 5 sessions of a signal blocks the entry; an empty calendar only means "unverified" (the desk shows it).
* The NSE F&O ban list is fetched automatically when NSE allows it.

## Weekly
* Skim `reports/remediation.md`. Do not set an attestation unless the real-world fact has occurred.

## Monthly, or after any change to strategy, risk, cost or universe files
* Trigger **Backtest**. It reruns the grid, benchmarks, C0 reproduction, the pre-registered experiments, the point-in-time test, stamps provenance and regenerates readiness. Until it succeeds, B1 and U1 earn no credit.
* Confirm the C0 reproduction reports no drift beyond tolerance (`reports/c0_baseline.md`).

## Never
* Raise risk limits (0.5% / 25% / 1.5%) or edit `settings.LIVE_EXECUTION_ENABLED`, `control/C0.json` or `experiments/PREREG_v1.*`.
* Delete failed experiments, hold-out logs or reports.
* Treat a backtest as proof, or a paper record under ~100 closed signals / 182 days as evidence of edge.


## Angel One data source (optional, one-time setup)
Used only when NSE's own files cannot be fetched. Read-only market data; no orders.
1. In Angel One, enable TOTP and note the **secret key** shown next to the QR code (not the 6-digit code).
2. At smartapi.angelone.in create an app and copy its **API key**.
3. In the GitHub repo: Settings, Secrets and variables, Actions, add four secrets: `ANGEL_API_KEY`, `ANGEL_CLIENT_CODE`, `ANGEL_PIN`, `ANGEL_TOTP_SECRET`.
4. After the next scan, health H15 names the source used. Anything but `ok` in `data_quality.crosscheck.angelone` means a login or data problem; the scan still runs.
Treat these four secrets like a bank password: never paste them in chat, issues or commits. Rotate them if exposed.
