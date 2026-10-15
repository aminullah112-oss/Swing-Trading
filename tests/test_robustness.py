import json, os, sys
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import backtest as bt
import experiments as ex
import holdout_guard as hg
import prereg
import risk
import robustness as rb
from test_backtest import synth


def fixture(n=1700, k=10):
    return {f'S{i}': synth(n=n, seed=i, drift=0.0009) for i in range(k)}, synth(n=n, seed=999)['Close']


def small_spec():
    spec = json.loads(json.dumps(prereg.load('PREREG_v3')))
    spec['windows'].update(design_end='2024-06-30', holdout_start='2024-07-01')
    return spec


def test_prereg_v3_is_pinned_and_counts_the_whole_family():
    s = prereg.load('PREREG_v3')
    assert s['multiple_testing']['n_tests'] == 17 and abs(prereg.alpha_per_test(s) - 0.05 / 17) < 1e-12
    assert [t['id'] for t in s['inferential_tests']] == ['R-NULL-A', 'R-NULL-B', 'R-CI', 'R-BENCH']
    assert {g['id'] for g in s['tolerance_gates']} == {'R-MC', 'R-REGIME', 'R-SENS', 'R-EXEC', 'R-SURV', 'R-HO'}
    assert 1 / (rb.N_DRAWS + 1) < prereg.alpha_per_test(s)          # the null test can reach the registered alpha at all
    assert 'does not authorise live trading' in s['verdict_rule']


def test_editing_the_preregistration_is_detected(tmp_path):
    import shutil
    for ext in ('json', 'sha256'):
        shutil.copy(f'experiments/PREREG_v3.{ext}', tmp_path / f'PREREG_v3.{ext}')
    (tmp_path / 'PREREG_v3.json').write_text((tmp_path / 'PREREG_v3.json').read_text().replace('0.35', '0.45').replace('35%', '45%'))
    with pytest.raises(prereg.PreregMismatch):
        prereg.load('PREREG_v3', directory=str(tmp_path))


def test_null_test_p_value_is_small_when_c0_beats_the_pool_and_large_when_it_does_not():
    rng = np.random.default_rng(1)
    dates = pd.date_range('2020-01-01', periods=300, freq='B')
    cand = pd.DataFrame({'symbol': [f's{i}' for i in range(len(dates) * 6)], 'signal_date': np.repeat(dates, 6),
                         'r': rng.normal(0.0, 1.0, len(dates) * 6), 'is_signal': False, 'stage_pass': True})
    c0_good = pd.DataFrame({'signal_date': dates, 'r': 2.5})
    c0_bad = pd.DataFrame({'signal_date': dates, 'r': -2.5})
    good = rb.null_test(c0_good, cand, ~cand['is_signal'], k=500)
    bad = rb.null_test(c0_bad, cand, ~cand['is_signal'], k=500)
    assert good['p_value'] <= 0.01 and bad['p_value'] >= 0.99
    assert good['draws'] == 500 and good['matched_c0_trades'] == len(dates)


def test_null_test_is_reproducible_and_reports_unmatched_dates():
    dates = pd.date_range('2020-01-01', periods=50, freq='B')
    cand = pd.DataFrame({'symbol': 'a', 'signal_date': dates[:40], 'r': np.linspace(-1, 1, 40), 'is_signal': False, 'stage_pass': True})
    c0 = pd.DataFrame({'signal_date': dates, 'r': 0.3})
    a, b = rb.null_test(c0, cand, ~cand['is_signal'], k=200), rb.null_test(c0, cand, ~cand['is_signal'], k=200)
    assert a == b and a['c0_trades_without_candidates'] == 10
    assert rb.null_test(c0, cand, cand['is_signal'], k=10)['status'] == 'unverifiable'


def test_candidate_table_excludes_nothing_it_should_mark_and_matches_c0_trades():
    frames, bench = fixture()
    cfg = ex.realistic_cfg()
    prepared = bt.prepare(frames)
    cand = rb.candidate_table(prepared, cfg, '2099-01-01')
    c0 = bt.generate_trades(frames, cfg, bench, prepared)
    assert len(cand) > 0 and cand['is_signal'].sum() >= len(c0)          # sequential-position rule only removes signals, never adds
    key = set(zip(c0['symbol'], c0['signal_date']))
    flagged = set(zip(cand[cand['is_signal']]['symbol'], cand[cand['is_signal']]['signal_date']))
    assert key <= flagged
    merged = c0.merge(cand, on=['symbol', 'signal_date'], suffixes=('', '_c'))
    assert np.allclose(merged['r'], merged['r_c'])                        # the candidate simulation is C0's simulation


def test_monte_carlo_is_reproducible_and_orders_correctly():
    rng = np.random.default_rng(3)
    r = pd.Series(rng.normal(0.001, 0.01, 750), index=pd.bdate_range('2020-01-01', periods=750))
    d1, c1, u1 = rb.mc_paths(r, 400, seed=5)
    d2, c2, u2 = rb.mc_paths(r, 400, seed=5)
    assert np.array_equal(d1, d2) and len(d1) == 400
    assert (d1 >= 0).all() and (d1 < 1).all() and (u1 >= 0).all()
    worse = rb.mc_paths(r * 3 - 0.001, 400, seed=5)[0]
    assert np.median(worse) > np.median(d1)                                # more volatile and lower drift: deeper drawdowns


def test_monte_carlo_with_only_gains_has_no_drawdown_and_gate_logic():
    r = pd.Series(0.001, index=pd.bdate_range('2020-01-01', periods=300))
    d, c, u = rb.mc_paths(r, 50, seed=1)
    assert d.max() == 0 and (c > 0).all() and u.max() == 0
    mc = rb.monte_carlo(r, np.array([1.0, -1.0, 1.0]), n_paths=50)
    assert mc['pass'] is True and mc['prob_drawdown_ge_25pct'] == 0
    bad = pd.Series(-0.01, index=r.index)
    assert rb.monte_carlo(bad, np.array([-1.0] * 5), n_paths=50)['pass'] is False


def test_losing_streaks_bounds():
    s = rb.losing_streaks(np.array([-1.0] * 6), n_paths=20)
    assert (s == 6).all()
    assert (rb.losing_streaks(np.array([1.0, 1.0, 1.0]), n_paths=20) == 0).all()


def test_stop_params_change_stop_distance_and_are_always_restored():
    orig = bt.stop_distance
    with rb.stop_params(atr_mult=3.0, min_pct=0.10):
        assert bt.stop_distance(100.0, 1.0) == 10.0
        assert bt.stop_distance(100.0, 5.0) == 15.0
    assert bt.stop_distance is orig and bt.stop_distance(100.0, 1.0) == max(risk.ATR_MULT * 1.0, 100.0 * risk.MIN_STOP_PCT)
    with pytest.raises(RuntimeError):
        with rb.stop_params(atr_mult=2.0):
            raise RuntimeError('boom')
    assert bt.stop_distance is orig


def test_stress_stop_exits_only_touches_stop_exits_and_lowers_r():
    t = pd.DataFrame({'reason': ['stop', 'ema50', 'gap_stop', 'time'], 'exit': [90.0, 120.0, 85.0, 110.0], 'plan_risk': [10.0] * 4,
                      'pnl_per_share': [-10.0, 20.0, -15.0, 10.0], 'gross_pnl_per_share': [-9.0, 21.0, -14.0, 11.0],
                      'slippage_per_share': [0.1] * 4})
    out = rb.stress_stop_exits(t, 100)                                    # 1% extra slippage
    assert out['pnl_per_share'].tolist() == pytest.approx([-10.9, 20.0, -15.85, 10.0])
    assert out['r'].tolist() == pytest.approx([-1.09, 2.0, -1.585, 1.0])
    assert t['pnl_per_share'].tolist() == [-10.0, 20.0, -15.0, 10.0]      # input untouched


def test_drop_fraction_is_seeded():
    t = pd.DataFrame({'x': range(1000)})
    a, b = rb.drop_fraction(t, 0.2, 7), rb.drop_fraction(t, 0.2, 7)
    assert a.equals(b) and 740 < len(a) < 860


def test_after_tax_cagr_is_below_pre_tax_and_zero_tax_on_losses():
    eq = pd.Series([100.0, 150.0], index=pd.to_datetime(['2020-01-01', '2021-01-01']))
    win = [{'exit_date': '2020-06-01', 'pnl': 50.0}]
    assert rb.after_tax_cagr(win, eq, 100.0, 0.2) == pytest.approx(((140 / 100) - 1) * 100, abs=1.0)
    loss = [{'exit_date': '2020-06-01', 'pnl': -10.0}]
    assert rb.after_tax_cagr(loss, eq, 100.0, 0.2) == pytest.approx(-10.0, abs=1.0)


def test_regime_report_flags_concentration_in_one_year():
    d = pd.to_datetime(['2018-03-01'] * 20 + ['2019-03-01'] * 20 + ['2020-03-01'] * 20)
    even = pd.DataFrame({'entry_date': d, 'r': [0.4, -0.2] * 30, 'regime': 'bull'})
    one_year = pd.DataFrame({'entry_date': d, 'r': [3.0] * 20 + [-0.1] * 20 + [-0.1] * 20, 'regime': 'bull'})
    ret = pd.Series(0.0005, index=pd.bdate_range('2018-01-01', '2020-12-31'))
    assert rb.regime_report(even, ret)['pass'] is True
    bad = rb.regime_report(one_year, ret)
    assert bad['pass'] is False and bad['max_single_year_share_of_total_r'] > 0.4


def test_survivorship_haircut_lowers_cagr_monotonically():
    frames, bench = fixture()
    cfg = ex.realistic_cfg()
    trades = bt.generate_trades(frames, cfg, bench)
    out = rb.survivorship_haircut(frames, trades, cfg, '2099-01-01', qs=(0.05, 0.2), draws=3)
    v = out['mean_cagr_pct_by_q']
    assert v['0.000'] >= v['0.050'] >= v['0.200'] and 'does not clear gate B2' in out['warning']


def test_battery_end_to_end_on_synthetic_data_and_holdout_is_spent_only_when_everything_passed(tmp_path):
    frames, bench = fixture()
    spec = small_spec()
    log = str(tmp_path / 'holdout.jsonl')
    rep = rb.run(frames, bench, spec=spec, holdout_log=log, draws=60, mc_paths_n=60, neighbours=[('min_score', 65), ('max_hold', 96)])
    assert set(rep['results']) >= {'R-NULL-A', 'R-NULL-B', 'R-CI', 'R-BENCH', 'R-MC', 'R-REGIME', 'R-SENS', 'R-EXEC', 'R-SURV', 'R-HO'}
    opened = hg.opened(log)
    if rep['results']['R-HO']['status'] == 'opened':
        assert ('R-HO', spec['_hash']) in opened and rep['robustness_passed'] in (True, False)
    else:
        assert not opened and rep['robustness_passed'] is False and rep['results']['R-HO']['failed']
    assert rep['failed'] == [k for k, v in rep['results'].items() if not v.get('pass')]
    md = rb.markdown(rep)
    assert 'Robustness passed' in md and 'not proof of a live edge' in md and 'Survivorship bias remains' in md


def test_a_failed_gate_never_opens_the_holdout(tmp_path):
    frames, bench = fixture(n=700, k=3)             # too little history for signals: tests cannot pass
    log = str(tmp_path / 'holdout.jsonl')
    rep = rb.run(frames, bench, spec=small_spec(), holdout_log=log, draws=20, mc_paths_n=20, skip_slow=True)
    assert rep['robustness_passed'] is False and rep['results']['R-HO']['status'] == 'not_opened' and not hg.opened(log)
