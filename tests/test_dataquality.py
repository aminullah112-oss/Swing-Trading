import os, sys
from datetime import date
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import dataquality as dq
import settings

EXP = date(2026, 10, 13)


def frame(n=200, end='2026-10-13', seed=0):
    idx = pd.bdate_range(end=end, periods=n)
    rng = np.random.default_rng(seed)
    c = 100 * np.cumprod(1 + 0.0005 + 0.01 * rng.standard_normal(n))
    o = c * (1 + 0.002 * rng.standard_normal(n))
    return pd.DataFrame({'Open': o, 'High': np.maximum(o, c) * 1.004, 'Low': np.minimum(o, c) * 0.996, 'Close': c,
                         'Volume': 1e6 * (1 + rng.random(n))}, index=idx)


def codes(df, **kw):
    return {i['code']: i['severity'] for i in dq.validate_bars(df, EXP, **kw)}


def test_clean_frame_has_no_errors():
    assert [i for i in dq.validate_bars(frame(), EXP) if i['severity'] == 'error'] == []


def test_each_failure_mode_is_detected():
    assert codes(pd.DataFrame())['empty'] == 'error'
    assert codes(frame(n=30))['too_short'] == 'error'
    f = frame(); dup = pd.concat([f, f.iloc[[-5]]]); assert codes(dup)['duplicate_dates'] == 'error'
    f = frame(); shuffled = f.iloc[::-1]; assert codes(shuffled)['out_of_order'] == 'error'
    f = frame(); f.iloc[-3, f.columns.get_loc('Close')] = np.nan; assert codes(f)['malformed_values'] == 'error'
    f = frame(); f.iloc[-10, f.columns.get_loc('Low')] = -1.0; assert codes(f)['non_positive_price'] == 'error'
    f = frame(); f.iloc[-2, f.columns.get_loc('High')] = f['Low'].iloc[-2] * 0.9; assert codes(f)['ohlc_inconsistent_recent'] == 'error'
    f = frame(); f.iloc[-1, f.columns.get_loc('Volume')] = 0; assert codes(f)['zero_volume_last'] == 'error'
    f = frame(); f.iloc[-1, f.columns.get_loc('Volume')] = -5; assert codes(f)['negative_volume'] == 'error'


def test_corporate_action_suspects_and_jumps():
    f = frame(); f.iloc[-40:, :4] = f.iloc[-40:, :4] * 0.4        # an unadjusted 60% drop 40 bars ago, persists
    assert codes(f)['suspect_corporate_action'] == 'error'
    g = frame(); g.iloc[-2:, :4] = g.iloc[-2:, :4] * 1.35         # +35% in the last bars cannot be verified
    assert codes(g)['recent_large_jump'] == 'error'
    h = frame(); h.iloc[-100:, :4] = h.iloc[-100:, :4] * 1.35     # an older 35% move is only a warning
    assert codes(h)['large_jump'] == 'warn'


def test_stale_and_future_bars_against_the_expected_session():
    assert codes(frame(end='2026-10-12'))['stale_bar'] == 'error'
    assert codes(frame(end='2026-10-14'))['future_bar'] == 'error'
    assert 'stale_bar' not in codes(frame(end='2026-10-13'))


def test_missing_sessions_and_non_session_bars():
    f = frame()
    gaps = f.drop(f.index[-30:-10])                               # 20 missing sessions inside the last 60
    assert codes(gaps)['missing_sessions'] == 'error'
    few = f.drop(f.index[-20:-13])
    assert codes(few)['missing_sessions'] == 'warn'
    # a known holiday explains a gap
    f2 = frame(); hol = f2.index[-20].date(); gap1 = f2.drop(f2.index[-20])
    assert 'missing_sessions' not in codes(gap1, holidays={hol})
    sat = f2.copy(); sat.loc[pd.Timestamp('2026-10-10')] = sat.iloc[-1]                # a Saturday bar (special session?)
    assert codes(sat.sort_index())['non_session_bar'] == 'warn'


def per(symbols_last, errors=None):
    errors = errors or {}
    return {s: {'last_bar': d, 'errors': errors.get(s, []), 'warns': [], 'issues': []} for s, d in symbols_last.items()}


def test_assess_trusts_a_fully_covered_universe_and_quarantines_bad_symbols():
    syms = {f'S{i}': EXP for i in range(100)}
    a = dq.assess(per(syms, {'S3': ['ohlc_inconsistent_recent']}), EXP, nifty_last_bar=EXP)
    assert a['status'] == 'TRUSTED' and 'S3' in a['quarantined']
    assert 'S3' not in dq.actionable_symbols(per(syms, {'S3': ['ohlc_inconsistent_recent']}), EXP) and 'S4' in dq.actionable_symbols(per(syms), EXP)


def test_assess_fails_closed_on_coverage_cutoff_nifty_and_critical_errors():
    old = date(2026, 10, 12)
    syms = {f'S{i}': (EXP if i < 90 else old) for i in range(100)}                # 90% official coverage < 95%
    a = dq.assess(per(syms), EXP, EXP)
    assert a['status'] == 'UNTRUSTED' and 'official daily bar' in a['reasons'][0] and a['official_coverage'] == 0.9
    full = {f'S{i}': EXP for i in range(100)}
    assert dq.assess(per(full), EXP, nifty_last_bar=old)['status'] == 'UNTRUSTED'      # Nifty not current
    assert dq.assess(per(full), EXP, nifty_last_bar=None)['status'] == 'UNTRUSTED'
    errs = {f'S{i}': ['ohlc_inconsistent_recent'] for i in range(5)}                   # 5% critical > 2% limit
    assert dq.assess(per(full, errs), EXP, EXP)['status'] == 'UNTRUSTED'
    assert dq.assess({}, EXP, EXP)['status'] == 'UNTRUSTED'
    # stale-only symbols reduce coverage but are not counted as critical data errors
    stale = {f'S{i}': (EXP if i >= 2 else old) for i in range(100)}
    a2 = dq.assess(per(stale, {'S0': ['stale_bar'], 'S1': ['stale_bar']}), EXP, EXP)
    assert a2['status'] == 'TRUSTED' and a2['critical_issue_share'] == 0.0
