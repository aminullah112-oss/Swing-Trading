"""The live scanner and the backtest must produce the same signal on the same data."""
import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import screener as sc
import backtest as bt
import strategy
from risk import stop_distance
from test_backtest import synth


def test_live_signal_equals_backtest_signal():
    checked = signals = 0
    for seed, drift in ((1, 0.0015), (2, 0.0010), (3, 0.0012)):
        df = synth(n=620, seed=seed, drift=drift)
        ind, sig = bt.signals_for(df, strategy.backtest_config())
        for t in range(260, 620, 2):
            rec, _ = sc.evaluate(df.iloc[:t + 1])
            expected = bool(sig['signal'].iat[t])
            assert (rec is not None) == expected, (seed, t)
            checked += 1
            if rec is not None:
                signals += 1
                assert rec['trigger'] == round(float(df['High'].iat[t]), 2)       # buy-stop at the signal-day high
                sd = stop_distance(float(df['Close'].iat[t]), float(ind['atr'].iat[t]))
                assert abs(rec['stop_loss'] - round(float(df['Close'].iat[t]) - sd, 2)) < 0.011
    assert checked > 400 and signals >= 5, (checked, signals)


def test_strategy_config_matches_declared_spec():
    cfg = strategy.backtest_config()
    assert (cfg.min_score, cfg.trigger, cfg.exit_mode, cfg.max_hold) == (72, 'prior_high', 'ema50', 120)
