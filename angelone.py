"""Angel One SmartAPI as a second, independent source of official daily bars (used when NSE's own files cannot be fetched).

Read-only market data: no order endpoint is touched here. Credentials come from environment variables (GitHub secrets in the
workflow) and are never logged or written to disk:
    ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PIN, ANGEL_TOTP_SECRET   (the base32 secret shown when TOTP is enabled)
Without them the module reports 'not_configured' and the scan carries on.

The output has the same shape as bhavcopy.fetch() ({'status', 'rows': {symbol: bar}}), so bhavcopy.reconcile() can cross-check and
fill from it unchanged. Written from Angel One's documented API (SmartConnect.generateSession / getCandleData with interval ONE_DAY,
OpenAPIScripMaster.json for symbol tokens); it has NOT been run against the live service from this environment, and the
instrument-master layout and rate limits are assumptions to confirm on the first run.
"""
import os
import time
from datetime import datetime, timedelta, timezone

import pandas as pd

MASTER_URL = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
NIFTY_FALLBACK_TOKEN = '99926000'
MIN_COVERAGE = 0.80          # share of requested symbols that must return a bar for the source to count as available
PACE_SECONDS = 0.4           # stay well under the historical-data request limit
ENV = ('ANGEL_API_KEY', 'ANGEL_CLIENT_CODE', 'ANGEL_PIN', 'ANGEL_TOTP_SECRET')


def credentials(env=None):
    env = os.environ if env is None else env
    vals = {k: (env.get(k) or '').strip() for k in ENV}
    return vals if all(vals.values()) else None


def load_master(loader=None):
    if loader:
        return loader()
    import json
    from urllib.request import Request, urlopen
    with urlopen(Request(MASTER_URL, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))


def token_map(master, symbols):
    """{symbol: token} for NSE cash-equity entries named 'SYMBOL-EQ', plus the Nifty 50 index token."""
    want = {f'{s}-EQ': s for s in symbols}
    out, nifty = {}, None
    for e in master:
        if e.get('exch_seg') != 'NSE':
            continue
        sym = e.get('symbol', '')
        if sym in want:
            out[want[sym]] = str(e['token'])
        elif e.get('name', '').upper() == 'NIFTY' or sym.upper() == 'NIFTY 50':
            if e.get('instrumenttype') in ('AMXIDX', '') and sym.upper() in ('NIFTY 50', 'NIFTY'):
                nifty = str(e['token'])
    return out, nifty or NIFTY_FALLBACK_TOKEN


def candles_to_bar(candles, session):
    """candles: [[iso_time, open, high, low, close, volume], ...]. Bar for `session` with prev_close from the candle before it."""
    day = pd.Timestamp(session).strftime('%Y-%m-%d')
    rows = [(str(c[0])[:10], c) for c in candles or []]
    rows.sort(key=lambda x: x[0])
    for i, (d, c) in enumerate(rows):
        if d == day and i > 0:
            try:
                o, h, l, cl, v = (float(x) for x in c[1:6])
                pc = float(rows[i - 1][1][4])
            except (TypeError, ValueError, IndexError):
                return None
            if min(o, h, l, cl, pc) <= 0 or h < max(o, cl, l) * 0.9995 or l > min(o, cl, h) * 1.0005:
                return None
            return {'open': o, 'high': h, 'low': l, 'close': cl, 'prev_close': pc, 'volume': v}
    return None


def _default_client(cred):
    from SmartApi import SmartConnect       # pip install smartapi-python pyotp (workflow installs them; tests inject a fake)
    import pyotp
    api = SmartConnect(api_key=cred['ANGEL_API_KEY'])
    s = api.generateSession(cred['ANGEL_CLIENT_CODE'], cred['ANGEL_PIN'], pyotp.TOTP(cred['ANGEL_TOTP_SECRET']).now())
    if not (s or {}).get('status'):
        raise RuntimeError(f"login refused: {(s or {}).get('message', 'no response')}")
    return api


def fetch(session, symbols, env=None, client_factory=None, master_loader=None, sleep=time.sleep, pace=PACE_SECONDS):
    """Returns {'status': 'ok'|'unavailable'|'not_configured', 'rows', 'nifty_bar', 'source', 'note'}. Never raises; never logs secrets."""
    base = {'session': str(session), 'source': 'angel one smartapi', 'rows': {}, 'nifty_bar': None,
            'retrieved_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    cred = credentials(env)
    if not cred:
        return dict(base, status='not_configured', note='ANGEL_* secrets not set')
    try:
        client = (client_factory or _default_client)(cred)
        tokens, nifty_tok = token_map(load_master(master_loader), symbols)
        frm = (pd.Timestamp(session) - timedelta(days=12)).strftime('%Y-%m-%d 09:15')
        to = pd.Timestamp(session).strftime('%Y-%m-%d 15:30')

        def bar_for(token):
            r = client.getCandleData({'exchange': 'NSE', 'symboltoken': token, 'interval': 'ONE_DAY', 'fromdate': frm, 'todate': to})
            return candles_to_bar((r or {}).get('data'), session)
        errors = 0
        for sym, tok in tokens.items():
            try:
                b = bar_for(tok)
                if b:
                    base['rows'][sym] = b
            except Exception:
                errors += 1
            sleep(pace)
        try:
            base['nifty_bar'] = bar_for(nifty_tok)
        except Exception:
            pass
        need = MIN_COVERAGE * len(symbols)
        if len(base['rows']) < need:
            return dict(base, status='unavailable', note=f"only {len(base['rows'])}/{len(symbols)} symbols returned a bar for {session} ({errors} errors, {len(symbols) - len(tokens)} without a token)")
        return dict(base, status='ok')
    except Exception as e:
        return dict(base, status='unavailable', note=f'{type(e).__name__}: {str(e)[:100]}')       # message only: never the credentials
