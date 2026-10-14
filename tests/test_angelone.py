import os, sys
from datetime import date
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import angelone as ao
import screener as sc
from test_scan_fail_closed import make_bulk, run_scan  # noqa: F401

S = date(2026, 10, 14)
ENVOK = {'ANGEL_API_KEY': 'KEY123', 'ANGEL_CLIENT_CODE': 'C1234', 'ANGEL_PIN': '9876', 'ANGEL_TOTP_SECRET': 'JBSWY3DPEHPK3PXP'}
SECRETS = tuple(ENVOK.values())


def master(syms):
    m = [{'token': str(1000 + i), 'symbol': f'{s}-EQ', 'name': s, 'exch_seg': 'NSE', 'instrumenttype': ''} for i, s in enumerate(syms)]
    m += [{'token': '5', 'symbol': 'RELIANCE-EQ', 'name': 'RELIANCE', 'exch_seg': 'BSE'},                     # wrong exchange: ignored
          {'token': '99926000', 'symbol': 'Nifty 50', 'name': 'Nifty 50', 'exch_seg': 'NSE', 'instrumenttype': 'AMXIDX'}]
    return m


def candles(prev=100.0, close=102.0, day='2026-10-14'):
    return [['2026-10-13T00:00:00+05:30', 99, 101, 98, prev, 1000], [f'{day}T00:00:00+05:30', 100, 103, 99, close, 5000]]


class FakeClient:
    def __init__(self, fail=(), data=None):
        self.calls, self.fail, self.data = [], set(fail), data

    def getCandleData(self, p):
        self.calls.append(p)
        if p['symboltoken'] in self.fail:
            raise RuntimeError('boom')
        return {'status': True, 'data': self.data if self.data is not None else candles()}


def test_credentials_are_all_or_nothing():
    assert ao.credentials({}) is None and ao.credentials(dict(ENVOK, ANGEL_PIN='')) is None
    assert ao.credentials(ENVOK) == ENVOK


def test_token_map_uses_nse_equity_entries_and_the_index():
    toks, nifty = ao.token_map(master(['AAA', 'BBB']), ['AAA', 'BBB', 'RELIANCE', 'MISSING'])
    assert toks == {'AAA': '1000', 'BBB': '1001'} and nifty == '99926000'
    assert ao.token_map([], ['A'])[1] == ao.NIFTY_FALLBACK_TOKEN


def test_candles_to_bar_rules():
    b = ao.candles_to_bar(candles(), S)
    assert b == {'open': 100.0, 'high': 103.0, 'low': 99.0, 'close': 102.0, 'prev_close': 100.0, 'volume': 5000.0}
    assert ao.candles_to_bar(candles(day='2026-10-13'), S) is None                  # no candle for the session
    assert ao.candles_to_bar([candles()[1]], S) is None                              # no previous candle: continuity unprovable
    bad = candles(); bad[1][2] = 90                                                  # high below close
    assert ao.candles_to_bar(bad, S) is None and ao.candles_to_bar(None, S) is None


def run(symbols, client, env=ENVOK):
    return ao.fetch(S, symbols, env=env, client_factory=lambda cred: client, master_loader=lambda: master(symbols), sleep=lambda s: None)


def test_fetch_ok_partial_not_configured_and_login_failure():
    syms = [f'S{i}' for i in range(10)]
    c = FakeClient()
    r = run(syms, c)
    assert r['status'] == 'ok' and len(r['rows']) == 10 and r['nifty_bar']['close'] == 102.0 and len(c.calls) == 11
    assert all(p['interval'] == 'ONE_DAY' and p['exchange'] == 'NSE' for p in c.calls)
    r = run(syms, FakeClient(fail={'1000', '1001', '1002'}))                       # 7/10 < 80%
    assert r['status'] == 'unavailable' and '7/10' in r['note']
    assert run(syms, FakeClient(fail={'1000'}))['status'] == 'ok'                  # 9/10 is enough
    assert ao.fetch(S, syms, env={})['status'] == 'not_configured'
    def bad_login(cred):
        raise RuntimeError('login refused: Invalid totp')
    r = ao.fetch(S, syms, env=ENVOK, client_factory=bad_login, master_loader=lambda: master(syms), sleep=lambda s: None)
    assert r['status'] == 'unavailable' and 'Invalid totp' in r['note']


def test_secrets_never_appear_in_any_returned_text():
    def bad_login(cred):
        raise RuntimeError('boom')
    for r in (ao.fetch(S, ['A'], env=ENVOK, client_factory=bad_login, master_loader=lambda: master(['A']), sleep=lambda s: None),
              run(['A'], FakeClient())):
        text = repr(r)
        assert not any(sec in text for sec in SECRETS)


# ------------------------------------------------------------ through the scanner: Yahoo lagging, NSE file unavailable, Angel One supplies
def test_scan_uses_angel_one_when_nse_is_unavailable(run_scan, monkeypatch):
    full = make_bulk()
    lag = full.copy()
    for t in sc.YF_TICKERS + sc.ALIAS_TICKERS + [sc.BENCH]:
        for f in ('Open', 'High', 'Low', 'Close', 'Volume'):
            lag.loc[lag.index[-1], (t, f)] = np.nan
    rows = {t.replace('.NS', ''): dict(open=float(full[(t, 'Open')].iloc[-1]), high=float(full[(t, 'High')].iloc[-1]), low=float(full[(t, 'Low')].iloc[-1]),
                                       close=float(full[(t, 'Close')].iloc[-1]), prev_close=float(full[(t, 'Close')].iloc[-2]), volume=float(full[(t, 'Volume')].iloc[-1]))
            for t in sc.YF_TICKERS}
    nc = full[(sc.BENCH, 'Close')]
    nb = {'open': float(nc.iloc[-1]), 'high': float(nc.iloc[-1]) * 1.001, 'low': float(nc.iloc[-1]) * 0.999, 'close': float(nc.iloc[-1]), 'prev_close': float(nc.iloc[-2]), 'volume': 0.0}
    monkeypatch.setattr(sc.angelone, 'fetch', lambda session, symbols, **k: {'status': 'ok', 'source': 'angel one smartapi', 'rows': rows, 'nifty_bar': nb, 'retrieved_at': 'x'})
    r = run_scan(lag, with_intraday=False)
    cc = r['data_quality']['crosscheck']
    assert cc['source'] == 'angel one smartapi' and len(cc['filled']) > 100 and cc['nifty']['filled'] is True and cc['angelone']['status'] == 'ok'
    assert r['data_quality']['status'] == 'TRUSTED' and r['actionable'] is True and r['summary']['signals'] > 0


def test_scan_carries_on_when_angel_is_not_configured(run_scan):
    r = run_scan(make_bulk())
    assert r['data_quality']['status'] == 'TRUSTED' and r['data_quality']['crosscheck']['angelone']['status'] == 'not_configured'
