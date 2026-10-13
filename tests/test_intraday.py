import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import intraday as it
import ledger as lg
import health as hl
import screener as sc
from test_backtest import synth
from test_readiness_health import hctx, lvl, RES

DAY = '2026-10-13'


def bars5(day=DAY, n=75, seed=0, start='09:15', tz='Asia/Kolkata'):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(f'{day} {start}', periods=n, freq='5min', tz=tz)
    c = 100 + np.cumsum(rng.normal(0, 0.2, n))
    o = np.r_[100.0, c[:-1]]
    return pd.DataFrame({'Open': o, 'High': np.maximum(o, c) + 0.1, 'Low': np.minimum(o, c) - 0.1, 'Close': c,
                         'Volume': rng.integers(1000, 5000, n).astype(float)}, index=idx)


def test_daily_bar_aggregation_matches_hand_calculation():
    d = bars5()
    b = it.daily_bar_from_intraday(d, DAY)
    assert b['open'] == d['Open'].iloc[0] and b['close_last'] == d['Close'].iloc[-1]
    assert b['high'] == d['High'].max() and b['low'] == d['Low'].min()
    assert b['volume'] == d['Volume'].sum() and b['bars'] == 75
    last = d.tail(6); typ = (last['High'] + last['Low'] + last['Close']) / 3
    assert np.isclose(b['close_vwap30'], (typ * last['Volume']).sum() / last['Volume'].sum())


def test_incomplete_or_wrong_day_sessions_are_rejected():
    assert it.daily_bar_from_intraday(bars5(n=50), DAY) is None                    # partial session
    assert it.daily_bar_from_intraday(bars5(n=75, start='08:00'), DAY) is None     # ends too early (13:55)
    assert it.daily_bar_from_intraday(bars5(), '2026-10-12') is None               # different date
    assert it.daily_bar_from_intraday(pd.DataFrame(), DAY) is None
    two = pd.concat([bars5('2026-10-12', seed=1), bars5(DAY, seed=2)])             # multi-day frame: picks the right day
    assert it.daily_bar_from_intraday(two, DAY)['open'] == two.loc[two.index.date == pd.Timestamp(DAY).date(), 'Open'].iloc[0]


def daily(n=60, end='2026-10-12', tz=None):
    idx = pd.bdate_range(end=end, periods=n)
    if tz:
        idx = idx.tz_localize(tz)
    return pd.DataFrame({'Open': 100.0, 'High': 101.0, 'Low': 99.0, 'Close': 100.0, 'Volume': 1e6}, index=idx)


def test_append_provisional_row_and_never_overwrites():
    b = it.daily_bar_from_intraday(bars5(), DAY)
    for tz in (None, 'Asia/Kolkata'):
        out = it.append_provisional(daily(tz=tz), b, 'last')
        assert len(out) == 61 and out.index[-1].date() == pd.Timestamp(DAY).date()
        assert out['Close'].iloc[-1] == b['close_last'] and out['High'].iloc[-1] >= out['Close'].iloc[-1] >= out['Low'].iloc[-1]
    v = it.append_provisional(daily(), b, 'vwap30')
    assert v['Close'].iloc[-1] == b['close_vwap30']
    same_day = daily(end=DAY)                                                      # official bar already there
    assert len(it.append_provisional(same_day, b, 'last')) == len(same_day)
    assert len(it.append_provisional(daily(), None, 'last')) == 60


def test_build_bars_skips_missing_tickers_and_short_sessions():
    a, c = bars5(seed=1), bars5(seed=2, n=40)
    frame = pd.concat({'AAA.NS': a, 'CCC.NS': c}, axis=1)
    out = it.build_bars(frame, {'AAA': 'AAA.NS', 'BBB': 'BBB.NS', 'CCC': 'CCC.NS'}, DAY)
    assert set(out) == {'AAA'}


def test_audit_and_method_choice():
    bars = {f'S{i}': {'open': 100, 'high': 101, 'low': 99, 'close_last': 100.00, 'close_vwap30': 100.30, 'volume': 1e6} for i in range(60)}
    official = {f'S{i}': {'open': 100, 'high': 101, 'low': 99, 'close': 100.28, 'volume': 1.02e6} for i in range(60)}
    a = it.audit(bars, None, official)
    assert a['symbols'] == 60 and a['median_abs_error_bps']['close_vwap30'] < a['median_abs_error_bps']['close_last']
    assert a['median_abs_error_bps']['volume'] > 0
    assert it.choose_method([a]) == 'vwap30'
    flipped = {'symbols': 80, 'median_abs_error_bps': {'close_last': 2.0, 'close_vwap30': 25.0}}
    assert it.choose_method([flipped]) == 'last'
    assert it.choose_method([]) == 'last'
    assert it.choose_method([{'symbols': 10, 'median_abs_error_bps': {'close_last': 50, 'close_vwap30': 1}}]) == 'last'   # too few symbols
    assert it.audit(bars, None, {}) is None


def _signal_case():
    for seed in range(1, 10):
        df = synth(n=620, seed=seed, drift=0.0015)
        for t in range(300, 619, 3):
            rec, _ = sc.evaluate(df.iloc[:t + 1])
            if rec:
                return df, t, rec
    raise AssertionError('no synthetic signal')


def test_ledger_verifies_or_voids_provisional_signals_against_the_official_bar():
    df, t, rec = _signal_case()
    led = lg.empty()
    res = {'scan_id': 'x', 'scan_date': '2026-10-14', 'stocks': [{
        'symbol': 'AAA', 'signal_date': str(df.index[t].date()), 'setup_type': rec['setup_type'], 'score': rec['score'],
        'price': rec['price'], 'trigger': rec['trigger'], 'stop_loss': rec['stop_loss'], 'plan_risk': rec['plan_risk'],
        'provisional': True, 'position': {'shares': 10, 'risk_amount': 100.0}}]}
    lg.add_signals(led, res)
    assert led['signals'][0]['provisional'] is True
    lg.update_status(led, {'AAA': df})
    s = led['signals'][0]
    assert s['status'] != 'void' and s['verified'] is True and s['trigger_official'] == rec['trigger']
    # a provisional "signal" on a date that is not a signal on the official bar is voided and excluded from stats
    bad = None
    for u in range(300, 619):
        r2, _ = sc.evaluate(df.iloc[:u + 1])
        if r2 is None:
            bad = u; break
    led2 = lg.empty()
    res2 = {'scan_id': 'x', 'scan_date': 'd', 'stocks': [dict(res['stocks'][0], signal_date=str(df.index[bad].date()))]}
    lg.add_signals(led2, res2)
    lg.update_status(led2, {'AAA': df})
    assert led2['signals'][0]['status'] == 'void' and 'official' in led2['signals'][0]['void_reason']
    summ = lg.summarize(led2)
    assert summ['void'] == 1 and summ['closed'] == 0 and lg.forward_returns(led2)[0].size == 0


def test_health_reports_provisional_data():
    res = dict(RES, provisional={'used': True, 'date': '2027-06-01', 'method': 'last', 'symbols': 150},
               provisional_audit={'median_abs_error_bps': {'close_last': 12.0}})
    c = hl.run_checks(hctx(res=res))
    assert lvl(c, 'H1c') == 'warn' and '12.0 bps' in next(x['msg'] for x in c if x['id'] == 'H1c')
    assert lvl(hl.run_checks(hctx(res=dict(RES, provisional={'used': False}))), 'H1c') is None
