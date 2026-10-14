#!/usr/bin/env python3
"""How long, and how far, C0's past trades ran: reports/trades_c0.csv -> reports/hold_stats.json (written by the Backtest workflow).
Descriptive history on a survivor-biased universe, used only to give the trade desk a realistic expectation of duration."""
import json
import os
import sys

import numpy as np
import pandas as pd

import provenance


def _q(x, qs=(25, 50, 75)):
    x = np.asarray(x, dtype=float)
    return {f'p{q}': (round(float(np.percentile(x, q)), 2) if len(x) else None) for q in qs}


def _block(t):
    w, lo = t[t['r'] > 0], t[t['r'] <= 0]
    return {'n': int(len(t)), 'win_rate': round(float((t['r'] > 0).mean()), 3), 'days_winners': _q(w['hold']), 'days_losers': _q(lo['hold']),
            'days_all': _q(t['hold']), 'r_winners': _q(w['r'], (50, 75, 90)), 'r_losers': _q(lo['r'], (10, 50))}


def build(trades):
    t = trades.dropna(subset=['r', 'hold'])
    out = {'overall': _block(t) if len(t) else None, 'by_setup': {}}
    for k, g in t.groupby('setup'):
        if len(g) >= 10:
            out['by_setup'][k] = _block(g)
    out['provenance'] = provenance.make('hold_stats', extra={'trades': int(len(t)), 'note': 'C0 backtest trades, survivor-biased'})
    return out


def main(path='reports/trades_c0.csv', out='reports/hold_stats.json'):
    if not os.path.exists(path):
        print(f'{path} missing: run the Backtest workflow first')
        return 1
    res = build(pd.read_csv(path))
    with open(out, 'w') as f:
        json.dump(res, f, indent=2)
    print(f"hold stats from {res['provenance']['trades']} trades")
    return 0


if __name__ == '__main__':
    sys.exit(main())
