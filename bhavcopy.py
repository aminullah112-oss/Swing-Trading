"""NSE bhavcopy: the exchange's own end-of-day file, used as an independent check on the Yahoo daily bars.

Two jobs, both guarded:
  1. CROSS-CHECK  for every symbol whose Yahoo bar exists for the expected session, compare the close with NSE's. A mismatch
                  (adjustment error, bad vendor print, wrong symbol mapping) quarantines the symbol. NSE's previous close is
                  also compared with Yahoo's previous bar: a gap there means an unadjusted split/bonus/dividend.
  2. FILL         when Yahoo has not published the expected session yet, append NSE's official bar for that symbol, but only if
                  NSE's previous close matches Yahoo's last close (continuity proves no corporate action sits between them).

Honest limits: file layouts and URLs are NSE's and have changed before (this parser accepts the current 'UDiFF' layout and the
older sec_bhavdata_full layout); NSE may block automated clients, in which case status is 'unavailable' and the scan carries on
without the check, saying so. The parsers are tested on synthetic samples written from the documented columns, not on live files.
"""
import csv
import io
import os
import zipfile
from datetime import datetime, timezone
from urllib.request import Request, urlopen

import pandas as pd

CLOSE_TOL = 0.0025          # |yahoo close / nse close - 1| beyond this is a mismatch
CONTINUITY_TOL = 0.005      # |yahoo last close / nse prev close - 1| beyond this blocks a fill
ADJUST_TOL = 0.01           # previous-close disagreement that signals an unadjusted corporate action
MAX_MISMATCH_SHARE = 0.05   # more than this share of compared symbols disagreeing makes the whole scan untrusted
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',
      'Accept': '*/*', 'Referer': 'https://www.nseindia.com/'}

URLS = (
    ('udiff', 'https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{ymd}_F_0000.csv.zip'),
    ('legacy', 'https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{dmy}.csv'),
)


def _num(x):
    try:
        v = float(str(x).replace(',', '').strip())
        return v if v == v and v > 0 else None
    except (TypeError, ValueError):
        return None


def _rows(text):
    rd = csv.DictReader(io.StringIO(text))
    return [{(k or '').strip().upper(): (v or '').strip() for k, v in r.items()} for r in rd]


def _bar(o, h, l, c, pc, v):
    o, h, l, c, pc = _num(o), _num(h), _num(l), _num(c), _num(pc)
    if None in (o, h, l, c, pc) or h < max(o, c, l) * 0.9995 or l > min(o, c, h) * 1.0005:
        return None
    return {'open': o, 'high': h, 'low': l, 'close': c, 'prev_close': pc, 'volume': _num(v) or 0.0}


def parse_udiff(text, session):
    """Current layout: TckrSymb, SctySrs, TradDt (YYYY-MM-DD), OpnPric, HghPric, LwPric, ClsPric, PrvsClsgPric, TtlTradgVol."""
    out = {}
    for r in _rows(text):
        if r.get('SCTYSRS') != 'EQ' or r.get('TRADDT', '')[:10] != str(session):
            continue
        b = _bar(r.get('OPNPRIC'), r.get('HGHPRIC'), r.get('LWPRIC'), r.get('CLSPRIC'), r.get('PRVSCLSGPRIC'), r.get('TTLTRADGVOL'))
        if b:
            out[r['TCKRSYMB']] = b
    return out


def parse_legacy(text, session):
    """Older layout: SYMBOL, SERIES, DATE1 (13-Oct-2026), PREV_CLOSE, OPEN_PRICE, HIGH_PRICE, LOW_PRICE, CLOSE_PRICE, TTL_TRD_QNTY."""
    out = {}
    want = pd.Timestamp(session).strftime('%d-%b-%Y').upper()
    for r in _rows(text):
        if r.get('SERIES') != 'EQ' or r.get('DATE1', '').upper() != want:
            continue
        b = _bar(r.get('OPEN_PRICE'), r.get('HIGH_PRICE'), r.get('LOW_PRICE'), r.get('CLOSE_PRICE'), r.get('PREV_CLOSE'), r.get('TTL_TRD_QNTY'))
        if b:
            out[r['SYMBOL']] = b
    return out


def _download(url, timeout=25):
    with urlopen(Request(url, headers=UA), timeout=timeout) as resp:
        raw = resp.read()
    if url.endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            return z.read(z.namelist()[0]).decode('utf-8', 'replace')
    return raw.decode('utf-8', 'replace')


def fetch(session, downloader=_download):
    """Returns {'status': 'ok'|'unavailable'|'disabled', 'rows': {symbol: bar}, ...}. Never raises."""
    base = {'session': str(session), 'retrieved_at': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'rows': {}}
    if os.environ.get('EDGE_BHAVCOPY', '1') == '0':
        return dict(base, status='disabled', note='EDGE_BHAVCOPY=0')
    d = pd.Timestamp(session)
    errors = []
    for name, tmpl in URLS:
        url = tmpl.format(ymd=d.strftime('%Y%m%d'), dmy=d.strftime('%d%m%Y'))
        for _ in range(2):
            try:
                text = downloader(url)
                rows = (parse_udiff if name == 'udiff' else parse_legacy)(text, session)
                if len(rows) >= 500:                               # a real bhavcopy has ~2000 EQ rows; fewer means a wrong or partial file
                    return dict(base, status='ok', source=f'nse bhavcopy ({name})', url=url, rows=rows)
                errors.append(f'{name}: only {len(rows)} usable EQ rows for {session}')
                break
            except Exception as e:                                 # blocked, 404 (not published yet), timeout, bad zip
                errors.append(f'{name}: {type(e).__name__}: {str(e)[:80]}')
    return dict(base, status='unavailable', note='; '.join(errors[-3:]))


def _day(ts):
    ts = pd.Timestamp(ts)
    return (ts.tz_localize(None) if ts.tzinfo else ts).normalize()


def reconcile(resolved, nse, expected):
    """resolved: {requested_symbol: (df, used_symbol)}. Returns (resolved_with_fills, report). Pure given `nse`."""
    rep = {'status': nse.get('status'), 'source': nse.get('source'), 'session': str(expected), 'retrieved_at': nse.get('retrieved_at'),
           'compared': 0, 'close_mismatch': {}, 'adjustment_mismatch': {}, 'filled': [], 'cannot_fill': [], 'not_in_bhavcopy': [],
           'mismatch_share': 0.0, 'note': nse.get('note')}
    if nse.get('status') != 'ok':
        return resolved, rep
    rows, out = nse['rows'], {}
    exp = _day(expected)
    for sym, (df, used) in resolved.items():
        row = rows.get(used)
        last = df.index[-1]
        if row is None:
            rep['not_in_bhavcopy'].append(used)
            out[sym] = (df, used)
            continue
        if _day(last) == exp:
            rep['compared'] += 1
            c = float(df['Close'].iloc[-1])
            if abs(c / row['close'] - 1) > CLOSE_TOL:
                rep['close_mismatch'][used] = round((c / row['close'] - 1) * 100, 3)
            if len(df) >= 2 and abs(float(df['Close'].iloc[-2]) / row['prev_close'] - 1) > ADJUST_TOL:
                rep['adjustment_mismatch'][used] = round((float(df['Close'].iloc[-2]) / row['prev_close'] - 1) * 100, 2)
            out[sym] = (df, used)
        elif _day(last) < exp:
            if abs(float(df['Close'].iloc[-1]) / row['prev_close'] - 1) <= CONTINUITY_TOL:
                ts = exp.tz_localize(last.tzinfo) if last.tzinfo else exp
                new = pd.DataFrame({'Open': [row['open']], 'High': [row['high']], 'Low': [row['low']], 'Close': [row['close']],
                                    'Volume': [row['volume']]}, index=[ts])
                new.index.name = df.index.name
                out[sym] = (pd.concat([df, new]), used)
                rep['filled'].append(used)
            else:
                rep['cannot_fill'].append(used)                    # prev close disagrees: do not splice across a possible corporate action
                out[sym] = (df, used)
        else:
            out[sym] = (df, used)
    bad = set(rep['close_mismatch']) | set(rep['adjustment_mismatch'])
    rep['mismatch_share'] = round(len(bad) / rep['compared'], 4) if rep['compared'] else 0.0
    return out, rep


def flag(per_symbol, rep):
    """Add quarantine errors to the data-quality summaries for symbols NSE disagrees with. Returns the number flagged."""
    n = 0
    for used, pct in rep.get('close_mismatch', {}).items():
        if used in per_symbol:
            per_symbol[used]['errors'].append('nse_close_mismatch'); n += 1
    for used in rep.get('adjustment_mismatch', {}):
        if used in per_symbol and 'nse_adjustment_mismatch' not in per_symbol[used]['errors']:
            per_symbol[used]['errors'].append('nse_adjustment_mismatch'); n += 1
    return n
