import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import hold_stats
import settings
import tradeplan as tp

REC = {'trigger': 100.0, 'stop_loss': 95.0, 'plan_risk': 5.0, 'ema_20': 98.0, 'ema_50': 94.0, 'ema50_slope_pct': 1.0, 'setup_type': 'TRENDING',
       'position': {'shares': 100, 'risk_amount': 500.0}}


def stats(n=200):
    blk = {'n': n, 'win_rate': 0.45, 'days_winners': {'p25': 30, 'p50': 48, 'p75': 80}, 'days_losers': {'p25': 3, 'p50': 6, 'p75': 12},
           'r_winners': {'p50': 1.8, 'p75': 3.0, 'p90': 5.5}}
    return {'overall': blk, 'by_setup': {'TRENDING': dict(blk, n=n)}}


def test_levels_stop_and_sell_trigger_follow_c0_arithmetic():
    p = tp.build(REC, stats(), 565000)
    lv = {l['r']: l for l in p['profit_review_levels']['levels']}
    assert lv[1]['price'] == 105.0 and lv[2]['price'] == 110.0 and lv[3]['price'] == 115.0 and lv[2]['gain_pct'] == 10.0
    assert p['stop']['price'] == 95.0 and p['stop']['basis'] == 'rule'
    s = p['sell_trigger']
    assert 'close below EMA50' in s['condition'] and s['ema50_now'] == 94.0 and s['ema50_in_about_a_week'] == 94.94 and '120 sessions' in s['time_exit']
    assert p['profit_review_levels']['basis'] == 'reference' and 'no fixed take-profit' in p['profit_review_levels']['note']


def test_duration_is_empirical_labelled_and_needs_enough_history():
    d = tp.build(REC, stats(), 565000)['expected_duration']
    assert d['basis'] == 'empirical' and d['winners_median_days'] == 48 and d['winners_range_days'] == [30, 80] and d['typical_winner_price'] == 109.0
    assert 'survivor-biased' in d['from']
    assert tp.build(REC, None, 565000)['expected_duration']['available'] is False
    assert tp.build(REC, stats(n=10), 565000)['expected_duration']['available'] is False          # too few trades
    thin = stats(); thin['by_setup']['TRENDING']['n'] = 5
    assert 'all setups' in tp.build(REC, thin, 565000)['expected_duration']['from']               # falls back to overall


def test_add_more_is_untested_defaults_to_no_and_respects_caps():
    a = tp.build(REC, stats(), 565000)['add_more']
    assert a['basis'] == 'untested' and a['default'] == 'do not add' and a['max_extra_shares'] <= 100
    assert any('move the stop up to the entry' in c for c in a['conditions'])
    big = dict(REC, position={'shares': 1300, 'risk_amount': 6500.0})                                # 1300 x 105 already ~24% of capital
    cap = int(565000 * settings.MAX_POS_PCT / 105) - 1300
    assert tp.build(big, stats(), 565000)['add_more']['max_extra_shares'] == max(0, cap)
    assert tp.build(dict(REC, position=None), stats(), 565000)['add_more']['max_extra_shares'] == 0


def test_hold_stats_from_trades():
    rng = np.random.default_rng(0)
    n = 120
    t = pd.DataFrame({'r': rng.normal(0.3, 1.5, n), 'hold': rng.integers(2, 120, n), 'setup': ['TRENDING'] * 80 + ['PULLBACK_EMA20'] * 30 + ['X'] * 10})
    s = hold_stats.build(t)
    assert s['overall']['n'] == 120 and set(s['by_setup']) == {'TRENDING', 'PULLBACK_EMA20', 'X'}
    b = s['by_setup']['TRENDING']
    assert b['days_winners']['p25'] <= b['days_winners']['p50'] <= b['days_winners']['p75'] and b['r_winners']['p50'] > 0
    assert s['provenance']['kind'] == 'hold_stats'
    plan = tp.build(REC, s, 565000)
    assert plan['expected_duration']['winners_median_days'] == b['days_winners']['p50']
