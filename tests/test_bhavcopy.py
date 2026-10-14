import os, sys
from datetime import date
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import bhavcopy as bc
import dataquality as dq
from test_scan_fail_closed import make_bulk, run_scan, EXPECTED  # noqa: F401  (run_scan is a fixture)
import screener as sc

S = date(2026, 10, 13)


def udiff(rows, day='2026-10-13'):
    head = 'TradDt,BizDt,Sgmt,FinInstrmTp,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric,TtlTradgVol'
    return '\n'.join([head] + [f'{day},{day},CM,STK,{s},{ser},{o},{h},{l},{c},{c},{pc},{v}' for s, ser, o, h, l, c, pc, v in rows])


def legacy(rows, day='13-Oct-2026'):
    head = 'SYMBOL, SERIES, DATE1, PREV_CLOSE, OPEN_PRICE, HIGH_PRICE, LOW_PRICE, LAST_PRICE, CLOSE_PRICE, AVG_PRICE, TTL_TRD_QNTY'
    return '\n'.join([head] + [f'{s}, {ser}, {day}, {pc}, {o}, {h}, {l}, {c}, {c}, {c}, {v}' for s, ser, o, h, l, c, pc, v in rows])


ROWS = [('AAA', 'EQ', 100, 103, 99, 102, 100.5, 5000), ('BBB', 'BE', 50, 51, 49, 50, 50, 10), ('CCC', 'EQ', 10, 9, 11, 10, 10, 100)]   # CCC: high < low


def test_parsers_read_both_layouts_keep_eq_only_and_reject_bad_rows_and_dates():
    for fn, text in ((bc.parse_udiff, udiff(ROWS)), (bc.parse_legacy, legacy(ROWS))):
        r = fn(text, S)
        assert set(r) == {'AAA'}                                   # BBB is series BE, CCC has an impossible OHLC
        assert r['AAA'] == {'open': 100.0, 'high': 103.0, 'low': 99.0, 'close': 102.0, 'prev_close': 100.5, 'volume': 5000.0}
    assert bc.parse_udiff(udiff(ROWS, day='2026-10-12'), S) == {} and bc.parse_legacy(legacy(ROWS, day='12-Oct-2026'), S) == {}   # stale file


def big(n=600, day='2026-10-13'):
    return udiff([(f'S{i}', 'EQ', 100, 101, 99, 100.5, 100, 1000) for i in range(n)], day)


def test_fetch_ok_fallback_and_failure_modes(monkeypatch):
    ok = bc.fetch(S, downloader=lambda url: big())
    assert ok['status'] == 'ok' and len(ok['rows']) == 600 and 'udiff' in ok['source']
    # first URL blocked, second (legacy layout) works
    def dl(url):
        if 'BhavCopy_NSE' in url:
            raise OSError('403 forbidden')
        return legacy([(f'S{i}', 'EQ', 100, 101, 99, 100.5, 100, 1000) for i in range(600)])
    r = bc.fetch(S, downloader=dl)
    assert r['status'] == 'ok' and 'legacy' in r['source']
    # not published yet / blocked everywhere
    def boom(url):
        raise OSError('404')
    u = bc.fetch(S, downloader=boom)
    assert u['status'] == 'unavailable' and u['rows'] == {} and '404' in u['note']
    # a partial or wrong-date file is not accepted
    assert bc.fetch(S, downloader=lambda url: udiff(ROWS))['status'] == 'unavailable'
    assert bc.fetch(S, downloader=lambda url: big(day='2026-10-12'))['status'] == 'unavailable'
    monkeypatch.setenv('EDGE_BHAVCOPY', '0')
    assert bc.fetch(S, downloader=boom)['status'] == 'disabled'


def frame(last_close, prev_close, end='2026-10-13', tz=None, n=70):
    idx = pd.bdate_range(end=end, periods=n)
    if tz:
        idx = idx.tz_localize(tz)
    c = np.full(n, 100.0); c[-1], c[-2] = last_close, prev_close
    return pd.DataFrame({'Open': c, 'High': c * 1.01, 'Low': c * 0.99, 'Close': c, 'Volume': 1e6}, index=idx)


def nse(rows):
    return {'status': 'ok', 'source': 'test', 'rows': {s: dict(open=o, high=h, low=l, close=c, prev_close=pc, volume=v) for s, o, h, l, c, pc, v in rows}}


def test_reconcile_matches_flags_mismatch_and_adjustment_gaps():
    res = {'A': (frame(102.0, 100.0), 'A'), 'B': (frame(106.0, 100.0), 'B'), 'C': (frame(102.0, 50.0), 'C'), 'D': (frame(102, 100), 'D')}
    n = nse([('A', 100, 103, 99, 102.1, 100, 1), ('B', 100, 103, 99, 102.0, 100, 1), ('C', 100, 103, 99, 102.0, 100, 1)])
    out, rep = bc.reconcile(res, n, S)
    assert rep['compared'] == 3 and rep['close_mismatch'] == {'B': round((106 / 102 - 1) * 100, 3)}        # A is within 0.25%
    assert list(rep['adjustment_mismatch']) == ['C'] and rep['not_in_bhavcopy'] == ['D']
    assert rep['mismatch_share'] == round(2 / 3, 4)
    per = {u: dq.summarize_symbol(df, S) for _, (df, u) in out.items()}
    assert bc.flag(per, rep) == 2 and 'nse_close_mismatch' in per['B']['errors'] and 'nse_adjustment_mismatch' in per['C']['errors']
    assert 'B' not in dq.actionable_symbols(per, S) and 'A' in dq.actionable_symbols(per, S)


def test_reconcile_fills_a_lagging_symbol_only_when_continuity_holds():
    lag = {'A': (frame(100.0, 99.0, end='2026-10-12'), 'A'), 'B': (frame(100.0, 99.0, end='2026-10-12'), 'B')}
    n = nse([('A', 101, 104, 100, 103, 100.2, 5000), ('B', 60, 62, 58, 61, 60, 5000)])           # B: NSE prev close 60 vs Yahoo 100: a split
    out, rep = bc.reconcile(lag, n, S)
    assert rep['filled'] == ['A'] and rep['cannot_fill'] == ['B']
    a = out['A'][0]
    assert a.index[-1] == pd.Timestamp('2026-10-13') and a['Close'].iloc[-1] == 103 and a['Volume'].iloc[-1] == 5000 and len(a) == 71
    assert out['B'][0].index[-1] == pd.Timestamp('2026-10-12')


def test_reconcile_handles_timezone_aware_indexes_and_unavailable_source():
    tz = {'A': (frame(100.0, 99.0, end='2026-10-12', tz='Asia/Kolkata'), 'A')}
    out, rep = bc.reconcile(tz, nse([('A', 101, 104, 100, 103, 100.2, 5000)]), S)
    assert rep['filled'] == ['A'] and out['A'][0].index[-1].tzinfo is not None and out['A'][0].index[-1].date() == S
    same, rep2 = bc.reconcile(tz, {'status': 'unavailable', 'rows': {}}, S)
    assert same is tz and rep2['status'] == 'unavailable' and rep2['filled'] == []


# ------------------------------------------------------------ end to end through the scanner
def nse_for_bulk(bulk, skew=None, n=None):
    """An NSE file that agrees with the synthetic Yahoo data (optionally with some symbols off by `skew`)."""
    rows = {}
    syms = sc.YF_TICKERS[:n] if n else sc.YF_TICKERS
    for i, t in enumerate(syms):
        c = bulk[(t, 'Close')].dropna()
        last, prev = float(c.iloc[-1]), float(c.iloc[-2])
        close = last * (1 + (skew or {}).get(i, 0.0))
        rows[t.replace('.NS', '')] = dict(open=last, high=last * 1.01, low=last * 0.99, close=close, prev_close=prev, volume=1e6)
    return {'status': 'ok', 'source': 'test file', 'rows': rows, 'retrieved_at': 'x'}


def test_scan_quarantines_symbols_nse_disagrees_with(run_scan, monkeypatch):
    bulk = make_bulk()
    monkeypatch.setattr(sc.bhavcopy, 'fetch', lambda session: nse_for_bulk(bulk, skew={3: 0.02, 7: -0.03}))
    r = run_scan(bulk)
    q = r['data_quality']['quarantined']
    bad = {sc.YF_TICKERS[3].replace('.NS', ''), sc.YF_TICKERS[7].replace('.NS', '')}
    assert r['data_quality']['status'] == 'TRUSTED' and bad <= set(q) and all('nse_close_mismatch' in q[s] for s in bad)
    assert not (bad & {s['symbol'] for s in r['stocks']})
    assert r['data_quality']['crosscheck']['compared'] > 100 and len(r['data_quality']['crosscheck']['close_mismatch']) == 2


def test_scan_fails_closed_when_yahoo_widely_disagrees_with_nse(run_scan, monkeypatch):
    bulk = make_bulk()
    monkeypatch.setattr(sc.bhavcopy, 'fetch', lambda session: nse_for_bulk(bulk, skew={i: 0.05 for i in range(0, 40)}))
    r = run_scan(bulk)
    assert r['data_quality']['status'] == 'UNTRUSTED' and r['actionable'] is False and r['stocks'] == []
    assert any("NSE's own file" in why for why in r['data_quality']['reasons'])


def test_nse_file_removes_the_yahoo_publication_lag(run_scan, monkeypatch):
    full = make_bulk()
    lag = full.copy()
    for t in sc.YF_TICKERS + sc.ALIAS_TICKERS:
        for f in ('Open', 'High', 'Low', 'Close', 'Volume'):
            lag.loc[lag.index[-1], (t, f)] = np.nan            # Yahoo has the row but no values for the stocks; the Nifty is current
    monkeypatch.setattr(sc.bhavcopy, 'fetch', lambda session: {
        'status': 'ok', 'source': 'test file', 'retrieved_at': 'x',
        'rows': {t.replace('.NS', ''): dict(open=float(full[(t, 'Open')].iloc[-1]), high=float(full[(t, 'High')].iloc[-1]), low=float(full[(t, 'Low')].iloc[-1]),
                                            close=float(full[(t, 'Close')].iloc[-1]), prev_close=float(full[(t, 'Close')].iloc[-2]), volume=float(full[(t, 'Volume')].iloc[-1]))
                 for t in sc.YF_TICKERS}})
    r = run_scan(lag, with_intraday=False)
    cc = r['data_quality']['crosscheck']
    assert len(cc['filled']) > 100 and r['data_quality']['status'] == 'TRUSTED' and r['actionable'] is True and r['summary']['signals'] > 0
    assert all(not s.get('provisional') for s in r['stocks'])


def test_unavailable_nse_file_does_not_block_but_is_recorded(run_scan):
    r = run_scan(make_bulk())
    assert r['data_quality']['status'] == 'TRUSTED' and r['data_quality']['crosscheck']['status'] == 'unavailable'


def test_health_reports_the_crosscheck_state():
    import health as hl
    from test_readiness_health import hctx, lvl, RES
    base = {'status': 'TRUSTED', 'official_coverage': 1.0, 'quarantined': {}, 'reasons': []}
    assert lvl(hl.run_checks(hctx(res=dict(RES, data_quality=dict(base, crosscheck={'status': 'unavailable', 'note': '403'})))), 'H15') == 'warn'
    ok = {'status': 'ok', 'compared': 150, 'close_mismatch': {}, 'adjustment_mismatch': {}, 'filled': []}
    assert lvl(hl.run_checks(hctx(res=dict(RES, data_quality=dict(base, crosscheck=ok)))), 'H15') == 'ok'
    assert lvl(hl.run_checks(hctx(res=dict(RES, data_quality=dict(base, crosscheck=dict(ok, close_mismatch={'X': 1.2}))))), 'H15') == 'warn'


# ------------------------------------------------------------ Nifty from NSE's index file
def index_csv(day='14-10-2026', close=22700.0, change=77.3, name='Nifty 50'):
    head = 'Index Name,Index Date,Open Index Value,High Index Value,Low Index Value,Closing Index Value,Points Change,Change(%),Volume'
    return head + f'\n{name},{day},22650.0,22750.0,22600.0,{close},{change},0.34,1000\nNifty Bank,{day},50000,50500,49800,50200,100,0.2,1'


def test_index_parse_and_fetch():
    b = bc.parse_index(index_csv(), date(2026, 10, 14))
    assert b['close'] == 22700.0 and abs(b['prev_close'] - 22622.7) < 1e-6
    assert bc.parse_index(index_csv(day='13-10-2026'), date(2026, 10, 14)) is None          # wrong date
    assert bc.parse_index(index_csv(close=22800.0, change=77.3).replace('22750.0', '22600.0'), date(2026, 10, 14)) is None   # high below close
    assert bc.fetch_index(date(2026, 10, 14), downloader=lambda u: index_csv())['status'] == 'ok'
    def boom(u):
        raise OSError('403')
    assert bc.fetch_index(date(2026, 10, 14), downloader=boom)['status'] == 'unavailable'


def test_fill_index_needs_continuity():
    idx = pd.bdate_range(end='2026-10-13', periods=30)
    df = pd.DataFrame({'Open': 22600.0, 'High': 22700.0, 'Low': 22500.0, 'Close': 22622.7, 'Volume': 0.0}, index=idx)
    ok = {'status': 'ok', 'bar': bc.parse_index(index_csv(), date(2026, 10, 14))}
    out, filled = bc.fill_index(df, ok, date(2026, 10, 14))
    assert filled and out.index[-1] == pd.Timestamp('2026-10-14') and out['Close'].iloc[-1] == 22700.0 and len(out) == 31
    far = {'status': 'ok', 'bar': dict(ok['bar'], prev_close=20000.0)}
    assert bc.fill_index(df, far, date(2026, 10, 14)) == (df, False) or not bc.fill_index(df, far, date(2026, 10, 14))[1]
    assert bc.fill_index(df, {'status': 'unavailable', 'bar': None}, date(2026, 10, 14))[1] is False
    assert bc.fill_index(out, ok, date(2026, 10, 14))[1] is False                            # already current


def test_scan_becomes_trusted_when_nse_supplies_stocks_and_the_nifty(run_scan, monkeypatch):
    full = make_bulk()
    lag = full.copy()
    for t in sc.YF_TICKERS + sc.ALIAS_TICKERS + [sc.BENCH]:
        for f in ('Open', 'High', 'Low', 'Close', 'Volume'):
            lag.loc[lag.index[-1], (t, f)] = np.nan            # Yahoo has no official values for anything, the Nifty included
    monkeypatch.setattr(sc.bhavcopy, 'fetch', lambda session: {
        'status': 'ok', 'source': 'test file', 'retrieved_at': 'x',
        'rows': {t.replace('.NS', ''): dict(open=float(full[(t, 'Open')].iloc[-1]), high=float(full[(t, 'High')].iloc[-1]), low=float(full[(t, 'Low')].iloc[-1]),
                                            close=float(full[(t, 'Close')].iloc[-1]), prev_close=float(full[(t, 'Close')].iloc[-2]), volume=float(full[(t, 'Volume')].iloc[-1]))
                 for t in sc.YF_TICKERS}})
    nc = full[(sc.BENCH, 'Close')]
    monkeypatch.setattr(sc.bhavcopy, 'fetch_index', lambda session: {'status': 'ok', 'bar': {
        'open': float(nc.iloc[-1]), 'high': float(nc.iloc[-1]) * 1.001, 'low': float(nc.iloc[-1]) * 0.999, 'close': float(nc.iloc[-1]),
        'prev_close': float(nc.iloc[-2]), 'volume': 0.0}})
    r = run_scan(lag, with_intraday=False)
    assert r['data_quality']['crosscheck']['nifty']['filled'] is True
    assert r['data_quality']['status'] == 'TRUSTED' and r['actionable'] is True and r['summary']['signals'] > 0
