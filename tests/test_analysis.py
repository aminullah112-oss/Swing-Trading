import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import analysis as an
import screener as sc
from test_backtest import synth

GOOD = {'avg_value_cr': 50.0, 'stop_pct': 4.0, 'trigger_gap_pct': 0.5, 'close_in_range': 0.8, 'ema_dist_pct': 1.0, 'vol_ratio': 1.2}


def st(checks, cid):
    return next(c['status'] for c in checks if c['id'] == cid)


def test_clean_signal_has_no_warnings():
    ch = an.build_checks(GOOD)
    assert all(c['status'] == 'ok' for c in ch) and an.execution_ok(ch)


def test_each_threshold_trips_independently():
    assert st(an.build_checks({**GOOD, 'avg_value_cr': 1.0}), 'liquidity') == 'block'
    assert st(an.build_checks({**GOOD, 'avg_value_cr': 3.0}), 'liquidity') == 'warn'
    assert st(an.build_checks({**GOOD, 'stop_pct': 12.0}), 'stop_width') == 'warn'
    assert st(an.build_checks({**GOOD, 'stop_pct': 16.0}), 'stop_width') == 'block'
    assert st(an.build_checks({**GOOD, 'trigger_gap_pct': 5.2}), 'trigger_gap') == 'warn'
    assert st(an.build_checks({**GOOD, 'close_in_range': 0.2}), 'close_strength') == 'warn'
    assert st(an.build_checks({**GOOD, 'ema_dist_pct': 9.0}), 'extension') == 'warn'
    assert st(an.build_checks({**GOOD, 'vol_ratio': 0.3}), 'volume') == 'warn'


def test_only_blocks_remove_a_signal_from_tradeable():
    warn_only = an.build_checks({**GOOD, 'stop_pct': 12, 'vol_ratio': 0.3, 'trigger_gap_pct': 6})
    assert an.execution_ok(warn_only)                       # warnings are information
    assert not an.execution_ok(an.build_checks({**GOOD, 'avg_value_cr': 0.5}))
    assert not an.execution_ok(an.build_checks({**GOOD, 'stop_pct': 20}))


def test_market_context_trend_labels():
    idx = pd.bdate_range('2024-01-01', periods=400)
    up = pd.Series(np.linspace(100, 200, 400), index=idx)
    c = an.market_context(up, 40, 160, 5)
    assert c['nifty']['trend'].startswith('Uptrend') and c['breadth_stage2_pct'] == 25.0 and c['signals'] == 5
    down = pd.Series(np.linspace(200, 100, 400), index=idx)
    assert an.market_context(down, 10, 160, 0)['nifty']['trend'].startswith('Downtrend')
    assert an.market_context(None, 10, 160, 0)['nifty'] is None
    assert an.market_context(up.head(20), 10, 160, 0)['nifty'] is None


def test_evaluate_adds_analysis_without_changing_the_signal():
    found = None
    for seed in range(1, 8):
        df = synth(n=620, seed=seed, drift=0.0015)
        for t in range(300, 620, 3):
            rec, _ = sc.evaluate(df.iloc[:t + 1])
            if rec:
                found = (rec, df.iloc[:t + 1]); break
        if found: break
    assert found, 'no synthetic signal found'
    rec, df = found
    assert rec['decision'] == 'SIGNAL' and rec['trigger'] > rec['stop_loss']
    assert {c['id'] for c in rec['checks']} == {'liquidity', 'stop_width', 'trigger_gap', 'close_strength', 'extension', 'volume'}
    assert rec['execution_ok'] == an.execution_ok(rec['checks'])
    sp = rec['spark']
    assert len(sp['close']) == len(sp['ema20']) == len(sp['ema50']) == 60 and sp['close'][-1] == rec['price']
    exp_stop_pct = (rec['trigger'] - rec['stop_loss']) / rec['trigger'] * 100
    assert abs(rec['stop_pct'] - exp_stop_pct) < 0.01
