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


CFG0 = bt.Config(slippage_bps=0, cost_bps=0, exit_mode='none', max_hold=50)


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
    cfg = bt.Config(slippage_bps=0, cost_bps=0, exit_mode='none', target_r=2)
    a = arrays(o=[100, 100, 100], h=[100, 101, 110], l=[99, 99, 96], c=[100, 100, 100])
    t = bt.simulate_trade(a, 0, cfg)
    assert t['reason'] == 'stop'


def test_target_fills_at_target_and_gap_above_fills_at_open():
    cfg = bt.Config(slippage_bps=0, cost_bps=0, exit_mode='none', target_r=2)
    a = arrays(o=[100, 100, 101], h=[100, 101, 107], l=[99, 99, 100], c=[100, 100, 106])
    t = bt.simulate_trade(a, 0, cfg)
    assert t['reason'] == 'target' and np.isclose(t['exit'], 106) and np.isclose(t['r'], 2.0)
    a = arrays(o=[100, 100, 108], h=[100, 101, 109], l=[99, 99, 107], c=[100, 100, 108])
    t = bt.simulate_trade(a, 0, cfg)
    assert t['reason'] == 'target_gap' and t['exit'] == 108


def test_costs_and_slippage_reduce_r():
    a = arrays(o=[100, 100, 100, 100], h=[100, 101, 101, 106], l=[99, 99, 99, 99], c=[100, 100, 100, 106])
    free = bt.simulate_trade(a, 0, bt.Config(slippage_bps=0, cost_bps=0, exit_mode='none', max_hold=3))
    paid = bt.simulate_trade(a, 0, bt.Config(slippage_bps=10, cost_bps=15, exit_mode='none', max_hold=3))
    assert free['reason'] == paid['reason'] == 'time' and paid['r'] < free['r'] - 0.05


def test_prior_high_trigger_skips_when_not_reached():
    cfg = bt.Config(trigger='prior_high', slippage_bps=0, cost_bps=0)
    a = arrays(o=[100, 100, 100], h=[102, 101, 101], l=[99, 99, 99], c=[100, 100, 100])
    assert bt.simulate_trade(a, 0, cfg) is None


def test_ema20_exit_fills_next_open():
    cfg = bt.Config(slippage_bps=0, cost_bps=0, exit_mode='ema20')
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


# ---------------- exit variants -----------------
def test_chandelier_ratchets_up_and_exits_on_trail():
    cfg = bt.Config(slippage_bps=0, cost_bps=0, exit_mode='chandelier', trail_k=2.0, max_hold=100)
    # signal close 100, atr 1 -> initial stop 97. Price runs to a high of 120 on day 4 -> trail 118.
    o = [100, 100, 106, 112, 118, 119, 112]
    h = [100, 102, 108, 114, 120, 120, 113]
    l = [99, 99, 105, 111, 117, 117, 108]
    c = [100, 101, 107, 113, 119, 118, 110]
    t = bt.simulate_trade(arrays(o, h, l, c, atr=[1.0] * 7), 0, cfg)
    assert t['reason'] == 'trail' and t['exit'] == 118 and np.isclose(t['r'], 6.0) and t['exit_idx'] == 5
    # same path but day 5 gaps open below the trail -> fills at the open
    o2 = list(o); o2[5] = 116
    t = bt.simulate_trade(arrays(o2, h, l, c, atr=[1.0] * 7), 0, cfg)
    assert t['reason'] == 'gap_trail' and t['exit'] == 116


def test_chandelier_trail_never_loosens():
    cfg = bt.Config(slippage_bps=0, cost_bps=0, exit_mode='chandelier', trail_k=2.0, max_hold=100)
    # high peaks early then ATR explodes: trail must stay at its peak level, not drop
    o = [100, 100, 110, 110, 110, 100]
    h = [100, 101, 112, 111, 111, 101]
    l = [99, 99, 109, 108, 108, 99]
    c = [100, 101, 111, 110, 110, 100]
    a = arrays(o, h, l, c, atr=[1.0, 1.0, 1.0, 5.0, 5.0, 5.0])
    t = bt.simulate_trade(a, 0, cfg)
    assert t['exit'] >= 110 - 1e-9 and t['reason'] in ('trail', 'gap_trail')   # trail held near 110 (112 - 2*1)


def test_ema50_exit_ignores_ema20_break():
    cfg = bt.Config(slippage_bps=0, cost_bps=0, exit_mode='ema50', max_hold=100)
    a = arrays(o=[100, 100, 101, 102, 103], h=[100, 101, 102, 103, 104], l=[99, 99, 100, 101, 102],
               c=[100, 101, 99, 102, 98], e20=[110] * 5)
    a['ema50'] = np.array([90.0, 90.0, 90.0, 90.0, 99.0])
    t = bt.simulate_trade(a, 0, cfg)
    # c[2]=99 < ema20 (110) is ignored; c[4]=98 < ema50 (99) -> exits at end of data close
    assert t['reason'] == 'ema50' and t['exit_idx'] == 4


def test_prepared_path_matches_unprepared():
    frames = {f'S{i}': synth(seed=i, drift=0.001) for i in range(3)}
    cfg = bt.Config(min_score=55, exit_mode='chandelier')
    t1 = bt.generate_trades(frames, cfg)
    t2 = bt.generate_trades(frames, cfg, prepared=bt.prepare(frames))
    pd.testing.assert_frame_equal(t1, t2)
    assert all(f in t1.columns for f in bt.FEATURES)


# ---------------- research module -----------------
def test_research_grid_and_diagnosis_run_on_synthetic():
    import research as rs
    frames = {f'S{i}': synth(n=1300, seed=i, drift=0.001) for i in range(8)}
    bench = synth(n=1300, seed=77)['Close']
    prepared = bt.prepare(frames)
    rows = rs.run_grid(frames, bench, prepared)
    assert len(rows) == rs.N_TRIALS == 12
    assert {'G1', 'G2', 'G3', 'promising'} <= set(rows[0])
    md = rs.grid_markdown(rows, 'note')
    assert 'Trials run: **12**' in md and 'Bonferroni' in md
    trades = bt.generate_trades(frames, rs.cfg_for('none', 'ema20', 40), bench, prepared)
    text, res = rs.diagnose(trades, 'test')
    assert 'Per-component bins' in text and 'learned_spearman_holdout' in res


def test_clustered_ci_is_wider_when_trades_share_a_month():
    import research as rs
    rng = np.random.default_rng(0)
    months = np.repeat(pd.period_range('2023-01', periods=40, freq='M').astype(str), 25)
    shock = np.repeat(rng.normal(0, 0.5, 40), 25)             # common monthly move
    r = shock + rng.normal(0, 1, len(months))
    clustered = rs.cluster_ci_mean(r, months, alpha=0.05)
    iid = rs.cluster_ci_mean(r, np.arange(len(r)), alpha=0.05)   # every trade its own cluster
    assert (clustered[1] - clustered[0]) > 1.5 * (iid[1] - iid[0])


def test_adjusted_ci_is_wider_than_unadjusted():
    import research as rs
    rng = np.random.default_rng(0)
    d = pd.DataFrame({'r': rng.normal(0.05, 1, 600),
                      'entry_date': pd.Timestamp('2023-01-02') + pd.to_timedelta(rng.integers(0, 900, 600), unit='D')})
    a = rs.adj_ci(d, 12); b = rs.adj_ci(d, 1)
    assert (a[1] - a[0]) > (b[1] - b[0])


def test_learned_score_has_no_signal_on_noise():
    import research as rs
    rng = np.random.default_rng(1)
    n = 4000
    df = pd.DataFrame({'r': rng.normal(0, 1, n), 'rsi': rng.uniform(30, 80, n), 'volr': rng.uniform(0.2, 3, n),
                       'nrising': rng.integers(0, 4, n), 'near52': rng.integers(0, 2, n),
                       'setup': rng.choice(list(rs.SETUP_POINTS), n)})
    tr, te = df.iloc[:2000], df.iloc[2000:]
    ls = rs.learned_score(tr, te)
    ci = rs.boot_spearman(ls, te['r'], np.arange(len(te)) // 20)
    assert ci[1] <= 0 <= ci[2] or abs(ci[0]) < 0.08     # pure noise: no dependable signal
