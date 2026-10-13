"""Provisional daily bars from 5-minute data, for when the vendor's daily bar for the latest session
is not published yet (observed: Yahoo returns a dated row with all-NaN closes while the full session
already exists as 5-minute bars).

A provisional bar is an approximation, so it is always labelled, and it is audited: when the official
daily bar appears, the error of each close definition is measured, and the better one is used from then
on. NSE's official close is a volume-weighted average of the last 30 minutes, not the last trade, so both
candidates are recorded.
"""
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

MIN_BARS = 70            # a 5-minute NSE session has 75 bars (09:15 to 15:30)
LAST_BAR_MIN_HHMM = (15, 20)
METHODS = ('last', 'vwap30')
BARS_BAND = 'provisional_bars.json'
AUDIT_FILE = 'provisional_audit.json'


def _to_ist(idx):
    return idx.tz_convert('Asia/Kolkata') if idx.tz is not None else idx


def daily_bar_from_intraday(df5, session_date):
    """df5: 5-minute OHLCV for one symbol (any number of days). session_date: date or Timestamp.
    Returns a dict for that session, or None if the session is missing or incomplete."""
    if df5 is None or len(df5) == 0:
        return None
    d = df5.dropna(subset=['Close']).copy()
    if d.empty:
        return None
    d.index = _to_ist(d.index)
    day = pd.Timestamp(session_date).date()
    d = d[d.index.date == day].sort_index()
    if len(d) < MIN_BARS:
        return None
    last = d.index[-1]
    if (last.hour, last.minute) < LAST_BAR_MIN_HHMM:
        return None
    vol = d['Volume'].fillna(0.0)
    last30 = d.tail(6)                                        # six 5-minute bars = 30 minutes
    typical = (last30['High'] + last30['Low'] + last30['Close']) / 3
    w = last30['Volume'].fillna(0.0)
    vwap30 = float((typical * w).sum() / w.sum()) if w.sum() > 0 else float(d['Close'].iloc[-1])
    return {
        'date': str(day), 'open': float(d['Open'].iloc[0]), 'high': float(d['High'].max()), 'low': float(d['Low'].min()),
        'close_last': float(d['Close'].iloc[-1]), 'close_vwap30': vwap30, 'volume': float(vol.sum()), 'bars': int(len(d)),
    }


def append_provisional(df, bar, method='last'):
    """Return df with one provisional row appended (index matches df's index type). Never overwrites a real bar."""
    if bar is None or method not in METHODS:
        return df
    ts = pd.Timestamp(bar['date'])
    if df.index.tz is not None:
        ts = ts.tz_localize(df.index.tz)
    if len(df) and df.index[-1] >= ts:
        return df
    close = bar['close_last'] if method == 'last' else bar['close_vwap30']
    row = pd.DataFrame({'Open': [bar['open']], 'High': [max(bar['high'], close)], 'Low': [min(bar['low'], close)],
                        'Close': [close], 'Volume': [bar['volume']]}, index=[ts])
    row.index.name = df.index.name
    return pd.concat([df, row])


def build_bars(intraday, symbols_to_tickers, session_date):
    """intraday: MultiIndex-column frame from yf.download(interval='5m'). symbols_to_tickers: {symbol_used: 'XXX.NS'}.
    Returns {symbol_used: bar}. Symbols whose session is incomplete are omitted."""
    out = {}
    if intraday is None or len(intraday) == 0:
        return out
    present = set(intraday.columns.get_level_values(0)) if hasattr(intraday.columns, 'levels') else set()
    for sym, tick in symbols_to_tickers.items():
        if tick not in present:
            continue
        bar = daily_bar_from_intraday(intraday[tick], session_date)
        if bar:
            out[sym] = bar
    return out


# ------------------------------------------------------------------ audit
def audit(bars, official_close, official_ohlcv=None):
    """Compare provisional bars with the official daily bar. bars: {symbol: bar}.
    official_ohlcv: {symbol: dict(open, high, low, close, volume)} (official). Returns summary dict or None."""
    errs = {'close_last': [], 'close_vwap30': [], 'high': [], 'low': [], 'open': [], 'volume': []}
    n = 0
    for sym, bar in bars.items():
        o = (official_ohlcv or {}).get(sym)
        if not o or not o.get('close') or np.isnan(o['close']):
            continue
        n += 1
        errs['close_last'].append(abs(bar['close_last'] / o['close'] - 1) * 1e4)
        errs['close_vwap30'].append(abs(bar['close_vwap30'] / o['close'] - 1) * 1e4)
        for k in ('high', 'low', 'open'):
            if o.get(k) and not np.isnan(o[k]):
                errs[k].append(abs(bar[k] / o[k] - 1) * 1e4)
        if o.get('volume') and o['volume'] > 0:
            errs['volume'].append(abs(bar['volume'] / o['volume'] - 1) * 1e4)
    if n == 0:
        return None
    med = lambda v: round(float(np.median(v)), 1) if v else None
    return {'symbols': n, 'median_abs_error_bps': {k: med(v) for k, v in errs.items()},
            'p90_abs_error_bps': {k: round(float(np.percentile(v, 90)), 1) if v else None for k, v in errs.items()}}


def choose_method(audits, min_symbols=50):
    """Use the close definition with the lower median error once an audit with enough symbols exists; default 'last'."""
    best, best_err = 'last', None
    tot = {'close_last': [], 'close_vwap30': []}
    for a in audits or []:
        if a.get('symbols', 0) >= min_symbols:
            for k in tot:
                e = a['median_abs_error_bps'].get(k)
                if e is not None:
                    tot[k].append(e)
    if tot['close_last'] and tot['close_vwap30']:
        m_last, m_vwap = float(np.mean(tot['close_last'])), float(np.mean(tot['close_vwap30']))
        best = 'vwap30' if m_vwap < m_last else 'last'
    return best


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(obj, path):
    with open(path + '.tmp', 'w') as f:
        json.dump(obj, f, indent=2)
    os.replace(path + '.tmp', path)


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')
