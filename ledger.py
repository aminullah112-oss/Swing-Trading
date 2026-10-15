"""Paper-trade ledger. Every scanner signal is logged and followed forward with the backtester's
own trade simulation (backtest.simulate_trade), so paper results and backtest results use one
definition of a trade. All fills here are SIMULATED (paper); none is a broker fill.

Lifecycle (TRANSITIONS is enforced; 'open' is the filled/triggered position):
  pending -> open -> closed          entry triggered on the permitted session, later exited
  pending -> expired                 the permitted entry session passed without a trigger (never revived)
  pending -> cancelled               operator or system cancel before the trigger
  pending -> void                    a provisional-bar signal that the official bar does not confirm
  (rejected)                         recorded at ingestion, never active: provisional, stale, duplicate, untrusted data
Every ingestion and transition is also written to the hash-chained events.jsonl when an event path is given.

The ledger stores signals; trade state is recomputed from price history on every update and frozen
once closed. No score ranking exists, so when the open-risk budget binds, signals are admitted in a
deterministic pseudo-random order (sha1), not by any 'quality' measure.
"""
import hashlib, json, math, os
import numpy as np
import pandas as pd

import backtest as bt
import settings
import strategy
from risk import stop_distance

VERSION = 2
ACTIVE = ('pending', 'open')
TERMINAL = ('closed', 'expired', 'cancelled', 'void', 'rejected')
TRANSITIONS = {
    'pending': {'open', 'closed', 'expired', 'cancelled', 'void'},     # open->closed may happen in one update
    'open': {'closed'},
    'closed': set(), 'expired': set(), 'cancelled': set(), 'void': set(), 'rejected': set(),
}


class IllegalTransition(Exception):
    pass


def transition(rec, new, reason='', events=None, ts=None, **data):
    """Move a record to a new status through the transition table; log it. Same-status is a no-op."""
    old = rec['status']
    if new == old:
        return False
    if new not in TRANSITIONS.get(old, ()):
        raise IllegalTransition(f"{rec.get('id')}: {old} -> {new} is not allowed (expired/closed/rejected signals are never revived)")
    rec['status'] = new
    rec.setdefault('history', []).append({'from': old, 'to': new, 'reason': reason, 'ts': ts})
    if events:
        import events as ev
        ev.append(events, 'transition', rec['id'], dict(data, **{'from': old, 'to': new, 'reason': reason}), ts)
    return True


def _log(events, etype, ref, data, ts=None):
    if events:
        import events as ev
        ev.append(events, etype, ref, data, ts)


def empty():
    return {'version': VERSION, 'strategy': strategy.describe(), 'started': None, 'updated': None,
            'last_update_ok': None, 'signals': [], 'summary': {}}


def load(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return empty()


def save(ledger, path):
    with open(path + '.tmp', 'w') as f:
        json.dump(ledger, f, indent=2, default=str)
    os.replace(path + '.tmp', path)


def _reject(ledger, r, reason, events, ts, results, holidays=frozenset()):
    sid = f"{r['symbol']}|{r['signal_date']}"
    rec = {'id': sid, 'symbol': r['symbol'], 'signal_date': r['signal_date'], 'setup': r.get('setup_type'),
           'score': r.get('score'), 'status': 'rejected', 'reject_reason': reason, 'scan_id': results.get('scan_id'),
           'shares': 0, 'risk_amount': 0.0, 'history': [{'from': None, 'to': 'rejected', 'reason': reason, 'ts': ts}]}
    try:
        import analysis
        rec['expires_on'] = str(analysis.next_session(pd.Timestamp(r['signal_date']).date(), holidays))
    except Exception:
        pass
    ledger['signals'].append(rec)
    _log(events, 'signal_rejected', sid, {'reason': reason, 'scan_id': results.get('scan_id')}, ts)
    return rec


def add_signals(ledger, results, events=None, ts=None, holidays=frozenset()):
    """Ingest a scan. Idempotent and fail-closed:
      * a scan whose data was not trusted (results['actionable'] is not True) adds nothing;
      * a scan_id already ingested adds nothing (replay protection), nor does a scan older than the last one;
      * only signals dated on the scan's data cutoff are accepted (a stale signal cannot be revived);
      * provisional-bar signals, duplicates of an id, and signals for a symbol that is already active are recorded
        as 'rejected' with the reason, so nothing disappears silently.
    Returns the number of signals accepted as pending."""
    import analysis
    sid_scan = results.get('scan_id')
    ledger.setdefault('ingested_scans', [])
    if sid_scan is not None and sid_scan in ledger['ingested_scans']:
        _log(events, 'ingest_duplicate_scan', str(sid_scan), {}, ts)
        return 0
    if results.get('actionable') is not True:
        why = 'scan data not trusted (not actionable): ' + '; '.join((results.get('data_quality') or {}).get('reasons', []) or ['no data_quality verdict'])
        ledger['last_ingest'] = {'scan_id': sid_scan, 'accepted': 0, 'blocked': why}
        _log(events, 'ingest_blocked', str(sid_scan), {'reason': why}, ts)
        return 0
    cutoff = results.get('data_cutoff')
    if cutoff and ledger.get('last_cutoff') and str(cutoff) < str(ledger['last_cutoff']):
        why = f"scan data cutoff {cutoff} is older than the last ingested cutoff {ledger['last_cutoff']} (replay)"
        ledger['last_ingest'] = {'scan_id': sid_scan, 'accepted': 0, 'blocked': why}
        _log(events, 'ingest_blocked', str(sid_scan), {'reason': why}, ts)
        return 0
    have = {s['id'] for s in ledger['signals']}
    busy = {s['symbol'] for s in ledger['signals'] if s['status'] in ACTIVE and counts_toward_limits(s)}
    by_id = {s['id']: s for s in ledger['signals']}
    exp_session = str(results.get('expected_session') or '')
    added = rejected = 0
    for r in results.get('stocks', []):
        sid = f"{r['symbol']}|{r['signal_date']}"
        old = by_id.get(sid)
        old_exp = (old.get('expires_on') or str(analysis.next_session(pd.Timestamp(r['signal_date']).date(), holidays))) if old else ''
        if old is not None and old['status'] == 'rejected' and str(old.get('reject_reason', '')).startswith('symbol already has an active signal') \
                and r['symbol'] not in busy and exp_session and exp_session < old_exp and not r.get('provisional'):
            # A rejection caused by stale bookkeeping (an earlier signal not yet advanced), while the entry session is still ahead: reinstate it, audited.
            old['status'] = 'pending'
            old['expires_on'] = old_exp
            old.pop('reject_reason', None)
            old.update({'shares': (r.get('position') or {}).get('shares', 0), 'risk_amount': (r.get('position') or {}).get('risk_amount', 0.0),
                        'trigger': r['trigger'], 'stop': r['stop_loss'], 'plan_risk': r['plan_risk'], 'close': r['price'], 'setup': r['setup_type'],
                        'score': r['score'], 'scan_id': sid_scan, 'simulated': True, 'provisional': False})
            old.setdefault('history', []).append({'from': 'rejected', 'to': 'pending', 'reason': 'reinstated: rejection was caused by stale bookkeeping, entry session still ahead', 'ts': ts})
            _log(events, 'signal_reinstated', sid, {'scan_id': sid_scan, 'reason': 'rejection caused by an earlier signal not yet advanced; entry session still ahead',
                                                       'trigger': old['trigger'], 'stop': old['stop'], 'shares': old['shares'], 'expires_on': old.get('expires_on')}, ts)
            busy.add(r['symbol']); added += 1
            continue
        if sid in have:
            ledger['duplicates_skipped'] = ledger.get('duplicates_skipped', 0) + 1
            continue
        have.add(sid)
        if r.get('provisional') or r.get('actionable') is False:
            _reject(ledger, r, 'provisional or non-actionable bar', events, ts, results, holidays); rejected += 1; continue
        if cutoff and str(r['signal_date']) != str(cutoff):
            _reject(ledger, r, f"stale signal: dated {r['signal_date']}, scan cutoff {cutoff}", events, ts, results, holidays); rejected += 1; continue
        if r['symbol'] in busy:
            _reject(ledger, r, 'symbol already has an active signal', events, ts, results, holidays); rejected += 1; continue
        pos = r.get('position') or {}
        sdate = pd.Timestamp(r['signal_date']).date()
        rec = {
            'id': sid, 'symbol': r['symbol'], 'signal_date': r['signal_date'], 'setup': r['setup_type'],
            'score': r['score'], 'in_stockedge': r.get('in_stockedge', False),
            'close': r['price'], 'trigger': r['trigger'], 'stop': r['stop_loss'], 'plan_risk': r['plan_risk'],
            'shares': pos.get('shares', 0), 'risk_amount': pos.get('risk_amount', 0.0),
            'status': 'pending', 'scan_id': sid_scan, 'provisional': False,
            'expires_on': str(analysis.next_session(sdate, holidays)), 'simulated': True,
            'history': [{'from': None, 'to': 'pending', 'reason': 'signal recorded', 'ts': ts}],
        }
        ledger['signals'].append(rec)
        _log(events, 'signal_recorded', sid, {'scan_id': sid_scan, 'trigger': rec['trigger'], 'stop': rec['stop'],
                                              'shares': rec['shares'], 'expires_on': rec['expires_on']}, ts)
        busy.add(r['symbol']); added += 1
    if sid_scan is not None:
        ledger['ingested_scans'].append(sid_scan)
    if cutoff:
        ledger['last_cutoff'] = str(cutoff)
    ledger['last_ingest'] = {'scan_id': sid_scan, 'accepted': added, 'rejected': rejected, 'blocked': None}
    if ledger['started'] is None and ledger['signals']:
        ledger['started'] = results.get('scan_date')
    return added


def _arrays(df):
    ind = bt.indicator_series(df)
    return {'open': df['Open'].astype(float).values, 'high': df['High'].astype(float).values,
            'low': df['Low'].astype(float).values, 'close': df['Close'].astype(float).values,
            'ema20': ind['ema_20'].values, 'ema50': ind['ema_50'].values, 'atr': ind['atr'].values}


def counts_toward_limits(rec):
    """Legacy records (pre-dating the fail-closed data gate) stay in the ledger as history but do not hold risk budget, occupy a
    symbol or a sector slot, or block new signals: they were produced by a pipeline the system no longer trusts."""
    return rec.get('evidence_eligible') is not False


def eff_shares(rec):
    return rec.get('filled_shares', rec.get('shares', 0))


def eff_risk(rec):
    sh = rec.get('shares', 0)
    return rec.get('risk_amount', 0.0) * (eff_shares(rec) / sh) if sh else 0.0


def update_status(ledger, frames, cfg=None, events=None, ts=None, expected_session=None, holidays=frozenset()):
    """Advance every pending/open signal using the latest bars. Returns number of changes.
    Expiry is calendar-based: the permitted entry session is expires_on; if that session's bar is in the data and the
    buy-stop was not hit, the signal expires and is never revived. If the data does not cover that session, the signal
    stays pending with needs_data=True (fail closed; reconcile() reports it) instead of being guessed at."""
    import analysis
    cfg = cfg or strategy.realistic_config()        # forward paper results use the itemised cost model
    liq = settings.LIQUIDITY_PARTICIPATION_CAP
    changed = 0
    for rec in ledger['signals']:
        if rec['status'] not in ACTIVE:
            continue
        df = frames.get(rec['symbol'])
        if df is None or len(df) < 60:
            continue
        sdate = pd.Timestamp(rec['signal_date'])
        if sdate not in df.index:
            continue
        s = df.index.get_loc(sdate)
        if rec.get('provisional') and not rec.get('verified'):
            # Legacy records generated from a provisional bar; re-check against the official one.
            import screener as sc
            official, _ = sc.evaluate(df.iloc[:s + 1])
            if official is None:
                transition(rec, 'void', 'official bar no longer qualifies as a signal', events, ts)
                rec['void_reason'] = 'official bar no longer qualifies as a signal'
                changed += 1
                continue
            rec['verified'] = True
            rec['trigger_official'] = official['trigger']
            rec['stop_official'] = official['stop_loss']
        n = len(df)
        if rec['status'] == 'open' and rec.get('entry_date') and pd.Timestamp(rec['entry_date']) not in df.index:
            # The fill was simulated on a bar that is not in the official data (an unfinished session). Correct it, with an audit trail.
            rec['status'] = 'void'
            rec['void_reason'] = 'entry was simulated on an unfinished session bar; the official bar decides'
            rec.setdefault('history', []).append({'from': 'open', 'to': 'void', 'reason': rec['void_reason'], 'ts': ts})
            _log(events, 'fill_voided', rec['id'], {'reason': rec['void_reason'], 'entry_date': rec['entry_date']}, ts)
            changed += 1
            continue
        if rec['status'] == 'pending':
            exp = rec.get('expires_on') or str(analysis.next_session(sdate.date(), holidays))
            rec['expires_on'] = exp
            if s + 1 >= n:
                rec['needs_data'] = bool(expected_session and str(expected_session) > exp)
                continue
            if df.index[s + 1].date() != pd.Timestamp(exp).date():
                rec['needs_data'] = True       # the bar for the permitted entry session is absent or the calendar disagrees
                continue
            rec.pop('needs_data', None)
        a = _arrays(df)
        t = bt.simulate_trade(a, s, cfg, rec['setup'], rec['score'])
        before = rec['status']
        if t is None:
            transition(rec, 'expired', 'entry session passed without the buy-stop triggering', events, ts)
            rec['expired_reason'] = 'trigger_not_hit'
            changed += 1
            continue
        e = t['entry_idx']
        if before == 'pending':
            vol = float(df['Volume'].iloc[e])
            cap_sh = int(liq * vol)
            if rec['shares'] > 0 and cap_sh <= 0:
                transition(rec, 'cancelled', 'no liquidity on the entry day', events, ts)
                rec['cancel_reason'] = 'no_liquidity'
                changed += 1
                continue
            if rec['shares'] > cap_sh:
                rec['filled_shares'] = cap_sh
                rec['fill_ratio'] = round(cap_sh / rec['shares'], 3)
                _log(events, 'partial_fill', rec['id'], {'wanted': rec['shares'], 'filled': cap_sh, 'entry_volume': vol}, ts)
        rec['entry_date'] = str(df.index[e].date())
        rec['entry'] = round(float(t['entry']), 2)
        reason = t['reason']
        if reason == 'end_of_data' or reason.endswith('_pending'):
            if before == 'pending':
                transition(rec, 'open', 'buy-stop triggered', events, ts, entry=rec['entry'], entry_date=rec['entry_date'])
            rec['mark_price'] = round(float(a['close'][-1]), 2)
            rec['unrealized_r'] = round(float(t['r']), 3)
            rec['exit_signal'] = reason.endswith('_pending')
            rec['days_held'] = int(t['hold'])
        else:
            rec.pop('mark_price', None); rec.pop('unrealized_r', None); rec.pop('exit_signal', None)
            if before == 'pending':
                transition(rec, 'open', 'buy-stop triggered', events, ts, entry=rec['entry'], entry_date=rec['entry_date'])
            transition(rec, 'closed', reason, events, ts, exit=round(float(t['exit']), 2), r=round(float(t['r']), 3))
            rec.update({'exit_date': str(df.index[t['exit_idx']].date()),
                        'exit': round(float(t['exit']), 2), 'exit_reason': reason, 'r': round(float(t['r']), 3),
                        'days_held': int(t['hold']), 'pnl_per_share': float(t['pnl_per_share'])})
            if reason.startswith('gap_'):
                rec['gap_through_stop'] = True
                rec['gap_loss_beyond_stop_r'] = round(max(0.0, (float(t['stop']) - float(t['exit'])) / float(t['plan_risk'])), 3)
            rec['pnl_inr'] = round(eff_shares(rec) * rec['pnl_per_share'], 2) if rec['shares'] else 0.0
        changed += 1
    return changed


def migrate(ledger, events=None, ts=None, holidays=frozenset()):
    """Bring a pre-lifecycle ledger (version 1) up to date, once. Legacy records were produced before the fail-closed
    data gate existed, so they stay in the ledger (nothing is deleted) but are flagged evidence_eligible=False:
    they do not count toward forward-validation gates. Each gets a 'legacy_import' event so the log can replay it."""
    import analysis
    n = 0
    for rec in ledger['signals']:
        if 'history' in rec:
            continue
        rec['legacy'] = True
        rec['evidence_eligible'] = False
        rec.setdefault('simulated', True)
        if rec['status'] in ('pending', 'open') and not rec.get('expires_on'):
            rec['expires_on'] = str(analysis.next_session(pd.Timestamp(rec['signal_date']).date(), holidays))
        rec['history'] = [{'from': None, 'to': rec['status'], 'reason': 'legacy import', 'ts': ts}]
        _log(events, 'legacy_import', rec['id'], {'status': rec['status'], 'signal_date': rec['signal_date']}, ts)
        n += 1
    ledger['version'] = VERSION
    ledger.setdefault('ingested_scans', sorted({r['scan_id'] for r in ledger['signals'] if r.get('scan_id')}))
    return n


def replay_statuses(event_list):
    """Rebuild each signal's status purely from the event log."""
    st = {}
    for e in event_list:
        if e['type'] == 'legacy_import':
            st[e['ref']] = e['data']['status']
        elif e['type'] == 'signal_recorded':
            st[e['ref']] = 'pending'
        elif e['type'] == 'signal_rejected':
            st[e['ref']] = 'rejected'
        elif e['type'] == 'signal_reinstated':
            st[e['ref']] = 'pending'
        elif e['type'] == 'fill_voided':
            st[e['ref']] = 'void'
        elif e['type'] == 'transition':
            st[e['ref']] = e['data']['to']
    return st


def reconcile(ledger, event_list=None, expected_session=None, holidays=frozenset(), pending_max_sessions=1):
    """Cross-check the ledger against itself, the event log and the calendar. Returns {'ok', 'issues': [...]}."""
    import analysis
    issues = []

    def add(kind, ref, detail):
        issues.append({'kind': kind, 'ref': ref, 'detail': detail})
    ids = [s['id'] for s in ledger['signals']]
    for i in {x for x in ids if ids.count(x) > 1}:
        add('duplicate_id', i, 'the same signal id appears more than once')
    per_symbol = {}
    for s in ledger['signals']:
        if s['id'] != f"{s['symbol']}|{s['signal_date']}":
            add('bad_id', s['id'], 'id does not match symbol|signal_date')
        if s['status'] in ACTIVE and counts_toward_limits(s):          # legacy history may overlap a current signal
            per_symbol.setdefault(s['symbol'], []).append(s['id'])
        if s['status'] not in TRANSITIONS:
            add('unknown_status', s['id'], s['status'])
        if s['status'] == 'closed' and any(k not in s for k in ('exit_date', 'exit', 'r', 'entry_date')):
            add('incomplete_closed', s['id'], 'closed without entry/exit fields')
        if s['status'] == 'pending':
            if s.get('needs_data'):
                add('needs_data', s['id'], f"pending past its entry session {s.get('expires_on')} but the data does not cover it")
            if expected_session and s.get('expires_on') and str(expected_session) > s['expires_on'] and not s.get('needs_data'):
                add('overdue_pending', s['id'], f"still pending although the entry session {s['expires_on']} has passed (expected session {expected_session})")
        for h in s.get('history', []):
            if h['from'] is not None and h['to'] not in TRANSITIONS.get(h['from'], ()) and not (h['from'] == 'rejected' and str(h.get('reason', '')).startswith('reinstated')) \
                    and not (h['from'] == 'open' and h['to'] == 'void'):
                add('illegal_history', s['id'], f"{h['from']} -> {h['to']}")
    for sym, lst in per_symbol.items():
        if len(lst) > 1:
            add('duplicate_active', sym, f'{len(lst)} active signals for one symbol: {lst}')
    if event_list is not None:
        rep = replay_statuses(event_list)
        for s in ledger['signals']:
            if rep.get(s['id']) is None:
                add('no_event', s['id'], 'ledger record has no event history (pre-event-log record or tampering)')
            elif rep[s['id']] != s['status']:
                add('event_mismatch', s['id'], f"ledger says {s['status']}, event replay says {rep[s['id']]}")
        for sid in rep:
            if sid not in set(ids):
                add('orphan_event', sid, 'event refers to a signal that is not in the ledger')
    return {'ok': not issues, 'issues': issues}


def _order_key(rec):
    return (rec['entry_date'], hashlib.sha1(rec['id'].encode()).hexdigest())


def mark_taken(ledger, capital, max_open_risk):
    """Replay which signals a trader following the risk budget would actually have taken."""
    cap = capital * max_open_risk
    entered = [r for r in ledger['signals'] if r.get('entry_date') and counts_toward_limits(r)]
    for r in ledger['signals']:
        r['taken'] = False
        r.pop('not_taken_reason', None)
        if not counts_toward_limits(r):
            r['not_taken_reason'] = 'legacy record: kept as history, holds no risk budget'
        elif r['status'] in ('expired', 'cancelled', 'void', 'rejected'):
            r['not_taken_reason'] = {'expired': 'entry session passed without a trigger', 'cancelled': r.get('cancel_reason', 'cancelled'),
                                     'void': r.get('void_reason', 'void'), 'rejected': r.get('reject_reason', 'rejected')}[r['status']]
        elif r['status'] == 'pending':
            r['not_taken_reason'] = 'not yet triggered'
    live = []   # (exit_date or None, risk)
    for rec in sorted(entered, key=_order_key):
        live = [(x, k) for x, k in live if x is None or x >= rec['entry_date']]
        risk_now = sum(k for _, k in live)
        if eff_shares(rec) > 0 and risk_now + eff_risk(rec) <= cap:
            rec['taken'] = True
            live.append((rec.get('exit_date'), eff_risk(rec)))
        else:
            rec['not_taken_reason'] = 'zero shares fundable' if eff_shares(rec) <= 0 else \
                f'aggregate open-risk budget {max_open_risk:.1%} of capital would be exceeded'


def forward_returns(ledger):
    """R per entered signal (closed = realised, open = marked to last close) and its entry month.
    Including open trades matters: under a slow exit, closed-only results are biased toward losers."""
    rs, months = [], []
    for r in ledger['signals']:
        if not r.get('entry_date') or r.get('evidence_eligible') is False:
            continue
        if r['status'] == 'closed':
            rs.append(float(r['r']))
        elif r['status'] == 'open':
            rs.append(float(r.get('unrealized_r', 0.0)))
        else:
            continue
        months.append(str(r['entry_date'])[:7])
    return np.array(rs, dtype=float), np.array(months)


OUTCOME_LABELS = {
    'won': 'Won: closed in profit', 'stopped': 'Lost: stop hit', 'exited_loss': 'Lost: exited at a loss (trend/time exit)',
    'open_profit': 'Open, in profit (mark-to-market)', 'open_loss': 'Open, at a loss (mark-to-market)',
    'never_triggered': 'Never triggered (buy-stop not reached)', 'waiting': 'Waiting for entry session',
    'not_tradable': 'Not tradable (rejected, cancelled or void)',
}


def classify_outcome(rec):
    """One outcome class per signal. C0 has no fixed take-profit: a winner is a trade closed above its entry (trend exit or
    time exit), so 'won' means profit realised by the rules, not a target hit."""
    st = rec['status']
    if st == 'closed':
        if rec.get('r', 0) > 0:
            return 'won'
        return 'stopped' if str(rec.get('exit_reason', '')).endswith(('stop', 'trail')) else 'exited_loss'
    if st == 'open':
        return 'open_profit' if rec.get('unrealized_r', 0.0) >= 0 else 'open_loss'
    return {'expired': 'never_triggered', 'pending': 'waiting'}.get(st, 'not_tradable')


def outcomes(ledger):
    """Tally of how the screened stocks fared, evidence-eligible signals only (legacy records are counted separately)."""
    elig = [r for r in ledger['signals'] if r.get('evidence_eligible') is not False]
    by = {k: {'n': 0, 'r': []} for k in OUTCOME_LABELS}
    setups = {}
    for r in elig:
        c = classify_outcome(r)
        by[c]['n'] += 1
        rv = r.get('r') if r['status'] == 'closed' else r.get('unrealized_r') if r['status'] == 'open' else None
        if rv is not None:
            by[c]['r'].append(float(rv))
        if c in ('won', 'stopped', 'exited_loss', 'open_profit', 'open_loss'):
            d = setups.setdefault(r.get('setup') or 'unknown', {'entered': 0, 'good': 0})
            d['entered'] += 1
            d['good'] += c in ('won', 'open_profit')
    entered = sum(by[k]['n'] for k in ('won', 'stopped', 'exited_loss', 'open_profit', 'open_loss'))
    closed = sum(by[k]['n'] for k in ('won', 'stopped', 'exited_loss'))
    return {
        'classes': {k: {'label': OUTCOME_LABELS[k], 'n': v['n'], 'avg_r': round(sum(v['r']) / len(v['r']), 3) if v['r'] else None} for k, v in by.items()},
        'entered': entered, 'closed': closed,
        'closed_win_rate': round(by['won']['n'] / closed, 3) if closed else None,
        'entered_in_profit_rate': round((by['won']['n'] + by['open_profit']['n']) / entered, 3) if entered else None,
        'trigger_rate': round(entered / (entered + by['never_triggered']['n']), 3) if entered + by['never_triggered']['n'] else None,
        'by_setup': {k: dict(v, hit_rate=round(v['good'] / v['entered'], 3)) for k, v in setups.items()},
        'legacy_excluded': len(ledger['signals']) - len(elig),
        'note': 'Win/loss counts are descriptive. Below ~100 closed signals they say little about the criteria; winners run under a slow exit, so early closed-only results skew to stops.',
    }


def summarize(ledger):
    sigs = ledger['signals']
    closed = [r for r in sigs if r['status'] == 'closed']
    open_ = [r for r in sigs if r['status'] == 'open']
    rs = np.array([r['r'] for r in closed], dtype=float)
    out = {
        'closed_eligible': sum(1 for r in closed if r.get('evidence_eligible') is not False),
        'first_eligible_signal': min((r['signal_date'] for r in sigs if r.get('evidence_eligible') is not False
                                      and r['status'] != 'rejected'), default=None),
        'signals': len(sigs), 'pending': sum(r['status'] == 'pending' for r in sigs), 'open': len(open_),
        'closed': len(closed), 'expired': sum(r['status'] == 'expired' for r in sigs),
        'void': sum(r['status'] == 'void' for r in sigs),
        'cancelled': sum(r['status'] == 'cancelled' for r in sigs), 'rejected': sum(r['status'] == 'rejected' for r in sigs),
        'win_rate': round(float((rs > 0).mean()), 3) if len(rs) else None,
        'avg_r': round(float(rs.mean()), 3) if len(rs) else None,
        'total_r': round(float(rs.sum()), 2) if len(rs) else 0.0,
        'open_unrealized_r': round(sum(r.get('unrealized_r', 0.0) for r in open_), 2),
        'taken_closed': sum(r.get('taken', False) for r in closed),
        'taken_pnl_inr': round(sum(r.get('pnl_inr', 0.0) for r in closed if r.get('taken')), 0),
        'avg_r_ci95': None,
        'avg_r_incl_open': None, 'total_r_incl_open': 0.0,
    }
    allr = np.array([r['r'] for r in closed] + [r.get('unrealized_r', 0.0) for r in open_], dtype=float)
    if len(allr):
        out['avg_r_incl_open'] = round(float(allr.mean()), 3)
        out['total_r_incl_open'] = round(float(allr.sum()), 2)
    if len(rs) >= 30:
        se = rs.std(ddof=1) / math.sqrt(len(rs))
        out['avg_r_ci95'] = [round(float(rs.mean() - 1.96 * se), 3), round(float(rs.mean() + 1.96 * se), 3)]
    out['outcomes'] = outcomes(ledger)
    out['note'] = ('Signal-level R includes every signal, taken or not. Closed-only averages are biased toward losers '
                   'for months, because stops hit fast while winners stay open under the slow exit; read the figure '
                   'that includes open trades (marked to the last close) alongside it. Interval is naive (signals '
                   'cluster by date); fewer than ~100 closed trades says almost nothing about expectancy.')
    return out


def refresh(ledger, results, frames, capital, max_open_risk, cfg=None, events=None, ts=None, expected_session=None, holidays=frozenset(), ingest=True):
    added = add_signals(ledger, results, events, ts, holidays) if ingest else 0
    changed = update_status(ledger, frames, cfg, events, ts, expected_session, holidays) if frames else 0
    mark_taken(ledger, capital, max_open_risk)
    ledger['summary'] = summarize(ledger)
    return added, changed
