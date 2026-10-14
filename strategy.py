"""The live strategy spec. Scanner, paper ledger and backtest all read it from here.

Provenance: this is the `prior_high/ema50/h120` row of reports/grid.md, one of three variants that
passed the pre-registered gates (design avg R > 0; hold-out month-clustered, Bonferroni-adjusted CI
lower bound > 0; hold-out portfolio CAGR > 0). Caveats that still apply: survivorship bias in the
universe, a strong 2023-26 hold-out, and wide confidence intervals. It is therefore a PAPER-TRADING
candidate, not a validated edge.

MIN_SCORE stays at 72 only because every tested signal had score >= 72 AND passed the filters.
The 0-100 score does not rank trades (reports/diagnosis.md), so it is a qualifier, not a conviction
measure. Removing it would be an untested change.
"""
NAME = 'slow-exit v4 (paper-trading candidate)'
MIN_SCORE = 72
TRIGGER = 'prior_high'    # buy-stop at the signal-day high; the signal expires if the next session never reaches it
EXIT_MODE = 'ema50'       # exit at the next open after a close below EMA50
MAX_HOLD = 120            # trading days
STOP_ATR_MULT = 1.5       # stop = signal close - max(1.5 x ATR, 3% of close)  (risk.stop_distance)


def backtest_config(**overrides):
    import backtest as bt
    return bt.Config(min_score=MIN_SCORE, trigger=TRIGGER, exit_mode=EXIT_MODE, max_hold=MAX_HOLD, **overrides)


def realistic_config(**overrides):
    """C0 under the itemised execution model (statutory costs, 10 bps slippage, liquidity caps). Used for forward paper
    results and for every experiment decision; backtest_config() stays the legacy-cost definition C0 was frozen with."""
    import dataclasses
    import settings
    cfg = backtest_config(cost_buy_bps=settings.COST_BUY_BPS, cost_sell_bps=settings.COST_SELL_BPS,
                          slippage_bps=settings.SLIPPAGE_BPS_PER_SIDE, participation_cap=settings.LIQUIDITY_PARTICIPATION_CAP,
                          adv_cap=settings.ADV_ORDER_CAP)
    return dataclasses.replace(cfg, **overrides) if overrides else cfg


def describe():
    return {'name': NAME, 'min_score': MIN_SCORE, 'trigger': TRIGGER, 'exit_mode': EXIT_MODE, 'max_hold': MAX_HOLD,
            'entry_rule': 'Buy-stop at the signal-day high, valid for the next session only.',
            'exit_rule': 'Exit at the next open after a daily close below EMA50, or after 120 trading days.',
            'stop_rule': 'Hard stop = signal close - max(1.5 x ATR, 3% of close), fixed at entry.'}
