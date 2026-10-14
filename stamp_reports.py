#!/usr/bin/env python3
"""Stamp the backtest reports with provenance. Run as the LAST step of the Backtest workflow.

Writes reports/provenance.json: commit, evidence/config/C0 hash, universe version+hash, generation time and the content
id of every report it covers. Readiness gives backtest-derived credit (B1, U1) only when this stamp matches the current
evidence_hash, is recent, and every covered report still has the recorded content id (so a report replaced or edited
after the run is detected)."""
import json
import os
import sys

import provenance as prov

REQUIRED = {'grid': 'reports/grid.json', 'benchmarks': 'reports/benchmarks.json', 'universe': 'reports/universe.json',
            'regime': 'reports/regime.json', 'baseline': 'reports/backtest_baseline.json', 'trigger': 'reports/backtest_trigger.json'}
OPTIONAL = {'pit': 'reports/pit_acceptance.json', 'experiments': 'reports/experiments.json'}     # stamped when present
REPORTS = {**REQUIRED, **OPTIONAL}


def main():
    # A stamp certifies that the reports were produced by the current code in THIS run. Stamping reports of unknown origin
    # (for example by hand, or from an older run) would manufacture provenance, so only the Backtest workflow may do it.
    if os.environ.get('GITHUB_WORKFLOW') != 'Backtest':
        print('REFUSED: reports can only be stamped inside the Backtest workflow (GITHUB_WORKFLOW=Backtest).')
        return 2
    missing = [k for k, p in REQUIRED.items() if prov.file_id(p) is None]
    if missing:
        print(f'FAIL: reports missing, refusing to stamp: {missing}')
        return 1
    p = prov.make('backtest', sources={k: v for k, v in REPORTS.items() if prov.file_id(v) is not None})
    with open('reports/provenance.json', 'w') as f:
        json.dump(p, f, indent=2)
    print('stamped', p['evidence_hash'], p['universe_version'], p['generated_at'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
