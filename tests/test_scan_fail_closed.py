"""End-to-end: the scanner must never emit an actionable signal from provisional, stale, partial or malformed data."""
import json, os, sys, zlib
from datetime import date
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import analysis
import screener as sc

END = '2026-10-13'
EXPECTED = date(2026, 10, 13)


def series(tick, n=330):
    rng = np.random.default_rng(zlib.crc32(tick.encode()))
    c = 100 * np.cumprod(1 + 0.0014 + 0.012 * rng.standard_normal(n))
    o = c * (1 + 0.003 * rng.standard_normal(n))
    return pd.DataFrame({'Open': o, 'High': np.maximum(o, c) * 1.006, 'Low': np.minimum(o, c) * 0.994, 'Close': c,
                         'Volume': 1e6 * (1 + rng.random(n))})


def make_bulk(end=END, n=330, nan_last_row=False, stale=(), stale_by=3, corrupt=(), corrupt_nifty=False):
    idx = pd.bdate_range(end=end, periods=n)
    tickers = sc.YF_TICKERS + sc.ALIAS_TICKERS + [sc.BENCH]
    cols = {}
    for t in tickers:
        s = series(t, n); s.index = idx
        if t in stale:
            s.iloc[-stale_by:] = np.nan
        if t in corrupt:
            s.iloc[-2, s.columns.get_loc('High')] = s['Low'].iloc[-2] * 0.8          # high below low: malformed bar
        for f in s.columns:
            cols[(t, f)] = s[f]
    df = pd.DataFrame(cols, index=idx)
    if nan_last_row:                                                    # vendor adds the next day's row, all empty
        df.loc[pd.bdate_range(end, periods=2)[-1]] = np.nan
    return df


def intraday_for(tickers, day='2026-10-13'):
    out = {}
    for t in tickers:
        rng = np.random.default_rng(zlib.crc32((t + 'i').encode()))
        n = 75
        idx = pd.date_range(f'{day} 09:15', periods=n, freq='5min', tz='Asia/Kolkata')
        c = 100 + np.cumsum(rng.normal(0, 0.1, n))
        o = np.r_[c[0], c[:-1]]
        out[t] = pd.DataFrame({'Open': o, 'High': np.maximum(o, c) + 0.05, 'Low': np.minimum(o, c) - 0.05, 'Close': c, 'Volume': 5e4}, index=idx)
    return pd.concat(out, axis=1)


@pytest.fixture
def run_scan(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sc, 'load_stockedge', lambda: set())
    monkeypatch.setattr(sc, 'retry_download', lambda syms: None)
    monkeypatch.setattr(sc.angelone, 'fetch', lambda session, symbols, **k: {'status': 'not_configured', 'rows': {}, 'nifty_bar': None})
    monkeypatch.setattr(sc.bhavcopy, 'fetch_index', lambda session: {'status': 'unavailable', 'bar': None, 'note': 'test: no network'})
    monkeypatch.setattr(sc.bhavcopy, 'fetch', lambda session: {'status': 'unavailable', 'rows': {}, 'note': 'test: no network'})
    monkeypatch.setattr(sc, 'probe_vendor', lambda: {'daily_5d': 'stub'})
    monkeypatch.setattr(analysis, 'expected_last_session', lambda now_ist, close_hhmm=(16, 30), holidays=frozenset(): EXPECTED)

    def go(bulk, with_intraday=True):
        monkeypatch.setattr(sc, 'fetch_bulk', lambda: bulk)
        monkeypatch.setattr(sc, 'fetch_intraday', lambda ticks: intraday_for(ticks) if with_intraday else None)
        sc.main()
        return json.load(open(tmp_path / 'results.json'))
    return go


def test_official_current_data_yields_actionable_signals(run_scan):
    r = run_scan(make_bulk())
    assert r['data_quality']['status'] == 'TRUSTED' and r['actionable'] is True
    assert r['summary']['signals'] > 0 and r['preview'] == []
    assert all(s['actionable'] and not s.get('provisional') for s in r['stocks'])
    assert r['provenance']['kind'] == 'scan' and r['provenance']['universe_version'] == sc.UNIVERSE_VERSION
    assert r['vendor']['vendor'].startswith('yahoo') and r['vendor']['retrieved_at'] and r['data_quality']['expected_session'] == '2026-10-13'


def test_provisional_bars_never_produce_actionable_signals(run_scan):
    """The vendor adds a dated but empty row for the expected session; only 5-minute data exists for it."""
    r = run_scan(make_bulk(end='2026-10-12', nan_last_row=True))
    assert r['data_quality']['status'] == 'UNTRUSTED' and r['actionable'] is False
    assert r['stocks'] == [] and r['summary']['signals'] == 0 and r['summary']['tradeable'] == 0     # nothing actionable
    assert r['provisional']['used'] and r['provisional']['actionable'] is False
    assert r['preview'], 'a preview may be shown, but only as a preview'
    for p in r['preview']:
        assert p['actionable'] is False and p['provisional'] is True and p['execution_ok'] is False and p['position'] is None
        assert any(c['id'] == 'provisional' and c['status'] == 'block' for c in p['checks'])
    assert any('official daily bar' in why for why in r['data_quality']['reasons'])


def test_stale_data_fails_closed_without_intraday_fallback(run_scan):
    r = run_scan(make_bulk(end='2026-10-12'), with_intraday=False)
    assert r['actionable'] is False and r['stocks'] == [] and r['preview'] == []
    assert r['data_quality']['official_coverage'] == 0.0


def test_partial_publication_fails_closed(run_scan):
    stale = set(sc.YF_TICKERS[:20])                                   # 20 of 159 symbols (12.6%) still on the previous session
    r = run_scan(make_bulk(stale=stale), with_intraday=False)
    assert r['data_quality']['status'] == 'UNTRUSTED' and r['stocks'] == []
    assert r['data_quality']['official_coverage'] < 0.95


def test_a_few_stale_or_malformed_symbols_are_quarantined_not_traded(run_scan):
    bad = set(sc.YF_TICKERS[:3])
    r = run_scan(make_bulk(stale=bad))                                # 3 of 159 stale (1.9%): universe still trusted
    assert r['data_quality']['status'] == 'TRUSTED'
    traded = {s['symbol'] for s in r['stocks']}
    assert not any(f'{t}' in traded for t in [x.replace('.NS', '') for x in bad])
    assert len(r['data_quality']['quarantined']) == 3
    corrupt = {sc.YF_TICKERS[5]}
    r2 = run_scan(make_bulk(corrupt=corrupt))
    sym = sc.YF_TICKERS[5].replace('.NS', '')
    assert sym not in {s['symbol'] for s in r2['stocks']} and sym in r2['data_quality']['quarantined']
    assert 'ohlc_inconsistent_recent' in r2['data_quality']['quarantined'][sym]


def test_widespread_malformed_data_fails_closed(run_scan):
    r = run_scan(make_bulk(corrupt=set(sc.YF_TICKERS[:10])), with_intraday=False)     # 6% critical errors > 2% limit
    assert r['data_quality']['status'] == 'UNTRUSTED' and r['stocks'] == []
    assert any('critical data errors' in why for why in r['data_quality']['reasons'])


def test_missing_nifty_bar_fails_closed(run_scan):
    bulk = make_bulk()
    bulk[(sc.BENCH, 'Close')] = np.nan
    r = run_scan(bulk, with_intraday=False)
    assert r['actionable'] is False and r['stocks'] == [] and any('Nifty' in why for why in r['data_quality']['reasons'])


def test_cutoffs_are_consistent_across_actionable_signals(run_scan):
    r = run_scan(make_bulk())
    assert {s['signal_date'] for s in r['stocks']} == {'2026-10-13'}
    assert r['data_cutoff'] == '2026-10-13' and r['sessions_behind'] == 0


def test_actionable_signals_carry_a_trade_plan(run_scan):
    r = run_scan(make_bulk())
    assert r['stocks']
    for s in r['stocks']:
        p = s['plan']
        assert p['stop']['price'] == s['stop_loss'] and p['entry']['buy_stop'] == s['trigger']
        assert [l['r'] for l in p['profit_review_levels']['levels']] == [1, 2, 3]
        assert p['sell_trigger']['ema50_now'] == s['ema_50'] and p['add_more']['default'] == 'do not add'
        assert p['expected_duration']['basis'] == 'empirical'
