# Failure drills

Each row is a failure that can happen in production, what the system must do, and the test that fails if it stops doing it.
Run all with `python -m pytest -q tests`. A drill that only passes on clean data is not a drill: every test below injects the fault.

| Failure | Required behaviour | Proof |
|---|---|---|
| Yahoo returns the unfinished live session as a bar | Bar dropped, scan continues | `test_dataquality.py::test_through_drops_bars_after_the_expected_session_only`, `test_scan_fail_closed.py::test_unfinished_live_session_is_ignored_not_treated_as_an_error` |
| Stale data / vendor lag | Scan UNTRUSTED, no actionable signals | `test_scan_fail_closed.py::test_stale_data_fails_closed_without_intraday_fallback` |
| Partial publication (half the universe lagging) | UNTRUSTED | `test_scan_fail_closed.py::test_partial_publication_fails_closed` |
| A few malformed or stale symbols | Those symbols quarantined, rest trade | `test_scan_fail_closed.py::test_a_few_stale_or_malformed_symbols_are_quarantined_not_traded` |
| Widespread malformed data | UNTRUSTED | `test_scan_fail_closed.py::test_widespread_malformed_data_fails_closed` |
| Missing Nifty bar | UNTRUSTED | `test_scan_fail_closed.py::test_missing_nifty_bar_fails_closed` |
| Split / bonus not adjusted (large one-day jump) | Symbol quarantined | `test_dataquality.py::test_corporate_action_suspects_and_jumps` |
| Duplicate, out-of-order, missing sessions | Detected | `test_dataquality.py::test_each_failure_mode_is_detected`, `test_missing_sessions_and_non_session_bars` |
| Yahoo and NSE bhavcopy disagree | Mismatch share above 5% = untrusted | `test_bhavcopy.py` |
| Delayed or double cron run | Ingestion idempotent, older scan blocked as replay | `test_lifecycle.py::test_ingestion_is_idempotent_by_scan_and_by_signal_id`, `test_older_scan_is_blocked_as_replay` |
| Entry-session bar missing | Signal stays pending and is flagged, not guessed | `test_lifecycle.py::test_missing_entry_session_bar_keeps_signal_pending_and_flags_it` |
| Fill or expiry decided on an unfinished session | Voided or reversed with an audit event | `test_lifecycle.py::test_fill_on_an_unfinished_session_is_voided_with_an_audit_trail`, `test_expiry_decided_on_an_unfinished_session_is_reversed_and_not_repeated` |
| Gap through the stop | Loss beyond 1R recorded, not clipped | `test_lifecycle.py::test_gap_through_stop_is_recorded_with_loss_beyond_one_r` |
| One byte changed in the event log | Chain verification fails, pre-trade NO-GO | `test_drills.py::test_flipping_one_byte_in_the_shipped_event_log_is_detected` |
| An event deleted from the log | Chain verification fails | `test_drills.py::test_deleting_an_event_from_the_middle_breaks_the_chain` |
| Scan results empty or unreadable | NO-GO, never a default GO | `test_drills.py::test_empty_or_unreadable_scan_results_mean_no_go_never_a_default_go` |
| Ledger does not reconcile / has no reconciliation | NO-GO | `test_drills.py::test_ledger_without_a_reconciliation_is_not_trusted` |
| Pre-registration edited or its pin removed | Every runner refuses, checklist blocks | `test_drills.py::test_a_modified_preregistration_blocks_the_checklist_and_every_runner`, `test_a_missing_pin_file_is_a_failure_not_a_pass` |
| Kill switch missing, corrupt or engaged | Order rejected | `test_riskgate.py::test_kill_switch_missing_corrupt_or_engaged_blocks` |
| Live flag flipped | Still no broker code, switch not environment-overridable | `test_riskgate.py::test_live_mode_still_has_no_broker_even_if_the_switch_were_flipped`, `test_live_switch_is_not_environment_overridable` |
| Future prices leak into a signal | Never | `test_pit_and_leakage.py::test_signals_never_use_future_bars`, `test_trades_before_a_cutoff_do_not_depend_on_later_prices` |

## Not covered by a test (be honest about it)

- GitHub Actions itself failing, being throttled, or running hours late. The retry loop in `screen.yml` and the freshness checks (P1) handle it; no test exercises GitHub.
- NSE changing the bhavcopy format. The parser fails loudly and the cross-check degrades to "unavailable", it does not invent data; a real format change needs a human.
- Your own mistakes at the broker. The system places no orders.
