#!/usr/bin/env python3
"""Write reports/pit_acceptance.json: whether the backtest universe is point-in-time (see pit.acceptance)."""
import argparse
import json
import os

import backtest as bt
import pit
import provenance


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, default=10)
    ap.add_argument('--cache', default='history_cache.pkl')
    ap.add_argument('--out', default='reports')
    a = ap.parse_args()
    frames, _ = bt.load_history(a.years, a.cache)
    res = pit.acceptance(pit.from_env(), frames)
    res['provenance'] = provenance.make('pit_acceptance')
    os.makedirs(a.out, exist_ok=True)
    with open(f'{a.out}/pit_acceptance.json', 'w') as f:
        json.dump(res, f, indent=2, default=str)
    print(json.dumps({k: v for k, v in res.items() if k != 'provenance'}, indent=2, default=str))


if __name__ == '__main__':
    main()
