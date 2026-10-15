#!/usr/bin/env python3
"""Daily paper-trade update: log today's signals, then advance every open one with fresh prices.
Runs after screener.py in the same workflow. Downloads only the symbols it needs."""
import json, os, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import analysis
import provenance as prov
import events as evlog
import screener as sc
import ledger as lg

LEDGER = 'ledger.json'
EVENTS = 'events.jsonl'


def fetch_frames(symbols):
    if not symbols:
        return {}
    import yfinance as yf
    ticks = [f'{s}.NS' for s in symbols]
    data = None
    for _ in range(3):
        try:
            data = yf.download(tickers=ticks, period='2y', interval='1d', group_by='ticker',
                               auto_adjust=True, progress=False, threads=True, timeout=60)
            if data is not None and not data.empty:
                break
        except Exception as e:
            print('download error:', e)
    if data is None or data.empty:
        return None
    frames = {}
    for s in symbols:
        df = sc.extract_df(data, f'{s}.NS')
        if df is not None:
            frames[s] = df
    return frames


def main():
    with open('results.json') as f:
        results = json.load(f)
    ok_chain, n_ev, problem = evlog.verify(EVENTS)
    if not ok_chain:
        print(f'FATAL: event log failed verification ({problem}); refusing to update the ledger.')
        sys.exit(2)
    holidays = analysis.load_holidays()
    now = datetime.now(timezone.utc)
    ts = now.isoformat(timespec='seconds')
    expected = analysis.expected_last_session(now.astimezone(ZoneInfo('Asia/Kolkata')), holidays=holidays)
    ledger = lg.load(LEDGER)
    migrated = lg.migrate(ledger, EVENTS, ts, holidays)
    if migrated:
        print(f'Migrated {migrated} legacy ledger records (kept, flagged evidence_eligible=False).')
    added0 = lg.add_signals(ledger, results, EVENTS, ts, holidays)      # idempotent; shows what is active before fetching
    need = sorted({r['symbol'] for r in ledger['signals'] if r['status'] in lg.ACTIVE})
    frames = fetch_frames(need)
    if frames:
        import dataquality
        frames = {k: dataquality.through(df, expected) for k, df in frames.items()}      # never simulate fills on the unfinished session
    ok = frames is not None
    if frames is None:
        print('WARNING: price download failed; signals logged but statuses not advanced.')
        frames = {}
    _, changed = lg.refresh(ledger, results, frames, sc.CAPITAL, sc.MAX_OPEN_RISK, events=EVENTS, ts=ts,
                            expected_session=expected, holidays=holidays)
    added = added0
    rec = lg.reconcile(ledger, evlog.read(EVENTS), expected, holidays)
    ledger['reconciliation'] = {'ok': rec['ok'], 'issues': rec['issues'][:50], 'checked': ts}
    ledger['updated'] = ts
    ledger['last_update_ok'] = ok
    ledger['provenance'] = prov.make('ledger', data_cutoff=results.get('data_cutoff'), sources={'results': 'results.json'}, extra={'scan_id': results.get('scan_id')})
    lg.save(ledger, LEDGER)
    s = ledger['summary']
    print(f"Ledger: {s['signals']} signals | pending {s['pending']} open {s['open']} closed {s['closed']} "
          f"expired {s['expired']} rejected {s['rejected']} | added {added}, updated {changed} | "
          f"reconciliation {'OK' if rec['ok'] else str(len(rec['issues'])) + ' issue(s)'}")
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
