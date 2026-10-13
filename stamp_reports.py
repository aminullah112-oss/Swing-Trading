#!/usr/bin/env python3
"""Stamp the backtest reports with provenance. Run as the LAST step of the Backtest workflow.

Writes reports/provenance.json: commit, evidence/config/C0 hash, universe version+hash, generation time and the content
id of every report it covers. Readiness gives backtest-derived credit (B1, U1) only when this stamp matches the current
evidence_hash, is recent, and every covered report still has the recorded content id (so a report replaced or edited
after the run is detected)."""
import json
import sys

import provenance as prov

REPORTS = {'grid': 'reports/grid.json', 'benchmarks': 'reports/benchmarks.json', 'universe': 'reports/universe.json',
           'regime': 'reports/regime.json', 'baseline': 'reports/backtest_baseline.json', 'trigger': 'reports/backtest_trigger.json',
           'pit': 'reports/pit_acceptance.json', 'experiments': 'reports/experiments.json'}


def main():
    missing = [k for k, p in REPORTS.items() if prov.file_id(p) is None]
    if missing:
        print(f'FAIL: reports missing, refusing to stamp: {missing}')
        return 1
    p = prov.make('backtest', sources=REPORTS)
    with open('reports/provenance.json', 'w') as f:
        json.dump(p, f, indent=2)
    print('stamped', p['evidence_hash'], p['universe_version'], p['generated_at'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
