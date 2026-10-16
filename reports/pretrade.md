# Pre-trade checklist: **GO** (paper only)

Generated 2026-10-16T17:00:45+00:00.

| Check | Result | Detail |
|---|---|---|
| P1 block | ✅ | scan data cutoff 2026-10-16 vs expected session 2026-10-16 (0 behind) |
| P2 block | ✅ | scan provenance current |
| P3 block | ✅ | data quality TRUSTED |
| P4 block | ✅ | health WARN: new entries allowed |
| P5 block | ✅ | event log verified (113 events) |
| P6 block | ✅ | ledger reconciles |
| P7 block | ✅ | live execution disabled (paper only) |
| P8 block | ✅ | control C0 and pre-registration intact |
| P9 warn | ⚠️ | holiday calendar has 0 entries for 2026: add exchange holidays to market_holidays.json |
| P10 warn | ⚠️ | backtest evidence stale: report has no provenance block (produced before provenance existed): rerun it |
| P11 info | ✅ | kill switch ENGAGED (no real orders possible; paper tracking continues) |

## Entries allowed (valid for the next session only; buy-stop, then stop)

- NAVINFLUOR [standard · Chemicals & agri]: buy-stop 8274.5, stop 7824.09, 6 shares, risk ₹2702, valid 2026-10-19
- BOSCHLTD [standard · Autos & ancillaries]: buy-stop 45885.0, stop 43769.64, 1 shares, risk ₹2115, valid 2026-10-19
- RAYMOND [standard · Textiles]: buy-stop 1171.4, stop 1027.65, 14 shares, risk ₹2012, valid 2026-10-19

## Rejected

- PNB: execution checks blocked it
- HAL: symbol already has an active signal
- MOTHERSON: symbol already has an active signal
- KAJARIACER: execution checks blocked it
- COFORGE: execution checks blocked it
- DIVISLAB: symbol already has an active signal; sector cap: 2 open positions already in Pharma & healthcare (limit 2)
- ETERNAL: execution checks blocked it; symbol already has an active signal; aggregate open-risk budget would be exceeded
- AUROPHARMA: aggregate open-risk budget would be exceeded; sector cap: 2 open positions already in Pharma & healthcare (limit 2)
- RADICO: aggregate open-risk budget would be exceeded

A GO means the checks passed, not that the trade is wise. Paper only: no order is sent anywhere.