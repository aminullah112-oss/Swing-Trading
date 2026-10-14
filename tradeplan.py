"""Per-opportunity trade plan from daily data: stop, profit review levels, how long such trades have lasted, the sell trigger and
an optional add-on rule. Every item carries its BASIS so nothing reads as more certain than it is:

  rule       part of control C0 and backtested: buy-stop above the signal-day high, fixed stop, exit at the next open after a
             daily close below EMA50, 120-session limit
  reference  arithmetic only: R-multiple price levels to review the trade at. C0 has no take-profit; it lets winners run
  empirical  how long, and how far, C0's past trades went (reports/hold_stats.json). Survivor-biased, historical, and a
             description of the past, not a forecast for this stock
  untested   a sensible rule that C0 never used and no backtest has checked; default is do not add
"""
import math

import settings

MIN_N = 30
R_LEVELS = (1, 2, 3)


def _pick(stats, setup):
    if not stats:
        return None, None
    s = (stats.get('by_setup') or {}).get(setup)
    if s and s.get('n', 0) >= MIN_N:
        return s, setup
    o = stats.get('overall')
    return (o, 'all setups') if o and o.get('n', 0) >= MIN_N else (None, None)


def build(rec, stats=None, capital=None, max_hold=120):
    capital = capital or settings.CAPITAL
    entry, stop, risk = rec['trigger'], rec['stop_loss'], rec['plan_risk']
    ema20, ema50, slope = rec.get('ema_20'), rec['ema_50'], rec.get('ema50_slope_pct')
    plan = {
        'entry': {'basis': 'rule', 'buy_stop': entry, 'valid': 'the next session only; if the stop is not reached the signal expires'},
        'stop': {'basis': 'rule', 'price': stop, 'note': 'fixed at entry; never moved down. A gap open below it fills at the open'},
        'profit_review_levels': {
            'basis': 'reference', 'note': 'C0 has no fixed take-profit. These are prices to review the trade at, not targets the backtest used',
            'levels': [{'r': k, 'price': round(entry + k * risk, 2), 'gain_pct': round(k * risk / entry * 100, 1)} for k in R_LEVELS]},
    }
    st, which = _pick(stats, rec.get('setup_type'))
    if st:
        w, lo = st['days_winners'], st['days_losers']
        plan['expected_duration'] = {
            'basis': 'empirical', 'from': f"{st['n']} past C0 trades ({which}); survivor-biased",
            'winners_median_days': w['p50'], 'winners_range_days': [w['p25'], w['p75']], 'losers_median_days': lo['p50'],
            'win_rate': st['win_rate'], 'typical_winner_r': st['r_winners']['p50'], 'strong_winner_r': st['r_winners']['p90'],
            'typical_winner_price': round(entry + st['r_winners']['p50'] * risk, 2),
            'note': 'Sessions the position was held before the exit rule or stop fired. A description of history, not a promise'}
    else:
        plan['expected_duration'] = {'basis': 'empirical', 'available': False,
                                     'note': f'needs at least {MIN_N} past C0 trades; appears after the next Backtest run (reports/hold_stats.json)'}
    ema_in_week = round(ema50 * (1 + slope / 100), 2) if slope is not None else None
    plan['sell_trigger'] = {
        'basis': 'rule', 'condition': 'a daily close below EMA50, then sell at the next open',
        'ema50_now': ema50, 'ema50_in_about_a_week': ema_in_week,
        'time_exit': f'sell after {max_hold} sessions if still held',
        'warning_signs': ([f'two closes below EMA20 ({ema20}): momentum fading, consider tightening attention'] if ema20 else [])
                         + ['EMA50 turning down while price is near it'],
        'note': 'The stop stays fixed. EMA50 rises with the trend, so the exit price usually ends above the stop once the trade works'}
    pos = rec.get('position') or {}
    orig = pos.get('shares', 0)
    add_px = round(entry + risk, 2)
    room = max(0, int(capital * settings.MAX_POS_PCT / add_px) - orig) if orig else 0
    add_sh = min(orig, room)
    plan['add_more'] = {
        'basis': 'untested', 'default': 'do not add', 'note': 'C0 never adds to positions and no backtest has tested it. Optional, and every limit still applies',
        'conditions': [f'daily close at or above {add_px} (entry + 1R)', f'close above EMA20 ({ema20}) and EMA50 rising',
                       f'move the stop up to the entry {entry} FIRST, so the original position carries no risk',
                       'total open risk stays within the 1.5% budget and this position within 25% of capital'],
        'max_extra_shares': add_sh, 'risk_of_add_inr': round(add_sh * risk, 0),
        'never_add': 'after a close below EMA20, when the stop has not been raised, or to a losing position'}
    return plan
