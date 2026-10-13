"""Market-data integrity checks. Pure functions, no network.

Principle: fail closed. A symbol whose data cannot be trusted is quarantined; if too much of the universe is
untrusted, or the latest session is not covered by OFFICIAL daily bars, no signal is actionable at all.

What is and is not verified (stated plainly so it is not over-claimed):
  verified    duplicate / out-of-order / missing sessions (against weekdays and any known holidays), malformed
              or non-positive values, OHLC consistency, zero volume, stale last bar, future-dated bars,
              consistency of the data cutoff across symbols
  heuristic   corporate actions: no corporate-action feed exists here, so large one-day moves are treated as
              possible unadjusted splits/bonuses and quarantined; dividends/splits adjustment itself is Yahoo's
  not verified the exchange holiday calendar (market_holidays.json is hand-maintained and may be incomplete),
              the vendor's adjusted closes against exchange official closes
"""
from collections import Counter
from datetime import timedelta

import numpy as np
import pandas as pd

import settings

LOOKBACK = 252
RECENT = 5
OHLC_TOL = 5e-4            # relative tolerance for adjusted-price rounding


def _issue(code, severity, detail):
    return {'code': code, 'severity': severity, 'detail': detail}


def _dates(idx):
    i = pd.DatetimeIndex(idx)
    return i.tz_localize(None) if i.tz is not None else i


def validate_bars(df, expected_session=None, holidays=frozenset(), lookback=LOOKBACK):
    """Issues found in one symbol's daily OHLCV frame (list of dicts; severity 'error' quarantines the symbol)."""
    out = []
    if df is None or len(df) == 0:
        return [_issue('empty', 'error', 'no bars')]
    if len(df) < 60:
        return [_issue('too_short', 'error', f'only {len(df)} bars')]
    idx = _dates(df.index)
    if idx.has_duplicates:
        out.append(_issue('duplicate_dates', 'error', f'{int(idx.duplicated().sum())} duplicated bar dates'))
    if not idx.is_monotonic_increasing:
        out.append(_issue('out_of_order', 'error', 'bars are not in chronological order'))
    w = df.tail(lookback)
    cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [c for c in cols if c not in w.columns]
    if missing_cols:
        return out + [_issue('malformed_columns', 'error', f'missing columns {missing_cols}')]
    vals = w[cols].astype(float)
    if not np.isfinite(vals.values).all():
        out.append(_issue('malformed_values', 'error', 'NaN or infinite OHLCV values in the lookback window'))
    px = vals[['Open', 'High', 'Low', 'Close']]
    if (px.values <= 0).any():
        out.append(_issue('non_positive_price', 'error', 'zero or negative price'))
    if (vals['Volume'] < 0).any():
        out.append(_issue('negative_volume', 'error', 'negative volume'))
    # OHLC consistency (tolerant of adjustment rounding)
    hi_bad = vals['High'] < (vals[['Open', 'Close', 'Low']].max(axis=1) * (1 - OHLC_TOL))
    lo_bad = vals['Low'] > (vals[['Open', 'Close', 'High']].min(axis=1) * (1 + OHLC_TOL))
    bad = (hi_bad | lo_bad)
    if bad.tail(RECENT).any():
        out.append(_issue('ohlc_inconsistent_recent', 'error', f'{int(bad.tail(RECENT).sum())} of the last {RECENT} bars violate high>=open/close/low>=low'))
    elif bad.mean() > 0.01:
        out.append(_issue('ohlc_inconsistent', 'warn', f'{int(bad.sum())} bars in the lookback violate OHLC consistency'))
    # volume
    if len(vals) and vals['Volume'].iloc[-1] == 0:
        out.append(_issue('zero_volume_last', 'error', 'last bar has zero volume'))
    elif (vals['Volume'] == 0).mean() > 0.05:
        out.append(_issue('zero_volume_frequent', 'warn', f"{(vals['Volume'] == 0).mean():.0%} of bars have zero volume"))
    # one-day moves: possible unadjusted corporate actions
    ret = vals['Close'].pct_change().abs().dropna()
    if len(ret):
        if (ret >= settings.JUMP_ERROR).any():
            out.append(_issue('suspect_corporate_action', 'error', f'a one-day move of {ret.max():.0%}: possible unadjusted split/bonus'))
        elif (ret.tail(RECENT) >= settings.JUMP_WARN).any():
            out.append(_issue('recent_large_jump', 'error', f'a one-day move of {ret.tail(RECENT).max():.0%} in the last {RECENT} bars cannot be verified'))
        elif (ret >= settings.JUMP_WARN).any():
            out.append(_issue('large_jump', 'warn', f'a one-day move of {ret.max():.0%} in the lookback'))
    # calendar
    d = _dates(w.index)
    wk = [x for x in d if x.weekday() >= 5]
    hol = [x for x in d if x.date() in holidays]
    if wk or hol:
        out.append(_issue('non_session_bar', 'warn', f'{len(wk)} weekend and {len(hol)} known-holiday bars (special sessions are possible)'))
    last60 = d[-60:]
    if len(last60) >= 2:
        span = pd.bdate_range(last60[0], last60[-1])
        expected_days = [x for x in span if x.date() not in holidays]
        missing = len(set(expected_days) - set(last60))
        if missing > 15:
            out.append(_issue('missing_sessions', 'error', f'{missing} sessions missing in the last 60'))
        elif missing > 5:
            out.append(_issue('missing_sessions', 'warn', f'{missing} sessions missing in the last 60 (unknown holidays are possible)'))
    # freshness against the expected session
    if expected_session is not None and len(d):
        last = d[-1].date()
        if last > expected_session:
            out.append(_issue('future_bar', 'error', f'last bar {last} is after the expected session {expected_session}'))
        elif last < expected_session:
            out.append(_issue('stale_bar', 'error', f'last bar {last} is before the expected session {expected_session}'))
    return out


def summarize_symbol(df, expected_session=None, holidays=frozenset()):
    issues = validate_bars(df, expected_session, holidays)
    last = None
    if df is not None and len(df):
        last = _dates(df.index)[-1].date()
    return {'last_bar': last, 'errors': [i['code'] for i in issues if i['severity'] == 'error'],
            'warns': [i['code'] for i in issues if i['severity'] == 'warn'], 'issues': issues}


def assess(per_symbol, expected_session, nifty_last_bar=None):
    """Universe-level verdict. per_symbol: {symbol: summarize_symbol(...)}. Status TRUSTED or UNTRUSTED with reasons."""
    n = len(per_symbol)
    reasons = []
    if n == 0:
        return {'status': 'UNTRUSTED', 'reasons': ['no symbols with data'], 'symbols': 0, 'official_coverage': 0.0,
                'cutoff_counts': {}, 'quarantined': {}, 'critical_issue_share': 1.0, 'expected_session': str(expected_session)}
    counts = Counter(str(v['last_bar']) for v in per_symbol.values())
    with_expected = sum(1 for v in per_symbol.values() if v['last_bar'] == expected_session)
    coverage = with_expected / n
    quarantined = {s: v['errors'] for s, v in per_symbol.items() if v['errors']}
    critical = {s: e for s, e in quarantined.items() if any(c != 'stale_bar' for c in e)}
    critical_share = len(critical) / n
    if coverage < settings.OFFICIAL_COVERAGE_MIN:
        reasons.append(f'only {coverage:.0%} of symbols have an official daily bar for the expected session {expected_session} '
                       f'(need {settings.OFFICIAL_COVERAGE_MIN:.0%}); last-bar dates: {dict(counts.most_common(3))}')
    if nifty_last_bar is None or nifty_last_bar != expected_session:
        reasons.append(f'the Nifty 50 has no official bar for {expected_session} (last: {nifty_last_bar})')
    if critical_share > settings.MAX_CRITICAL_ISSUE_SHARE:
        reasons.append(f'{len(critical)} symbols ({critical_share:.1%}) have critical data errors (limit {settings.MAX_CRITICAL_ISSUE_SHARE:.0%})')
    return {'status': 'UNTRUSTED' if reasons else 'TRUSTED', 'reasons': reasons, 'symbols': n,
            'official_coverage': round(coverage, 4), 'cutoff_counts': dict(counts.most_common(5)),
            'quarantined': quarantined, 'critical_issue_share': round(critical_share, 4),
            'expected_session': str(expected_session)}


def actionable_symbols(per_symbol, expected_session):
    """Symbols that may generate actionable signals: official expected-session bar and no errors."""
    return {s for s, v in per_symbol.items() if v['last_bar'] == expected_session and not v['errors']}
