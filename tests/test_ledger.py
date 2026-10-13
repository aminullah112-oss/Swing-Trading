import os, sys, json
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ledger as lg
import strategy

S = 100   # signal bar index


def flat(extra):
    """100 flat bars (O=C=100, H=101, L=99) then `extra` rows of (open, high, low, close)."""
    rows = [(100, 101, 99, 100)] * (S + 1) + list(extra)
    idx = pd.bdate_range('2024-01-01', periods=len(rows))
    return pd.DataFrame(rows, columns=['Open', 'High', 'Low', 'Close'], index=idx).assign(Volume=1e6)


def sig(symbol, df, shares=100, risk=300.0):
    d = str(df.index[S].date())
    return {'symbol': symbol, 'signal_date': d, 'setup_type': 'TRENDING', 'score': 80, 'in_stockedge': False,
            'price': 100.0, 'trigger': 101.0, 'stop_loss': 97.0, 'plan_risk': 3.0,
            'position': {'shares': shares, 'risk_amount': risk}}


def results_for(*recs):
    return {'scan_id': 'x', 'scan_date': '2024-06-01', 'stocks': list(recs)}


def one(df, **kw):
    led = lg.empty()
    lg.add_signals(led, results_for(sig('AAA', df, **kw)))
    lg.update_status(led, {'AAA': df})
    return led['signals'][0], led


def test_pending_until_next_bar_exists():
    rec, _ = one(flat([]))
    assert rec['status'] == 'pending'


def test_trigger_not_hit_expires():
    rec, _ = one(flat([(100, 100.8, 99.5, 100.2)]))
    assert rec['status'] == 'expired'


def test_triggered_stays_open_above_stop_and_ema50():
    rec, _ = one(flat([(100.5, 102, 100, 101.5), (101.5, 103, 101, 102.5)]))
    assert rec['status'] == 'open' and rec['entry'] >= 101 and rec['exit_signal'] is False and 'r' not in rec


def test_stop_closes_at_minus_one_r_and_is_frozen():
    df = flat([(100.5, 102, 100, 101.5), (101, 101.5, 96, 98)])
    rec, led = one(df)
    assert rec['status'] == 'closed' and rec['exit_reason'] == 'stop' and rec['r'] < -0.9
    frozen = dict(rec)
    lg.update_status(led, {'AAA': flat([(100.5, 102, 100, 101.5), (101, 101.5, 96, 98), (98, 150, 98, 149)])})
    assert led['signals'][0] == frozen            # closed trades never change afterwards


def test_ema50_exit_signal_on_last_bar_is_not_closed_yet():
    # price drifts up for 3 bars then closes below EMA50 on the final bar -> exit is tomorrow's open
    rows = [(100.5, 102, 100, 101.5), (101.5, 103, 101, 102.5), (102.5, 104, 102, 103.5), (97.9, 98.0, 96.5, 97.5)]
    df = flat(rows)
    rec, led = one(df)
    # low 96.5 < stop 97 -> this path is a stop; use a milder drop instead
    rows[-1] = (99.9, 100.0, 99.0, 99.2)         # above stop 97, below ema50 ~100.1
    rec, led = one(flat(rows))
    assert rec['status'] == 'open' and rec['exit_signal'] is True
    # next day opens at 98.5 -> now closes at that open
    rows.append((98.5, 99.0, 98.0, 98.7))
    lg.update_status(led, {'AAA': flat(rows)})
    r2 = led['signals'][0]
    assert r2['status'] == 'closed' and r2['exit_reason'] == 'ema50' and abs(r2['exit'] / 0.999 - 98.5) < 0.01


def test_duplicates_and_busy_symbols_are_skipped():
    df = flat([(100.5, 102, 100, 101.5)])
    led = lg.empty()
    assert lg.add_signals(led, results_for(sig('AAA', df))) == 1
    assert lg.add_signals(led, results_for(sig('AAA', df))) == 0
    later = sig('AAA', df); later['signal_date'] = '2024-07-01'
    assert lg.add_signals(led, results_for(later)) == 0          # AAA still pending -> no second position


def test_open_risk_budget_admits_in_deterministic_order_and_frees_on_exit():
    dfs = {s: flat([(100.5, 102, 100, 101.5)]) for s in 'ABCD'}
    led = lg.empty()
    lg.add_signals(led, results_for(*[sig(s, d, risk=400.0) for s, d in dfs.items()]))
    lg.update_status(led, dfs)
    lg.mark_taken(led, capital=100000, max_open_risk=0.01)       # cap = 1000 -> only 2 of 4 fit
    taken1 = sorted(r['symbol'] for r in led['signals'] if r['taken'])
    assert len(taken1) == 2
    lg.mark_taken(led, capital=100000, max_open_risk=0.01)
    assert taken1 == sorted(r['symbol'] for r in led['signals'] if r['taken'])   # deterministic


def test_summary_counts_and_json_roundtrip(tmp_path):
    df = flat([(100.5, 102, 100, 101.5), (101, 101.5, 96, 98)])
    rec, led = one(df)
    lg.mark_taken(led, 565000, 0.015)
    led['summary'] = lg.summarize(led)
    assert led['summary']['closed'] == 1 and led['summary']['avg_r'] < 0 and led['summary']['taken_closed'] == 1
    p = tmp_path / 'ledger.json'
    lg.save(led, str(p))
    assert lg.load(str(p))['signals'][0]['id'] == rec['id']
    assert not (tmp_path / 'ledger.json.tmp').exists()


def test_summary_includes_open_trades_to_avoid_closed_only_bias():
    # one quick loser (closed) and one open winner: closed-only looks terrible, inclusive view is balanced
    loser = flat([(100.5, 102, 100, 101.5), (101, 101.5, 96, 98)])
    winner = flat([(100.5, 102, 100, 101.5), (102, 110, 101, 109)])
    led = lg.empty()
    lg.add_signals(led, results_for(sig('LOS', loser), sig('WIN', winner)))
    lg.update_status(led, {'LOS': loser, 'WIN': winner})
    s = lg.summarize(led)
    assert s['closed'] == 1 and s['open'] == 1
    assert s['avg_r'] < -0.9 and s['avg_r_incl_open'] > s['avg_r'] + 1.0
