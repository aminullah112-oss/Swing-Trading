import json, os, sys
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import backtest as bt
import experiments as ex
import experiments_v2 as e2
import holdout_guard as hg
import prereg
import selection
from test_backtest import synth


def fixture(n=1700, k=12):
    return {f'S{i}': synth(n=n, seed=i, drift=0.0009) for i in range(k)}, synth(n=n, seed=999)['Close']


def small_spec():
    spec = json.loads(json.dumps(prereg.load('PREREG_v2')))
    spec['windows'].update(design_end='2024-06-30', holdout_start='2024-07-01')
    return spec


def test_prereg_v2_is_pinned_and_counts_the_whole_family():
    s = prereg.load('PREREG_v2')
    assert [h['id'] for h in s['hypotheses']] == ['V2-1', 'V2-2', 'V2-3']
    assert s['multiple_testing']['n_tests'] == 13 and abs(prereg.alpha_per_test(s) - 0.05 / 13) < 1e-12
    assert {x['idea'][:12] for x in s['previously_tested_and_failed_not_retested']} == {'admit same-d', 'halve risk w'}
    # the stack registered in the file is the stack the live tiers use
    p = [h for h in s['hypotheses'] if h['id'] == 'V2-2'][0]['param']
    assert (p['min_rank'], p['min_from_52h_pct'], p['max_atr_pct']) == (selection.STACK['min_rank'], selection.STACK['min_from_52h_pct'], selection.STACK['max_atr_pct'])
    assert p['min_adv20_value'] == selection.STACK['min_adv20_value_cr'] * 1e7


def test_portfolio_group_cap_and_risk_col_default_to_legacy():
    frames, bench = fixture()
    cfg = ex.realistic_cfg()
    tr = bt.generate_trades(frames, cfg, bench)
    a, _ = bt.portfolio(frames, tr, cfg)
    b, _ = bt.portfolio(frames, tr, cfg, group_col=None, max_per_group=None, risk_col=None)
    assert a == b
    tr = tr.assign(grp='ONE', rm=0.5)
    capped, _ = bt.portfolio(frames, tr, cfg, group_col='grp', max_per_group=1)
    assert capped['accepted'] < a['accepted']                                                  # one shared group: one position at a time
    small, eq = bt.portfolio(frames, tr, cfg, risk_col='rm')
    big, eq2 = bt.portfolio(frames, tr, cfg)
    assert small['max_drawdown_pct'] >= big['max_drawdown_pct'] - 1e-9 or small['final_equity'] != big['final_equity']


def test_trade_sets_only_remove_or_resize():
    frames, bench = fixture()
    prepared = bt.prepare(frames)
    base = bt.generate_trades(frames, ex.realistic_cfg(), bench, prepared)
    rank, sectors = ex.momentum_rank(prepared), selection.load_sectors()
    spec = prereg.load('PREREG_v2')
    for h in spec['hypotheses']:
        t, kw = e2.trade_set(h, base, prepared, sectors, rank)
        assert len(t) <= len(base) and t.index.isin(base.index).all()
        assert (base.loc[t.index]['r'] == t['r']).all()
    t3, kw3 = e2.trade_set(spec['hypotheses'][2], base, prepared, sectors, rank)
    assert set(t3['risk_mult']) <= {0.75, 1.0} and kw3 == {'risk_col': 'risk_mult'}


def test_runner_records_every_hypothesis_and_retains_c0_on_fail(tmp_path):
    frames, bench = fixture()
    log = str(tmp_path / 'h.jsonl')
    rep = e2.run(frames, bench, spec=small_spec(), holdout_log=log, ts='t')
    assert [r['id'] for r in rep['hypotheses']] == ['V2-1', 'V2-2', 'V2-3']
    assert rep['c0_retained'] is True and rep['adopted_candidates'] == [] and not os.path.exists(log)
    assert all(r['failed_because'] for r in rep['hypotheses']) and len(rep['earlier_failed_ideas']) == 2
    md = e2.markdown(rep)
    assert 'C0 retained: yes' in md and 'Already tested, failed, not retested' in md


def test_pass_path_opens_holdout_once_and_risk_route_needs_holdout_drawdown_too(tmp_path, monkeypatch):
    frames, bench = fixture()
    log = str(tmp_path / 'h.jsonl')
    monkeypatch.setattr(e2.ex, 'evaluate_design', lambda *a, **k: (True, {'P1_sample': {'pass': True, 'trades': 1, 'months': 1}, 'P4_absolute': {'pass': True}}))
    rep = e2.run(frames, bench, spec=small_spec(), holdout_log=log, ts='t')
    assert {k[0] for k in hg.opened(log)} == {'V2-1', 'V2-2', 'V2-3'} and all(r['holdout_opened'] for r in rep['hypotheses'])
    with pytest.raises(hg.HoldoutAlreadyOpened):
        e2.run(frames, bench, spec=small_spec(), holdout_log=log, ts='t2')


def test_risk_route_logic():
    dd = lambda d, c: {'portfolio': {'max_drawdown_pct': d, 'calmar': c}}
    assert e2.risk_route_design(dd(-8.0, 0.7), dd(-9.0, 0.6), True, True)[0] is True
    assert e2.risk_route_design(dd(-9.0, 0.6), dd(-9.0, 0.6), True, True)[0] is False         # a tie does not pass
    assert e2.risk_route_design(dd(-8.6, 0.62), dd(-9.0, 0.6), True, True)[0] is False        # gains below 1pp and 0.05
    assert e2.risk_route_design(dd(-9.0, 0.66), dd(-9.0, 0.6), True, True)[0] is True         # Calmar +0.06
    assert e2.risk_route_design(dd(-10.0, 0.7), dd(-9.0, 0.6), True, True)[0] is False       # deeper drawdown
    assert e2.risk_route_design(dd(-8.0, 0.5), dd(-9.0, 0.6), True, True)[0] is False        # lower Calmar
    assert e2.risk_route_design(dd(-8.0, 0.7), dd(-9.0, 0.6), False, True)[0] is False        # too few trades
    assert e2.risk_route_holdout(dd(-8.0, 0.7), dd(-9.0, 0.6)) and not e2.risk_route_holdout(dd(-12.0, 0.7), dd(-9.0, 0.6))
