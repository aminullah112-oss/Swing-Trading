import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import analysis as an
import screener as sc
from test_backtest import synth

GOOD = {'avg_value_cr': 50.0, 'stop_pct': 4.0, 'trigger_gap_pct': 0.5, 'close_in_range': 0.8, 'ema_dist_pct': 1.0, 'vol_ratio': 1.2}


def st(checks, cid):
    return next(c['status'] for c in checks if c['id'] == cid)


def test_clean_signal_has_no_warnings():
    ch = an.build_checks(GOOD)
    assert all(c['status'] == 'ok' for c in ch) and an.execution_ok(ch)


def test_each_threshold_trips_independently():
    assert st(an.build_checks({**GOOD, 'avg_value_cr': 1.0}), 'liquidity') == 'block'
    assert st(an.build_checks({**GOOD, 'avg_value_cr': 3.0}), 'liquidity') == 'warn'
    assert st(an.build_checks({**GOOD, 'stop_pct': 12.0}), 'stop_width') == 'warn'
    assert st(an.build_checks({**GOOD, 'stop_pct': 16.0}), 'stop_width') == 'block'
    assert st(an.build_checks({**GOOD, 'trigger_gap_pct': 5.2}), 'trigger_gap') == 'warn'
    assert st(an.build_checks({**GOOD, 'close_in_range': 0.2}), 'close_strength') == 'warn'
    assert st(an.build_checks({**GOOD, 'ema_dist_pct': 9.0}), 'extension') == 'warn'
    assert st(an.build_checks({**GOOD, 'vol_ratio': 0.3}), 'volume') == 'warn'


def test_only_blocks_remove_a_signal_from_tradeable():
    warn_only = an.build_checks({**GOOD, 'stop_pct': 12, 'vol_ratio': 0.3, 'trigger_gap_pct': 6})
    assert an.execution_ok(warn_only)                       # warnings are information
    assert not an.execution_ok(an.build_checks({**GOOD, 'avg_value_cr': 0.5}))
    assert not an.execution_ok(an.build_checks({**GOOD, 'stop_pct': 20}))


def test_market_context_trend_labels():
    idx = pd.bdate_range('2024-01-01', periods=400)
    up = pd.Series(np.linspace(100, 200, 400), index=idx)
    c = an.market_context(up, 40, 160, 5)
    assert c['nifty']['trend'].startswith('Uptrend') and c['breadth_stage2_pct'] == 25.0 and c['signals'] == 5
    down = pd.Series(np.linspace(200, 100, 400), index=idx)
    assert an.market_context(down, 10, 160, 0)['nifty']['trend'].startswith('Downtrend')
    assert an.market_context(None, 10, 160, 0)['nifty'] is None
    assert an.market_context(up.head(20), 10, 160, 0)['nifty'] is None


def test_evaluate_adds_analysis_without_changing_the_signal():
    found = None
    for seed in range(1, 8):
        df = synth(n=620, seed=seed, drift=0.0015)
        for t in range(300, 620, 3):
            rec, _ = sc.evaluate(df.iloc[:t + 1])
            if rec:
                found = (rec, df.iloc[:t + 1]); break
        if found: break
    assert found, 'no synthetic signal found'
    rec, df = found
    assert rec['decision'] == 'SIGNAL' and rec['trigger'] > rec['stop_loss']
    assert {c['id'] for c in rec['checks']} == {'liquidity', 'stop_width', 'trigger_gap', 'close_strength', 'extension', 'volume'}
    assert rec['execution_ok'] == an.execution_ok(rec['checks'])
    sp = rec['spark']
    assert len(sp['close']) == len(sp['ema20']) == len(sp['ema50']) == 60 and sp['close'][-1] == rec['price']
    exp_stop_pct = (rec['trigger'] - rec['stop_loss']) / rec['trigger'] * 100
    assert abs(rec['stop_pct'] - exp_stop_pct) < 0.01


# ---------------- data lag / session calendar -----------------
from datetime import datetime, date, timezone, timedelta
IST = timezone(timedelta(hours=5, minutes=30))


def ist(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=IST)


def test_expected_last_session_logic():
    # 2026-10-14 is a Wednesday
    assert an.expected_last_session(ist(2026, 10, 14, 17, 0)) == date(2026, 10, 14)    # after the close + buffer: today
    assert an.expected_last_session(ist(2026, 10, 14, 9, 0)) == date(2026, 10, 13)     # before the close: yesterday
    assert an.expected_last_session(ist(2026, 10, 14, 16, 0)) == date(2026, 10, 13)    # data not yet reliable
    assert an.expected_last_session(ist(2026, 10, 12, 9, 0)) == date(2026, 10, 9)      # Monday morning -> Friday
    assert an.expected_last_session(ist(2026, 10, 17, 12, 0)) == date(2026, 10, 16)    # Saturday -> Friday
    assert an.expected_last_session(ist(2026, 10, 18, 22, 0)) == date(2026, 10, 16)    # Sunday night -> Friday
    assert an.expected_last_session(ist(2026, 10, 16, 18, 0)) == date(2026, 10, 16)    # Friday evening


def test_sessions_behind_counts_weekdays_only():
    assert an.sessions_behind(date(2026, 10, 12), date(2026, 10, 12)) == 0
    assert an.sessions_behind(date(2026, 10, 12), date(2026, 10, 13)) == 1
    assert an.sessions_behind(date(2026, 10, 9), date(2026, 10, 12)) == 1             # Fri -> Mon is one session
    assert an.sessions_behind(date(2026, 10, 9), date(2026, 10, 13)) == 2
    assert an.sessions_behind(date(2026, 10, 14), date(2026, 10, 13)) == 0            # ahead of expectation: fine


def test_the_real_case_that_prompted_this():
    # scan at 2026-10-14 00:44 IST with data through 12 Oct: expected session is 13 Oct -> one behind
    exp = an.expected_last_session(ist(2026, 10, 14, 0, 44))
    assert exp == date(2026, 10, 13) and an.sessions_behind(date(2026, 10, 12), exp) == 1


def test_regime_series_states():
    idx = pd.bdate_range('2022-01-03', periods=500)
    up = pd.Series(np.linspace(100, 200, 500), index=idx)
    assert an.regime_series(up).iloc[-1] == 'uptrend'
    down = pd.Series(np.linspace(200, 100, 500), index=idx)
    assert an.regime_series(down).iloc[-1] == 'downtrend'
    crash = pd.Series(np.r_[np.linspace(100, 200, 400), np.linspace(200, 150, 100)], index=idx)
    assert an.regime_series(crash).iloc[-1] in ('pullback_in_uptrend', 'bounce_below_ema200', 'downtrend')
    # same labels as the text shown on the desk
    assert an.trend_label(110, 105, 100).startswith('Uptrend') and an.trend_label(90, 95, 100).startswith('Downtrend')


# ---------------- holiday calendar and ticker aliases -----------------
import json


def test_holidays_are_skipped_in_expected_session_and_lag_counts():
    hol = {date(2026, 10, 13)}                                     # pretend Tuesday 13 Oct were a holiday
    assert an.expected_last_session(ist(2026, 10, 14, 0, 44), holidays=hol) == date(2026, 10, 12)
    assert an.sessions_behind(date(2026, 10, 12), date(2026, 10, 14), hol) == 1        # 13th is not a session
    assert an.sessions_behind(date(2026, 10, 12), date(2026, 10, 14), set()) == 2
    # a holiday today means yesterday's data is current even after the close
    assert an.expected_last_session(ist(2026, 10, 13, 18, 0), holidays=hol) == date(2026, 10, 12)
    # and with no holiday the same scan time is genuinely one session behind
    exp = an.expected_last_session(ist(2026, 10, 14, 0, 44), holidays=set())
    assert an.sessions_behind(date(2026, 10, 12), exp, set()) == 1


def test_load_holidays_is_forgiving(tmp_path):
    p = tmp_path / 'h.json'
    p.write_text(json.dumps({'holidays': ['2026-10-20', 'not-a-date', '2026-11-08']}))
    assert an.load_holidays(str(p)) == {date(2026, 10, 20), date(2026, 11, 8)}
    assert an.load_holidays(str(tmp_path / 'missing.json')) == set()
    p.write_text('{ broken')
    assert an.load_holidays(str(p)) == set()
    p.write_text('[1, 2]')
    assert an.load_holidays(str(p)) == set()


def _bulk(spec, last='2026-10-12', n=120):
    idx = pd.bdate_range(end=last, periods=n)
    cols = {}
    for tick, end_offset in spec.items():
        i = idx[: n - end_offset] if end_offset else idx
        for f, v in (('Open', 100.0), ('High', 101.0), ('Low', 99.0), ('Close', 100.0), ('Volume', 1e6)):
            cols[(tick, f)] = pd.Series(v, index=i).reindex(idx)
    return pd.DataFrame(cols, index=idx)


def test_alias_is_preferred_and_stale_tickers_are_rejected():
    bulk = _bulk({'ETERNAL.NS': 0, 'ZOMATO.NS': 70, 'TMPV.NS': 0, 'TATAMOTORS.NS': 80, 'INFY.NS': 0, 'DEAD.NS': 90})
    last = bulk.index.max()
    df, used, why = sc.resolve_symbol(bulk, 'ZOMATO', last)
    assert used == 'ETERNAL' and df is not None and why is None
    assert sc.resolve_symbol(bulk, 'TATAMOTORS', last)[1] == 'TMPV'
    assert sc.resolve_symbol(bulk, 'INFY', last)[1] == 'INFY'
    df, used, why = sc.resolve_symbol(bulk, 'DEAD', last)                   # series that stopped ~90 sessions ago
    assert df is None and why


def test_old_ticker_used_when_alias_has_no_data():
    bulk = _bulk({'ZOMATO.NS': 0})
    df, used, _ = sc.resolve_symbol(bulk, 'ZOMATO', bulk.index.max())
    assert used == 'ZOMATO' and df is not None


def test_stale_original_with_no_alias_is_missing_not_silently_used():
    bulk = _bulk({'ZOMATO.NS': 70, 'INFY.NS': 0})
    df, used, why = sc.resolve_symbol(bulk, 'ZOMATO', bulk.index.max())     # alias absent from the frame, original is stale
    assert df is None


def test_alias_table_is_wired_into_downloads():
    assert sc.SYMBOL_ALIASES['ZOMATO'] == ['ETERNAL'] and 'ETERNAL.NS' in sc.ALIAS_TICKERS
    assert all(k in sc.NSE_STOCKS for k in sc.SYMBOL_ALIASES)


def test_diagnose_symbol_reports_each_candidate_ticker():
    bulk = _bulk({'ETERNAL.NS': 0, 'TMPV.NS': 60})
    d = sc.diagnose_symbol(bulk, 'ZOMATO')
    assert [x['ticker'] for x in d] == ['ETERNAL.NS', 'ZOMATO.NS']
    assert d[0]['in_download'] and d[0]['rows'] > 0 and not d[1]['in_download']
    g = sc.diagnose_symbol(bulk, 'TATAMOTORS')
    assert g[0]['in_download'] and g[0]['last_bar'] < str(bulk.index.max().date())      # present but stops early
