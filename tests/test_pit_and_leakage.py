"""Phase 4: survivorship acceptance, look-ahead, same-bar fills, stop/target ambiguity, unfilled orders, liquidity, isolation."""
import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import backtest as bt
import experiments as ex
import pit
import strategy
from test_backtest import synth
from test_ledger import flat, S


# ---------------------------------------------------------------- point-in-time acceptance
def frames_for(*syms, n=800):
    return {s: synth(n=n, seed=i) for i, s in enumerate(syms)}


def spans(rows):
    return {s: [(pd.Timestamp(a), pd.Timestamp(b) if b else pd.Timestamp.max)] for s, a, b in rows}


def test_no_pit_file_is_not_survivorship_free():
    r = pit.acceptance(None, frames_for('A'))
    assert r['passed'] is False and r['status'] == 'no_pit_universe' and 'survivorship' in r['reasons'][0]


def test_pit_file_without_departed_stocks_fails():
    r = pit.acceptance(spans([('A', '2020-01-01', None), ('B', '2020-01-01', None)]), frames_for('A', 'B'), today='2023-01-01')
    assert not r['passed'] and any('no stock that left the index' in x for x in r['reasons'])


def test_departed_stocks_without_prices_fail():
    sp = spans([('A', '2020-01-01', None), ('GONE', '2020-01-01', '2021-06-30')])
    r = pit.acceptance(sp, frames_for('A'), today='2023-01-01')
    assert not r['passed'] and any('departed' in x for x in r['reasons'])


def test_full_pit_universe_with_delisted_prices_passes():
    sp = spans([('A', '2020-01-01', None), ('GONE', '2020-01-01', '2021-06-30')])
    fr = {'A': synth(n=800, seed=1), 'GONE': synth(n=380, seed=2)}
    r = pit.acceptance(sp, fr, today='2023-01-01')
    assert r['passed'], r['reasons']
    assert r['delisted_total'] == 1 and r['delisted_with_prices'] == 1


def test_low_price_coverage_fails():
    sp = spans([('A', '2020-01-01', None), ('B', '2020-01-01', None), ('GONE', '2020-01-01', '2021-06-30')])
    fr = {'A': synth(n=800, seed=1), 'GONE': synth(n=380, seed=2)}                    # B has no prices at all
    r = pit.acceptance(sp, fr, today='2023-01-01')
    assert not r['passed'] and any('coverage' in x for x in r['reasons'])


def test_membership_filter_blocks_signals_outside_membership():
    frames = {'AAA': synth(n=1500, seed=3, drift=0.0012)}
    cfg = strategy.backtest_config()
    allow = bt.generate_trades(frames, cfg, None, None, membership=None)
    assert len(allow) > 0
    none = bt.generate_trades(frames, cfg, None, None, membership={'AAA': [(pd.Timestamp('1990-01-01'), pd.Timestamp('1990-12-31'))]})
    assert len(none) == 0


# ---------------------------------------------------------------- look-ahead
def test_signals_never_use_future_bars():
    df = synth(n=900, seed=5, drift=0.0012)
    cfg = strategy.backtest_config()
    _, full = bt.signals_for(df, cfg)
    for t in (320, 480, 640, 800):
        _, cut = bt.signals_for(df.iloc[:t + 1], cfg)
        a, b = full.iloc[t], cut.iloc[t]
        assert (a['score'], a['stage'], a['setup'], bool(a['passed'])) == (b['score'], b['stage'], b['setup'], bool(b['passed'])), t


def test_trades_before_a_cutoff_do_not_depend_on_later_prices():
    frames = {f'S{i}': synth(n=1500, seed=i, drift=0.001) for i in range(6)}
    cfg = strategy.backtest_config()
    full = bt.generate_trades(frames, cfg)
    cutoff = frames['S0'].index[1100]
    altered = {}
    for s, df in frames.items():
        d = df.copy()
        d.loc[d.index > cutoff, ['Open', 'High', 'Low', 'Close']] *= 5.0        # revise everything after the cutoff
        altered[s] = d
    alt = bt.generate_trades(altered, cfg)
    key = ['symbol', 'signal_date', 'entry_date', 'exit_date', 'entry', 'exit', 'r']
    a = full[full['exit_date'] <= cutoff - pd.Timedelta(days=5)][key].reset_index(drop=True)
    b = alt[alt['exit_date'] <= cutoff - pd.Timedelta(days=5)][key].reset_index(drop=True)
    assert len(a) > 0 and a.equals(b)


def test_cross_sectional_momentum_rank_is_causal():
    frames = {f'S{i}': synth(n=700, seed=i) for i in range(8)}
    full = ex.momentum_rank(bt.prepare(frames))
    cut_frames = {s: df.iloc[:600] for s, df in frames.items()}
    cut = ex.momentum_rank(bt.prepare(cut_frames))
    d = cut.index[-1]
    assert np.allclose(full.loc[d].values, cut.loc[d].values, equal_nan=True)


# ---------------------------------------------------------------- fills
def test_fills_never_happen_on_the_signal_bar_and_stay_inside_the_bar():
    frames = {f'S{i}': synth(n=1500, seed=i, drift=0.001) for i in range(8)}
    tr = bt.generate_trades(frames, strategy.backtest_config())
    assert len(tr) > 0
    assert (tr['entry_date'] > tr['signal_date']).all() and (tr['exit_date'] >= tr['entry_date']).all()
    cfg = strategy.backtest_config()
    slip = cfg.slippage_bps / 1e4
    for _, t in tr.iterrows():
        df = frames[t['symbol']]
        bar = df.loc[t['entry_date']]
        raw = t['entry'] / (1 + slip)
        assert bar['Low'] - 1e-6 <= raw <= bar['High'] + 1e-6 or raw >= bar['Open'] - 1e-6        # buy-stop fills at max(open, trigger) <= high


def test_unfilled_buy_stop_expires_without_a_trade():
    df = flat([(100, 100.8, 99.5, 100.2), (100.2, 120, 100, 119)])               # next bar high 100.8 < trigger 101; breakout comes a day late
    a = bt._arrays_for_test(df) if hasattr(bt, '_arrays_for_test') else None
    import ledger as lg
    arr = lg._arrays(df)
    assert bt.simulate_trade(arr, S, strategy.backtest_config(), 'T', 80) is None


def test_stop_wins_when_stop_and_target_are_inside_one_bar():
    df = flat([(100.5, 102, 100, 101.5), (101.5, 140, 90, 120)])                  # day 2 spans both the stop (97) and any target
    import ledger as lg
    cfg = strategy.backtest_config(target_r=2.0)
    t = bt.simulate_trade(lg._arrays(df), S, cfg, 'T', 80)
    assert t['reason'] == 'stop' and t['r'] < 0


def test_gap_open_below_stop_exits_at_the_open_not_the_stop():
    df = flat([(100.5, 102, 100, 101.5), (90, 91, 88, 89)])
    import ledger as lg
    t = bt.simulate_trade(lg._arrays(df), S, strategy.backtest_config(), 'T', 80)
    assert t['reason'] == 'gap_stop' and t['exit'] < 91 and t['r'] < -1.5


def test_liquidity_cap_reduces_the_position():
    frames = {f'S{i}': synth(n=1500, seed=i, drift=0.001) for i in range(8)}
    base = strategy.backtest_config()
    tr = bt.generate_trades(frames, base)
    free_stats, _ = bt.portfolio(frames, tr, base)
    cap = ex.realistic_cfg(participation_cap=1e-9, adv_cap=1e-9)
    capped_stats, _ = bt.portfolio(frames, tr, cap)
    assert capped_stats['liquidity_limited_orders'] > 0 and capped_stats['accepted'] < free_stats['accepted']


# ---------------------------------------------------------------- hold-out isolation
def test_design_window_trades_do_not_see_the_holdout():
    frames = {f'S{i}': synth(n=1700, seed=i, drift=0.001) for i in range(8)}
    cfg = ex.realistic_cfg()
    end = pd.Timestamp('2024-06-30')
    a = ex.window(bt.generate_trades(frames, cfg), None, end)
    changed = {}
    for s, df in frames.items():
        d = df.copy(); d.loc[d.index > end + pd.Timedelta(days=200), ['Open', 'High', 'Low', 'Close']] *= 0.3
        changed[s] = d
    b = ex.window(bt.generate_trades(changed, cfg), None, end)
    key = ['symbol', 'signal_date', 'entry_date', 'exit_date', 'r']
    a = a[a['exit_date'] <= end + pd.Timedelta(days=150)][key].reset_index(drop=True)
    b = b[b['exit_date'] <= end + pd.Timedelta(days=150)][key].reset_index(drop=True)
    assert len(a) > 0 and a.equals(b)
