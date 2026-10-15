# Pre-trade checklist: **NO-GO** (paper only)

Generated 2026-10-15T06:09:06+00:00.

| Check | Result | Detail |
|---|---|---|
| P1 block | ✅ | scan data cutoff 2026-10-14 vs expected session 2026-10-14 (0 behind) |
| P2 block | ✅ | scan provenance current |
| P3 block | ✅ | data quality TRUSTED |
| P4 block | ❌ | health DEGRADED: new entries NOT allowed |
| P5 block | ✅ | event log verified (59 events) |
| P6 block | ❌ | ledger reconciliation 3 issue(s): duplicate_active |
| P7 block | ✅ | live execution disabled (paper only) |
| P8 block | ✅ | control C0 and pre-registration intact |
| P9 warn | ⚠️ | holiday calendar has 0 entries for 2026: add exchange holidays to market_holidays.json |
| P10 warn | ⚠️ | backtest evidence stale: report has no provenance block (produced before provenance existed): rerun it |
| P11 info | ✅ | kill switch ENGAGED (no real orders possible; paper tracking continues) |

## No entries allowed today


## Rejected

- *: entries blocked: health DEGRADED: new entries NOT allowed; ledger reconciliation 3 issue(s): duplicate_active

A GO means the checks passed, not that the trade is wise. Paper only: no order is sent anywhere.