#!/usr/bin/env python3
"""Compare the same-universe momentum replica (and the strategy) with the OFFICIAL Nifty200 Momentum 30
total-return series, to measure how much this stock list flatters results.

Sources, tried in order (all failures are recorded, so the report says exactly what happened):
  1. a hand-supplied CSV `official_index.csv` (date,value) - always works; download the index's historical
     total-return data from niftyindices.com and commit it
  2. niftyindices.com historical total-return endpoint (community-documented, unofficial; NSE may block
     cloud IPs or change it)
  3. Yahoo Finance candidates: an index ticker and ETFs that track the index (price-only, net of fees, short
     history, but a real investable alternative)

Reading the result: the replica is price-only, so the official total-return series gets a dividend advantage
of roughly 1 percentage point a year; the measured flattery is therefore understated by about that much.

One-sided logic: the strategy's own numbers are also upward-biased by survivorship. If it still trails the
official index, the shortfall is robust. If it beats the index, that is inconclusive.
"""
import json
import os
import time
from datetime import date

import numpy as np
import pandas as pd

import benchmarks as bm

INDEX_NAMES = ['NIFTY200 MOMENTUM 30', 'Nifty200 Momentum 30']
CONTROL_NAMES = ['NIFTY 50']                      # sanity check: official Nifty 50 TRI vs the price index
URL = 'https://niftyindices.com/Backpage.aspx/getTotalReturnIndexString'
REFERER = 'https://niftyindices.com/reports/historical-data'
DATE_FORMATS = ['%d-%b-%Y', '%d-%B-%Y', '%d%m%Y']
CHUNK_DAYS = 300
YAHOO_CANDIDATES = ['MOMENTUM30.NS', 'MOM30IETF.NS', 'MOMOMENTUM.NS', '^NIFTY200MOMENTM30', 'NIFTY200MOMENTM30.NS']
DATE_KEYS = ('Date', 'HistoricalDate', 'date', 'TIMESTAMP', 'Index Date')
VALUE_KEYS = ('TotalReturnsIndex', 'TotalReturnIndex', 'TotalReturnsIndexValue', 'TRI', 'Total Returns Index', 'Close', 'close')
DATE_PARSE = ('%d %b %Y', '%d-%b-%Y', '%d-%B-%Y', '%Y-%m-%d', '%b %d %Y', '%d/%m/%Y', '%d %B %Y')


# --------------------------------------------------------------------------- parsing
def _parse_date(v):
    s = str(v).strip()
    for f in DATE_PARSE:
        try:
            return pd.to_datetime(s, format=f)
        except (ValueError, TypeError):
            continue
    try:
        return pd.to_datetime(s)
    except (ValueError, TypeError):
        return pd.NaT


def parse_records(payload):
    """Accepts the response text/dict/list in any of the shapes seen in community code and returns a level Series."""
    obj = payload
    if isinstance(obj, (str, bytes)):
        obj = json.loads(obj)
    if isinstance(obj, dict) and 'd' in obj:
        obj = obj['d']
    if isinstance(obj, (str, bytes)):
        obj = json.loads(obj)
    if not isinstance(obj, list) or not obj:
        return pd.Series(dtype=float)
    rows = {}
    for rec in obj:
        if not isinstance(rec, dict):
            continue
        dk = next((k for k in DATE_KEYS if k in rec), None)
        vk = next((k for k in VALUE_KEYS if k in rec), None)
        if dk is None or vk is None:
            continue
        d = _parse_date(rec[dk])
        try:
            v = float(str(rec[vk]).replace(',', ''))
        except ValueError:
            continue
        if pd.notna(d) and v > 0:
            rows[d.normalize()] = v
    return pd.Series(rows).sort_index() if rows else pd.Series(dtype=float)


def build_payload(name, start, end, fmt):
    cinfo = "{'name':'%s','startDate':'%s','endDate':'%s','indexName':'%s'}" % (name, start.strftime(fmt), end.strftime(fmt), name)
    return {'cinfo': cinfo}


# --------------------------------------------------------------------------- sources
def load_manual_csv(path='official_index.csv'):
    """date,value (any header names; first column = date, first numeric column = level)."""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    if df.shape[1] < 2:
        return None
    d = df.iloc[:, 0].map(_parse_date)
    vals = pd.to_numeric(df.iloc[:, 1].astype(str).str.replace(',', ''), errors='coerce')
    s = pd.Series(vals.values, index=d).dropna()
    s = s[~s.index.isna()]
    return s.sort_index() if len(s) > 20 else None


def fetch_niftyindices(name, start, end, session=None, sleep=0.4):
    """Chunked requests to niftyindices.com. Returns (level Series, diagnostics list)."""
    import requests
    s = session or requests.Session()
    diag = []
    headers = {'Content-Type': 'application/json; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest', 'Referer': REFERER,
               'Origin': 'https://niftyindices.com', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
               'Accept': 'application/json, text/javascript, */*; q=0.01'}
    try:
        s.get('https://niftyindices.com/', headers={'User-Agent': headers['User-Agent']}, timeout=30)   # cookies
    except Exception as e:
        diag.append({'source': 'niftyindices', 'name': name, 'step': 'warmup', 'error': str(e)[:120]})
    for fmt in DATE_FORMATS:
        pieces, ok_any = [], False
        cur = pd.Timestamp(start)
        while cur <= pd.Timestamp(end):
            nxt = min(cur + pd.Timedelta(days=CHUNK_DAYS), pd.Timestamp(end))
            rec = {'source': 'niftyindices', 'name': name, 'format': fmt, 'chunk': f'{cur.date()}..{nxt.date()}'}
            try:
                r = s.post(URL, json=build_payload(name, cur, nxt, fmt), headers=headers, timeout=45)
                rec['status'] = r.status_code
                ser = parse_records(r.text) if r.status_code == 200 else pd.Series(dtype=float)
                rec['records'] = int(len(ser))
                if len(ser):
                    pieces.append(ser); ok_any = True
            except Exception as e:
                rec['error'] = str(e)[:140]
            diag.append(rec)
            cur = nxt + pd.Timedelta(days=1)
            time.sleep(sleep)
            if not ok_any and len(diag) >= 3 and all(d.get('records', 0) == 0 for d in diag[-3:]):
                break                                           # this format is not working; try the next one
        if pieces:
            out = pd.concat(pieces)
            return out[~out.index.duplicated(keep='last')].sort_index(), diag
    return pd.Series(dtype=float), diag


def probe_yahoo(candidates=YAHOO_CANDIDATES, downloader=None):
    """Which Yahoo tickers return history? Returns ({ticker: Series level}, diagnostics)."""
    if downloader is None:
        import yfinance as yf
        downloader = lambda t: yf.download(t, period='max', interval='1d', auto_adjust=True, progress=False, threads=False)
    found, diag = {}, []
    for t in candidates:
        rec = {'source': 'yahoo', 'ticker': t}
        try:
            d = downloader(t)
            if d is not None and len(d):
                close = d['Close'] if 'Close' in d else d.iloc[:, 0]
                close = close.squeeze().dropna().astype(float)
                if len(close) > 60:
                    found[t] = close
                    rec.update({'rows': int(len(close)), 'first': str(close.index[0].date()), 'last': str(close.index[-1].date())})
                else:
                    rec['rows'] = int(len(close))
            else:
                rec['rows'] = 0
        except Exception as e:
            rec['error'] = str(e)[:120]
        diag.append(rec)
    return found, diag


# --------------------------------------------------------------------------- comparison
def compare(replica_ret, official_level, label):
    """Replica (daily returns) vs an official level series over their overlap."""
    off = official_level.astype(float).pct_change().dropna()
    j = pd.concat([replica_ret.rename('replica'), off.rename('official')], axis=1, join='inner').dropna()
    if len(j) < 60:
        return None
    pr, po = bm.perf(j['replica']), bm.perf(j['official'])
    monthly = (1 + j).groupby(j.index.to_period('M')).prod() - 1
    te = float((j['replica'] - j['official']).std() * np.sqrt(bm.TRADING_DAYS) * 100)
    return {'label': label, 'start': str(j.index[0].date()), 'end': str(j.index[-1].date()), 'days': int(len(j)),
            'replica': pr, 'official': po,
            'cagr_gap_pts': round(pr['cagr_pct'] - po['cagr_pct'], 1),
            'monthly_correlation': round(float(monthly['replica'].corr(monthly['official'])), 2) if len(monthly) > 6 else None,
            'tracking_error_pct': round(te, 1),
            'calendar_years': {'replica': bm.calendar_years(j['replica']), 'official': bm.calendar_years(j['official'])}}


def strategy_vs_official(strategy_ret, official_level, label):
    off = official_level.astype(float).pct_change().dropna()
    j = pd.concat([strategy_ret.rename('s'), off.rename('o')], axis=1, join='inner').dropna()
    if len(j) < 60:
        return None
    ps, po = bm.perf(j['s']), bm.perf(j['o'])
    trails = (ps['sharpe'] is not None and po['sharpe'] is not None and po['sharpe'] >= ps['sharpe'])
    return {'label': label, 'start': str(j.index[0].date()), 'end': str(j.index[-1].date()), 'strategy': ps, 'official': po,
            'official_sharpe_at_least_strategy': bool(trails),
            'reading': ('The strategy trails the official index on Sharpe even though its own numbers carry survivorship flattery, '
                        'so the shortfall is robust.' if trails else
                        'The strategy beats the official index on Sharpe over this window. That is inconclusive: the strategy\'s '
                        'numbers are upward-biased by survivorship, so part or all of the edge may not be real.')}


# --------------------------------------------------------------------------- orchestration
def obtain(start, end, manual_path='official_index.csv', fetcher=fetch_niftyindices, yahoo=probe_yahoo):
    """Returns ({'official': Series|None, 'official_source': str, 'control': Series|None, 'etfs': {ticker: Series}}, diagnostics)."""
    diag, out = [], {'official': None, 'official_source': None, 'control': None, 'etfs': {}}
    manual = load_manual_csv(manual_path)
    if manual is not None:
        out['official'], out['official_source'] = manual, f'manual CSV ({manual_path})'
        diag.append({'source': 'manual', 'rows': int(len(manual)), 'first': str(manual.index[0].date()), 'last': str(manual.index[-1].date())})
    else:
        for name in INDEX_NAMES:
            ser, d = fetcher(name, start, end)
            diag += d
            if len(ser) > 200:
                out['official'], out['official_source'] = ser, f'niftyindices.com ({name})'
                break
    for name in CONTROL_NAMES:
        ser, d = fetcher(name, start, end)
        diag += d
        if len(ser) > 200:
            out['control'] = ser
    found, d = yahoo()
    diag += d
    out['etfs'] = found
    return out, diag


def build_report(series_bundle, data, diag):
    rep = {'generated': date.today().isoformat(), 'official_source': data['official_source'], 'diagnostics': diag,
           'official_vs_replica': None, 'strategy_vs_official': None, 'control_check': None, 'etfs': {}}
    mom = series_bundle['mom']
    strat_full = series_bundle['strat']['baseline'].get('full', pd.Series(dtype=float))
    if data['official'] is not None:
        rep['official_vs_replica'] = compare(mom, data['official'], 'Momentum-30 replica vs official TRI')
        rep['strategy_vs_official'] = strategy_vs_official(strat_full, data['official'], 'Live strategy vs official TRI')
    if data['control'] is not None and series_bundle['nifty'] is not None:
        # Official Nifty 50 TRI minus the price index: should be roughly the dividend yield (about 1%/yr)
        c = compare(series_bundle['nifty'], data['control'], 'Nifty 50 price vs official Nifty 50 TRI')
        rep['control_check'] = c
    for t, lvl in data['etfs'].items():
        rep['etfs'][t] = {'vs_replica': compare(mom, lvl, f'replica vs {t}'), 'strategy': strategy_vs_official(strat_full, lvl, f'strategy vs {t}')}
    return rep


def markdown(rep):
    L = ['# Official index comparison', '',
         'Purpose: measure how much the stock list flatters results, using the real Nifty200 Momentum 30 series. The replica is '
         'price-only, so the official total-return series carries roughly a 1 point a year dividend advantage; measured flattery is '
         'understated by about that much.', '']
    ok = [d for d in rep['diagnostics'] if d.get('records') or d.get('rows')]
    L += [f"**Official series source:** {rep['official_source'] or 'NONE obtained automatically'}", '']
    ovr = rep['official_vs_replica']
    if ovr:
        L += [f"## Replica vs official ({ovr['start']} to {ovr['end']}, {ovr['days']} days)", '',
              '| | CAGR | Max DD | Calmar | Sharpe |', '|---|---|---|---|---|']
        for k, nm in (('replica', 'Momentum-30 replica (our universe)'), ('official', 'Official Nifty200 Momentum 30 TRI')):
            v = ovr[k]; L.append(f"| {nm} | {v['cagr_pct']}% | {v['max_drawdown_pct']}% | {v['calmar']} | {v['sharpe']} |")
        L += ['', f"**Replica minus official: {ovr['cagr_gap_pts']:+.1f} CAGR points** (monthly correlation {ovr['monthly_correlation']}, "
                  f"tracking error {ovr['tracking_error_pct']}%). A large positive gap is the survivorship and composition flattery in this universe.", '']
        ys = sorted(set(ovr['calendar_years']['replica']) | set(ovr['calendar_years']['official']))
        L += ['| Year | ' + ' | '.join(ys) + ' |', '|---|' + '---|' * len(ys)]
        for k, nm in (('replica', 'Replica'), ('official', 'Official TRI')):
            L.append(f'| {nm} | ' + ' | '.join(str(ovr['calendar_years'][k].get(y, '')) for y in ys) + ' |')
        L.append('')
    svo = rep['strategy_vs_official']
    if svo:
        L += [f"## Live strategy vs official index ({svo['start']} to {svo['end']})", '', '| | CAGR | Max DD | Calmar | Sharpe |', '|---|---|---|---|---|']
        for k, nm in (('strategy', 'Live strategy (portfolio)'), ('official', 'Official Nifty200 Momentum 30 TRI')):
            v = svo[k]; L.append(f"| {nm} | {v['cagr_pct']}% | {v['max_drawdown_pct']}% | {v['calmar']} | {v['sharpe']} |")
        L += ['', f"**{svo['reading']}**", '']
    cc = rep['control_check']
    if cc:
        L += [f"## Method check: Nifty 50 price index vs official Nifty 50 TRI", '',
              f"Gap {cc['cagr_gap_pts']:+.1f} CAGR points (price minus total return); expect about -1 to -1.5 (dividends). "
              'Far from that means a data or parsing problem.', '']
    for t, v in rep['etfs'].items():
        L += [f"## ETF / index ticker `{t}` (real, investable, net of fees)", '']
        r1, r2 = v['vs_replica'], v['strategy']
        if r1:
            L.append(f"- Replica minus {t}: {r1['cagr_gap_pts']:+.1f} CAGR points over {r1['start']} to {r1['end']}")
        if r2:
            L.append(f"- Strategy vs {t}: Sharpe {r2['strategy']['sharpe']} vs {r2['official']['sharpe']}. {r2['reading']}")
        L.append('')
    if not ovr and not rep['etfs']:
        L += ['## No comparison possible yet', '',
              'No official or ETF series could be obtained automatically. Options: download the index\'s historical total-return data from '
              'niftyindices.com (Reports, Historical Data, Total Returns Index) and commit it as `official_index.csv` with columns date,value; '
              'the next run will use it.', '']
    L += ['## What was tried', '', '| Source | Detail | Result | Attempts |', '|---|---|---|---|']
    groups = {}
    for d in rep['diagnostics']:
        det = d.get('name') or d.get('ticker') or ''
        res = ', '.join(f'{k}={str(d[k])[:90]}' for k in ('status', 'records', 'rows', 'first', 'last', 'error') if k in d) or '—'
        key = (d['source'], det, res)
        g = groups.setdefault(key, {'n': 0, 'first': d.get('chunk') or d.get('step') or ''})
        g['n'] += 1
    for (src, det, res), g in list(groups.items())[:30]:
        L.append(f"| {src} | {det} | {res} | {g['n']} |")
    return '\n'.join(L)


def main():
    import argparse
    import backtest as bt
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, default=10)
    ap.add_argument('--cache', default='history_cache.pkl')
    ap.add_argument('--out', default='reports')
    a = ap.parse_args()
    frames, bench = bt.load_history(a.years, a.cache)
    bundle = bm.compute_series(frames, bench)
    start = pd.Timestamp(date.today().year - a.years, 1, 1)
    data, diag = obtain(start, pd.Timestamp(date.today()))
    rep = build_report(bundle, data, diag)
    os.makedirs(a.out, exist_ok=True)
    with open(f'{a.out}/official_index.json', 'w') as f:
        json.dump(rep, f, indent=2, default=str)
    md = markdown(rep)
    with open(f'{a.out}/official_index.md', 'w') as f:
        f.write(md)
    print(md)


if __name__ == '__main__':
    main()
