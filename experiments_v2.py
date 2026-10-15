#!/usr/bin/env python3
"""PREREG_v2 runner: sector cap (V2-1), preferred-tier stack (V2-2), volatility-scaled risk (V2-3) against control C0.

Same discipline as experiments.py (PREREG_v1): realistic costs, walk-forward by calendar year, Bonferroni over the whole family
(v1 + earlier benchmark tests + these), once-only hold-out, every run kept. V2-1 and V2-3 reduce risk by construction, so they may
also pass on a registered RISK route: design and hold-out drawdown no worse than C0's and Calmar not lower. See PREREG_v2.json."""
import argparse
import json
import os
from datetime import datetime, timezone

import pandas as pd

import backtest as bt
import events as evlog
import experiments as ex
import holdout_guard as hg
import metrics as mx
import prereg
import provenance
import selection


def trade_set(h, base, prepared, sectors, rank):
    """(trades, port_kwargs) for a hypothesis. Filters only remove trades; the rest are untouched."""
    p = h['param']
    if h['id'] == 'V2-1':
        t = base.copy()
        t['sector'] = [selection.sector_of(s, sectors) for s in t['symbol']]
        return t, {'group_col': 'sector', 'max_per_group': p['max_per_sector']}
    if h['id'] == 'V2-2':
        r = pd.Series([rank.at[d, s] if d in rank.index else float('nan') for s, d in zip(base['symbol'], base['signal_date'])], index=base.index)
        keep = ((r >= p['min_rank']) & (base['from_52h'] >= p['min_from_52h_pct']) & (base['adv20_value'] >= p['min_adv20_value'])
                & (base['atr_pct'] <= p['max_atr_pct']) & (base['regime'] == p['regime']))
        return base[keep], {}
    if h['id'] == 'V2-3':
        t = base.copy()
        t['risk_mult'] = (t['atr_pct'] > p['atr_pct_threshold']).map({True: p['risk_multiplier'], False: 1.0})
        return t, {'risk_col': 'risk_mult'}
    raise ValueError(h['id'])


def run_port(frames, trades, cfg, **kw):
    if trades.empty:
        return {'accepted': 0}, pd.Series(dtype=float), {'portfolio': None}
    stats, eq, taken = bt.portfolio(frames, trades, cfg, detail=True, **kw)
    ret = eq.pct_change().dropna() if len(eq) else pd.Series(dtype=float)
    return stats, ret, mx.full(ret, trades['r'].values, taken, eq, stats)


DD_GAIN_PP, CALMAR_GAIN = 1.0, 0.05           # PREREG_v2.risk_reduction_rule: ties do not pass


def _risk_ok(v_m, c_m):
    v, c = v_m.get('portfolio') or {}, c_m.get('portfolio') or {}
    if not (v and c) or v.get('max_drawdown_pct') is None or c.get('max_drawdown_pct') is None:
        return False
    no_worse = v['max_drawdown_pct'] >= c['max_drawdown_pct'] and (v.get('calmar') or 0) >= (c.get('calmar') or 0)
    better = v['max_drawdown_pct'] >= c['max_drawdown_pct'] + DD_GAIN_PP or (v.get('calmar') or 0) >= (c.get('calmar') or 0) + CALMAR_GAIN
    return bool(no_worse and better)


def risk_route_design(v_m, c_m, p1, p4):
    """Registered second route for risk-reducing layers: drawdown no worse, Calmar not lower, and a real gain in one of them."""
    v, c = v_m.get('portfolio') or {}, c_m.get('portfolio') or {}
    ok = _risk_ok(v_m, c_m)
    return bool(ok and p1 and p4), {'design_dd': [v.get('max_drawdown_pct'), c.get('max_drawdown_pct')], 'design_calmar': [v.get('calmar'), c.get('calmar')], 'pass': bool(ok and p1 and p4)}


def risk_route_holdout(v_m, c_m):
    return _risk_ok(v_m, c_m)


def run(frames, bench, prepared=None, spec=None, holdout_log=None, data_cutoff=None, ts=None):
    spec = spec or prereg.load('PREREG_v2')
    alpha = prereg.alpha_per_test(spec)
    design_end, ho_start = spec['windows']['design_end'], spec['windows']['holdout_start']
    prepared = prepared if prepared is not None else bt.prepare(frames)
    cutoff = data_cutoff or str(max(df.index[-1] for df in frames.values()).date())
    cfg = ex.realistic_cfg()
    fd, bd, pd_ = ex.design_view(frames, bench, prepared, design_end)          # design numbers never see post-design prices (review F6)
    base_d = bt.generate_trades(fd, cfg, bd, pd_)
    base = bt.generate_trades(frames, cfg, bench, prepared)
    rank_d, rank, sectors = ex.momentum_rank(pd_), ex.momentum_rank(prepared), selection.load_sectors()
    _, c0_dret, c0_dm = run_port(fd, ex.window(base_d, None, design_end), cfg)
    _, _, c0_hm = run_port(frames, ex.window(base, ho_start), cfg)
    out_h = []
    for h in spec['hypotheses']:
        t_all_d, kw = trade_set(h, base_d, pd_, sectors, rank_d)
        vcfg = cfg
        t_design = ex.window(t_all_d, None, design_end)
        _, v_ret, v_m = run_port(fd, t_design, vcfg, **kw)
        main_ok, detail = ex.evaluate_design(h, t_design, v_ret, c0_dret, alpha, v_m)
        risk_reducing = h['id'] in ('V2-1', 'V2-3')
        route_ok, route = (False, None)
        if risk_reducing:
            route_ok, route = risk_route_design(v_m, c0_dm, detail['P1_sample']['pass'], detail['P4_absolute']['pass'])
        passed = main_ok or route_ok
        rec = {'id': h['id'], 'name': h['name'], 'change': h['change'], 'param': h['param'], 'design': v_m, 'design_criteria': detail,
               'risk_route': route, 'design_passed': passed, 'passed_via': 'return edge' if main_ok else ('risk route' if route_ok else None),
               'holdout_opened': False, 'holdout_passed': None, 'adopted_as_candidate': False}
        if passed:
            hg.open_once(h['id'], spec['_hash'], cutoff, holdout_log, ts)
            t_all, kw = trade_set(h, base, prepared, sectors, rank)
            _, _, v_hm = run_port(frames, ex.window(t_all, ho_start), vcfg, **kw)
            ho_ok, ho_detail = ex.evaluate_holdout(v_hm, c0_hm)
            if rec['passed_via'] == 'risk route':
                ho_ok = ho_ok and risk_route_holdout(v_hm, c0_hm)
                ho_detail['risk_route_holdout_ok'] = risk_route_holdout(v_hm, c0_hm)
            hg.record_result(h['id'], spec['_hash'], ho_ok, ho_detail, holdout_log, ts)
            rec.update({'holdout_opened': True, 'holdout': v_hm, 'holdout_criteria': ho_detail, 'holdout_passed': ho_ok, 'adopted_as_candidate': ho_ok})
        else:
            rec['failed_because'] = [k for k, v in detail.items() if not v['pass']]
        out_h.append(rec)
    return {'provenance': provenance.make('experiments_v2', data_cutoff=cutoff, extra={'prereg': spec['id'], 'prereg_hash': spec['_hash']}),
            'control': {'id': 'C0', 'design': c0_dm, 'holdout': c0_hm}, 'hypotheses': out_h,
            'adopted_candidates': [r['id'] for r in out_h if r['adopted_as_candidate']],
            'c0_retained': not any(r['adopted_as_candidate'] for r in out_h),
            'earlier_failed_ideas': spec['previously_tested_and_failed_not_retested'],
            'universe': {'version': provenance.universe_info()['version'], 'symbols_with_data': len(frames), 'survivorship_bias': True}}


def markdown(rep):
    pv = rep['provenance']
    L = ['# Pre-registered selection experiments (PREREG_v2)', '',
         f"Universe {pv['universe_version']} ({rep['universe']['symbols_with_data']} symbols, survivorship bias present), data cutoff {pv['data_cutoff']}, "
         f"pre-registration `{pv['prereg_hash'][:12]}`. Realistic costs; Bonferroni over 13 tests. **C0 retained: {'yes' if rep['c0_retained'] else 'NO'}.** "
         f"Candidates: {rep['adopted_candidates'] or 'none'}.", '',
         '| ID | Change | Design net (CAGR / maxDD / Calmar) | Trades / months | Passed via | Hold-out | Result |', '|---|---|---|---|---|---|---|']
    L.append(f"| C0 | control | {ex._fmt(rep['control']['design']['portfolio'])} | — | — | — | control |")
    for r in rep['hypotheses']:
        d = r['design_criteria']['P1_sample']
        ho = 'not opened' if not r['holdout_opened'] else ('passed' if r['holdout_passed'] else 'FAILED')
        res = 'candidate' if r['adopted_as_candidate'] else 'failed' + (' (' + ', '.join(r.get('failed_because', [])) + ')' if r.get('failed_because') else ' at hold-out')
        L.append(f"| {r['id']} | {r['name']} | {ex._fmt(r['design'].get('portfolio'))} | {d['trades']} / {d['months']} | {r['passed_via'] or '—'} | {ho} | {res} |")
    L += ['', '## Already tested, failed, not retested', ''] + [f"- {x['idea']} ({x['where']}): {x['result']}. Live default: {x['live_default']}" for x in rep['earlier_failed_ideas']]
    L += ['', 'Every run is kept in reports/experiments/history/. A pass is a reason for forward paper testing only.']
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, default=12)
    ap.add_argument('--cache', default='history_cache_12y.pkl')
    ap.add_argument('--out', default='reports')
    a = ap.parse_args()
    spec = prereg.load('PREREG_v2')
    frames, bench = bt.load_history(a.years, a.cache)
    rep = run(frames, bench, spec=spec)
    os.makedirs(f'{a.out}/experiments/history', exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    md = markdown(rep)
    for path, body in ((f'{a.out}/experiments_v2.json', json.dumps(rep, indent=2, default=str)), (f'{a.out}/experiments_v2.md', md),
                       (f'{a.out}/experiments/history/{stamp}_v2_{spec["_hash"][:8]}.json', json.dumps(rep, indent=2, default=str)),
                       (f'{a.out}/experiments/history/{stamp}_v2_{spec["_hash"][:8]}.md', md)):
        with open(path, 'w') as f:
            f.write(body)
    evlog.append(f'{a.out}/experiments/runs.jsonl', 'experiment_run', stamp, {'prereg_hash': spec['_hash'], 'adopted': rep['adopted_candidates'], 'c0_retained': rep['c0_retained']})
    print(md)


if __name__ == '__main__':
    main()
