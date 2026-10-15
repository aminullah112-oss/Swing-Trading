# Pre-trade checklist: **GO** (paper only)

Generated 2026-10-15T19:24:44+00:00.

| Check | Result | Detail |
|---|---|---|
| P1 block | ✅ | scan data cutoff 2026-10-15 vs expected session 2026-10-15 (0 behind) |
| P2 block | ✅ | scan provenance current |
| P3 block | ✅ | data quality TRUSTED |
| P4 block | ✅ | health WARN: new entries allowed |
| P5 block | ✅ | event log verified (89 events) |
| P6 block | ✅ | ledger reconciles |
| P7 block | ✅ | live execution disabled (paper only) |
| P8 block | ✅ | control C0 and pre-registration intact |
| P9 warn | ⚠️ | holiday calendar has 0 entries for 2026: add exchange holidays to market_holidays.json |
| P10 warn | ⚠️ | backtest evidence stale: report has no provenance block (produced before provenance existed): rerun it |
| P11 info | ✅ | kill switch ENGAGED (no real orders possible; paper tracking continues) |

## Entries allowed (valid for the next session only; buy-stop, then stop)

- COFORGE [standard · IT]: buy-stop 1970.0, stop 1840.51, 21 shares, risk ₹2719, valid 2026-10-16
- AUROPHARMA [standard · Pharma & healthcare]: buy-stop 1684.3, stop 1622.23, 45 shares, risk ₹2793, valid 2026-10-16
- RAYMOND [standard · Textiles]: buy-stop 1188.4, stop 1035.69, 13 shares, risk ₹1985, valid 2026-10-16

## Rejected

- ETERNAL: execution checks blocked it
- LAURUSLABS: aggregate open-risk budget would be exceeded
- DIVISLAB: aggregate open-risk budget would be exceeded
- HAL: aggregate open-risk budget would be exceeded
- PNB: execution checks blocked it; aggregate open-risk budget would be exceeded
- RADICO: aggregate open-risk budget would be exceeded
- KAJARIACER: execution checks blocked it; aggregate open-risk budget would be exceeded
- NAVINFLUOR: aggregate open-risk budget would be exceeded
- MOTHERSON: aggregate open-risk budget would be exceeded

A GO means the checks passed, not that the trade is wise. Paper only: no order is sent anywhere.