# Pre-trade checklist: **NO-GO** (paper only)

Generated 2026-10-14T19:36:19+00:00.

| Check | Result | Detail |
|---|---|---|
| P1 block | ❌ | scan data cutoff 2026-10-13 vs expected session 2026-10-14 (1 behind) |
| P2 block | ✅ | scan provenance current |
| P3 block | ❌ | data quality UNTRUSTED: only 0% of symbols have an official daily bar for the expected session 2026-10-14 (need 95%); last-bar dates: {'2026-10-13': 159}; the Nifty 50 has no official bar for 2026-10-14 (last: 2026-10-13) |
| P4 block | ❌ | health DEGRADED: new entries NOT allowed |
| P5 block | ✅ | event log verified (42 events) |
| P6 block | ✅ | ledger reconciles |
| P7 block | ✅ | live execution disabled (paper only) |
| P8 block | ✅ | control C0 and pre-registration intact |
| P9 warn | ⚠️ | holiday calendar has 0 entries for 2026: add exchange holidays to market_holidays.json |
| P10 warn | ⚠️ | backtest evidence stale: report has no provenance block (produced before provenance existed): rerun it |
| P11 info | ✅ | kill switch ENGAGED (no real orders possible; paper tracking continues) |

## No entries allowed today


## Rejected

- *: entries blocked: scan data cutoff 2026-10-13 vs expected session 2026-10-14 (1 behind); data quality UNTRUSTED: only 0% of symbols have an official daily bar for the expected session 2026-10-14 (need 95%); last-bar dates: {'2026-10-13': 159}; the Nifty 50 has no official bar for 2026-10-14 (last: 2026-10-13); health DEGRADED: new entries NOT allowed

A GO means the checks passed, not that the trade is wise. Paper only: no order is sent anywhere.