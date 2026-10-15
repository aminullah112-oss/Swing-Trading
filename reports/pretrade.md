# Pre-trade checklist: **GO** (paper only)

Generated 2026-10-15T06:28:35+00:00.

| Check | Result | Detail |
|---|---|---|
| P1 block | ✅ | scan data cutoff 2026-10-14 vs expected session 2026-10-14 (0 behind) |
| P2 block | ✅ | scan provenance current |
| P3 block | ✅ | data quality TRUSTED |
| P4 block | ✅ | health WARN: new entries allowed |
| P5 block | ✅ | event log verified (59 events) |
| P6 block | ✅ | ledger reconciles |
| P7 block | ✅ | live execution disabled (paper only) |
| P8 block | ✅ | control C0 and pre-registration intact |
| P9 warn | ⚠️ | holiday calendar has 0 entries for 2026: add exchange holidays to market_holidays.json |
| P10 warn | ⚠️ | backtest evidence stale: report has no provenance block (produced before provenance existed): rerun it |
| P11 info | ✅ | kill switch ENGAGED (no real orders possible; paper tracking continues) |

## Entries allowed (valid for the next session only; buy-stop, then stop)

- MOTHERSON [standard · Autos & ancillaries]: buy-stop 162.69, stop 152.42, 275 shares, risk ₹2824, valid 2026-10-15

## Rejected

- DIVISLAB: symbol already has an active signal; sector cap: 2 open positions already in Pharma & healthcare (limit 2)
- COFORGE: symbol already has an active signal
- ETERNAL: execution checks blocked it; symbol already has an active signal; sector cap: 2 open positions already in FMCG & consumer (limit 2)
- KAJARIACER: execution checks blocked it; symbol already has an active signal
- HAL: symbol already has an active signal
- RADICO: symbol already has an active signal; sector cap: 2 open positions already in FMCG & consumer (limit 2)
- NAVINFLUOR: symbol already has an active signal
- RAYMOND: symbol already has an active signal
- AUROPHARMA: symbol already has an active signal; sector cap: 2 open positions already in Pharma & healthcare (limit 2)
- PNB: execution checks blocked it; symbol already has an active signal

A GO means the checks passed, not that the trade is wise. Paper only: no order is sent anywhere.