import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import screener as sc
import backtest as bt

KEYS = ['price', 'ema_20', 'ema_50', 'ema_200', 'ema20_slope', 'ema50_slope', 'ema200_slope', 'rsi',
        'rsi_5ago', 'st_dir', 'vol_ratio', 'vol_5d', 'ema20_dist', 'from_52h', 'atr', 'atr_pct', 'high', 'low']


def synth(n=700, seed=0, drift=0.0008):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range('2020-01-01', periods=n)
    c = 100 * np.cumprod(1 + drift + 0.015 * rng.standard_normal(n))
    o = c * (1 + 0.004 * rng.standard_normal(n))
    h = np.maximum(o, c) * (1 + 0.006 * rng.random(n))
    l = np.minimum(o, c) * (1 - 0.006 * rng.random(n))
    v = 1e6 * (1 + rng.random(n))
    return pd.DataFrame({'Open': o, 'High': h, 'Low': l, 'Close': c, 'Volume': v}, index=idx)


def test_indicator_series_matches_live_scanner():
    df = synth()
    ser = bt.indicator_series(df)
    for t in (300, 411, 520, 699):
        live = sc.indicators(df.iloc[:t + 1])
        for k in KEYS:
            assert np.isclose(ser[k].iloc[t], live[k], rtol=1e-9, atol=1e-9), (t, k, ser[k].iloc[t], live[k])


def test_no_lookahead_signals_ignore_future_bars():
    df = synth()
    cfg = bt.Config()
    _, full = bt.signals_for(df, cfg)
    _, part = bt.signals_for(df.iloc[:450], cfg)
    pd.testing.assert_frame_equal(full.iloc[:450], part)


def arrays(o, h, l, c, e20=None, atr=None):
    n = len(c)
    return {'open': np.array(o, float), 'high': np.array(h, float), 'low': np.array(l, float),
            'close': np.array(c, float), 'ema20': np.array(e20 if e20 is not None else [0.0] * n, float),
            'atr': np.array(atr if atr is not None else [1.0] * n, float)}


CFG0 = bt.Config(slippage_bps=0, cost_bps=0, ema20_exit=False, max_hold=50)


def test_stop_hit_intraday_is_minus_one_r():
    # signal close 100, atr 1 -> stop distance max(1.5, 3.0)=3 -> stop 97
    a = arrays(o=[100, 100, 99], h=[100, 101, 100], l=[99, 99, 96], c=[100, 100, 98])
    t = bt.simulate_trade(a, 0, CFG0)
    assert t['reason'] == 'stop' and t['exit'] == 97
    assert np.isclose(t['r'], (97 - 100) / 3)


def test_gap_through_stop_loses_more_than_one_r():
    a = arrays(o=[100, 100, 94], h=[100, 101, 95], l=[99, 99, 93], c=[100, 100, 94])
    t = bt.simulate_trade(a, 0, CFG0)
    assert t['reason'] == 'gap_stop' and t['exit'] == 94 and t['r'] < -1.9


def test_stop_beats_target_inside_same_bar():
    cfg = bt.Config(slippage_bps=0, cost_bps=0, ema20_exit=False, target_r=2)
    a = arrays(o=[100, 100, 100], h=[100, 101, 110], l=[99, 99, 96], c=[100, 100, 100])
    t = bt.simulate_trade(a, 0, cfg)
    assert t['reason'] == 'stop'


def test_target_fills_at_target_and_gap_above_fills_at_open():
    cfg = bt.Config(slippage_bps=0, cost_bps=0, ema20_exit=False, target_r=2)
    a = arrays(o=[100, 100, 101], h=[100, 101, 107], l=[99, 99, 100], c=[100, 100, 106])
    t = bt.simulate_trade(a, 0, cfg)
    assert t['reason'] == 'target' and np.isclose(t['exit'], 106) and np.isclose(t['r'], 2.0)
    a = arrays(o=[100, 100, 108], h=[100, 101, 109], l=[99, 99, 107], c=[100, 100, 108])
    t = bt.simulate_trade(a, 0, cfg)
    assert t['reason'] == 'target_gap' and t['exit'] == 108


def test_costs_and_slippage_reduce_r():
    a = arrays(o=[100, 100, 100, 100], h=[100, 101, 101, 106], l=[99, 99, 99, 99], c=[100, 100, 100, 106])
    free = bt.simulate_trade(a, 0, bt.Config(slippage_bps=0, cost_bps=0, ema20_exit=False, max_hold=3))
    paid = bt.simulate_trade(a, 0, bt.Config(slippage_bps=10, cost_bps=15, ema20_exit=False, max_hold=3))
    assert free['reason'] == paid['reason'] == 'time' and paid['r'] < free['r'] - 0.05


def test_prior_high_trigger_skips_when_not_reached():
    cfg = bt.Config(trigger='prior_high', slippage_bps=0, cost_bps=0)
    a = arrays(o=[100, 100, 100], h=[102, 101, 101], l=[99, 99, 99], c=[100, 100, 100])
    assert bt.simulate_trade(a, 0, cfg) is None


def test_ema20_exit_fills_next_open():
    cfg = bt.Config(slippage_bps=0, cost_bps=0, ema20_exit=True)
    a = arrays(o=[100, 100, 101, 102], h=[100, 101, 102, 103], l=[99, 99, 100, 101],
               c=[100, 101, 99, 102], e20=[90, 100, 100, 100])
    t = bt.simulate_trade(a, 0, cfg)
    assert t['reason'] == 'ema20' and t['exit'] == 102 and t['exit_idx'] == 3


def test_end_to_end_runs_and_is_deterministic():
    frames = {f'S{i}': synth(seed=i, drift=0.001) for i in range(6)}
    bench = synth(seed=99)['Close']
    cfg = bt.Config(min_score=55)
    r1, t1, eq1 = bt.run(frames, cfg, bench)
    r2, t2, eq2 = bt.run(frames, cfg, bench)
    assert r1 == r2 and len(t1) > 0
    assert (t1['exit_date'] >= t1['entry_date']).all() and (t1['entry_date'] > t1['signal_date']).all()
    # no symbol has overlapping trades
    for _, g in t1.groupby('symbol'):
        g = g.sort_values('entry_date')
        assert (g['entry_date'].iloc[1:].values > g['exit_date'].iloc[:-1].values).all()
    assert r1['portfolio']['accepted'] > 0 and r1['portfolio']['max_drawdown_pct'] <= 0
    assert r1['in_sample']['trades'] + r1['out_of_sample']['trades'] == r1['all_trades']['trades']


def test_portfolio_respects_open_risk_budget():
    frames = {f'S{i}': synth(seed=i, drift=0.001) for i in range(12)}
    cfg = bt.Config(min_score=55, risk_pct=0.005, max_open_risk=0.01)   # at most 2 concurrent positions
    rep, trades, eq = bt.run(frames, cfg)
    assert rep['portfolio']['rejected_by_limits'] > 0
