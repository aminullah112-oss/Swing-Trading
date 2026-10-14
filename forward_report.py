#!/usr/bin/env python3
"""Forward-validation report from the paper ledger and the event log: every signal and its fate, with reasons.

Reads ledger.json and events.jsonl only. Nothing here is edited by hand, and nothing is invented: simulated fills are
labelled simulated, legacy (pre-fail-closed) records are listed but excluded from every statistic, and no number is shown
without the count behind it. Statistics need volume to mean anything; the report says how far from the readiness
thresholds the record is."""
import json
import os
from collections import Counter

import numpy as np

import events as evlog
import health as hl
import ledger as lg
import readiness as rd
import research as rs


def build(ledger, event_list, capital, now=None):
    sigs = ledger.get('signals', [])
    eligible = [s for s in sigs if s.get('evidence_eligible') is not False]
    legacy = [s for s in sigs if s.get('evidence_eligible') is False]
    status = Counter(s['status'] for s in eligible)
    rs_, months = lg.forward_returns(ledger)
    ci = rs.cluster_ci_mean(rs_, months) if len(rs_) >= 2 else None
    closed = [s for s in eligible if s['status'] == 'closed']
    # rolling expectancy over the last 30 / 60 closed signals
    ordered = sorted(closed, key=lambda s: s['exit_date'])
    roll = {k: round(float(np.mean([s['r'] for s in ordered[-k:]])), 3) for k in (30, 60) if len(ordered) >= k}
    dd, now_pct = hl.taken_equity(ledger, capital) if capital and sigs else (0.0, 0.0)
    gaps = [s for s in closed if s.get('gap_through_stop')]
    partial = [s for s in eligible if s.get('fill_ratio') is not None]
    summ = ledger.get('summary') or {}
    chain = evlog.verify('events.jsonl') if os.path.exists('events.jsonl') else (True, 0, None)
    return {
        'all_fills_simulated': True,
        'signals_total': len(sigs), 'evidence_eligible': len(eligible), 'legacy_excluded': len(legacy),
        'by_status': dict(status), 'not_taken_reasons': dict(Counter(s.get('not_taken_reason') for s in eligible if s.get('not_taken_reason'))),
        'closed': len(closed), 'forward_avg_r_incl_open': float(rs_.mean()) if len(rs_) else None,
        'forward_avg_r_ci95_clustered': [round(ci[0], 3), round(ci[1], 3)] if ci else None,
        'effective_independent_months': int(len(set(months))) if len(months) else 0,
        'rolling_expectancy_last_closed': roll, 'taken_equity_drawdown_pct': round(dd, 2), 'taken_equity_now_pct': round(now_pct, 2),
        'gap_through_stop_exits': len(gaps), 'partial_fills': len(partial),
        'readiness_distance': {'closed_needed': rd.MIN_CLOSED, 'closed_have': summ.get('closed_eligible', 0),
                               'days_needed': rd.MIN_DAYS, 'first_eligible_signal': summ.get('first_eligible_signal')},
        'event_log': {'verified': chain[0], 'events': chain[1], 'problem': chain[2]},
        'reconciliation': ledger.get('reconciliation'),
    }


def markdown(rep):
    c = rep['readiness_distance']
    L = ['# Forward validation (paper, simulated fills)', '',
         f"Signals recorded: {rep['signals_total']} ({rep['evidence_eligible']} evidence-eligible, {rep['legacy_excluded']} legacy excluded). "
         f"Event log: {'verified' if rep['event_log']['verified'] else 'FAILED: ' + str(rep['event_log']['problem'])} ({rep['event_log']['events']} events). "
         f"Every fill here is simulated; none is a broker fill.", '',
         f"By status: {rep['by_status'] or 'none yet'}.", '']
    if rep['not_taken_reasons']:
        L += ['Signals not taken, with reasons:', ''] + [f'- {k}: {v}' for k, v in rep['not_taken_reasons'].items()] + ['']
    L += [f"Closed eligible signals: {c['closed_have']} of {c['closed_needed']} needed; first eligible signal {c['first_eligible_signal']}; {c['days_needed']} days required.", '']
    if rep['forward_avg_r_incl_open'] is None:
        L.append('No entered, eligible signals yet: no expectancy can be stated.')
    else:
        L.append(f"Average R including open trades: {rep['forward_avg_r_incl_open']:+.3f} over {rep['effective_independent_months']} entry months; "
                 f"month-clustered 95% CI {rep['forward_avg_r_ci95_clustered']}. Rolling expectancy (last closed): {rep['rolling_expectancy_last_closed'] or 'needs 30+ closed'}.")
    L += ['', f"Taken-signal equity drawdown {rep['taken_equity_drawdown_pct']}% of capital (now {rep['taken_equity_now_pct']:+}%). "
          f"Gap-through-stop exits: {rep['gap_through_stop_exits']}. Partial fills: {rep['partial_fills']}.", '',
          'Interpretation: below ~100 closed signals over at least 182 days these figures say almost nothing about edge.']
    return '\n'.join(L)


def main():
    led = lg.load('ledger.json')
    res = json.load(open('results.json')) if os.path.exists('results.json') else {}
    rep = build(led, evlog.read('events.jsonl'), (res.get('risk_config') or {}).get('capital'))
    os.makedirs('reports', exist_ok=True)
    with open('reports/forward.json', 'w') as f:
        json.dump(rep, f, indent=2, default=str)
    with open('reports/forward.md', 'w') as f:
        f.write(markdown(rep))
    print(markdown(rep))


if __name__ == '__main__':
    main()
