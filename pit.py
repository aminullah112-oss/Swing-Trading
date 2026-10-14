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


def coverage(spans, frames, today=None):
    """Share of (symbol, month) membership months for which the frames hold price history."""
    if not spans:
        return None
    total = have = 0
    for sym, ranges in spans.items():
        df = frames.get(sym)
        for s, e in ranges:
            lo = max(s, pd.Timestamp('2000-01-01')); hi = min(e, pd.Timestamp(today) if today is not None else pd.Timestamp.today().normalize())
            if hi < lo:
                continue
            months = pd.period_range(lo, hi, freq='M')
            total += len(months)
            if df is not None and len(df):
                have += sum(1 for m in months if ((df.index >= m.start_time) & (df.index <= m.end_time)).any())
    return round(have / total, 3) if total else None


def acceptance(spans, frames, today=None, min_coverage=0.95):
    """Objective test for a survivorship-free universe. B2 is not credited unless this passes (and the attestation is set).
    Passes only if ALL hold: a membership file exists; price coverage of member-months >= min_coverage; at least one member
    that LEFT the index (membership ended before today) is present AND has price history; the file reaches back to the start
    of the price data. Without a file the result is 'no_pit_universe' and the backtest keeps its survivorship-bias label."""
    today = pd.Timestamp(today) if today is not None else pd.Timestamp.today().normalize()
    if not spans:
        return {'passed': False, 'status': 'no_pit_universe', 'reasons': ['no point-in-time membership file (EDGE_PIT_UNIVERSE); results are survivorship-biased'],
                'coverage': None, 'delisted_with_prices': 0, 'delisted_total': 0}
    reasons = []
    cov = coverage(spans, frames, today)
    if cov is None or cov < min_coverage:
        reasons.append(f'price coverage of member-months {cov} < {min_coverage}')
    delisted = [s for s, rr in spans.items() if all(e < today for _, e in rr)]
    with_px = [s for s in delisted if frames.get(s) is not None and len(frames[s])]
    if not delisted:
        reasons.append('membership file lists no stock that left the index: it cannot be point-in-time')
    elif not with_px:
        reasons.append(f'none of the {len(delisted)} departed stocks has price history: delisted names are missing')
    elif len(with_px) / len(delisted) < 0.5:
        reasons.append(f'only {len(with_px)}/{len(delisted)} departed stocks have price history')
    first_px = min((df.index[0] for df in frames.values() if len(df)), default=None)
    first_member = min((s for rr in spans.values() for s, _ in rr if s != pd.Timestamp.min), default=None)
    if first_px is not None and first_member is not None and first_member > first_px + pd.Timedelta(days=365):
        reasons.append(f'membership starts {first_member.date()}, well after the price data begins {first_px.date()}')
    return {'passed': not reasons, 'status': 'pass' if not reasons else 'fail', 'reasons': reasons, 'coverage': cov,
            'delisted_total': len(delisted), 'delisted_with_prices': len(with_px)}
