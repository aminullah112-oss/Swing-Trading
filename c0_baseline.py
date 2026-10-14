#!/usr/bin/env python3
"""Reproduce control C0 from raw data and compare it with the frozen baseline.

Writes reports/c0_baseline.json|md with provenance. Reproduction is exact for the same data (the trades digest
proves it); against the frozen numbers it is compared with a stated tolerance, because Yahoo revises adjusted
history, and any drift is reported, never absorbed silently.
"""
import hashlib
import json
import os

import pandas as pd

import backtest as bt
import provenance
import strategy

CONTROL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'control')
SPLIT = '2023-01-01'


def trades_digest(trades):
    t = trades.sort_values(['symbol', 'signal_date']).copy()
    cols = ['symbol', 'signal_date', 'entry_date', 'exit_date', 'entry', 'exit', 'r']
    t = t[cols].copy()
    for c in ('entry', 'exit', 'r'):
        t[c] = t[c].astype(float).round(8)
    return hashlib.sha256(t.to_csv(index=False).encode()).hexdigest()[:16]


def reproduce(frames, bench, prepared=None, cfg=None, data_cutoff=None):
    cfg = cfg or strategy.backtest_config(split_date=SPLIT)
    prepared = prepared if prepared is not None else bt.prepare(frames)
    rep, trades, eq = bt.run(frames, cfg, bench, prepared)
    ho = trades[trades['entry_date'] >= pd.Timestamp(SPLIT)]
    ho_stats, _ = bt.portfolio(frames, ho, cfg)
    cutoff = data_cutoff or str(max(df.index[-1] for df in frames.values()).date())
    return {
        'provenance': provenance.make('c0_baseline', data_cutoff=cutoff),
        'control': {'id': 'C0', 'c0_hash': provenance.c0_hash()},
        'trades': int(len(trades)), 'trades_digest': trades_digest(trades),
        'all_trades': rep['all_trades'], 'design': rep['in_sample'], 'holdout': rep['out_of_sample'],
        'portfolio_full': rep['portfolio'], 'portfolio_holdout': ho_stats,
        'symbols_with_data': len(frames),
    }


def compare_to_frozen(result, frozen):
    """List of drifts beyond tolerance (empty = reproduces the frozen baseline within tolerance)."""
    tol = frozen['tolerance']
    g = frozen['grid_row_prior_high_ema50_h120']
    drifts = []

    def chk(name, new, old, tol_abs):
        if new is None or old is None:
            drifts.append(f'{name}: missing value'); return
        if abs(float(new) - float(old)) > tol_abs:
            drifts.append(f'{name}: {new} vs frozen {old} (tolerance {tol_abs})')
    chk('design avg R', result['design'].get('avg_r'), g['design_avg_r'], tol['avg_r_abs'])
    chk('hold-out avg R', result['holdout'].get('avg_r'), g['holdout_avg_r'], tol['avg_r_abs'] * 4)
    chk('hold-out portfolio CAGR %', result['portfolio_holdout'].get('cagr_pct'), g['holdout_port_cagr'], tol['cagr_pts'] * 2)
    d_new, d_old = result['design'].get('trades'), g['design_n']
    if d_new is None or abs(d_new - d_old) > tol['trades_rel'] * d_old:
        drifts.append(f'design trades: {d_new} vs frozen {d_old} (tolerance {tol["trades_rel"]:.0%})')
    return drifts


def markdown(result, drifts):
    p = result['provenance']
    L = ['# C0 baseline reproduction', '',
         f"Control C0 (`c0_hash` {result['control']['c0_hash']}) reproduced from raw data. Universe {p['universe_version']} "
         f"({p['universe_count']} configured, {result['symbols_with_data']} with data), data cutoff {p['data_cutoff']}, commit {p['commit_sha'][:10]}.", '',
         f"Trades: {result['trades']} · trades digest `{result['trades_digest']}` (identical data and code give an identical digest).", '',
         '| Slice | Trades | Win | Avg R | 95% CI (naive iid) | PF |', '|---|---|---|---|---|---|']
    for k, nm in (('all_trades', 'All'), ('design', 'Design (before 2023)'), ('holdout', 'Hold-out (2023+)')):
        v = result[k]
        L.append(f"| {nm} | {v.get('trades')} | {v.get('win_rate')} | {v.get('avg_r')} | {v.get('avg_r_ci95')} | {v.get('profit_factor')} |")
    L += ['', f"Portfolio, full period: `{json.dumps(result['portfolio_full'], default=str)}`", '',
          f"Portfolio, hold-out from a fresh start: `{json.dumps(result['portfolio_holdout'], default=str)}`", '']
    L += (['**Reproduces the frozen baseline within tolerance.**'] if not drifts else
          ['**Drift versus the frozen baseline (investigate before trusting any later comparison):**'] + [f'- {d}' for d in drifts])
    return '\n'.join(L)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, default=10)
    ap.add_argument('--cache', default='history_cache.pkl')
    ap.add_argument('--out', default='reports')
    a = ap.parse_args()
    frames, bench = bt.load_history(a.years, a.cache)
    res = reproduce(frames, bench)
    trades = bt.run(frames, strategy.backtest_config(split_date=SPLIT), bench)[1]      # same call reproduce() makes; kept for hold_stats
    with open(os.path.join(CONTROL, 'c0_frozen_baseline.json')) as f:
        frozen = json.load(f)
    drifts = compare_to_frozen(res, frozen)
    res['drift_vs_frozen'] = drifts
    os.makedirs(a.out, exist_ok=True)
    with open(f'{a.out}/c0_baseline.json', 'w') as f:
        json.dump(res, f, indent=2, default=str)
    trades.to_csv(f'{a.out}/trades_c0.csv', index=False)
    import hold_stats
    hold_stats.main(f'{a.out}/trades_c0.csv', f'{a.out}/hold_stats.json')
    md = markdown(res, drifts)
    with open(f'{a.out}/c0_baseline.md', 'w') as f:
        f.write(md)
    print(md)


if __name__ == '__main__':
    main()
