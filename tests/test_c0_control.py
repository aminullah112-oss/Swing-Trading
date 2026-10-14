"""C0 is the control. These tests pin its definition and its legacy results so it can never change silently."""
import json, os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import backtest as bt
import c0_baseline as c0
import provenance
import settings
import strategy
import universe
from test_backtest import synth

ROOT = os.path.join(os.path.dirname(__file__), '..')
PINNED_C0_HASH = '5e7924a41b0ee220'
PINNED_LEGACY_DIGEST = '21cd82a8c5241215'      # 10 synthetic symbols, seeds 0-9, 1500 bars, legacy flat costs
PINNED_LEGACY_TRADES = 122


def fixture():
    frames = {f'S{i}': synth(n=1500, seed=i, drift=0.0009) for i in range(10)}
    return frames, synth(n=1500, seed=999)['Close']


def test_c0_definition_is_pinned_and_matches_the_control_file():
    assert provenance.c0_hash() == PINNED_C0_HASH, 'C0 strategy identity changed: create a new strategy ID, do not edit C0'
    ctrl = json.load(open(os.path.join(ROOT, 'control', 'C0.json')))
    assert ctrl['c0_hash'] == provenance.c0_hash() and ctrl['spec'] == strategy.describe()
    assert (strategy.MIN_SCORE, strategy.TRIGGER, strategy.EXIT_MODE, strategy.MAX_HOLD) == (72, 'prior_high', 'ema50', 120)


def test_c0_legacy_results_are_bit_for_bit_reproducible():
    frames, bench = fixture()
    cfg = bt.Config(min_score=72, trigger='prior_high', exit_mode='ema50', max_hold=120)        # legacy flat costs
    _, trades, _ = bt.run(frames, cfg, bench)
    assert len(trades) == PINNED_LEGACY_TRADES and c0.trades_digest(trades) == PINNED_LEGACY_DIGEST
    _, trades2, _ = bt.run(frames, cfg, bench)
    assert c0.trades_digest(trades2) == PINNED_LEGACY_DIGEST                                     # deterministic


def test_new_execution_model_is_off_by_default_so_c0_is_unaffected():
    cfg = strategy.backtest_config()
    assert cfg.cost_buy_bps is None and cfg.participation_cap is None and cfg.adv_cap is None
    assert (cfg.cost_bps, cfg.slippage_bps) == (settings.LEGACY_COST_BPS_PER_SIDE, settings.LEGACY_SLIPPAGE_BPS_PER_SIDE)


def test_universe_versions_are_frozen_and_the_discrepancy_is_documented():
    assert universe.verify_manifest() == []
    legacy, cur = universe.load('U160_legacy'), universe.load('U159_v2')
    assert len(legacy['symbols']) == 160 and len(cur['symbols']) == 159
    assert universe.diff('U160_legacy', 'U159_v2') == {'removed': ['GUJARATGAS'], 'added': []}
    assert '156' in legacy['notes']                                # the unidentifiable 'agreed' count is recorded, not hidden


def test_changing_a_frozen_universe_is_detected(tmp_path, monkeypatch):
    import shutil
    d = tmp_path / 'universe'; shutil.copytree(os.path.join(ROOT, 'universe'), d)
    monkeypatch.setattr(universe, 'DIR', str(d))
    assert universe.verify_manifest() == []
    data = json.load(open(d / 'U159_v2.json')); data['symbols'].append('NEWSTOCK')
    json.dump(data, open(d / 'U159_v2.json', 'w'))
    assert any('changed after being frozen' in p for p in universe.verify_manifest())


def test_reproduce_and_compare_to_frozen_flags_drift():
    frames, bench = fixture()
    res = c0.reproduce(frames, bench)
    assert res['trades_digest'] and res['control']['c0_hash'] == PINNED_C0_HASH and res['provenance']['universe_version'] == universe.CURRENT
    frozen = json.load(open(os.path.join(ROOT, 'control', 'c0_frozen_baseline.json')))
    drifts = c0.compare_to_frozen(res, frozen)            # synthetic data is nowhere near the real baseline: drift must be reported
    assert drifts and any('design' in d for d in drifts)
    same = {'design': {'avg_r': 0.22, 'trades': 3310}, 'holdout': {'avg_r': 0.633},
            'portfolio_holdout': {'cagr_pct': 6.7}}
    assert c0.compare_to_frozen(same, frozen) == []
    assert 'Drift versus the frozen baseline' in c0.markdown(res, drifts)


def test_itemised_costs_liquidity_and_gross_net_decomposition():
    frames, bench = fixture()
    base = dict(min_score=72, trigger='prior_high', exit_mode='ema50', max_hold=120)
    legacy = bt.generate_trades(frames, bt.Config(**base), bench)
    item = bt.generate_trades(frames, bt.Config(**base, cost_buy_bps=settings.COST_BUY_BPS, cost_sell_bps=settings.COST_SELL_BPS), bench)
    assert len(legacy) == len(item)
    assert (item['r'] > legacy['r'] - 1e-9).mean() > 0.99          # itemised round trip (24.8 bps) is cheaper than the flat 30 bps
    gross = item['gross_pnl_per_share']; net = item['pnl_per_share']
    assert np.allclose(gross - item['cost_per_share'] - item['slippage_per_share'], net, atol=1e-6)    # exact decomposition
    # a tight liquidity cap limits fills and is counted
    tight = bt.Config(**base, participation_cap=1e-9)
    stats, _ = bt.portfolio(frames, legacy, tight)
    assert stats['accepted'] == 0 and stats['rejected_by_limits'] > 0
    loose = bt.Config(**base, participation_cap=0.05, adv_cap=0.02)
    stats2, _, taken = bt.portfolio(frames, legacy, loose, detail=True)
    assert stats2['accepted'] > 0 and all(t['shares'] >= 1 for t in taken) and 'avg_exposure_pct' in stats2 and 'time_in_cash_pct' in stats2
