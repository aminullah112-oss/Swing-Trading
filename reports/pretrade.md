# Pre-trade checklist: **GO (no qualifying signals)** (paper only)

Generated 2026-10-15T11:25:28+00:00.

| Check | Result | Detail |
|---|---|---|
| P1 block | ✅ | scan data cutoff 2026-10-15 vs expected session 2026-10-15 (0 behind) |
| P2 block | ✅ | scan provenance current |
| P3 block | ✅ | data quality TRUSTED |
| P4 block | ✅ | health WARN: new entries allowed |
| P5 block | ✅ | event log verified (83 events) |
| P6 block | ✅ | ledger reconciles |
| P7 block | ✅ | live execution disabled (paper only) |
| P8 block | ✅ | control C0 and pre-registration intact |
| P9 warn | ⚠️ | holiday calendar has 0 entries for 2026: add exchange holidays to market_holidays.json |
| P10 warn | ⚠️ | backtest evidence stale: report has no provenance block (produced before provenance existed): rerun it |
| P11 info | ✅ | kill switch ENGAGED (no real orders possible; paper tracking continues) |

## No entries allowed today


## Rejected

- COFORGE: symbol already has an active signal; aggregate open-risk budget would be exceeded
- ETERNAL: execution checks blocked it; symbol already has an active signal; aggregate open-risk budget would be exceeded
- AUROPHARMA: aggregate open-risk budget would be exceeded
- RAYMOND: aggregate open-risk budget would be exceeded
- LAURUSLABS: aggregate open-risk budget would be exceeded
- DIVISLAB: aggregate open-risk budget would be exceeded
- HAL: symbol already has an active signal; aggregate open-risk budget would be exceeded
- PNB: execution checks blocked it; aggregate open-risk budget would be exceeded
- RADICO: aggregate open-risk budget would be exceeded
- KAJARIACER: execution checks blocked it; aggregate open-risk budget would be exceeded
- NAVINFLUOR: aggregate open-risk budget would be exceeded
- MOTHERSON: aggregate open-risk budget would be exceeded

A GO means the checks passed, not that the trade is wise. Paper only: no order is sent anywhere.