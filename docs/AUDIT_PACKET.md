# Packet for an independent reviewer

Purpose: someone who did not build this should try to break the evidence. Look for ways the backtest or the paper record could look
better than reality. Nothing here asks you to judge the strategy's merit.

## Reproduce

```
pip install -r requirements.txt pytest
python -m pytest -q tests                     # all tests
python backtest.py --years 12 --cache history_cache_12y.pkl --name trigger --trigger prior_high
python c0_baseline.py --years 12 --cache history_cache_12y.pkl
python experiments.py && python experiments_v2.py && python robustness.py
```
The Backtest workflow does the same and commits `reports/`. Control C0 is pinned by `c0_hash 5e7924a41b0ee220`.

## Where bias could hide (check these first)

| Risk | Where to look | What a reviewer should try |
|---|---|---|
| Look-ahead in indicators | `backtest.indicator_series`, `screener.indicators` | Truncate a frame at t; signals at t must not change (`tests/test_pit_and_leakage.py` does this; extend it) |
| Look-ahead in entry/exit fills | `backtest.simulate_trade` | Entry must be on t+1 or later, inside that bar's range; stop-before-target in a shared bar |
| Cross-sectional rank uses future data | `experiments.momentum_rank` | Compare rank at t on full vs truncated universe |
| Survivorship | `universe/`, `pit.py` | Count symbols with data starting late or ending early; see `docs/PIT_DATA_REQUEST.md` |
| Adjusted-price artefacts | `dataquality.py`, Yahoo `auto_adjust` | Spot-check against raw bhavcopy around splits/dividends |
| Costs too low | `settings.py` COST_*, SLIPPAGE | Compare to a real contract note; `robustness.py` R-EXEC doubles them |
| Window cherry-picking | `experiments/PREREG_v*.json`, `holdout_log.jsonl` | Confirm hashes pinned before results; hold-out opened once per hypothesis |
| Multiple testing | `multiple_testing` in each PREREG | Count every test ever run on this data (v1: 8, benchmarks: 2, v2: 3, v3: 4 inferential) |
| Forward record polluted | `ledger.py`, `events.jsonl` | Verify the hash chain; check legacy records are excluded from evidence |
| Paper fills too generous | `ledger.update_status` | Fills need the buy-stop reached on a COMPLETED session; check gap and liquidity handling |

## Known weaknesses already admitted

- Universe is today's list (survivorship). Signals use Yahoo adjusted bars, daily only.
- C0 was chosen with knowledge of 2023+ data; the 2025+ hold-out has been looked at by PREREG_v1/v2/v3 (once per hypothesis).
- The null model in `robustness.py` ignores the one-position-per-symbol rule.
- The score does not rank trades (`reports/diagnosis.md`); conviction tiers are a checklist count.

## Report format

For each finding: file and line, the mechanism, a concrete input that shows the effect, and the size of the effect if you can estimate it.
