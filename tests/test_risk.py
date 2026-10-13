import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from risk import size_position, stop_distance


def test_risk_limited():
    p = size_position(750000, 0.01, 1000, 50)
    assert p['shares'] == 150 and p['risk_amount'] == 7500 and p['note'] is None


def test_position_cap_binds():
    p = size_position(750000, 0.01, 1000, 30)   # risk allows 250 shares, cap allows 187
    assert p['shares'] == 187 and 'position cap' in p['note']


def test_no_forced_minimum():
    p = size_position(100000, 0.005, 5000, 400)  # risk budget 500 < one-share stop 400? 1 share ok
    assert p['shares'] == 1
    p = size_position(100000, 0.005, 5000, 600)  # 500/600 -> 0
    assert p['shares'] == 0 and p['note']


def test_cash_limit():
    p = size_position(750000, 0.01, 1000, 50, cash=40000)
    assert p['shares'] == 40 and 'cash' in p['note']


def test_atr_floor_is_3pct():
    assert stop_distance(1000, 5) == 30      # 1.5*5=7.5 < 3%
    assert stop_distance(1000, 40) == 60


def test_invalid_inputs_return_zero():
    assert size_position(0, 0.01, 100, 5)['shares'] == 0
    assert size_position(1e5, 0.01, 100, 0)['shares'] == 0
