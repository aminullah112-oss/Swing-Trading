#!/usr/bin/env python3
"""Pre-registered experiment runner (PREREG_v1). Compares eight fixed variants with control C0 under the realistic
execution model, walk-forward by calendar year, with a once-only hold-out and Bonferroni-corrected intervals.

What this can and cannot show (also printed in the report):
  * Variants have fixed parameters, so 'walk-forward' here is year-by-year out-of-sample consistency, not refitting.
  * The universe is today's list (survivorship bias remains unless a point-in-time file passes pit.acceptance()).
  * C0 was selected on data that includes 2023+, so a variant beating C0 there is weak evidence; a variant that does NOT
    beat C0 is informative. Passing is a reason for forward paper testing, never for live capital.
  * Every run is kept: reports/experiments/history/ is append-only and failed variants stay on record.
"""
import argparse
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import backtest as bt
import events as evlog
import holdout_guard as hg
import metrics as mx
import prereg
import provenance
import research as rs
import settings
import strategy

BLOCK_YEARS = list(range(2017, 2025))
# Pre-registered thresholds (PREREG_v1.walk_forward_pass_criteria). Module constants so tests can exercise the pass path.
MIN_TRADES, MIN_MONTHS, N_BLOCKS, MIN_BLOCKS_WON = 100, 40, 8, 5


def realistic_cfg(**kw):
    return strategy.realistic_config(**kw)


def momentum_rank(prepared):
    """Cross-sectional percentile rank (0..1) of the volatility-adjusted momentum indicator, per date, across the universe."""
    mom = pd.DataFrame({s: p['ind']['mom'] for s, p in prepared.items()})
    return mom.rank(axis=1, pct=True)


def apply_filter(h, trades, rank):
    p = h['param']
    if h['id'] == 'H1':
        r = np.array([rank.at[d, s] if d in rank.index else np.nan for s, d in zip(trades['symbol'], trades['signal_date'])])
        return trades[r >= p['min_rank']]
    if h['id'] == 'H2':
        return trades[trades['from_52h'] >= p['min_from_52h_pct']]
    if h['id'] == 'H3':
        return trades[trades['adv20_value'] >= p['min_adv20_value']]
    if h['id'] == 'H4':
        return trades[trades['atr_pct'] <= p['max_atr_pct']]
    if h['id'] == 'H5':
        return trades[trades['score'] >= p['min_score']]
    if h['id'] == 'H6':
        return trades[trades['regime'] == p['regime']]
    return trades


def window(trades, lo=None, hi=None):
    t = trades
    if lo is not None:
        t = t[t['entry_date'] >= pd.Timestamp(lo)]
    if hi is not None:
        t = t[t['entry_date'] <= pd.Timestamp(hi)]
    return t


def run_port(frames, trades, cfg):
    """(stats, daily net returns, metrics block) for the trades given, starting fresh with cfg.capital."""
    if trades.empty:
        return {'accepted': 0}, pd.Series(dtype=float), {'portfolio': None}
    stats, eq, taken = bt.portfolio(frames, trades, cfg, detail=True)
    ret = eq.pct_change().dropna() if len(eq) else pd.Series(dtype=float)
    m = mx.full(ret, trades['r'].values, taken, eq, stats)
    return stats, ret, m


def paired_diff(a, b):
    idx = a.index.union(b.index)
    return a.reindex(idx).fillna(0.0) - b.reindex(idx).fillna(0.0)


def month_labels(idx):
    return idx.to_period('M').astype(str).values


def evaluate_design(h, v_trades, v_ret, c0_ret, alpha, v_port):
    """Pre-registered walk-forward criteria P1-P4. Returns (passed, detail)."""
    d = {}
    n = int(len(v_trades))
    months = int(pd.Series(v_trades['entry_date']).dt.to_period('M').nunique()) if n else 0
    d['P1_sample'] = {'trades': n, 'months': months, 'pass': bool(n >= MIN_TRADES and months >= MIN_MONTHS)}
    diff = paired_diff(v_ret, c0_ret)
    ci = rs.cluster_ci_mean(diff.values, month_labels(diff.index), alpha=alpha) if len(diff) > 60 else None
    d['P2_net_edge_vs_C0'] = {'mean_daily_diff_pct': round(float(diff.mean()) * 100, 5) if len(diff) else None,
                              'ci_pct': [round(ci[0] * 100, 5), round(ci[1] * 100, 5)] if ci else None, 'alpha': alpha,
                              'pass': bool(ci and ci[0] > 0)}
    yv, yc = mx.yearly_returns(v_ret), mx.yearly_returns(c0_ret)
    blocks = [y for y in BLOCK_YEARS if y in yv and y in yc]
    wins = sum(yv[y] > yc[y] for y in blocks)
    d['P3_consistency'] = {'blocks': len(blocks), 'variant_beats_C0': int(wins), 'by_year': {y: [round(yv[y] * 100, 1), round(yc[y] * 100, 1)] for y in blocks},
                           'pass': bool(len(blocks) >= N_BLOCKS and wins >= MIN_BLOCKS_WON)}
    cagr = (v_port.get('portfolio') or {}).get('cagr_pct')
    d['P4_absolute'] = {'net_cagr_pct': cagr, 'pass': bool(cagr is not None and cagr > 0)}
    return all(x['pass'] for x in d.values()), d


def evaluate_holdout(v_m, c_m):
    vp, cp = v_m.get('portfolio') or {}, c_m.get('portfolio') or {}
    o1 = bool(vp.get('calmar') is not None and cp.get('calmar') is not None and vp['calmar'] >= cp['calmar'])
    o2 = bool(vp.get('cagr_pct') is not None and vp['cagr_pct'] > 0)
    o3 = bool(vp.get('max_drawdown_pct') is not None and cp.get('max_drawdown_pct') is not None and vp['max_drawdown_pct'] >= cp['max_drawdown_pct'] - 2.0)
    return (o1 and o2 and o3), {'O1_calmar_ge_C0': o1, 'O2_net_cagr_positive': o2, 'O3_dd_within_2pp': o3, 'variant': vp, 'C0': cp}


def score_diagnostics(design_trades):
    t = design_trades
    if len(t) < 60:
        return {'note': 'fewer than 60 design trades'}
    cl = rs.month_clusters(t)
    sp = rs.boot_spearman(t['score'].values, t['r'].values, cl)
    gap = rs.tercile_gap(t['score'].values, t['r'].values, cl)
    pred = bool(sp and sp[1] > 0 and gap and gap[1] > 0)
    return {'spearman_score_vs_R_with_ci': sp, 'top_minus_bottom_tercile_R_with_ci': gap, 'score_predictive': pred,
            'conclusion': 'score predicts R' if pred else 'no reliable evidence that the 0-100 score predicts R: it is a qualifier, not a conviction measure'}


def benchmark_block(frames, bench, c0_ret, c0_port, lo, hi):
    import benchmarks as bm
    closes = pd.DataFrame({s: df['Close'].astype(float) for s, df in frames.items()}).sort_index()
    ew = closes.pct_change().mean(axis=1)
    mom, _ = bm.momentum_portfolio(closes)
    nifty = bench.astype(float).pct_change() if bench is not None else None
    sl = lambda r: r[(r.index >= pd.Timestamp(lo)) & ((r.index <= pd.Timestamp(hi)) if hi else True)]
    out = {'C0 (net, realistic costs)': mx.perf(c0_ret)}
    expo = (c0_port.get('exposure') or {}).get('avg_exposure_pct')
    vol = (mx.perf(c0_ret) or {}).get('vol_pct')
    for name, r in (('Equal-weight universe', ew), ('Momentum-30 replica', mom), ('Nifty 50', nifty)):
        if r is None or len(r) == 0 or not isinstance(r.index, pd.DatetimeIndex):
            continue
        r = sl(r)
        out[name] = mx.perf(r)
        if expo:
            out[f'{name}, exposure-matched ({expo}% invested, cash 0%)'] = mx.perf(mx.exposure_matched(r, expo))
        if vol:
            out[f'{name}, volatility-matched to C0 ({vol}%)'] = mx.perf(mx.vol_matched(r, vol))
    return out


def run(frames, bench, prepared=None, spec=None, holdout_log=None, data_cutoff=None, ts=None):
    spec = spec or prereg.load()
    alpha = prereg.alpha_per_test(spec)
    design_end, ho_start = spec['windows']['design_end'], spec['windows']['holdout_start']
    prepared = prepared if prepared is not None else bt.prepare(frames)
    cutoff = data_cutoff or str(max(df.index[-1] for df in frames.values()).date())
    cfg = realistic_cfg()
    base = bt.generate_trades(frames, cfg, bench, prepared)
    rank = momentum_rank(prepared)

    c0_design = window(base, None, design_end)
    _, c0_dret, c0_dm = run_port(frames, c0_design, cfg)
    c0_ho = window(base, ho_start)
    _, c0_hret, c0_hm = run_port(frames, c0_ho, cfg)
    legacy_cfg = strategy.backtest_config()
    legacy = bt.generate_trades(frames, legacy_cfg, bench, prepared)
    _, _, c0_legacy_m = run_port(frames, window(legacy, None, design_end), legacy_cfg)

    results = []
    for h in spec['hypotheses']:
        vcfg, v_all = cfg, None
        if h['id'] == 'H7':
            vcfg, v_all = realistic_cfg(risk_pct=h['param']['risk_pct']), base
        elif h['id'] == 'H8':
            vcfg = realistic_cfg(max_hold=h['param']['max_hold'])
            v_all = bt.generate_trades(frames, vcfg, bench, prepared)
        else:
            v_all = apply_filter(h, base, rank)
        v_design = window(v_all, None, design_end)
        _, v_ret, v_m = run_port(frames, v_design, vcfg)
        passed, detail = evaluate_design(h, v_design, v_ret, c0_dret, alpha, v_m)
        rec = {'id': h['id'], 'name': h['name'], 'change': h['change'], 'param': h['param'], 'design': v_m,
               'design_criteria': detail, 'design_passed': passed, 'holdout_opened': False, 'holdout_passed': None, 'adopted_as_candidate': False}
        if passed:
            hg.open_once(h['id'], spec['_hash'], cutoff, holdout_log, ts)              # logged BEFORE any hold-out number is computed
            _, _, v_hm = run_port(frames, window(v_all, ho_start), vcfg)
            ho_ok, ho_detail = evaluate_holdout(v_hm, c0_hm)
            hg.record_result(h['id'], spec['_hash'], ho_ok, ho_detail, holdout_log, ts)
            rec.update({'holdout_opened': True, 'holdout': v_hm, 'holdout_criteria': ho_detail, 'holdout_passed': ho_ok, 'adopted_as_candidate': ho_ok})
        else:
            rec['failed_because'] = [k for k, v in detail.items() if not v['pass']]
        results.append(rec)

    out = {
        'provenance': provenance.make('experiments', data_cutoff=cutoff, extra={'prereg': spec['id'], 'prereg_hash': spec['_hash']}),
        'control': {'id': 'C0', 'design': c0_dm, 'holdout': c0_hm, 'design_legacy_costs': c0_legacy_m},
        'hypotheses': results,
        'adopted_candidates': [r['id'] for r in results if r['adopted_as_candidate']],
        'c0_retained': not any(r['adopted_as_candidate'] for r in results),
        'score_diagnostics': score_diagnostics(c0_design),
        'benchmarks_design': benchmark_block(frames, bench, c0_dret, c0_dm, '2000-01-01', design_end),
        'benchmarks_holdout_reference_only': benchmark_block(frames, bench, c0_hret, c0_hm, ho_start, None) if len(c0_hret) > 20 else None,
        'universe': {'version': provenance.universe_info()['version'], 'symbols_with_data': len(frames), 'survivorship_bias': True},
    }
    return out


def _fmt(p):
    return '—' if not p else f"{p['cagr_pct']}% / {p['max_drawdown_pct']}% / Calmar {p['calmar']}"


def markdown(rep):
    pv = rep['provenance']
    L = ['# Pre-registered experiments (PREREG_v1)', '',
         f"Universe {pv['universe_version']} ({rep['universe']['symbols_with_data']} symbols with data, survivorship bias present), data cutoff {pv['data_cutoff']}, "
         f"commit {pv['commit_sha'][:10]}, pre-registration `{pv['prereg_hash'][:12]}`. Realistic execution model; Bonferroni family of 8.", '',
         f"**C0 retained: {'yes' if rep['c0_retained'] else 'NO — see candidates'}.** Candidates adopted for forward testing: {rep['adopted_candidates'] or 'none'}.", '',
         '| ID | Change | Design net (CAGR / maxDD / Calmar) | P1 sample | P2 net edge vs C0 (CI of daily diff, %) | P3 yrs better | P4 | Hold-out | Result |',
         '|---|---|---|---|---|---|---|---|---|']
    c = rep['control']['design']['portfolio']
    L.append(f"| C0 | control | {_fmt(c)} | — | — | — | — | — | control |")
    for r in rep['hypotheses']:
        d = r['design_criteria']
        ho = 'not opened' if not r['holdout_opened'] else ('passed' if r['holdout_passed'] else 'FAILED')
        res = 'candidate' if r['adopted_as_candidate'] else 'failed' + (' (' + ', '.join(r.get('failed_because', [])) + ')' if r.get('failed_because') else ' at hold-out')
        L.append(f"| {r['id']} | {r['name']} | {_fmt(r['design'].get('portfolio'))} | {d['P1_sample']['trades']} tr / {d['P1_sample']['months']} mo "
                 f"| {d['P2_net_edge_vs_C0']['ci_pct']} | {d['P3_consistency']['variant_beats_C0']}/{d['P3_consistency']['blocks']} | {d['P4_absolute']['net_cagr_pct']} | {ho} | {res} |")
    sd = rep['score_diagnostics']
    L += ['', '## Score predictiveness (design window)', '', f"{sd.get('conclusion', sd.get('note'))}. Spearman {sd.get('spearman_score_vs_R_with_ci')}, tercile gap {sd.get('top_minus_bottom_tercile_R_with_ci')}.",
          '', '## C0 versus same-universe benchmarks (design window; net of costs for C0)', '', '| Series | CAGR % | MaxDD % | Calmar | Sharpe | Sortino |', '|---|---|---|---|---|---|']
    for k, v in rep['benchmarks_design'].items():
        if v:
            L.append(f"| {k} | {v['cagr_pct']} | {v['max_drawdown_pct']} | {v['calmar']} | {v['sharpe']} | {v['sortino']} |")
    L += ['', 'Hold-out (2025+) figures for C0 and the benchmarks are in the JSON as reference only; C0 was selected using data that includes this period.',
          '', 'Failed variants stay in this report and in reports/experiments/history/. Passing a pre-registered test is a reason for forward paper testing, not for live capital.']
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, default=10)
    ap.add_argument('--cache', default='history_cache.pkl')
    ap.add_argument('--out', default='reports')
    a = ap.parse_args()
    spec = prereg.load()                                         # raises if the registration was modified
    frames, bench = bt.load_history(a.years, a.cache)
    rep = run(frames, bench, spec=spec)
    os.makedirs(f'{a.out}/experiments/history', exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for path in (f'{a.out}/experiments.json', f'{a.out}/experiments/history/{stamp}_{spec["_hash"][:8]}.json'):
        with open(path, 'w') as f:
            json.dump(rep, f, indent=2, default=str)
    md = markdown(rep)
    with open(f'{a.out}/experiments.md', 'w') as f:
        f.write(md)
    with open(f'{a.out}/experiments/history/{stamp}_{spec["_hash"][:8]}.md', 'w') as f:
        f.write(md)
    evlog.append(f'{a.out}/experiments/runs.jsonl', 'experiment_run', stamp, {'prereg_hash': spec['_hash'], 'adopted': rep['adopted_candidates'],
                                                                            'c0_retained': rep['c0_retained']})
    print(md)


if __name__ == '__main__':
    main()
