import json, os, shutil, sys
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import backtest as bt
import events as evlog
import experiments as ex
import holdout_guard as hg
import metrics as mx
import prereg
from test_backtest import synth

ROOT = os.path.join(os.path.dirname(__file__), '..')


def fixture(n=1700, k=12):
    frames = {f'S{i}': synth(n=n, seed=i, drift=0.0009) for i in range(k)}
    return frames, synth(n=n, seed=999)['Close']


def small_spec():
    spec = prereg.load()
    spec = json.loads(json.dumps(spec))
    spec['windows'].update(design_end='2024-06-30', holdout_start='2024-07-01')
    return spec


# ---------------------------------------------------------------- pre-registration is pinned
def test_prereg_is_pinned_and_complete():
    spec = prereg.load()
    assert spec['control'] == 'C0' and spec['registered_before_any_result'] is True
    assert [h['id'] for h in spec['hypotheses']] == [f'H{i}' for i in range(1, 9)]
    assert spec['multiple_testing']['n_tests'] == len(spec['hypotheses']) and abs(prereg.alpha_per_test(spec) - 0.05 / 8) < 1e-12
    assert (ex.MIN_TRADES, ex.MIN_MONTHS, ex.N_BLOCKS, ex.MIN_BLOCKS_WON) == (100, 40, 8, 5)       # code matches the registered criteria
    assert '100 trades' in spec['walk_forward_pass_criteria']['P1_sample'] and '40 distinct' in spec['walk_forward_pass_criteria']['P1_sample']
    assert 'at least 5 of the 8' in spec['walk_forward_pass_criteria']['P3_consistency']


def test_editing_the_registration_after_the_fact_is_refused(tmp_path):
    d = tmp_path / 'experiments'; shutil.copytree(os.path.join(ROOT, 'experiments'), d)
    assert prereg.load(directory=str(d))['_hash']
    spec = json.load(open(d / 'PREREG_v1.json')); spec['hypotheses'][0]['param']['min_rank'] = 0.5
    json.dump(spec, open(d / 'PREREG_v1.json', 'w'))
    with pytest.raises(prereg.PreregMismatch):
        prereg.load(directory=str(d))
    os.remove(d / 'PREREG_v1.sha256')
    with pytest.raises(prereg.PreregMismatch):
        prereg.load(directory=str(d))


# ---------------------------------------------------------------- hold-out is once-only
def test_holdout_can_be_opened_once_per_hypothesis_and_prereg(tmp_path):
    p = str(tmp_path / 'h.jsonl')
    hg.open_once('H1', 'abc', '2026-10-13', p)
    with pytest.raises(hg.HoldoutAlreadyOpened):
        hg.open_once('H1', 'abc', '2026-10-13', p)
    hg.open_once('H2', 'abc', '2026-10-13', p)              # a different hypothesis has its own hold-out
    hg.open_once('H1', 'def', '2026-10-13', p)              # a new registration is a new family
    assert len(hg.opened(p)) == 3 and evlog.verify(p)[0]


def test_tampered_holdout_log_blocks_opening(tmp_path):
    p = str(tmp_path / 'h.jsonl')
    hg.open_once('H1', 'abc', 'x', p)
    lines = open(p).read().splitlines()
    open(p, 'w').write(lines[0].replace('H1', 'H9') + '\n')
    with pytest.raises(hg.HoldoutAlreadyOpened):
        hg.open_once('H2', 'abc', 'x', p)


# ---------------------------------------------------------------- the runner
def test_runner_fail_path_records_every_variant_and_retains_c0(tmp_path):
    frames, bench = fixture()
    log = str(tmp_path / 'h.jsonl')
    rep = ex.run(frames, bench, spec=small_spec(), holdout_log=log, ts='t')
    assert [r['id'] for r in rep['hypotheses']] == [f'H{i}' for i in range(1, 9)]          # none dropped
    for r in rep['hypotheses']:
        assert set(r['design_criteria']) == {'P1_sample', 'P2_net_edge_vs_C0', 'P3_consistency', 'P4_absolute'}
        assert r['design_passed'] is False and r['holdout_opened'] is False and r['failed_because']       # synthetic data: too few months/blocks
    assert rep['c0_retained'] is True and rep['adopted_candidates'] == []
    assert not os.path.exists(log) or hg.opened(log) == {}                                    # hold-out never opened for failed variants
    assert rep['provenance']['prereg_hash'] == prereg.load()['_hash'] and rep['universe']['survivorship_bias'] is True
    md = ex.markdown(rep)
    assert 'C0 retained: yes' in md and all(f'| H{i} |' in md for i in range(1, 9))


def test_runner_pass_path_opens_holdout_once_then_refuses(tmp_path, monkeypatch):
    frames, bench = fixture()
    log = str(tmp_path / 'h.jsonl')
    monkeypatch.setattr(ex, 'evaluate_design', lambda *a, **k: (True, {'P1_sample': {'pass': True}}))
    rep = ex.run(frames, bench, spec=small_spec(), holdout_log=log, ts='t')
    opened = hg.opened(log)
    assert {k[0] for k in opened} == {f'H{i}' for i in range(1, 9)}
    assert all(r['holdout_opened'] for r in rep['hypotheses'])
    types = [e['type'] for e in evlog.read(log)]
    assert types.count('holdout_opened') == 8 and types.count('holdout_result') == 8
    assert types[0] == 'holdout_opened'                                                      # opened before the result is recorded
    with pytest.raises(hg.HoldoutAlreadyOpened):
        ex.run(frames, bench, spec=small_spec(), holdout_log=log, ts='t2')


def test_filters_only_remove_trades_and_never_change_the_remaining_ones():
    frames, bench = fixture()
    prepared = bt.prepare(frames)
    base = bt.generate_trades(frames, ex.realistic_cfg(), bench, prepared)
    rank = ex.momentum_rank(prepared)
    spec = prereg.load()
    for h in spec['hypotheses'][:6]:
        sub = ex.apply_filter(h, base, rank)
        assert len(sub) <= len(base)
        assert sub.index.isin(base.index).all() and (base.loc[sub.index]['r'] == sub['r']).all()


def test_h7_changes_sizing_only_and_h8_changes_exit_only():
    spec = prereg.load()
    h7 = [h for h in spec['hypotheses'] if h['id'] == 'H7'][0]
    assert h7['param'] == {'risk_pct': 0.0025} and ex.realistic_cfg(**h7['param']).max_open_risk == 0.015


def test_realistic_costs_exceed_legacy_costs():
    frames, bench = fixture()
    prepared = bt.prepare(frames)
    legacy = bt.generate_trades(frames, bt.Config(min_score=72, trigger='prior_high', exit_mode='ema50', max_hold=120), bench, prepared)
    real = bt.generate_trades(frames, ex.realistic_cfg(), bench, prepared)
    assert len(real) > 0
    assert real['cost_per_share'].sum() > 0 and (real['gross_pnl_per_share'] - real['pnl_per_share']).sum() > 0


# ---------------------------------------------------------------- metrics
def test_metrics_basic_properties():
    idx = pd.bdate_range('2020-01-01', periods=500)
    r = pd.Series(np.random.default_rng(0).normal(0.0006, 0.01, 500), index=idx)
    m = mx.perf(r)
    assert m['sortino'] > m['sharpe'] > 0 and m['max_drawdown_pct'] < 0 and m['calmar'] > 0
    t = mx.trade_stats([2, -1, -1, 3, -1])
    assert t['trades'] == 5 and t['profit_factor'] == round(5 / 3, 3) and t['expectancy_r'] == 0.4 and t['win_rate'] == 0.4


def test_benchmark_matching_scales_exposure_and_volatility():
    idx = pd.bdate_range('2020-01-01', periods=500)
    b = pd.Series(np.random.default_rng(1).normal(0.0005, 0.012, 500), index=idx)
    half = mx.exposure_matched(b, 50.0)
    assert abs(half.mean() - 0.5 * b.mean()) < 1e-12 and abs(half.std() - 0.5 * b.std()) < 1e-12
    v = mx.vol_matched(b, 10.0)
    assert abs(v.std() * np.sqrt(252) * 100 - 10.0) < 1e-9


def test_taken_stats_report_gross_net_and_cost_drag():
    idx = pd.bdate_range('2020-01-01', periods=300)
    eq = pd.Series(np.linspace(565000, 600000, 300), index=idx)
    taken = [{'shares': 100, 'entry': 100.0, 'gross': 1000.0, 'pnl': 800.0, 'cost': 120.0, 'slippage': 80.0}]
    s = mx.taken_stats(taken, eq)
    assert s['gross_pnl'] == 1000 and s['net_pnl'] == 800 and s['cost_drag_pct_of_gross'] == 20.0 and s['turnover_x_per_year'] > 0
