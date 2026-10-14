"""Known events that make a new entry riskier than the chart shows: results, ex-dates, F&O ban, ASM/GSM.

Where each comes from, and how far to trust it:
  event_calendar.json   operator-maintained (earnings, ex-dividend, splits, bonuses, ASM/GSM lists). Authoritative when filled in.
  NSE F&O ban list      downloaded best-effort for the session; unavailable = recorded as unverified, not as 'clear'.
  yfinance earnings     best-effort per signal; often missing or wrong for Indian stocks. Used only as a hint.
A known event inside the window BLOCKS the entry (it only removes trades). An unknown one is flagged as unverified on the desk.
"""
import csv
import io
import json
import os
import re
from datetime import date, datetime
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

import settings

HERE = os.path.dirname(os.path.abspath(__file__))
BAN_URL = 'https://nsearchives.nseindia.com/archives/fo/sec_ban/fo_secban_{dmy}.csv'
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36', 'Referer': 'https://www.nseindia.com/'}
KINDS = {'earnings': 'results', 'ex_date': 'ex-dividend/ex-date', 'corporate_action': 'corporate action', 'other': 'event'}


def load_manual(path=None):
    try:
        with open(path or os.path.join(HERE, 'event_calendar.json')) as f:
            d = json.load(f)
    except (OSError, ValueError):
        return {'events': [], 'asm_gsm': [], 'updated': None}
    ev = []
    for e in d.get('events', []):
        try:
            ev.append({'symbol': str(e['symbol']).upper(), 'date': datetime.strptime(str(e['date'])[:10], '%Y-%m-%d').date(),
                       'kind': e.get('kind', 'other'), 'note': e.get('note', '')})
        except (KeyError, ValueError):
            continue
    return {'events': ev, 'asm_gsm': [str(s).upper() for s in d.get('asm_gsm', [])], 'updated': d.get('updated')}


def parse_ban(text):
    """Symbols in the F&O ban file (layout: a header line then 'serial,SYMBOL' rows; tolerant of variations)."""
    out = set()
    for row in csv.reader(io.StringIO(text)):
        for cell in row[1:] if len(row) > 1 else row:
            tok = cell.strip().upper()
            if re.fullmatch(r'[A-Z0-9&\-]{2,20}', tok) and not tok.isdigit() and tok not in ('SECURITIES', 'SYMBOL', 'NONE'):
                out.add(tok)
    return out


def fetch_ban(session, downloader=None):
    """{'status': 'ok'|'unavailable'|'disabled', 'symbols': set}. Never raises."""
    if downloader is None and os.environ.get('EDGE_EVENTS', '1') == '0':
        return {'status': 'disabled', 'symbols': set()}
    url = BAN_URL.format(dmy=pd.Timestamp(session).strftime('%d%m%Y'))
    try:
        if downloader:
            text = downloader(url)
        else:
            with urlopen(Request(url, headers=UA), timeout=20) as r:
                text = r.read().decode('utf-8', 'replace')
        return {'status': 'ok', 'symbols': parse_ban(text), 'url': url}
    except Exception as e:
        return {'status': 'unavailable', 'symbols': set(), 'note': f'{type(e).__name__}: {str(e)[:80]}'}


def fetch_earnings_yf(symbol):
    """Next earnings date from yfinance, or None. Best-effort only."""
    if os.environ.get('EDGE_EVENTS', '1') == '0':
        return None
    try:
        import yfinance as yf
        cal = yf.Ticker(f'{symbol}.NS').calendar
        d = (cal.get('Earnings Date') if isinstance(cal, dict) else None) or []
        d = d if isinstance(d, (list, tuple)) else [d]
        return min(pd.Timestamp(x).date() for x in d) if d else None
    except Exception:
        return None


def sessions_between(start, end, holidays=frozenset()):
    """Trading sessions after `start` up to and including `end` (0 if end <= start)."""
    if end <= start:
        return 0
    return int(np.busday_count(start + pd.Timedelta(days=1), end + pd.Timedelta(days=1), holidays=sorted(holidays)))


def assess(symbol, signal_date, manual, ban, earnings_date=None, holidays=frozenset(), window=None):
    """{'blocked': bool, 'reasons': [...], 'unverified': [...]} for an entry on the session after signal_date."""
    window = window or settings.EVENT_WINDOW_SESSIONS
    reasons, unverified = [], []
    for e in manual['events']:
        if e['symbol'] == symbol:
            n = sessions_between(signal_date, e['date'], holidays)
            if 0 <= (e['date'] - signal_date).days and n <= window:
                reasons.append(f"{KINDS.get(e['kind'], 'event')} on {e['date']} ({n} session(s) away){': ' + e['note'] if e['note'] else ''}")
    if earnings_date and not any(e['symbol'] == symbol and e['kind'] == 'earnings' for e in manual['events']):
        n = sessions_between(signal_date, earnings_date, holidays)
        if 0 <= (earnings_date - signal_date).days and n <= window:
            reasons.append(f'results expected {earnings_date} ({n} session(s) away, from yfinance: confirm)')
    if symbol in manual['asm_gsm']:
        reasons.append('on the ASM/GSM surveillance list')
    if symbol in ban['symbols']:
        reasons.append('in the F&O ban list')
    if ban['status'] != 'ok':
        unverified.append('F&O ban list not retrieved')
    if earnings_date is None and not any(e['symbol'] == symbol and e['kind'] == 'earnings' for e in manual['events']):
        unverified.append('results date unknown: check before entry')
    if not manual['updated']:
        unverified.append('event_calendar.json has not been filled in')
    return {'blocked': bool(reasons), 'reasons': reasons, 'unverified': unverified}
