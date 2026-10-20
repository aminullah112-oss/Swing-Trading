# Pre-trade checklist: **GO** (paper only)

Generated 2026-10-20T08:29:40+00:00.

| Check | Result | Detail |
|---|---|---|
| P1 block | ✅ | scan data cutoff 2026-10-19 vs expected session 2026-10-19 (0 behind) |
| P2 block | ✅ | scan provenance current |
| P3 block | ✅ | data quality TRUSTED |
| P4 block | ✅ | health WARN: new entries allowed |
| P5 block | ✅ | event log verified (142 events) |
| P6 block | ✅ | ledger reconciles |
| P7 block | ✅ | live execution disabled (paper only) |
| P8 block | ✅ | control C0 and pre-registration intact |
| P9 warn | ⚠️ | holiday calendar has 0 entries for 2026: add exchange holidays to market_holidays.json |
| P10 warn | ✅ | backtest evidence current |
| P11 info | ✅ | kill switch ENGAGED (no real orders possible; paper tracking continues) |

## Entries allowed (valid for the next session only; buy-stop, then stop)

- RAYMOND [standard · Textiles]: buy-stop 1140.8, stop 1029.01, 18 shares, risk ₹2012, valid 2026-10-20
- MOTHERSON [standard · Autos & ancillaries]: buy-stop 161.22, stop 150.96, 275 shares, risk ₹2822, valid 2026-10-20

## Rejected

- RADICO: symbol already has an active signal
- HAL: symbol already has an active signal
- KAJARIACER: execution checks blocked it; symbol already has an active signal
- DIVISLAB: symbol already has an active signal; sector cap: 2 open positions already in Pharma & healthcare (limit 2)
- ETERNAL: execution checks blocked it
- COFORGE: execution checks blocked it; symbol already has an active signal
- PNB: symbol already has an active signal

A GO means the checks passed, not that the trade is wise. Paper only: no order is sent anywhere.