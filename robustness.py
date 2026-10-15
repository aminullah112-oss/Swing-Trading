#!/usr/bin/env python3
"""PREREG_v3 robustness battery for control C0. It tests C0; it never changes it and never feeds a readiness weight.

  R-NULL-A/B  C0 versus random entries with the same exits (date-matched), 2000 draws
  R-CI        month-clustered CI of C0's expectancy
  R-BENCH     C0 versus the exposure-matched Nifty
  R-MC        Monte Carlo (stationary block bootstrap) drawdown distribution
  R-REGIME    year / regime concentration
  R-SENS      one-at-a-time parameter neighbours
  R-EXEC      execution stress (slippage, costs, stop slippage, liquidity, missed fills, tax shown)
  R-SURV      synthetic survivorship haircut (a sensitivity, NOT evidence about survivorship)
  R-HO        hold-out confirmation, opened once and only when everything else has passed

Design-window numbers only, except R-HO. Thresholds live in experiments/PREREG_v3.json (hash-pinned). Failures are reported,
never repaired. Known limits are printed in the report."""
import argparse
import contextlib
import dataclasses
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import backtest as bt
import events as evlog
import experiments as ex
import holdout_guard as hg
import metrics as mx
import prereg
import provenance
import research as rs
import risk

SEED = 20261015
N_DRAWS = 2000          # null-model draws (PREREG_v3)
MC_PATHS = 5000         # Monte Carlo paths (PREREG_v3)
MC_BLOCK = 63           # mean block length, trading days (trades are held 40-120 days, so serial dependence lives at that scale)
NIFTY_DIV_YIELD = 0.013 # the Nifty price index excludes dividends that the adjusted stock series include; added back at this assumed annual yield
STOP_REASONS = ('stop', 'trail', 'gap_stop', 'gap_trail')


# ------------------------------------------------------------------ R-NULL: random entries with the same exits
def candidate_table(prepared, cfg, design_end):
    """Every bar that could have been an entry (the buy-stop triggers), simulated with C0's exact rules.
    Columns: symbol, signal_date, r, is_signal (C0 would signal), stage_pass (passes the stage-2/filter rules)."""
    end = pd.Timestamp(design_end)
    sy, dt, rr, sg, st = [], [], [], [], []
    for sym, p in prepared.items():
        sig, a, dates = p['sig'], p['a'], p['dates']
        passed, score, atr = sig['passed'].values.astype(bool), sig['score'].values, a['atr']
        for i in range(bt.WARMUP, len(dates) - 1):
            if dates[i] > end:
                break
            if not np.isfinite(atr[i]) or atr[i] <= 0:
                continue
            t = bt.simulate_trade(a, i, cfg)
            if t is None:
                continue
            sy.append(sym); dt.append(dates[i]); rr.append(t['r'])
            sg.append(bool(passed[i] and score[i] >= cfg.min_score)); st.append(bool(passed[i]))
    return pd.DataFrame({'symbol': sy, 'signal_date': dt, 'r': rr, 'is_signal': sg, 'stage_pass': st})


def null_test(c0, cand, pool, k=N_DRAWS, seed=SEED):
    """Date-matched random-entry null. For every signal date, draw as many entries as C0 took, from `pool` (a boolean mask over
    `cand` that already excludes C0's own signals). Statistic: mean net R per trade."""
    pc = cand[pool]
    by_date = {d: g['r'].values for d, g in pc.groupby('signal_date')}
    counts = c0.groupby('signal_date').size()
    plan = [(by_date[d], int(n)) for d, n in counts.items() if d in by_date]
    matched = int(sum(n for d, n in counts.items() if d in by_date))
    if not plan or matched == 0:
        return {'status': 'unverifiable', 'reason': 'no overlapping candidate dates', 'pool_size': int(len(pc))}
    c0_mean = float(c0[c0['signal_date'].isin(by_date)]['r'].mean())
    rng = np.random.default_rng(seed)
    sums = np.zeros(k)
    drawn = 0
    for arr, n in plan:
        if n >= len(arr):
            sums += arr.sum(); drawn += len(arr)
        elif n == 1:
            sums += arr[rng.integers(0, len(arr), size=k)]; drawn += 1
        else:
            idx = np.argpartition(rng.random((k, len(arr))), n - 1, axis=1)[:, :n]
            sums += arr[idx].sum(axis=1); drawn += n
    means = sums / drawn
    p = float((1 + (means >= c0_mean).sum()) / (1 + k))
    return {'status': 'ok', 'c0_mean_r': round(c0_mean, 4), 'null_mean_r': round(float(means.mean()), 4),
            'null_p05': round(float(np.percentile(means, 5)), 4), 'null_p95': round(float(np.percentile(means, 95)), 4),
            'p_value': round(p, 5), 'draws': int(k), 'matched_c0_trades': matched, 'c0_trades_without_candidates': int(len(c0) - matched),
            'pool_size': int(len(pc)), 'note': 'Null ignores the one-position-per-symbol rule; C0 obeys it.'}


# ------------------------------------------------------------------ R-MC: Monte Carlo drawdown
def mc_paths(ret, n_paths=MC_PATHS, mean_block=MC_BLOCK, seed=SEED, batch=1000, length=None):
    """Stationary block bootstrap of daily returns. Yields (max_drawdown_depth, cagr, longest_underwater_days) per path."""
    r = np.asarray(pd.Series(ret).dropna(), dtype=float)
    T0 = len(r)
    T = int(length) if length else T0           # path length; may be shorter than the source (e.g. the length of the hold-out)
    rng = np.random.default_rng(seed)
    depth, cagr, under = [], [], []
    remaining = int(n_paths)
    while remaining > 0:
        m = min(batch, remaining)
        remaining -= m
        idx = np.empty((m, T), dtype=np.int64)
        idx[:, 0] = rng.integers(0, T0, m)
        restart = rng.random((m, T)) < 1.0 / mean_block
        start = rng.integers(0, T0, (m, T))
        for t in range(1, T):
            idx[:, t] = np.where(restart[:, t], start[:, t], (idx[:, t - 1] + 1) % T0)
        eq = np.cumprod(1.0 + r[idx], axis=1)
        peak = np.maximum.accumulate(eq, axis=1)
        dd = eq / peak - 1.0
        depth.append(-dd.min(axis=1))
        cagr.append(eq[:, -1] ** (252.0 / T) - 1.0)
        below = dd < 0
        cur = np.zeros(m); best = np.zeros(m)
        for t in range(T):
            cur = (cur + 1) * below[:, t]
            best = np.maximum(best, cur)
        under.append(best)
    return np.concatenate(depth), np.concatenate(cagr), np.concatenate(under)


def losing_streaks(r, n_paths=MC_PATHS, seed=SEED):
    """Longest run of non-winning trades when the trade order is shuffled."""
    r = np.asarray(r, dtype=float)
    rng = np.random.default_rng(seed)
    loss = np.stack([rng.permutation(r) <= 0 for _ in range(n_paths)])
    cur = np.zeros(n_paths); best = np.zeros(n_paths)
    for t in range(loss.shape[1]):
        cur = (cur + 1) * loss[:, t]
        best = np.maximum(best, cur)
    return best


def monte_carlo(ret, trade_r, n_paths=MC_PATHS, spec_gate=None, holdout_days=None):
    depth, cagr, under = mc_paths(ret, n_paths)
    streak = losing_streaks(trade_r, min(n_paths, 2000)) if len(trade_r) else np.array([0.0])
    g = spec_gate or {'p95_depth_max_pct': 35.0, 'prob_depth_25_max': 0.25}
    out = {'paths': int(len(depth)), 'mean_block_days': MC_BLOCK,
           'max_drawdown_depth_pct': {q: round(float(np.percentile(depth, q)) * 100, 1) for q in (5, 50, 95, 99)},
           'prob_drawdown_ge_20pct': round(float((depth >= 0.20).mean()), 3), 'prob_drawdown_ge_25pct': round(float((depth >= 0.25).mean()), 3),
           'prob_drawdown_ge_30pct': round(float((depth >= 0.30).mean()), 3), 'prob_drawdown_ge_50pct': round(float((depth >= 0.50).mean()), 3),
           'cagr_pct': {q: round(float(np.percentile(cagr, q)) * 100, 1) for q in (5, 50, 95)},
           'prob_negative_cagr': round(float((cagr < 0).mean()), 3),
           'longest_underwater_days': {q: int(np.percentile(under, q)) for q in (50, 95)},
           'longest_losing_streak_trades': {q: int(np.percentile(streak, q)) for q in (50, 95)}}
    if holdout_days:
        hd = mc_paths(ret, max(n_paths // 2, 50), length=holdout_days)[0]
        out['holdout_length_p95_depth_pct'] = round(float(np.percentile(hd, 95)) * 100, 1)
        out['holdout_days'] = int(holdout_days)
    p95 = out['max_drawdown_depth_pct'][95]
    out['pass'] = bool(p95 <= g['p95_depth_max_pct'] and out['prob_drawdown_ge_25pct'] <= g['prob_depth_25_max'])
    out['p95_depth_pct'] = p95
    return out


# ------------------------------------------------------------------ R-REGIME
STRESS_WINDOWS = {'2018 mid/small-cap crash': ('2018-01-15', '2018-10-31'), '2020 COVID crash': ('2020-02-15', '2020-04-30'),
                  '2022 rate-hike chop': ('2022-01-01', '2022-12-31')}


def regime_report(trades, ret):
    t = trades
    years = {}
    for y, g in t.groupby(t['entry_date'].dt.year):
        years[int(y)] = {'trades': int(len(g)), 'avg_r': round(float(g['r'].mean()), 3), 'win_rate': round(float((g['r'] > 0).mean()), 3), 'sum_r': round(float(g['r'].sum()), 2)}
    qual = {y: v for y, v in years.items() if v['trades'] >= 15}
    total = float(t['r'].sum())
    share = {y: (v['sum_r'] / total if total > 0 else None) for y, v in qual.items()}
    pos_share = sum(v['avg_r'] > 0 for v in qual.values()) / len(qual) if qual else 0.0
    max_share = max((s for s in share.values() if s is not None), default=None)
    by_regime = {k: {'trades': int(len(g)), 'avg_r': round(float(g['r'].mean()), 3)} for k, g in t.groupby('regime')}
    stress = {}
    for name, (lo, hi) in STRESS_WINDOWS.items():
        g = t[(t['entry_date'] >= lo) & (t['entry_date'] <= hi)]
        w = ret[(ret.index >= lo) & (ret.index <= hi)]
        pm = mx.perf(w) if len(w) >= 20 else None
        stress[name] = {'trades': int(len(g)), 'avg_r': round(float(g['r'].mean()), 3) if len(g) else None,
                        'window_return_pct': round(float((1 + w).prod() - 1) * 100, 1) if len(w) else None,
                        'window_max_drawdown_pct': pm['max_drawdown_pct'] if pm else None}
    ok = bool(qual and total > 0 and pos_share >= 0.60 and max_share is not None and max_share <= 0.40)
    return {'by_year': years, 'years_considered': len(qual), 'share_of_years_positive': round(pos_share, 3),
            'max_single_year_share_of_total_r': round(max_share, 3) if max_share is not None else None,
            'by_nifty_regime': by_regime, 'stress_windows': stress, 'pass': ok}


# ------------------------------------------------------------------ R-SENS
@contextlib.contextmanager
def stop_params(atr_mult=None, min_pct=None):
    """Temporarily change the stop-distance rule inside the backtester. Always restored."""
    orig = bt.stop_distance
    bt.stop_distance = lambda price, atr: orig(price, atr, atr_mult=atr_mult or risk.ATR_MULT, min_pct=min_pct or risk.MIN_STOP_PCT)
    try:
        yield
    finally:
        bt.stop_distance = orig


def with_exit_span(prepared, frames, span):
    out = {}
    for s, p in prepared.items():
        arr = frames[s]['Close'].astype(float).ewm(span=span, adjust=False).mean().values
        out[s] = {**p, 'a': {**p['a'], 'ema50': arr}}
    return out


NEIGHBOURS = [('min_score', 58), ('min_score', 65), ('min_score', 79), ('min_score', 86), ('max_hold', 96), ('max_hold', 144),
              ('exit_ema_span', 40), ('exit_ema_span', 60), ('atr_mult', 1.2), ('atr_mult', 1.8), ('stop_floor_pct', 0.024), ('stop_floor_pct', 0.036)]


def _metrics(frames, trades, cfg, design_end):
    t = ex.window(trades, None, design_end)
    stats, ret, m = ex.run_port(frames, t, cfg)
    p = m.get('portfolio') or {}
    return {'trades': int(len(t)), 'avg_r': round(float(t['r'].mean()), 3) if len(t) else None, 'cagr_pct': p.get('cagr_pct'),
            'max_drawdown_pct': p.get('max_drawdown_pct'), 'calmar': p.get('calmar')}, ret, stats


def sensitivity(frames, bench, prepared, design_end, c0_calmar, neighbours=NEIGHBOURS):
    rows = []
    for name, val in neighbours:
        cfg = ex.realistic_cfg()
        prep, ctx = prepared, contextlib.nullcontext()
        if name == 'min_score':
            cfg = ex.realistic_cfg(min_score=val)
        elif name == 'max_hold':
            cfg = ex.realistic_cfg(max_hold=val)
        elif name == 'exit_ema_span':
            prep = with_exit_span(prepared, frames, val)
        elif name == 'atr_mult':
            ctx = stop_params(atr_mult=val)
        elif name == 'stop_floor_pct':
            ctx = stop_params(min_pct=val)
        with ctx:
            trades = bt.generate_trades(frames, cfg, bench, prep)
            m, _, _ = _metrics(frames, trades, cfg, design_end)
        rows.append({'param': name, 'value': val, **m})
    keep = [r for r in rows if r['calmar'] is not None and c0_calmar and r['calmar'] >= 0.7 * c0_calmar]
    all_pos = all((r['cagr_pct'] or 0) > 0 for r in rows)
    share = len(keep) / len(rows) if rows else 0.0
    return {'neighbours': rows, 'share_keeping_70pct_of_c0_calmar': round(share, 3), 'all_cagr_positive': bool(all_pos),
            'pass': bool(rows and c0_calmar and share >= 0.75 and all_pos)}


# ------------------------------------------------------------------ R-EXEC and R-SURV
def stress_stop_exits(trades, bps):
    """Extra slippage on exits that happen because a stop was hit. Returns a modified copy."""
    t = trades.copy()
    m = t['reason'].isin(STOP_REASONS)
    extra = t['exit'] * bps / 1e4 * m
    t['pnl_per_share'] = t['pnl_per_share'] - extra
    t['gross_pnl_per_share'] = t['gross_pnl_per_share'] - extra
    t['slippage_per_share'] = t['slippage_per_share'] + extra
    t['exit'] = t['exit'] - extra
    t['r'] = t['pnl_per_share'] / t['plan_risk']
    return t


def drop_fraction(trades, frac, seed):
    rng = np.random.default_rng(seed)
    return trades[rng.random(len(trades)) >= frac]


def after_tax_cagr(taken, eq, capital, rate=0.20):
    if not taken or len(eq) == 0:
        return None
    df = pd.DataFrame(taken)
    df['year'] = pd.to_datetime(df['exit_date']).dt.year
    yearly = df.groupby('year')['pnl'].sum()
    tax = float(sum(rate * max(0.0, v) for v in yearly))
    final = capital + float(df['pnl'].sum()) - tax
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1e-9)
    return round(((final / capital) ** (1 / years) - 1) * 100, 1) if final > 0 else -100.0


def execution_stress(frames, bench, prepared, design_end, seed=SEED):
    import settings
    base_kw = dict(slippage_bps=settings.SLIPPAGE_BPS_PER_SIDE, cost_buy_bps=settings.COST_BUY_BPS, cost_sell_bps=settings.COST_SELL_BPS,
                   participation_cap=settings.LIQUIDITY_PARTICIPATION_CAP, adv_cap=settings.ADV_ORDER_CAP)
    base_cfg = ex.realistic_cfg()
    base_tr = bt.generate_trades(frames, base_cfg, bench, prepared)
    scen = {}

    def run_case(name, cfg, trades):
        t = ex.window(trades, None, design_end)
        stats, eq, taken = bt.portfolio(frames, t, cfg, detail=True)
        ret = eq.pct_change().dropna() if len(eq) else pd.Series(dtype=float)
        p = mx.perf(ret) or {}
        scen[name] = {'trades_accepted': stats.get('accepted'), 'cagr_pct': p.get('cagr_pct'), 'max_drawdown_pct': p.get('max_drawdown_pct'),
                      'calmar': p.get('calmar'), 'after_tax_cagr_pct': after_tax_cagr(taken, eq, cfg.capital)}

    run_case('base (realistic)', base_cfg, base_tr)
    for mult in (2, 3):
        cfg = ex.realistic_cfg(slippage_bps=base_kw['slippage_bps'] * mult)
        run_case(f'slippage x{mult}', cfg, bt.generate_trades(frames, cfg, bench, prepared))
    cfg_c2 = ex.realistic_cfg(cost_buy_bps=base_kw['cost_buy_bps'] * 2, cost_sell_bps=base_kw['cost_sell_bps'] * 2)
    run_case('statutory costs x2', cfg_c2, bt.generate_trades(frames, cfg_c2, bench, prepared))
    run_case('+25 bps on stop exits', base_cfg, stress_stop_exits(base_tr, 25))
    cfg_liq = ex.realistic_cfg(participation_cap=base_kw['participation_cap'] / 2, adv_cap=base_kw['adv_cap'] / 2)
    run_case('liquidity caps halved', cfg_liq, base_tr)
    missed = []
    for d in range(5):
        run_case(f'_missed{d}', base_cfg, drop_fraction(base_tr, 0.20, seed + d))
        missed.append(scen.pop(f'_missed{d}'))
    scen['20% of entries missed (worst of 5)'] = min(missed, key=lambda x: x['cagr_pct'] if x['cagr_pct'] is not None else -1e9)
    gap = base_tr['entry'] / (base_tr['stop'] + base_tr['plan_risk']) - 1.0          # fill versus the planned buy-stop
    run_case('miss the 20% largest gap-up fills', base_cfg, base_tr[gap < gap.quantile(0.80)])
    cfg_h = ex.realistic_cfg(slippage_bps=base_kw['slippage_bps'] * 2, cost_buy_bps=base_kw['cost_buy_bps'] * 2, cost_sell_bps=base_kw['cost_sell_bps'] * 2,
                             participation_cap=base_kw['participation_cap'] / 2, adv_cap=base_kw['adv_cap'] / 2)
    run_case('combined harsh case', cfg_h, stress_stop_exits(bt.generate_trades(frames, cfg_h, bench, prepared), 25))
    base_c, harsh_c = scen['base (realistic)']['cagr_pct'], scen['combined harsh case']['cagr_pct']
    keeps_half = bool(base_c and harsh_c is not None and harsh_c >= 0.5 * base_c)
    ok = all((v['cagr_pct'] or -1) > 0 for v in scen.values()) and keeps_half
    return {'scenarios': scen, 'harsh_keeps_half_of_base_cagr': keeps_half, 'pass': bool(ok), 'tax_note': 'After-tax CAGR applies 20% to positive realised net gains per calendar year; no loss carry-forward, LTCG rates or surcharge. Indicative only.'}, base_tr


def survivorship_haircut(frames, trades, cfg, design_end, qs=(0.005, 0.01, 0.02, 0.03), loss=0.40, draws=8, seed=SEED):
    t0 = ex.window(trades, None, design_end).reset_index(drop=True)
    rng = np.random.default_rng(seed)
    cat = -loss * t0['entry'].values - t0['cost_per_share'].values
    rows = {}
    for q in (0.0,) + tuple(qs):
        cagrs = []
        for _ in range(1 if q == 0 else draws):
            t = t0.copy()
            hit = rng.random(len(t)) < q
            t['pnl_per_share'] = np.where(hit, np.minimum(t['pnl_per_share'].values, cat), t['pnl_per_share'].values)
            t['r'] = t['pnl_per_share'] / t['plan_risk']
            stats, _ = bt.portfolio(frames, t, cfg)
            cagrs.append(stats.get('cagr_pct'))
        rows[q] = round(float(np.mean([c for c in cagrs if c is not None])), 1) if cagrs else None
    breakeven = None
    keys = sorted(rows)
    for a, b in zip(keys, keys[1:]):
        if rows[a] is not None and rows[b] is not None and rows[a] > 0 >= rows[b]:
            breakeven = round(a + (b - a) * rows[a] / (rows[a] - rows[b]), 4)
            break
    q1 = rows.get(0.01)
    # Inclusion bias (today's constituents were partly chosen because they rose) works like a uniform drag on every trade's R.
    r_rows = {}
    for h in (0.0, 0.05, 0.10, 0.20, 0.30):
        t = t0.copy()
        t['pnl_per_share'] = t['pnl_per_share'] - h * t['plan_risk']
        t['r'] = t['pnl_per_share'] / t['plan_risk']
        r_rows[h] = bt.portfolio(frames, t, cfg)[0].get('cagr_pct')
    be_r = None
    ks = sorted(r_rows)
    for a_, b_ in zip(ks, ks[1:]):
        if r_rows[a_] is not None and r_rows[b_] is not None and r_rows[a_] > 0 >= r_rows[b_]:
            be_r = round(a_ + (b_ - a_) * r_rows[a_] / (r_rows[a_] - r_rows[b_]), 3)
            break
    r10 = r_rows.get(0.10)
    return {'cagr_pct_by_r_haircut': {f'{k:.2f}': v for k, v in r_rows.items()}, 'break_even_r_haircut': be_r,
            'r_haircut_note': 'average R per trade that can be lost to inclusion/selection bias before net CAGR reaches zero (None = positive across the grid)',
            'loss_on_hit_pct': loss * 100, 'mean_cagr_pct_by_q': {f'{k:.3f}': v for k, v in rows.items()}, 'break_even_q': breakeven,
            'break_even_note': 'None = CAGR stays positive across the whole grid' if breakeven is None else 'probability per trade at which net CAGR reaches zero (interpolated)',
            'pass': bool(q1 is not None and q1 > 0 and r10 is not None and r10 > 0),
            'warning': 'Synthetic sensitivity. It does not measure real survivorship bias and does not clear gate B2.'}


# ------------------------------------------------------------------ R-BENCH
def quarter_labels(idx):
    return pd.DatetimeIndex(idx).to_period('Q').astype(str).values


def bench_test(c0_ret, bench, avg_exposure_pct, alpha):
    if bench is None or len(c0_ret) < 60:
        return {'status': 'unverifiable', 'pass': False, 'reason': 'no benchmark series or too few days'}
    b = bench.pct_change().dropna()
    b = b[(b.index >= c0_ret.index[0]) & (b.index <= c0_ret.index[-1])]
    b = b + NIFTY_DIV_YIELD / 252                                  # price index -> approximate total return
    em = mx.exposure_matched(b, avg_exposure_pct)
    diff = ex.paired_diff(c0_ret, em)
    ci = rs.cluster_ci_mean(diff.values, quarter_labels(diff.index), alpha=alpha)       # quarters: trades are held for months
    bh, c0p = mx.perf(b), mx.perf(c0_ret)
    return {'status': 'ok', 'avg_exposure_pct': avg_exposure_pct, 'assumed_nifty_dividend_yield': NIFTY_DIV_YIELD, 'mean_daily_excess_pct': round(float(diff.mean()) * 100, 5),
            'ci_pct': [round(ci[0] * 100, 5), round(ci[1] * 100, 5)] if ci else None, 'alpha': alpha,
            'c0': c0p, 'nifty_buy_and_hold': bh, 'nifty_exposure_matched': mx.perf(em), 'pass': bool(ci and ci[0] > 0)}


# ------------------------------------------------------------------ orchestration
def run(frames, bench, prepared=None, spec=None, holdout_log=None, data_cutoff=None, ts=None, draws=N_DRAWS, mc_paths_n=MC_PATHS,
        neighbours=NEIGHBOURS, skip_slow=False):
    spec = spec or prereg.load('PREREG_v3')
    alpha = prereg.alpha_per_test(spec)
    design_end, ho_start = spec['windows']['design_end'], spec['windows']['holdout_start']
    prepared = prepared if prepared is not None else bt.prepare(frames)
    cutoff = data_cutoff or str(max(df.index[-1] for df in frames.values()).date())
    cfg = ex.realistic_cfg()
    fd, bd, pd_ = ex.design_view(frames, bench, prepared, design_end)        # design numbers never see post-design prices
    base_d = bt.generate_trades(fd, cfg, bd, pd_)
    c0 = ex.window(base_d, None, design_end)
    stats, c0_ret, c0_m = ex.run_port(fd, c0, cfg)
    c0p = c0_m.get('portfolio') or {}
    res = {}

    cand = candidate_table(pd_, cfg, design_end)
    res['R-NULL-A'] = null_test(c0, cand, ~cand['is_signal'], draws)
    res['R-NULL-B'] = null_test(c0, cand, (~cand['is_signal']) & cand['stage_pass'], draws)
    for k in ('R-NULL-A', 'R-NULL-B'):
        res[k]['pass'] = bool(res[k].get('status') == 'ok' and res[k]['p_value'] <= alpha)
    ci = rs.cluster_ci_mean(c0['r'].values, c0['entry_date'].dt.to_period('Q').astype(str).values, alpha=alpha) if len(c0) > 5 else None     # quarters, confidence 1 - alpha
    res['R-CI'] = {'avg_r': round(float(c0['r'].mean()), 4) if len(c0) else None, 'trades': int(len(c0)), 'alpha': alpha,
                   'ci': [round(ci[0], 4), round(ci[1], 4)] if ci else None, 'pass': bool(ci and ci[0] > 0)}
    res['R-BENCH'] = bench_test(c0_ret, bd, stats.get('avg_exposure_pct', 0.0) or 0.0, alpha)
    ho_days = int(bench[bench.index >= ho_start].shape[0]) if bench is not None else 250
    res['R-MC'] = monte_carlo(c0_ret, c0['r'].values, mc_paths_n, holdout_days=max(ho_days, 20)) if len(c0_ret) > 60 else {'status': 'unverifiable', 'pass': False}
    res['R-REGIME'] = regime_report(c0, c0_ret) if len(c0) else {'pass': False}
    if skip_slow:
        for k in ('R-SENS', 'R-EXEC', 'R-SURV'):
            res[k] = {'status': 'skipped', 'pass': False}
    else:
        res['R-SENS'] = sensitivity(fd, bd, pd_, design_end, c0p.get('calmar'), neighbours)
        res['R-EXEC'], _ = execution_stress(fd, bd, pd_, design_end)
        res['R-SURV'] = survivorship_haircut(fd, base_d, cfg, design_end)
    others_ok = all(v.get('pass') for v in res.values())
    if others_ok:
        hg.open_once('R-HO', spec['_hash'], cutoff, holdout_log, ts)
        base = bt.generate_trades(frames, cfg, bench, prepared)
        _, _, ho_m = ex.run_port(frames, ex.window(base, ho_start), cfg)
        hp = ho_m.get('portfolio') or {}
        p95 = res['R-MC'].get('holdout_length_p95_depth_pct', res['R-MC']['p95_depth_pct'])        # a path as short as the hold-out, not the whole design window
        ho_ok = bool(hp.get('cagr_pct') is not None and hp['cagr_pct'] > 0 and hp.get('max_drawdown_pct') is not None and -hp['max_drawdown_pct'] <= p95)
        hg.record_result('R-HO', spec['_hash'], ho_ok, {'holdout': hp, 'mc_p95_depth_pct': p95}, holdout_log, ts)
        res['R-HO'] = {'status': 'opened', 'holdout': hp, 'mc_p95_depth_pct': p95, 'pass': ho_ok}
    else:
        res['R-HO'] = {'status': 'not_opened', 'reason': 'another test or gate already failed; the hold-out is not spent', 'pass': False,
                       'failed': [k for k, v in res.items() if not v.get('pass')]}
    failed = [k for k, v in res.items() if not v.get('pass')]
    return {'provenance': provenance.make('robustness', data_cutoff=cutoff, extra={'prereg': spec['id'], 'prereg_hash': spec['_hash']}),
            'control': {'id': 'C0', 'design': c0_m}, 'results': res, 'failed': failed, 'robustness_passed': not failed,
            'universe': {'version': provenance.universe_info()['version'], 'symbols_with_data': len(frames), 'survivorship_bias': True},
            'limits': ['Survivorship bias remains: the universe is today\'s list. R-SURV is a synthetic haircut, not a fix.',
                       'Yahoo adjusted daily bars; no intraday path, so stop-versus-target order inside a bar is assumed.',
                       'The design window includes data C0 was originally chosen on; the hold-out has been looked at by PREREG_v1/v2.',
                       'The null model ignores the one-position-per-symbol rule.']}


def _status(v):
    return 'PASS' if v.get('pass') else ('not run' if v.get('status') in ('skipped', 'not_opened') else 'FAIL')


def markdown(rep):
    pv, r = rep['provenance'], rep['results']
    L = ['# Robustness battery for control C0 (PREREG_v3)', '',
         f"Universe {pv['universe_version']} ({rep['universe']['symbols_with_data']} symbols, survivorship bias present), data cutoff {pv['data_cutoff']}, "
         f"pre-registration `{pv['prereg_hash'][:12]}`. Realistic costs. **Robustness passed: {'yes' if rep['robustness_passed'] else 'NO'}.** "
         f"Failed or not run: {rep['failed'] or 'none'}.", '',
         'Passing means no registered test rejected C0. It is not proof of a live edge, changes no readiness weight and does not authorise live trading.', '',
         '| Test | Result | Key numbers |', '|---|---|---|']
    for k in ('R-NULL-A', 'R-NULL-B'):
        v = r[k]
        L.append(f"| {k} random entries ({'any bar' if k.endswith('A') else 'stage-2 bars'}) | {_status(v)} | C0 avg R {v.get('c0_mean_r')} vs null {v.get('null_mean_r')} "
                 f"(5-95%: {v.get('null_p05')}..{v.get('null_p95')}), p = {v.get('p_value')} |")
    v = r['R-CI']; L.append(f"| R-CI expectancy | {_status(v)} | avg R {v['avg_r']} over {v['trades']} trades, CI {v['ci']} |")
    v = r['R-BENCH']; L.append(f"| R-BENCH vs exposure-matched Nifty | {_status(v)} | excess/day {v.get('mean_daily_excess_pct')}%, CI {v.get('ci_pct')} |")
    v = r['R-MC']; L.append(f"| R-MC drawdown | {_status(v)} | p95 depth {v.get('p95_depth_pct')}%, P(DD>=25%) {v.get('prob_drawdown_ge_25pct')}, P(DD>=30%) {v.get('prob_drawdown_ge_30pct')} |")
    v = r['R-REGIME']; L.append(f"| R-REGIME | {_status(v)} | positive years {v.get('share_of_years_positive')}, biggest year share {v.get('max_single_year_share_of_total_r')} |")
    v = r['R-SENS']; L.append(f"| R-SENS plateau | {_status(v)} | {v.get('share_keeping_70pct_of_c0_calmar')} of neighbours keep 70% of Calmar; all CAGR>0: {v.get('all_cagr_positive')} |")
    v = r['R-EXEC']; L.append(f"| R-EXEC stress | {_status(v)} | worst scenario CAGR {min([s['cagr_pct'] for s in v['scenarios'].values() if s['cagr_pct'] is not None], default=None)} |" if v.get('scenarios') else f"| R-EXEC | {_status(v)} | |")
    v = r['R-SURV']; L.append(f"| R-SURV haircut | {_status(v)} | CAGR by delisting q: {v.get('mean_cagr_pct_by_q')}, break-even q {v.get('break_even_q')}; by R removed per trade: {v.get('cagr_pct_by_r_haircut')}, break-even {v.get('break_even_r_haircut')}R |")
    v = r['R-HO']; L.append(f"| R-HO hold-out | {_status(v)} | {v.get('holdout') or v.get('reason')} |")
    mc = r['R-MC']
    if mc.get('max_drawdown_depth_pct'):
        L += ['', '## Monte Carlo drawdown (design-window daily returns, block bootstrap)', '',
              f"Max drawdown depth percentiles: {mc['max_drawdown_depth_pct']} (hold-out-length paths p95: {mc.get('holdout_length_p95_depth_pct')}). CAGR percentiles: {mc['cagr_pct']}. P(CAGR<0) {mc['prob_negative_cagr']}. "
              f"Longest underwater (days): {mc['longest_underwater_days']}. Longest losing streak (trades): {mc['longest_losing_streak_trades']}."]
    rg = r['R-REGIME']
    if rg.get('by_year'):
        L += ['', '## By year (design window)', '', '| Year | Trades | Avg R | Win | Sum R |', '|---|---|---|---|---|']
        L += [f"| {y} | {v['trades']} | {v['avg_r']} | {v['win_rate']} | {v['sum_r']} |" for y, v in rg['by_year'].items()]
        L += ['', 'Stress windows: ' + '; '.join(f"{k}: {v}" for k, v in rg['stress_windows'].items())]
    sn = r['R-SENS']
    if sn.get('neighbours'):
        L += ['', '## Parameter neighbours (descriptive; none is adopted)', '', '| Parameter | Value | Trades | Avg R | CAGR | MaxDD | Calmar |', '|---|---|---|---|---|---|---|']
        L += [f"| {n['param']} | {n['value']} | {n['trades']} | {n['avg_r']} | {n['cagr_pct']} | {n['max_drawdown_pct']} | {n['calmar']} |" for n in sn['neighbours']]
    ec = r['R-EXEC']
    if ec.get('scenarios'):
        L += ['', '## Execution stress (design window)', '', '| Scenario | CAGR | MaxDD | Calmar | After-tax CAGR |', '|---|---|---|---|---|']
        L += [f"| {k} | {v['cagr_pct']} | {v['max_drawdown_pct']} | {v['calmar']} | {v['after_tax_cagr_pct']} |" for k, v in ec['scenarios'].items()]
        L += ['', ec['tax_note']]
    L += ['', '## Limits', ''] + [f'- {x}' for x in rep['limits']]
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, default=12)
    ap.add_argument('--cache', default='history_cache_12y.pkl')
    ap.add_argument('--out', default='reports')
    a = ap.parse_args()
    spec = prereg.load('PREREG_v3')
    frames, bench = bt.load_history(a.years, a.cache)
    rep = run(frames, bench, spec=spec)
    os.makedirs(f'{a.out}/experiments/history', exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    md = markdown(rep)
    for path, body in ((f'{a.out}/robustness.json', json.dumps(rep, indent=2, default=str)), (f'{a.out}/robustness.md', md),
                       (f'{a.out}/experiments/history/{stamp}_v3_{spec["_hash"][:8]}.json', json.dumps(rep, indent=2, default=str)),
                       (f'{a.out}/experiments/history/{stamp}_v3_{spec["_hash"][:8]}.md', md)):
        with open(path, 'w') as f:
            f.write(body)
    evlog.append(f'{a.out}/experiments/runs.jsonl', 'experiment_run', stamp, {'prereg_hash': spec['_hash'], 'robustness_passed': rep['robustness_passed'], 'failed': rep['failed']})
    print(md)


if __name__ == '__main__':
    main()
