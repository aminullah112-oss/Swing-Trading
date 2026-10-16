# Pre-trade checklist: **GO** (paper only)

Generated 2026-10-16T19:02:49+00:00.

| Check | Result | Detail |
|---|---|---|
| P1 block | ✅ | scan data cutoff 2026-10-16 vs expected session 2026-10-16 (0 behind) |
| P2 block | ✅ | scan provenance current |
| P3 block | ✅ | data quality TRUSTED |
| P4 block | ✅ | health WARN: new entries allowed |
| P5 block | ✅ | event log verified (122 events) |
| P6 block | ✅ | ledger reconciles |
| P7 block | ✅ | live execution disabled (paper only) |
| P8 block | ✅ | control C0 and pre-registration intact |
| P9 warn | ⚠️ | holiday calendar has 0 entries for 2026: add exchange holidays to market_holidays.json |
| P10 warn | ⚠️ | backtest evidence stale: report has no provenance block (produced before provenance existed): rerun it |
| P11 info | ✅ | kill switch ENGAGED (no real orders possible; paper tracking continues) |

## Entries allowed (valid for the next session only; buy-stop, then stop)

- HAL [standard · Capital goods & defence]: buy-stop 4989.0, stop 4809.4, 15 shares, risk ₹2694, valid 2026-10-19
- MOTHERSON [standard · Autos & ancillaries]: buy-stop 162.77, stop 152.72, 281 shares, risk ₹2824, valid 2026-10-19
- NAVINFLUOR [standard · Chemicals & agri]: buy-stop 8274.5, stop 7824.09, 6 shares, risk ₹2702, valid 2026-10-19

## Rejected

- PNB: execution checks blocked it
- KAJARIACER: execution checks blocked it; aggregate open-risk budget would be exceeded
- COFORGE: execution checks blocked it; aggregate open-risk budget would be exceeded
- DIVISLAB: aggregate open-risk budget would be exceeded
- BOSCHLTD: aggregate open-risk budget would be exceeded
- RAYMOND: aggregate open-risk budget would be exceeded
- ETERNAL: execution checks blocked it; aggregate open-risk budget would be exceeded
- AUROPHARMA: aggregate open-risk budget would be exceeded
- RADICO: aggregate open-risk budget would be exceeded

A GO means the checks passed, not that the trade is wise. Paper only: no order is sent anywhere.