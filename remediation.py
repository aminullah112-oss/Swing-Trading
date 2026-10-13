#!/usr/bin/env python3
"""Remediation matrix: for every readiness gate that is not passed, why, who can clear it, what it depends on and what it
would be worth. Reads readiness.json (and the baseline reports); changes no weight, criterion or score.

'Expected contribution' is stated ONLY when the gate can genuinely be passed by the action named. A gate whose evidence
currently points to failure is listed with contribution 0 and the reason, because promising points that the evidence does
not support is exactly the mistake this programme exists to prevent."""
import json
import os

import readiness as rd

OWNER = {'blocked_defect': 'Engineering / operator (rerun workflow)', 'pending_time': 'Calendar time (cannot be accelerated)',
         'unverifiable': 'Operator attestation of a real-world fact', 'failed': 'Strategy research (evidence says no)', 'passed': '—'}

ACTION = {
    'B1': ('Run the Backtest workflow so reports are stamped with the current evidence_hash.', 'Workflow run; universe U159_v2 unchanged.',
           'reports/provenance.json matches evidence_hash, is < 45 days old, and the live variant passes G1-G3.'),
    'U1': ('Rerun the Backtest workflow, then judge the hold-out. Frozen numbers show C0 Calmar 0.42 against momentum-30 1.05 and equal-weight 0.83.',
           'Fresh stamped benchmarks.json.', 'C0 hold-out Calmar >= every same-universe benchmark. On the frozen numbers it is not: do not expect these points.'),
    'B2': ('Build a point-in-time membership file (index reconstitution notices) and delisted-stock prices; set EDGE_PIT_UNIVERSE; rerun Backtest; then attest.',
           'External data (NSE index notices, bhavcopy for delisted names) that this environment cannot fetch.',
           'reports/pit_acceptance.json passes (coverage >= 95%, departed stocks with prices) AND the rerun passes the same gates AND attestations.json is set by the operator.'),
    'F1': ('Run the daily screen and ledger for months. No shortcut exists.', 'Signals arriving and resolving.', '>= 100 closed evidence-eligible signals.'),
    'F2': ('Wait. The clock starts at the first evidence-eligible signal recorded under the fail-closed pipeline.', 'Calendar.', '>= 182 days since the first eligible signal.'),
    'F3': ('Accumulate forward data after F1/F2.', 'F1, F2.', 'Month-clustered 95% CI lower bound of forward expectancy (closed + open) > 0.'),
    'F4': ('Accumulate forward data after F1/F2.', 'F1, F2, B1.', 'Forward CI upper bound >= backtest design-period average R.'),
    'E1': ('Needs real fills, therefore a live trial, which needs explicit operator authorisation and every safety gate. Not available in paper mode.',
           'Operator authorisation; micro-live prerequisites.', '>= 30 real fills in live_fills.csv with slippage within 2x the model.'),
    'S1': ('Needs a >= 10% Nifty drawdown to occur during the forward record, with the rules followed. Cannot be created or backdated.', 'Market event.',
           'Operator attests market_stress_observed after it has actually happened.'),
    'O1': ('Run the Daily Stock Screen on a day the vendor has published the official bars; health must be OK/WARN with trusted data and consistent artefacts.',
           'Vendor publishes daily bars; Yahoo reachable from Actions.', 'health OK/WARN, data_quality TRUSTED, no inconsistencies.'),
    'R1': ('Already within bounds.', '—', 'risk/trade <= 1%, open risk <= 3%, position <= 25%.'),
}


def build(readiness):
    rows = []
    for g in readiness['gates']:
        act, dep, acc = ACTION[g['id']]
        state = g.get('evidence_state', rd.evidence_state(g['id'], g['status']))
        rows.append({'id': g['id'], 'label': g['label'], 'weight': g['points'], 'critical': g['critical'], 'status': g['status'],
                     'state': state, 'owner': OWNER[state], 'action': act, 'depends_on': dep, 'acceptance': acc, 'detail': g.get('detail', '')})
    # What could realistically be earned soon vs. only with time/events. U1 is excluded while the evidence points to failure.
    near = [r for r in rows if r['state'] == 'blocked_defect' and r['id'] != 'U1']
    expected_now = sum(r['weight'] for r in rows if r['state'] == 'passed') + sum(r['weight'] for r in near)
    return {'gates': rows, 'score_now': readiness['policy']['score'], 'ceiling_after_reruns': round(expected_now, 2),
            'u1_note': 'U1 excluded from the near-term ceiling: the frozen hold-out comparison shows C0 below momentum-30 and equal-weight on Calmar.'}


def markdown(rep):
    L = ['# Remediation matrix', '', f"Score now: **{rep['score_now']}/10**. Ceiling reachable by reruns and operator action alone: **{rep['ceiling_after_reruns']}/10**. "
         f"{rep['u1_note']}", '',
         '| Gate | Weight | State | Owner | Action | Depends on | Acceptance |', '|---|---|---|---|---|---|---|']
    for r in rep['gates']:
        L.append(f"| {r['id']}{' ⚠' if r['critical'] else ''} | {r['weight']:g} | {r['state']} | {r['owner']} | {r['action']} | {r['depends_on']} | {r['acceptance']} |")
    L += ['', '⚠ = critical gate. States: passed, failed (evidence says no), blocked_defect (we can fix by rerunning or repairing), pending_time, unverifiable (needs a human fact).']
    return '\n'.join(L)


def main():
    with open('readiness.json') as f:
        rep = build(json.load(f))
    os.makedirs('reports', exist_ok=True)
    with open('reports/remediation.json', 'w') as f:
        json.dump(rep, f, indent=2)
    with open('reports/remediation.md', 'w') as f:
        f.write(markdown(rep))
    print(markdown(rep))


if __name__ == '__main__':
    main()
