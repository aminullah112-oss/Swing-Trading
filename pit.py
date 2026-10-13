"""Point-in-time universe hook (survivorship-bias fix), data-agnostic.

The membership file is a CSV with columns: symbol,start,end  (dates YYYY-MM-DD; blank end = still a member).
Point EDGE_PIT_UNIVERSE at it and the backtests only take a signal when the stock was a member on the
signal date. Building the file needs index-reconstitution history (for example NSE's semi-annual review
notices) and delisted-stock prices (for example NSE bhavcopy). Neither can be fetched from here, so no
file ships with the repo: without one, nothing changes.

Honest limit: membership alone does not fix survivorship. Delisted names also need PRICES. coverage()
reports the share of member-days that actually have price history; below ~95% the result is still biased
and gate B2 should stay unattested.
"""
import csv
import os

import pandas as pd


def load_membership(path):
    spans = {}
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            sym = (row.get('symbol') or '').strip()
            if not sym:
                continue
            start = pd.Timestamp(row['start']) if (row.get('start') or '').strip() else pd.Timestamp.min
            end = pd.Timestamp(row['end']) if (row.get('end') or '').strip() else pd.Timestamp.max
            spans.setdefault(sym, []).append((start, end))
    return spans


def from_env():
    path = os.environ.get('EDGE_PIT_UNIVERSE')
    if path and os.path.exists(path):
        return load_membership(path)
    return None


def is_member(spans, symbol, date):
    if spans is None:
        return True
    d = pd.Timestamp(date)
    return any(s <= d <= e for s, e in spans.get(symbol, []))


def symbols(spans):
    return sorted(spans)


def coverage(spans, frames):
    """Share of (symbol, month) membership months for which the frames hold price history."""
    if not spans:
        return None
    total = have = 0
    for sym, ranges in spans.items():
        df = frames.get(sym)
        for s, e in ranges:
            lo = max(s, pd.Timestamp('2000-01-01')); hi = min(e, pd.Timestamp.today().normalize())
            if hi < lo:
                continue
            months = pd.period_range(lo, hi, freq='M')
            total += len(months)
            if df is not None and len(df):
                have += sum(1 for m in months if ((df.index >= m.start_time) & (df.index <= m.end_time)).any())
    return round(have / total, 3) if total else None
