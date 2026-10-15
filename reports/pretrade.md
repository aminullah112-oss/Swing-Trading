# Pre-trade checklist: **GO** (paper only)

Generated 2026-10-15T06:37:35+00:00.

| Check | Result | Detail |
|---|---|---|
| P1 block | ✅ | scan data cutoff 2026-10-14 vs expected session 2026-10-14 (0 behind) |
| P2 block | ✅ | scan provenance current |
| P3 block | ✅ | data quality TRUSTED |
| P4 block | ✅ | health WARN: new entries allowed |
| P5 block | ✅ | event log verified (60 events) |
| P6 block | ✅ | ledger reconciles |
| P7 block | ✅ | live execution disabled (paper only) |
| P8 block | ✅ | control C0 and pre-registration intact |
| P9 warn | ⚠️ | holiday calendar has 0 entries for 2026: add exchange holidays to market_holidays.json |
| P10 warn | ⚠️ | backtest evidence stale: report has no provenance block (produced before provenance existed): rerun it |
| P11 info | ✅ | kill switch ENGAGED (no real orders possible; paper tracking continues) |

## Entries allowed (valid for the next session only; buy-stop, then stop)

- DIVISLAB [standard · Pharma & healthcare]: buy-stop 9315.0, stop 8683.95, 4 shares, risk ₹2524, valid 2026-10-15
- COFORGE [standard · IT]: buy-stop 1964.9, stop 1834.21, 21 shares, risk ₹2744, valid 2026-10-15
- HAL [standard · Capital goods & defence]: buy-stop 4948.7, stop 4757.18, 14 shares, risk ₹2681, valid 2026-10-15

## Rejected

- ETERNAL: execution checks blocked it
- KAJARIACER: execution checks blocked it
- RADICO: aggregate open-risk budget would be exceeded
- NAVINFLUOR: aggregate open-risk budget would be exceeded
- RAYMOND: aggregate open-risk budget would be exceeded
- AUROPHARMA: aggregate open-risk budget would be exceeded
- PNB: execution checks blocked it; aggregate open-risk budget would be exceeded
- MOTHERSON: aggregate open-risk budget would be exceeded

A GO means the checks passed, not that the trade is wise. Paper only: no order is sent anywhere.