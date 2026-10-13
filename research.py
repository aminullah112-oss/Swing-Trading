#!/usr/bin/env python3
"""
Pre-registered research on top of backtest.py. Nothing here is tuned after seeing results.

1. GRID: a fixed list of 12 variants (2 entry modes x 6 exit rules). The list below is the whole
   set of trials. Confidence intervals on the hold-out are month-clustered bootstraps widened with a Bonferroni correction
   for N = len(VARIANTS), so that "best of 12" luck doesn't look like an edge.

   A variant is PROMISING only if ALL gates hold:
     G1  design-period (entries before SPLIT) average R > 0
     G2  hold-out average R > 0 with the Bonferroni-adjusted 95% CI lower bound > 0
     G3  hold-out portfolio CAGR > 0 after costs, from a fresh start on the split date
   Passing is a reason to paper trade, not to trade. Failing every variant is a valid outcome.

2. DIAGNOSIS of the 0-100 score on two reference configurations: does the score (and each of its
   components) predict R? Bins are measured on the design period and re-checked on the hold-out.
   A "learned" additive score fitted on the design period only is compared with the live score
   on the hold-out.

CAVEAT: the setup-level pattern (TRENDING > PULLBACK) was seen on the full sample before this
module was written, so the hold-out is not clean for that one idea. Only forward (paper-trading)
data can settle it.
"""
import json, os
import numpy as np
import pandas as pd

import backtest as bt

SPLIT = '2023-01-01'

# (label, trigger, exit_mode, max_hold). This list IS the trial count.
VARIANTS = [
    (f'{trig}/{ex}/h{hold}', trig, ex, hold)
    for trig in ('none', 'prior_high')
    for ex, hold in (('ema20', 40), ('ema50', 40), ('ema50', 120),
                     ('chandelier', 40), ('chandelier', 120), ('none', 120))
]
N_TRIALS = len(VARIANTS)

# Reference configs for the score diagnosis (also fixed in advance)
DIAG_REFS = [('baseline: next-open, ema20 exit, 40d', 'none', 'ema20', 40),
             ('slow exit: next-open, chandelier(3 ATR), 120d', 'none', 'chandelier', 120)]


def cfg_for(trigger, exit_mode, hold):
    return bt.Config(trigger=trigger, exit_mode=exit_mode, max_hold=hold, split_date=SPLIT)


def month_clusters(trades):
    """Trades entered in the same month share the market's move, so they are not independent."""
    return trades['entry_date'].dt.to_period('M').astype(str).values


def cluster_ci_mean(r, clusters, alpha=0.05, n=2000, seed=0):
    """Percentile CI for the mean of r, resampling whole clusters (months) with replacement."""
    r = np.asarray(r, dtype=float)
    if len(r) < 2:
        return None
    codes, uniq = pd.factorize(clusters)
    k = len(uniq)
    sums = np.bincount(codes, weights=r, minlength=k); cnt = np.bincount(codes, minlength=k).astype(float)
    idx = np.random.default_rng(seed).integers(0, k, size=(n, k))
    means = sums[idx].sum(1) / cnt[idx].sum(1)
    return [float(np.percentile(means, 100 * alpha / 2)), float(np.percentile(means, 100 * (1 - alpha / 2)))]


def adj_ci(trades, n_trials):
    """Month-clustered CI at Bonferroni-adjusted confidence for n_trials comparisons."""
    return cluster_ci_mean(trades['r'].values, month_clusters(trades), alpha=0.05 / n_trials)


def holdout_portfolio(frames, trades, cfg):
    h = trades[trades['entry_date'] >= pd.Timestamp(cfg.split_date)]
    stats, _ = bt.portfolio(frames, h, cfg)
    return stats


def run_grid(frames, bench, prepared):
    rows = []
    for label, trig, ex, hold in VARIANTS:
        cfg = cfg_for(trig, ex, hold)
        rep, trades, _ = bt.run(frames, cfg, bench, prepared)
        design, hold_out = bt.split_in_out_of_sample(trades, SPLIT)
        yrs = max((trades['entry_date'].max() - trades['entry_date'].min()).days / 365.25, 1e-9) if len(trades) else 1
        ci = adj_ci(hold_out, N_TRIALS) if len(hold_out) else None
        hp = holdout_portfolio(frames, trades, cfg) if len(hold_out) else {}
        g1 = len(design) > 0 and design['r'].mean() > 0
        g2 = ci is not None and ci[0] > 0
        g3 = hp.get('cagr_pct', -999) > 0
        rows.append({
            'label': label, 'trades_per_year': round(len(trades) / yrs), 'avg_hold': round(trades['hold'].mean(), 1) if len(trades) else 0,
            'design_n': len(design), 'design_avg_r': round(design['r'].mean(), 3) if len(design) else None,
            'holdout_n': len(hold_out), 'holdout_avg_r': round(hold_out['r'].mean(), 3) if len(hold_out) else None,
            'holdout_adj_ci': [round(ci[0], 3), round(ci[1], 3)] if ci else None,
            'full_pf': rep['all_trades'].get('profit_factor'),
            'full_cagr': rep['portfolio'].get('cagr_pct'), 'full_maxdd': rep['portfolio'].get('max_drawdown_pct'),
            'holdout_port_cagr': hp.get('cagr_pct'), 'holdout_port_maxdd': hp.get('max_drawdown_pct'),
            'G1': bool(g1), 'G2': bool(g2), 'G3': bool(g3), 'promising': bool(g1 and g2 and g3),
        })
    return rows


def grid_markdown(rows, bench_note):
    L = ['# Exit/entry variant grid', '',
         f'Trials run: **{N_TRIALS}** (fixed in advance). Hold-out = entries from {SPLIT}. '
         f'CIs are month-clustered bootstrap intervals (trades entered in the same month share market moves, so they are not independent), at Bonferroni-adjusted confidence for {N_TRIALS} trials (alpha = 0.05/{N_TRIALS}).', '',
         'Gates: **G1** design avg R > 0 · **G2** hold-out adjusted CI lower bound > 0 · **G3** hold-out portfolio CAGR > 0.', '',
         '| Variant | Trades/yr | Avg hold | Design n / avg R | Hold-out n / avg R | Hold-out adj. CI | Full PF | Full CAGR / maxDD | Hold-out portfolio CAGR / maxDD | G1 | G2 | G3 |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        ok = lambda b: '✅' if b else '❌'
        L.append(f"| {r['label']} | {r['trades_per_year']} | {r['avg_hold']} | {r['design_n']} / {r['design_avg_r']} | "
                 f"{r['holdout_n']} / {r['holdout_avg_r']} | {r['holdout_adj_ci']} | {r['full_pf']} | "
                 f"{r['full_cagr']}% / {r['full_maxdd']}% | {r['holdout_port_cagr']}% / {r['holdout_port_maxdd']}% | "
                 f"{ok(r['G1'])} | {ok(r['G2'])} | {ok(r['G3'])} |")
    prom = [r['label'] for r in rows if r['promising']]
    L += ['', f'**Promising (all gates): {prom if prom else "none"}**', '', bench_note, '',
          '_Survivorship bias flatters every row. Passing all gates would justify paper trading only._']
    return '\n'.join(L)


# --------------------------------------------------------------------------------------
# Score diagnosis
# --------------------------------------------------------------------------------------
LIVE_POINTS = {
    'rsi': [(0, 38, 0), (38, 45, 8), (45, 62, 20), (62, 70, 13), (70, 76, 4), (76, 101, 0)],
    'volr': [(0, 0.7, 3), (0.7, 1.2, 7), (1.2, 1.8, 13), (1.8, 1e9, 20)],
}
SETUP_POINTS = {'PULLBACK_EMA20': 20, 'PULLBACK_EMA50': 14, 'COMPRESSION': 12, 'BREAKOUT_CONT': 10, 'TRENDING': 6}
NRISING_POINTS = {0: 3, 1: 3, 2: 10, 3: 15}
NEAR52_POINTS = {0: 0, 1: 3}


def component_bins(df):
    """Return {component: Series of bin labels} aligned with df, plus live-point lookup."""
    out, pts = {}, {}
    for comp in ('rsi', 'volr'):
        lab, p = [], {}
        edges = LIVE_POINTS[comp]
        for lo, hi, pt in edges:
            name = f'{lo:g}-{hi:g}' if hi < 1e8 else f'{lo:g}+'
            p[name] = pt
        def which(v, edges=edges):
            for lo, hi, pt in edges:
                if lo <= v < hi:
                    return f'{lo:g}-{hi:g}' if hi < 1e8 else f'{lo:g}+'
            return 'other'
        out[comp] = df[comp].map(which); pts[comp] = p
    out['nrising'] = df['nrising'].astype(str); pts['nrising'] = {str(k): v for k, v in NRISING_POINTS.items()}
    out['near52'] = df['near52'].astype(str);   pts['near52'] = {str(k): v for k, v in NEAR52_POINTS.items()}
    out['setup'] = df['setup'];                 pts['setup'] = dict(SETUP_POINTS)
    return out, pts


def rank_corr(x, y):
    """Spearman correlation via ranks (no scipy dependency)."""
    rx = pd.Series(x).rank().values; ry = pd.Series(y).rank().values
    if len(rx) < 3 or rx.std() == 0 or ry.std() == 0:
        return float('nan')
    return float(np.corrcoef(rx, ry)[0, 1])


def _cluster_indices(clusters, n, seed):
    codes, uniq = pd.factorize(clusters)
    groups = [np.where(codes == c)[0] for c in range(len(uniq))]
    rng = np.random.default_rng(seed)
    for _ in range(n):
        yield np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])


def boot_spearman(x, y, clusters, n=500, seed=0):
    """Spearman with a month-clustered bootstrap CI (point, lo, hi)."""
    rx = pd.Series(np.asarray(x)).rank().values; ry = pd.Series(np.asarray(y)).rank().values
    if len(rx) < 30:
        return None
    point = float(np.corrcoef(rx, ry)[0, 1])
    bs = [np.corrcoef(rx[i], ry[i])[0, 1] for i in _cluster_indices(clusters, n, seed)]
    return [round(point, 3), round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)]


def tercile_gap(score, r, clusters, n=500, seed=0):
    """Avg R of top score tercile minus bottom tercile, month-clustered bootstrap CI."""
    s = np.asarray(score, dtype=float); rr = np.asarray(r, dtype=float)
    if len(s) < 60:
        return None
    lo, hi = np.quantile(s, [1 / 3, 2 / 3])
    def gap(ix):
        t, b = rr[ix][s[ix] >= hi], rr[ix][s[ix] <= lo]
        return t.mean() - b.mean() if len(t) and len(b) else np.nan
    point = gap(np.arange(len(s)))
    gs = [gap(i) for i in _cluster_indices(clusters, n, seed)]
    return [round(float(point), 3), round(float(np.nanpercentile(gs, 2.5)), 3), round(float(np.nanpercentile(gs, 97.5)), 3)]


def learned_score(train, test, k=300):
    """Additive score: each component's bin -> shrunk mean R measured on `train`; applied to `test`."""
    bt_train, _ = component_bins(train)
    bt_test, _ = component_bins(test)
    out = pd.Series(0.0, index=test.index)
    for comp in bt_train:
        g = pd.DataFrame({'b': bt_train[comp].values, 'r': train['r'].values}).groupby('b')['r'].agg(['mean', 'count'])
        shrunk = (g['mean'] * g['count'] / (g['count'] + k)).to_dict()
        out += bt_test[comp].map(shrunk).fillna(0.0)
    return out


def diagnose(trades, label):
    design, hold = bt.split_in_out_of_sample(trades, SPLIT)
    L = [f'## Score diagnosis: {label}', '', f'Design n={len(design)}, hold-out n={len(hold)}.', '']
    if len(design) < 100 or len(hold) < 100:
        return '\n'.join(L + ['Not enough trades.']), {}
    cd, ch = month_clusters(design), month_clusters(hold)
    res = {'live_spearman_design': boot_spearman(design['score'], design['r'], cd),
           'live_spearman_holdout': boot_spearman(hold['score'], hold['r'], ch),
           'live_tercile_gap_holdout': tercile_gap(hold['score'], hold['r'], ch)}
    L += ['**Does the live score predict R?** Spearman (point, month-clustered 95% CI):',
          f"- design: {res['live_spearman_design']}", f"- hold-out: {res['live_spearman_holdout']}",
          f"- hold-out top-tercile minus bottom-tercile avg R (point, CI): {res['live_tercile_gap_holdout']}", '']

    d_bins, pts = component_bins(design); h_bins, _ = component_bins(hold)
    L += ['**Per-component bins** (live points → realised avg R). A sound score would have R rising with points in both periods.', '',
          '| Component | Bin | Live pts | Design n | Design avg R | Hold-out n | Hold-out avg R |', '|---|---|---|---|---|---|---|']
    agree = {}
    for comp in d_bins:
        dg = pd.DataFrame({'b': d_bins[comp].values, 'r': design['r'].values}).groupby('b')['r'].agg(['count', 'mean'])
        hg = pd.DataFrame({'b': h_bins[comp].values, 'r': hold['r'].values}).groupby('b')['r'].agg(['count', 'mean'])
        bins = [b for b in pts[comp] if b in dg.index]
        for b in bins:
            hn = int(hg.loc[b, 'count']) if b in hg.index else 0
            hm = f"{hg.loc[b, 'mean']:+.3f}" if b in hg.index else ''
            L.append(f"| {comp} | {b} | {pts[comp][b]} | {int(dg.loc[b, 'count'])} | {dg.loc[b, 'mean']:+.3f} | {hn} | {hm} |")
        if len(bins) > 2:
            p = pd.Series([pts[comp][b] for b in bins], dtype=float)
            agree[comp] = (round(rank_corr(p, [dg.loc[b, 'mean'] for b in bins]), 2),
                           round(rank_corr(p, [hg.loc[b, 'mean'] if b in hg.index else 0.0 for b in bins]), 2))
    L += ['', 'Rank agreement between live points and realised R (design, hold-out); +1 = score is right, -1 = backwards:']
    L += [f'- {c}: {v}' for c, v in agree.items()]
    res['rank_agreement'] = agree

    ls = learned_score(design, hold)
    res['learned_spearman_holdout'] = boot_spearman(ls, hold['r'], ch)
    res['learned_tercile_gap_holdout'] = tercile_gap(ls, hold['r'], ch)
    L += ['', '**Learned additive score** (bin means from the design period only, shrunk toward 0), evaluated on the hold-out:',
          f"- Spearman: {res['learned_spearman_holdout']}", f"- top minus bottom tercile avg R: {res['learned_tercile_gap_holdout']}",
          '', 'Compare with the live score above. If the learned score\'s CI also spans 0, no component of the score carries a '
          'dependable signal and the ranking should be dropped rather than refitted.']
    return '\n'.join(L), res


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, default=10)
    ap.add_argument('--cache', default='history_cache.pkl')
    ap.add_argument('--out', default='reports')
    a = ap.parse_args()
    frames, bench = bt.load_history(a.years, a.cache)
    prepared = bt.prepare(frames)
    os.makedirs(a.out, exist_ok=True)

    rows = run_grid(frames, bench, prepared)
    first = bt.generate_trades(frames, cfg_for('none', 'ema20', 40), bench, prepared)
    span = (first['entry_date'].min(), first['exit_date'].max()) if len(first) else (None, None)
    hold_start = pd.Timestamp(SPLIT)
    b_hold = bt.benchmark_stats(bench, hold_start, span[1]) if span[1] is not None else None
    note = f'Nifty buy-and-hold since {SPLIT}: {json.dumps(b_hold)}'
    with open(f'{a.out}/grid.md', 'w') as f:
        f.write(grid_markdown(rows, note))
    with open(f'{a.out}/grid.json', 'w') as f:
        json.dump(rows, f, indent=2)
    print(grid_markdown(rows, note))

    parts = ['# Score diagnosis', '', 'Fixed reference configurations; see research.py docstring for caveats.', '']
    for label, trig, ex, hold in DIAG_REFS:
        trades = bt.generate_trades(frames, cfg_for(trig, ex, hold), bench, prepared)
        md, _ = diagnose(trades, label)
        parts += [md, '']
    with open(f'{a.out}/diagnosis.md', 'w') as f:
        f.write('\n'.join(parts))
    print('\n'.join(parts))


if __name__ == '__main__':
    main()
