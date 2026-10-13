#!/usr/bin/env python3
"""Go-live readiness scorecard. The 'fit for real money' rating, computed from evidence.

Points are earned only by verified evidence. Facts the code cannot check (survivorship-free test,
market stress, correct capital) come from attestations.json and default to "no". Nothing here is
tuned to produce a nicer number: every threshold below was fixed before it was ever evaluated.

Score (0-10) and the live-risk policy it implies:

    kill switch tripped, capital not confirmed, or live-loss budget used up -> PAPER ONLY (0% live risk)
    B1, O1, R1 pass and micro_live_acknowledged (attestations.json)       -> MICRO-LIVE: <= 0.05% risk/trade,
                                                                          an experiment that buys evidence about
                                                                          execution and starts a real forward
                                                                          record; it does NOT claim an edge exists
    4.5 <= score < 6.5 and forward gates F1-F3 pass                    -> FILL TEST: <= 0.10% risk/trade
                                                                          (to gather the live-fill evidence E1)
    6.5 <= score < 8   and B2, F3, F4 pass                              -> <= 0.25% risk/trade
    score >= 8         and every critical gate passes                   -> <= 0.50% risk/trade

The policy is a proposal for a cautious ramp, not a guarantee of profit. Edit it knowingly.
"""
import csv, json, os
from datetime import datetime, timezone

import numpy as np

import ledger as lg
import provenance as provn
import research as rs
import settings
import strategy

LIVE_LABEL = f'{strategy.TRIGGER}/{strategy.EXIT_MODE}/h{strategy.MAX_HOLD}'
MODEL_SLIPPAGE_BPS = 10.0            # per side, as in backtest.Config
MIN_CLOSED = 100
MIN_DAYS = 182
MIN_FILLS = 30
MICRO_RISK_PCT = 0.05          # % of capital risked per trade in the micro-live experiment
LIVE_LOSS_BUDGET_PCT = 2.0      # stop all live trading if net realised live loss reaches this % of capital
CLUSTER_ALPHA = 0.05

# id, label, points, critical
GATES = [
    ('B1', 'Live variant passes the pre-registered backtest gates', 0.5, False),
    ('U1', 'Beats buy-and-hold of the same universe AND a momentum-30 replica per unit of drawdown (hold-out)', 1.0, True),
    ('B2', 'Survivorship-free backtest passes the same gates (attested)', 1.5, True),
    ('F1', f'At least {MIN_CLOSED} closed forward signals', 1.0, False),
    ('F2', f'At least {MIN_DAYS} days of forward record', 1.0, False),
    ('F3', 'Forward expectancy (closed + open) has a 95% CI lower bound above 0', 1.5, True),
    ('F4', 'Forward expectancy is not clearly below the backtest design-period figure', 1.0, True),
    ('E1', f'At least {MIN_FILLS} live fills with slippage within 2x the model', 1.0, True),
    ('S1', 'Forward record includes a >=10% Nifty drawdown, rules followed (attested)', 0.5, False),
    ('O1', 'Operations healthy: no health FAIL and no data lag', 0.5, False),
    ('R1', 'Risk limits within safe bounds (risk/trade <= 1%, open risk <= 3%, position <= 25%)', 0.5, False),
]
assert abs(sum(g[2] for g in GATES) - 10.0) < 1e-9


# Why a gate has not passed. Used by the remediation matrix; it never changes a score.
#   passed          evidence satisfies the pre-registered criterion
#   failed          evidence exists and does not satisfy it
#   blocked_defect  cannot be evaluated because of an engineering/ops defect or stale evidence: fixable by us
#   pending_time    needs calendar time or more observations: cannot be accelerated
#   unverifiable    needs a human attestation or an external event the code cannot observe
TIME_GATES = ('F1', 'F2', 'F3', 'F4', 'E1')


def evidence_state(gid, status):
    if status == 'pass':
        return 'passed'
    if status == 'fail':
        return 'pending_time' if gid in ('F1', 'F2') else 'failed'
    if status == 'manual':
        return 'unverifiable'
    if status in ('stale', 'blocked'):
        return 'blocked_defect'
    return 'pending_time' if gid in TIME_GATES else 'blocked_defect'     # 'insufficient'


def _g(gid, status, value=None, threshold=None, detail=''):
    _, label, pts, crit = next(g for g in GATES if g[0] == gid)
    return {'id': gid, 'label': label, 'points': pts, 'critical': crit, 'status': status,
            'earned': pts if status == 'pass' else 0.0, 'value': value, 'threshold': threshold, 'detail': detail,
            'evidence_state': evidence_state(gid, status)}


def stale_evidence(ctx):
    """Reasons the backtest-derived reports (grid, benchmarks, universe) cannot be credited. Empty = current.
    Requires reports/provenance.json (written by stamp_reports.py) to match the current evidence_hash and universe, to be
    recent, and every covered report to still have the content id recorded when it was stamped."""
    rp = ctx.get('report_provenance')
    why = list(provn.problems(rp, 'backtest', ctx.get('now')))
    if rp and ctx.get('report_ids') is not None:
        for name, rid in (rp.get('source_ids') or {}).items():
            if ctx['report_ids'].get(name) != rid:
                why.append(f'report {name} changed since it was stamped ({rid} -> {ctx["report_ids"].get(name)})')
    return why


def consistency(ctx):
    """Cross-artefact consistency (health / ledger / scan / readiness inputs). Empty = consistent."""
    ids, res, led, health = ctx.get('artifact_ids'), ctx.get('results') or {}, ctx.get('ledger') or {}, ctx.get('health') or {}
    if ids is None:
        return []
    out = []
    lp = (led.get('provenance') or {})
    hp = (health.get('provenance') or {})
    if led.get('signals') and not lp:
        out.append('ledger.json has no provenance block')
    if lp.get('source_ids', {}).get('results') not in (None, ids.get('results')) :
        out.append('ledger.json was built from a different results.json than the current one')
    if hp and hp.get('source_ids', {}).get('results') != ids.get('results'):
        out.append('health.json was computed from a different results.json than the current one')
    if hp and hp.get('source_ids', {}).get('ledger') != ids.get('ledger'):
        out.append('health.json was computed from a different ledger.json than the current one')
    if res.get('provenance') and res['provenance'].get('universe_hash') != provn.universe_info()['hash']:
        out.append('results.json was produced for a different universe than the current one')
    return out


def live_variant(grid):
    for r in grid or []:
        if r.get('label') == LIVE_LABEL:
            return r
    return None


def forward_ci(ledger):
    rs_, months = lg.forward_returns(ledger)
    if len(rs_) < 2:
        return None, rs_, months
    ci = rs.cluster_ci_mean(rs_, months, alpha=CLUSTER_ALPHA)
    return ci, rs_, months


def fills_stats(fills):
    """fills: list of dict rows from live_fills.csv. Slippage in bps, positive = worse than planned."""
    ent, ext = [], []
    for f in fills:
        try:
            pe, ae = float(f['planned_entry']), float(f['actual_entry'])
            ent.append((ae - pe) / pe * 1e4)
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
        try:
            px, ax = float(f['planned_exit']), float(f['actual_exit'])
            ext.append((px - ax) / px * 1e4)
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            pass
    return {'n_entries': len(ent), 'n_exits': len(ext),
            'entry_slip_bps': round(float(np.mean(ent)), 1) if ent else None,
            'exit_slip_bps': round(float(np.mean(ext)), 1) if ext else None}


def evaluate(ctx):
    led, res, grid, att = ctx['ledger'], ctx.get('results') or {}, ctx.get('grid'), ctx.get('attest') or {}
    uni, fills, health = ctx.get('universe'), ctx.get('fills') or [], ctx.get('health') or {}
    now = ctx.get('now') or datetime.now(timezone.utc)
    out = []

    # --- backtest evidence (only if the reports are current for this code, config and universe)
    stale = stale_evidence(ctx)
    row = live_variant(grid)
    if stale:
        grid, row, uni = None, None, None
        ctx = dict(ctx, benchmarks={})
    out.append(_g('B1', 'stale' if stale else ('pass' if row and row.get('promising') else ('fail' if row else 'insufficient')),
                  value=f"G1/G2/G3 = {row['G1']}/{row['G2']}/{row['G3']}" if row else None, threshold='all three gates',
                  detail=('STALE EVIDENCE, no credit: ' + stale[0] + ' (rerun the Backtest workflow)') if stale
                  else f'variant {LIVE_LABEL}' + ('' if row else ' not found in reports/grid.json')))

    bm = ctx.get('benchmarks') or {}
    hold = (bm.get('periods') or {}).get('holdout') or {}
    s_b, ew_b, mom_b = hold.get('Live strategy (baseline)'), hold.get('Equal-weight universe'), hold.get('H1 momentum-30 replica')
    if s_b and ew_b and s_b.get('calmar') is not None and ew_b.get('calmar') is not None:
        rivals = {'universe buy-and-hold': ew_b['calmar']}
        if mom_b and mom_b.get('calmar') is not None:
            rivals['momentum-30 replica'] = mom_b['calmar']
        best = max(rivals.values())
        txt = ', '.join(f'{k} {v:.2f}' for k, v in rivals.items())
        out.append(_g('U1', 'pass' if s_b['calmar'] >= best else 'fail', value=f"strategy {s_b['calmar']:.2f} vs {txt}",
                      threshold='Calmar >= every same-universe benchmark (hold-out)',
                      detail=f"hold-out CAGR {s_b['cagr_pct']}% / DD {s_b['max_drawdown_pct']}% (reports/benchmarks.md)"))
    elif row and uni and (uni.get('holdout') or {}).get('equal_weight') and row.get('holdout_port_cagr') is not None:
        u = uni['holdout']['equal_weight']
        s_ratio = row['holdout_port_cagr'] / abs(row['holdout_port_maxdd']) if row['holdout_port_maxdd'] else float('inf')
        u_ratio = u['cagr_pct'] / abs(u['max_drawdown_pct']) if u['max_drawdown_pct'] else float('inf')
        out.append(_g('U1', 'pass' if s_ratio >= u_ratio else 'fail', value=f'strategy {s_ratio:.2f} vs universe {u_ratio:.2f}',
                      threshold='CAGR/|maxDD| >= universe',
                      detail=f"hold-out CAGR {row['holdout_port_cagr']}% / DD {row['holdout_port_maxdd']}% vs universe "
                             f"{u['cagr_pct']}% / {u['max_drawdown_pct']}% (run Backtest to add the momentum benchmark)"))
    else:
        out.append(_g('U1', 'stale' if stale else 'insufficient',
                      detail=('STALE EVIDENCE, no credit: ' + stale[0]) if stale else 'reports/benchmarks.json and universe.json missing: rerun the Backtest workflow'))

    # B2 needs the attestation AND the machine-checked point-in-time acceptance (reports/pit_acceptance.json): delisted names with
    # prices, >=95% coverage. A tightening of the original attestation-only gate; it can only withhold credit.
    pit_res = ctx.get('pit')
    pit_ok = bool(pit_res and pit_res.get('passed') and not stale)
    ok = bool(att.get('survivorship_free_backtest_passed')) and pit_ok
    if ok:
        out.append(_g('B2', 'pass', detail='attested and reports/pit_acceptance.json passed'))
    elif att.get('survivorship_free_backtest_passed') and not pit_ok:
        out.append(_g('B2', 'fail', detail='attested, but the point-in-time acceptance test did not pass: ' + '; '.join((pit_res or {}).get('reasons', ['reports/pit_acceptance.json missing or stale']))))
    else:
        out.append(_g('B2', 'manual', detail='survivorship bias remains: ' + '; '.join((pit_res or {}).get('reasons', ['no point-in-time universe tested'])[:2])
                      + ' (attestations.json: survivorship_free_backtest_passed also required)'))

    # --- forward evidence
    summ = led.get('summary') or {}
    # Only evidence-eligible signals count: legacy records pre-date the fail-closed data gate and are excluded.
    closed = summ.get('closed_eligible', summ.get('closed', 0))
    out.append(_g('F1', 'pass' if closed >= MIN_CLOSED else 'fail', value=closed, threshold=MIN_CLOSED,
                  detail=f"{summ.get('closed', 0) - closed} legacy closed signal(s) excluded" if summ.get('closed', 0) > closed else ''))
    started = summ.get('first_eligible_signal', led.get('started')) if 'closed_eligible' in summ else led.get('started')
    days = max(0, (now.date() - datetime.fromisoformat(str(started)[:10]).date()).days) if started else 0
    out.append(_g('F2', 'pass' if days >= MIN_DAYS else 'fail', value=days, threshold=MIN_DAYS))

    ci, rs_, months = forward_ci(led)
    enough = closed >= MIN_CLOSED and days >= MIN_DAYS and ci is not None
    if enough:
        out.append(_g('F3', 'pass' if ci[0] > 0 else 'fail', value=f'mean {rs_.mean():+.3f} CI [{ci[0]:+.3f}, {ci[1]:+.3f}]', threshold='lower bound > 0'))
        design = row['design_avg_r'] if row else None
        if design is None:
            out.append(_g('F4', 'insufficient', detail='no backtest figure to compare against'))
        else:
            out.append(_g('F4', 'pass' if ci[1] >= design else 'fail', value=f'CI upper {ci[1]:+.3f}', threshold=f'>= backtest design avg R {design:+.3f}'))
    else:
        why = f'needs {MIN_CLOSED}+ closed signals and {MIN_DAYS}+ days first (have {closed}, {days})'
        out.append(_g('F3', 'insufficient', detail=why))
        out.append(_g('F4', 'insufficient', detail=why))

    fs = fills_stats(fills)
    lim = 2 * MODEL_SLIPPAGE_BPS
    if fs['n_entries'] >= MIN_FILLS and fs['entry_slip_bps'] is not None:
        bad = fs['entry_slip_bps'] > lim or (fs['n_exits'] >= 10 and fs['exit_slip_bps'] is not None and fs['exit_slip_bps'] > lim)
        out.append(_g('E1', 'fail' if bad else 'pass', value=fs, threshold=f'<= {lim:g} bps per side'))
    else:
        out.append(_g('E1', 'insufficient', value=fs, threshold=f'{MIN_FILLS}+ fills in live_fills.csv'))

    out.append(_g('S1', 'pass' if att.get('market_stress_observed') else 'manual', detail='attestations.json: market_stress_observed'))

    # --- operations and risk
    hs = health.get('status')
    lagging = any(c.get('id') == 'H1b' for c in health.get('checks', []))
    incons = consistency(ctx)
    dq = res.get('data_quality') or {}
    if incons:
        out.append(_g('O1', 'blocked', value=hs, threshold='artefacts consistent', detail='inconsistent artefacts, regenerate: ' + '; '.join(incons[:3])))
    elif res and dq.get('status') == 'UNTRUSTED':
        out.append(_g('O1', 'fail', value=hs, threshold='trusted data',
                      detail='latest scan data UNTRUSTED (no actionable signals): ' + '; '.join(dq.get('reasons', [])[:2])))
    elif lagging:
        out.append(_g('O1', 'fail', value=hs, threshold='no data lag',
                      detail='market data is behind the expected session; a system that buys the session after a signal cannot be traded on stale bars'))
    else:
        out.append(_g('O1', 'pass' if hs in ('OK', 'WARN') else ('fail' if hs in ('FAIL', 'DEGRADED') else 'insufficient'), value=hs, threshold='OK/WARN',
                      detail='health DEGRADED/FAIL earns no operations credit' if hs in ('FAIL', 'DEGRADED') else ''))
    cfg = res.get('risk_config') or {}
    safe = bool(cfg) and cfg.get('risk_pct', 99) <= 1.0 and cfg.get('max_open_risk_pct', 99) <= 3.0 and cfg.get('max_pos_pct', 99) <= 25.0
    out.append(_g('R1', 'pass' if safe else ('fail' if cfg else 'insufficient'), value=cfg or None))
    return out


def live_budget(fills, capital):
    """Net realised P&L of closed live trades in live_fills.csv (needs shares, actual_entry, actual_exit)."""
    pnl, n = 0.0, 0
    for f in fills or []:
        try:
            sh, ae, ax = float(f['shares']), float(f['actual_entry']), float(f['actual_exit'])
        except (KeyError, TypeError, ValueError):
            continue
        pnl += sh * (ax - ae); n += 1
    budget = (capital or 0) * LIVE_LOSS_BUDGET_PCT / 100
    return {'closed_live_trades': n, 'net_pnl_inr': round(pnl, 2), 'loss_budget_inr': round(budget, 2),
            'exhausted': bool(budget > 0 and pnl <= -budget)}


def policy(gates, att, health, fills=None, capital=None):
    by = {g['id']: g for g in gates}
    score = round(sum(g['earned'] for g in gates), 2)
    p = lambda i: by[i]['status'] == 'pass'
    crit_ok = all(p(g['id']) for g in gates if g['critical'])
    reasons = []
    allowed = 0.0
    mode = 'PAPER ONLY'
    budget = live_budget(fills, capital)
    if health.get('status') in ('FAIL', 'DEGRADED') or settings.LIVE_EXECUTION_ENABLED:
        reasons.append(f"health {health.get('status')} (data/ledger untrusted, kill switch or broken pipeline)" if health.get('status') in ('FAIL', 'DEGRADED')
                       else 'LIVE_EXECUTION_ENABLED is True without authorisation')
    elif budget['exhausted']:
        reasons.append(f"live-loss budget used up: net {budget['net_pnl_inr']} INR vs limit -{budget['loss_budget_inr']} INR; review before resuming")
    elif not att.get('capital_confirmed'):
        reasons.append('capital not confirmed in attestations.json')
    elif score >= 8 and crit_ok:
        allowed, mode = 0.5, 'FULL (cap 0.50%)'
    elif score >= 6.5 and p('B2') and p('F3') and p('F4'):
        allowed, mode = 0.25, 'REDUCED (cap 0.25%)'
    elif score >= 4.5 and p('F1') and p('F2') and p('F3'):
        allowed, mode = 0.10, 'FILL TEST (cap 0.10%)'
    elif p('B1') and p('O1') and p('R1') and att.get('micro_live_acknowledged'):
        allowed, mode = MICRO_RISK_PCT, f'MICRO-LIVE experiment (cap {MICRO_RISK_PCT}%)'
    missing = [f"{g['id']} {g['label']}" for g in gates if g['status'] != 'pass']
    if allowed == 0 and not reasons:
        reasons.append(f'score {score} below the tier thresholds or required gates not passed')
        if not att.get('micro_live_acknowledged'):
            reasons.append('micro-live experiment not acknowledged in attestations.json (optional)')
    return {'score': score, 'mode': mode, 'live_risk_pct_allowed': allowed, 'reasons': reasons,
            'critical_gates_passed': crit_ok, 'unmet': missing, 'live_budget': budget}


def _load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def load_fills(path='live_fills.csv'):
    try:
        with open(path, newline='') as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def markdown(res):
    L = [f"# Readiness scorecard: {res['policy']['score']}/10 — {res['policy']['mode']}", '',
         f"Generated {res['generated']}. Live risk allowed: **{res['policy']['live_risk_pct_allowed']}%** per trade.", '',
         '| Gate | Points | Status | Value / detail |', '|---|---|---|---|']
    sym = {'pass': '✅ pass', 'fail': '❌ fail', 'insufficient': '⏳ not enough data', 'manual': '🖐 not attested', 'stale': '♻️ stale evidence', 'blocked': '🛠 blocked'}
    for g in res['gates']:
        d = g['value'] if g['value'] not in (None, '') else g['detail']
        if g['value'] not in (None, '') and g['detail']:
            d = f"{g['value']} — {g['detail']}"
        L.append(f"| {g['id']} {g['label']}{' **(critical)**' if g['critical'] else ''} | {g['earned']:g}/{g['points']:g} | {sym[g['status']]} | {d} |")
    if res['policy']['reasons']:
        L += ['', 'Why not higher: ' + '; '.join(res['policy']['reasons'])]
    L += ['', 'Points come only from verified evidence. Gates marked "not attested" need a human to set the flag in `attestations.json` once it is true.']
    return '\n'.join(L)


ARTEFACTS = {'results': 'results.json', 'ledger': 'ledger.json', 'health': 'health.json', 'grid': 'reports/grid.json',
             'benchmarks': 'reports/benchmarks.json', 'universe': 'reports/universe.json', 'attestations': 'attestations.json',
             'report_provenance': 'reports/provenance.json'}


def main():
    health = _load('health.json', {})
    ctx = {'ledger': _load('ledger.json', lg.empty()), 'results': _load('results.json', {}),
           'grid': _load('reports/grid.json'), 'universe': _load('reports/universe.json'), 'benchmarks': _load('reports/benchmarks.json'),
           'attest': _load('attestations.json', {}), 'fills': load_fills(), 'health': health,
           'report_provenance': _load('reports/provenance.json'), 'pit': _load('reports/pit_acceptance.json'),
           'report_ids': {k: provn.file_id(p) for k, p in __import__('stamp_reports').REPORTS.items()},
           'artifact_ids': {k: provn.file_id(p) for k, p in ARTEFACTS.items()}}
    gates = evaluate(ctx)
    pol = policy(gates, ctx['attest'], health, ctx['fills'], (ctx['results'].get('risk_config') or {}).get('capital'))
    res = {'generated': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'policy': pol, 'gates': gates,
           'inputs': ctx['artifact_ids'], 'stale_evidence': stale_evidence(ctx), 'inconsistencies': consistency(ctx),
           'provenance': provn.make('readiness', data_cutoff=ctx['results'].get('data_cutoff'), sources=ARTEFACTS)}
    with open('readiness.json.tmp', 'w') as f:
        json.dump(res, f, indent=2, default=str)
    os.replace('readiness.json.tmp', 'readiness.json')
    os.makedirs('reports', exist_ok=True)
    with open('reports/readiness.md', 'w') as f:
        f.write(markdown(res))
    print(markdown(res))


if __name__ == '__main__':
    main()
