import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import backtest as bt
import benchmarks as bm
import readiness as rd
from test_backtest import synth
from test_readiness_health import ctx, by_id, UNI_WINS, GRID, lg


def panel(n_stocks=45, n=900, seed=0, drifts=None):
    idx = pd.bdate_range('2020-01-01', periods=n)
    rng = np.random.default_rng(seed)
    cols = {}
    for i in range(n_stocks):
        mu = (drifts or {}).get(i, 0.0004)
        cols[f'S{i}'] = 100 * np.cumprod(1 + mu + 0.012 * rng.standard_normal(n))
    return pd.DataFrame(cols, index=idx)


def test_perf_matches_hand_calculation():
    idx = pd.bdate_range('2021-01-04', periods=253)
    r = pd.Series(0.001, index=idx)
    p = bm.perf(r)
    assert 27 < p['cagr_pct'] < 31 and p['max_drawdown_pct'] == 0 and p['calmar'] is None
    r2 = r.copy(); r2.iloc[100] = -0.2
    p2 = bm.perf(r2)
    assert p2['max_drawdown_pct'] < -19 and p2['calmar'] is not None
    assert bm.perf(pd.Series([0.01] * 5)) is None


def test_momentum_score_prefers_strong_low_vol_trend_and_avoids_lookahead():
    p = panel(drifts={0: 0.003})                                    # stock 0 trends strongly
    s = bm.momentum_scores(p)
    last = s.iloc[-1].dropna()
    assert last.idxmax() == 'S0'
    # scores at a date must not change when later prices change
    p2 = p.copy(); p2.iloc[-30:, 3] *= 5
    assert np.allclose(bm.momentum_scores(p2).iloc[-60].dropna().values, s.iloc[-60].dropna().values)


def test_rebalance_dates_are_last_trading_day_of_march_and_september():
    idx = pd.bdate_range('2021-01-01', '2022-12-31')
    d = bm.rebalance_dates(idx)
    assert [x.month for x in d] == [3, 9, 3, 9]
    assert all(x == idx[(idx.year == x.year) & (idx.month == x.month)].max() for x in d)


def test_momentum_portfolio_picks_top_n_costs_apply_and_no_lookahead():
    p = panel(drifts={0: 0.003, 1: 0.0025})
    free, hold = bm.momentum_portfolio(p, top_n=30, cost_bps=0)
    paid, _ = bm.momentum_portfolio(p, top_n=30, cost_bps=25)
    assert all(len(v) == 30 for v in hold.values()) and 'S0' in list(hold.values())[0]
    assert (free - paid).sum() > 0 and (free - paid).min() >= -1e-12
    first = list(hold)[0]
    p2 = p.copy(); p2.loc[p2.index > pd.Timestamp(first), :] *= 3.0           # perturb everything after the first rebalance
    _, hold2 = bm.momentum_portfolio(p2, top_n=30, cost_bps=0)
    assert hold2[first] == hold[first]


def test_h2_admits_by_momentum_rank_and_h3_scales_risk():
    idx = pd.bdate_range('2023-01-02', periods=30)
    fr = {s: pd.DataFrame({'Close': 100.0}, index=idx) for s in ('A', 'B')}
    cfg = bt.Config(capital=100000, risk_pct=0.005, max_open_risk=0.005, max_pos_pct=0.9)      # room for exactly one position
    base = {'entry_date': idx[1], 'exit_date': idx[10], 'entry': 100.0, 'plan_risk': 5.0, 'pnl_per_share': 5.0}
    # A has the higher old score, B the higher momentum rank; only one slot, and only B wins money
    tr2 = pd.DataFrame([dict(base, symbol='A', score=90, mom=0.1, pnl_per_share=-5.0), dict(base, symbol='B', score=70, mom=2.0, pnl_per_share=5.0)])
    _, e1 = bt.portfolio(fr, tr2, cfg)
    _, e2 = bt.portfolio(fr, tr2, cfg, order_col='mom')
    assert e1.iloc[-1] < cfg.capital < e2.iloc[-1]
    _, half = bt.portfolio(fr, tr2, bt.Config(capital=100000, risk_pct=0.005, max_open_risk=0.005, max_pos_pct=0.9), order_col='mom',
                           risk_scale=lambda d: 0.5)
    gain_full, gain_half = e2.iloc[-1] - cfg.capital, half.iloc[-1] - cfg.capital
    assert 0.4 < gain_half / gain_full < 0.6


def test_full_run_report_and_markdown_on_synthetic_data():
    frames = {f'S{i}': synth(n=1500, seed=i, drift=0.0007) for i in range(40)}
    bench = synth(n=1500, seed=999)['Close']
    rep = bm.run(frames, bench)
    assert set(rep['periods']) == {'design', 'holdout'}
    for k in ('Live strategy (baseline)', 'H1 momentum-30 replica', 'Equal-weight universe', 'Nifty 50'):
        assert k in rep['periods']['holdout']
    assert set(rep['hypotheses']) == {'baseline', 'H2', 'H3'} and isinstance(rep['verdict']['H2'], bool)
    md = bm.markdown(rep)
    assert 'Pre-registered hypotheses' in md and 'momentum-30 replica' in md and 'weak evidence' in md


def test_scorecard_u1_uses_same_source_benchmarks():
    def bmk(strategy_calmar, ew_calmar, mom_calmar):
        row = lambda c: {'cagr_pct': 5.0, 'max_drawdown_pct': -10.0, 'calmar': c, 'sharpe': 1.0}
        return {'periods': {'holdout': {'Live strategy (baseline)': row(strategy_calmar), 'Equal-weight universe': row(ew_calmar),
                                        'H1 momentum-30 replica': row(mom_calmar)}}}
    def u1(b):
        c = ctx(lg.empty(), uni=UNI_WINS); c['benchmarks'] = b
        return by_id(rd.evaluate(c))['U1']
    assert u1(bmk(1.0, 0.8, 0.9))['status'] == 'pass'
    g = u1(bmk(1.0, 0.8, 1.4))
    assert g['status'] == 'fail' and 'momentum-30 replica 1.40' in g['value']       # must beat the momentum replica too
    assert u1(bmk(0.5, 0.8, 0.4))['status'] == 'fail'
    assert by_id(rd.evaluate(ctx(lg.empty(), uni=UNI_WINS)))['U1']['status'] == 'pass'   # old inputs still work without benchmarks
