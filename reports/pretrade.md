# Pre-trade checklist: **NO-GO** (paper only)

Generated 2026-11-09T23:21:19+00:00.

| Check | Result | Detail |
|---|---|---|
| P1 block | ✅ | scan data cutoff 2026-11-09 vs expected session 2026-11-09 (0 behind) |
| P2 block | ✅ | scan provenance current |
| P3 block | ❌ | data quality UNTRUSTED: 37 symbols (23.3%) have critical data errors (limit 2%); Yahoo disagrees with NSE's own file for 23% of compared symbols (limit 5%) |
| P4 block | ❌ | health FAIL: new entries NOT allowed |
| P5 block | ✅ | event log verified (330 events) |
| P6 block | ❌ | ledger reconciliation 3 issue(s): needs_data |
| P7 block | ✅ | live execution disabled (paper only) |
| P8 block | ✅ | control C0 and pre-registration intact |
| P9 warn | ⚠️ | holiday calendar has 0 entries for 2026: add exchange holidays to market_holidays.json |
| P10 warn | ✅ | backtest evidence current |
| P11 info | ✅ | kill switch ENGAGED (no real orders possible; paper tracking continues) |

## No entries allowed today


## Rejected

- *: entries blocked: data quality UNTRUSTED: 37 symbols (23.3%) have critical data errors (limit 2%); Yahoo disagrees with NSE's own file for 23% of compared symbols (limit 5%); health FAIL: new entries NOT allowed; ledger reconciliation 3 issue(s): needs_data

A GO means the checks passed, not that the trade is wise. Paper only: no order is sent anywhere.