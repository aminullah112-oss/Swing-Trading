import json, os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import benchmarks as bm
import official_index as oi
from test_backtest import synth


def level(n=900, start='2020-01-01', daily=0.0006, seed=0, vol=0.01):
    idx = pd.bdate_range(start, periods=n)
    r = np.random.default_rng(seed).normal(daily, vol, n)
    return pd.Series(1000 * np.cumprod(1 + r), index=idx)


# ------------------------------------------------------------ parsing
def test_parse_records_accepts_the_shapes_seen_in_the_wild():
    recs = [{'Date': '13 Oct 2026', 'TotalReturnsIndex': '31,245.60'}, {'Date': '12 Oct 2026', 'TotalReturnsIndex': '31000.5'}]
    for payload in (json.dumps({'d': json.dumps(recs)}), {'d': json.dumps(recs)}, json.dumps(recs), recs):
        s = oi.parse_records(payload)
        assert list(s.index) == [pd.Timestamp('2026-10-12'), pd.Timestamp('2026-10-13')] and s.iloc[-1] == 31245.60
    alt = [{'HistoricalDate': '2026-10-13', 'TRI': 100.0}, {'date': '13-Oct-2026', 'close': 101.0}]
    assert len(oi.parse_records(alt)) == 1                                   # same day, two spellings: de-duplicated
    assert oi.parse_records(json.dumps({'d': '[]'})).empty
    assert oi.parse_records('[{"x": 1}]').empty
    assert oi.parse_records([{'Date': 'garbage', 'TRI': 5}, {'Date': '2026-01-02', 'TRI': 'n/a'}, {'Date': '2026-01-02', 'TRI': -1}]).empty


def test_build_payload_uses_the_documented_cinfo_shape():
    p = oi.build_payload('NIFTY200 MOMENTUM 30', pd.Timestamp('2024-01-02'), pd.Timestamp('2024-12-31'), '%d-%b-%Y')
    assert list(p) == ['cinfo'] and "'name':'NIFTY200 MOMENTUM 30'" in p['cinfo'] and "'startDate':'02-Jan-2024'" in p['cinfo']
    assert "'indexName':'NIFTY200 MOMENTUM 30'" in p['cinfo']
    assert "'endDate':'31122024'" in oi.build_payload('X', pd.Timestamp('2024-01-02'), pd.Timestamp('2024-12-31'), '%d%m%Y')['cinfo']


# ------------------------------------------------------------ niftyindices fetch with a fake session
class FakeResp:
    def __init__(self, status, text): self.status_code, self.text = status, text


def make_session(accept_fmt, status=200, calls=None):
    class S:
        def get(self, *a, **k): return FakeResp(200, '')
        def post(self, url, json=None, headers=None, timeout=None):
            if calls is not None: calls.append(json['cinfo'])
            if status != 200: return FakeResp(status, 'Forbidden')
            c = json['cinfo']
            m = {'%d-%b-%Y': '-Jan-' in c or '-Feb-' in c or '-Mar-' in c or '-Apr-' in c or '-May-' in c or '-Jun-' in c
                 or '-Jul-' in c or '-Aug-' in c or '-Sep-' in c or '-Oct-' in c or '-Nov-' in c or '-Dec-' in c}
            if accept_fmt == '%d-%b-%Y' and not m['%d-%b-%Y']:
                return FakeResp(200, '{"d": "[]"}')
            if accept_fmt == '%d%m%Y' and m['%d-%b-%Y']:
                return FakeResp(200, '{"d": "[]"}')
            import re
            ds = re.findall(r"'(?:start|end)Date':'([^']+)'", c)
            fmt = '%d-%b-%Y' if m['%d-%b-%Y'] else '%d%m%Y'
            a, b = (pd.to_datetime(x, format=fmt) for x in ds)
            days = pd.bdate_range(a, b)
            recs = [{'Date': d.strftime('%d %b %Y'), 'TotalReturnsIndex': str(1000 + i)} for i, d in enumerate(days)]
            return FakeResp(200, json_dumps({'d': json_dumps(recs)}))
    return S()


json_dumps = json.dumps


def test_fetch_chunks_the_range_and_concatenates_without_duplicates():
    calls = []
    ser, diag = oi.fetch_niftyindices('NIFTY200 MOMENTUM 30', pd.Timestamp('2022-01-03'), pd.Timestamp('2024-12-31'),
                                      session=make_session('%d-%b-%Y', calls=calls), sleep=0)
    expected_chunks = int(np.ceil((pd.Timestamp('2024-12-31') - pd.Timestamp('2022-01-03')).days / (oi.CHUNK_DAYS + 1)))
    assert abs(len(calls) - expected_chunks) <= 1 and ser.index.is_unique and ser.index.is_monotonic_increasing
    assert ser.index[0] >= pd.Timestamp('2022-01-03') and ser.index[-1] <= pd.Timestamp('2024-12-31') and len(ser) > 500
    assert all(d.get('status') == 200 for d in diag if 'status' in d)


def test_fetch_falls_back_to_the_next_date_format():
    ser, diag = oi.fetch_niftyindices('X', pd.Timestamp('2023-01-02'), pd.Timestamp('2023-12-29'), session=make_session('%d%m%Y'), sleep=0)
    assert len(ser) > 200
    fmts = [d['format'] for d in diag if 'format' in d]
    assert fmts[0] == '%d-%b-%Y' and '%d%m%Y' in fmts                       # first format yielded nothing, second worked


def test_blocked_requests_give_an_empty_series_and_a_readable_diagnosis_without_endless_retries():
    calls = []
    ser, diag = oi.fetch_niftyindices('X', pd.Timestamp('2016-01-01'), pd.Timestamp('2026-10-13'),
                                      session=make_session('%d-%b-%Y', status=403, calls=calls), sleep=0)
    assert ser.empty and any(d.get('status') == 403 for d in diag)
    assert len(calls) <= 3 * len(oi.DATE_FORMATS)                             # gave up after a few failures per format, not 12 x 3


# ------------------------------------------------------------ other sources
def test_manual_csv_loader_is_flexible(tmp_path):
    p = tmp_path / 'o.csv'
    s = level(n=60)
    pd.DataFrame({'Date': s.index.strftime('%d-%b-%Y'), 'Total Returns Index': [f'{v:,.2f}' for v in s.values]}).to_csv(p, index=False)
    out = oi.load_manual_csv(str(p))
    assert len(out) == 60 and abs(out.iloc[-1] - float(f'{s.iloc[-1]:.2f}')) < 0.01
    p.write_text('date,value\n2024-01-01,1\n')
    assert oi.load_manual_csv(str(p)) is None                                 # too short
    assert oi.load_manual_csv(str(tmp_path / 'missing.csv')) is None


def test_probe_yahoo_records_what_each_candidate_returned():
    good = pd.DataFrame({'Close': level(n=300).values}, index=level(n=300).index)

    def dl(t):
        if t == 'GOOD.NS': return good
        if t == 'BOOM.NS': raise RuntimeError('rate limited')
        return pd.DataFrame()
    found, diag = oi.probe_yahoo(['GOOD.NS', 'EMPTY.NS', 'BOOM.NS'], downloader=dl)
    assert set(found) == {'GOOD.NS'}
    by = {d['ticker']: d for d in diag}
    assert by['GOOD.NS']['rows'] == 300 and by['EMPTY.NS']['rows'] == 0 and 'rate limited' in by['BOOM.NS']['error']


# ------------------------------------------------------------ comparison maths
def test_compare_recovers_a_known_flattery():
    off = level(n=1000, seed=3)
    daily = off.pct_change().dropna()
    flattered = (1 + daily) * 1.05 ** (1 / 252) - 1                          # replica grows 5% a year faster than the official series
    c = oi.compare(flattered, off, 'test')
    expected = 5.0 * (1 + c['official']['cagr_pct'] / 100)                   # a 5% multiplicative edge is 5 x (1 + base growth) CAGR points
    assert abs(c['cagr_gap_pts'] - expected) < 0.4 and c['monthly_correlation'] > 0.98 and c['tracking_error_pct'] < 1.0
    assert oi.compare(flattered.head(20), off, 'x') is None                  # no meaningful overlap


def test_strategy_verdict_is_one_sided():
    off = level(n=800, daily=0.001, seed=1)
    weak = off.pct_change().dropna() * 0.2                                    # same shape, far less return: trails
    v = oi.strategy_vs_official(weak, off, 'x')
    assert v['official_sharpe_at_least_strategy'] and 'robust' in v['reading']
    strong = pd.Series(np.random.default_rng(5).normal(0.0015, 0.004, 700), index=off.index[100:])
    v2 = oi.strategy_vs_official(strong, off, 'x')
    assert not v2['official_sharpe_at_least_strategy'] and 'inconclusive' in v2['reading']


# ------------------------------------------------------------ orchestration
def test_obtain_prefers_manual_csv_and_falls_through_names(tmp_path):
    seen = []

    def fetcher(name, a, b):
        seen.append(name)
        return (level(n=400) if name == 'NIFTY200 MOMENTUM 30' else pd.Series(dtype=float)), [{'source': 'niftyindices', 'name': name}]
    nofind = lambda: ({}, [])
    p = tmp_path / 'o.csv'
    s = level(n=100)
    pd.DataFrame({'date': s.index.strftime('%Y-%m-%d'), 'value': s.values}).to_csv(p, index=False)
    out, _ = oi.obtain(pd.Timestamp('2020-01-01'), pd.Timestamp('2026-01-01'), manual_path=str(p), fetcher=fetcher, yahoo=nofind)
    assert out['official_source'].startswith('manual') and 'NIFTY200 MOMENTUM 30' not in seen      # manual wins, no scraping needed
    seen.clear()
    out, _ = oi.obtain(pd.Timestamp('2020-01-01'), pd.Timestamp('2026-01-01'), manual_path=str(tmp_path / 'no.csv'), fetcher=fetcher, yahoo=nofind)
    assert 'niftyindices.com' in out['official_source'] and out['control'] is None and seen[0] == 'NIFTY200 MOMENTUM 30'


def test_report_end_to_end_with_and_without_data(tmp_path):
    frames = {f'S{i}': synth(n=1500, seed=i, drift=0.0007) for i in range(40)}
    bench = synth(n=1500, seed=999)['Close']
    bundle = bm.compute_series(frames, bench)
    # an "official" series that the replica beats by about 6 points a year
    mom = bundle['mom']
    off = (1 + (mom - 0.06 / 252)).cumprod() * 1000
    data = {'official': off, 'official_source': 'manual CSV (test)', 'control': None, 'etfs': {}}
    rep = oi.build_report(bundle, data, [{'source': 'manual', 'rows': len(off)}])
    assert 4.5 < rep['official_vs_replica']['cagr_gap_pts'] < 7.5 and rep['strategy_vs_official'] is not None
    md = oi.markdown(rep)
    assert 'Replica minus official' in md and 'What was tried' in md and 'dividend advantage' in md
    empty = oi.build_report(bundle, {'official': None, 'official_source': None, 'control': None, 'etfs': {}},
                            [{'source': 'niftyindices', 'name': 'X', 'format': '%d-%b-%Y', 'chunk': 'a..b', 'status': 403}])
    md2 = oi.markdown(empty)
    assert 'No comparison possible yet' in md2 and 'official_index.csv' in md2 and 'status=403' in md2
