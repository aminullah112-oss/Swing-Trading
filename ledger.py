"""Paper-trade ledger. Every scanner signal is logged and followed forward with the backtester's
own trade simulation (backtest.simulate_trade), so paper results and backtest results use one
definition of a trade. Statuses: pending -> open -> closed, or pending -> expired.

The ledger stores signals; trade state is recomputed from price history on every update and frozen
once closed. No score ranking exists, so when the open-risk budget binds, signals are admitted in a
deterministic pseudo-random order (sha1), not by any 'quality' measure.
"""
import hashlib, json, math, os
import numpy as np
import pandas as pd

import backtest as bt
import strategy
from risk import stop_distance

VERSION = 1
ACTIVE = ('pending', 'open')


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


def add_signals(ledger, results):
    """Append today's scanner signals. Skips duplicates and symbols that already have an
    unresolved signal (the backtest also holds one position per symbol)."""
    have = {s['id'] for s in ledger['signals']}
    busy = {s['symbol'] for s in ledger['signals'] if s['status'] in ACTIVE}
    added = 0
    for r in results.get('stocks', []):
        sid = f"{r['symbol']}|{r['signal_date']}"
        if sid in have or r['symbol'] in busy:
            continue
        pos = r.get('position') or {}
        ledger['signals'].append({
            'id': sid, 'symbol': r['symbol'], 'signal_date': r['signal_date'], 'setup': r['setup_type'],
            'score': r['score'], 'in_stockedge': r.get('in_stockedge', False),
            'close': r['price'], 'trigger': r['trigger'], 'stop': r['stop_loss'], 'plan_risk': r['plan_risk'],
            'shares': pos.get('shares', 0), 'risk_amount': pos.get('risk_amount', 0.0),
            'status': 'pending', 'scan_id': results.get('scan_id'),
        })
        busy.add(r['symbol']); added += 1
    if ledger['started'] is None and ledger['signals']:
        ledger['started'] = results.get('scan_date')
    return added


def _arrays(df):
    ind = bt.indicator_series(df)
    return {'open': df['Open'].astype(float).values, 'high': df['High'].astype(float).values,
            'low': df['Low'].astype(float).values, 'close': df['Close'].astype(float).values,
            'ema20': ind['ema_20'].values, 'ema50': ind['ema_50'].values, 'atr': ind['atr'].values}


def update_status(ledger, frames, cfg=None):
    """Advance every pending/open signal using the latest bars. Returns number of changes."""
    cfg = cfg or strategy.backtest_config()
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
        a = _arrays(df)
        t = bt.simulate_trade(a, s, cfg, rec['setup'], rec['score'])
        n = len(df)
        before = rec['status']
        if t is None:
            rec['status'] = 'pending' if s + 1 >= n else 'expired'
        else:
            rec['entry_date'] = str(df.index[t['entry_idx']].date())
            rec['entry'] = round(float(t['entry']), 2)
            reason = t['reason']
            if reason == 'end_of_data' or reason.endswith('_pending'):
                rec['status'] = 'open'
                rec['mark_price'] = round(float(a['close'][-1]), 2)
                rec['unrealized_r'] = round(float(t['r']), 3)
                rec['exit_signal'] = reason.endswith('_pending')
                rec['days_held'] = int(t['hold'])
            else:
                rec.pop('mark_price', None); rec.pop('unrealized_r', None); rec.pop('exit_signal', None)
                rec.update({'status': 'closed', 'exit_date': str(df.index[t['exit_idx']].date()),
                            'exit': round(float(t['exit']), 2), 'exit_reason': reason, 'r': round(float(t['r']), 3),
                            'days_held': int(t['hold']), 'pnl_per_share': float(t['pnl_per_share'])})
                rec['pnl_inr'] = round(rec['shares'] * rec['pnl_per_share'], 2) if rec['shares'] else 0.0
        if rec['status'] != before or t is not None:
            changed += 1
    return changed


def _order_key(rec):
    return (rec['entry_date'], hashlib.sha1(rec['id'].encode()).hexdigest())


def mark_taken(ledger, capital, max_open_risk):
    """Replay which signals a trader following the risk budget would actually have taken."""
    cap = capital * max_open_risk
    entered = [r for r in ledger['signals'] if r.get('entry_date')]
    for r in ledger['signals']:
        r['taken'] = False
    live = []   # (exit_date or None, risk)
    for rec in sorted(entered, key=_order_key):
        live = [(x, k) for x, k in live if x is None or x >= rec['entry_date']]
        risk_now = sum(k for _, k in live)
        if rec['shares'] > 0 and risk_now + rec['risk_amount'] <= cap:
            rec['taken'] = True
            live.append((rec.get('exit_date'), rec['risk_amount']))


def forward_returns(ledger):
    """R per entered signal (closed = realised, open = marked to last close) and its entry month.
    Including open trades matters: under a slow exit, closed-only results are biased toward losers."""
    rs, months = [], []
    for r in ledger['signals']:
        if not r.get('entry_date'):
            continue
        if r['status'] == 'closed':
            rs.append(float(r['r']))
        elif r['status'] == 'open':
            rs.append(float(r.get('unrealized_r', 0.0)))
        else:
            continue
        months.append(str(r['entry_date'])[:7])
    return np.array(rs, dtype=float), np.array(months)


def summarize(ledger):
    sigs = ledger['signals']
    closed = [r for r in sigs if r['status'] == 'closed']
    open_ = [r for r in sigs if r['status'] == 'open']
    rs = np.array([r['r'] for r in closed], dtype=float)
    out = {
        'signals': len(sigs), 'pending': sum(r['status'] == 'pending' for r in sigs), 'open': len(open_),
        'closed': len(closed), 'expired': sum(r['status'] == 'expired' for r in sigs),
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
    out['note'] = ('Signal-level R includes every signal, taken or not. Closed-only averages are biased toward losers '
                   'for months, because stops hit fast while winners stay open under the slow exit; read the figure '
                   'that includes open trades (marked to the last close) alongside it. Interval is naive (signals '
                   'cluster by date); fewer than ~100 closed trades says almost nothing about expectancy.')
    return out


def refresh(ledger, results, frames, capital, max_open_risk, cfg=None):
    added = add_signals(ledger, results)
    changed = update_status(ledger, frames, cfg) if frames else 0
    mark_taken(ledger, capital, max_open_risk)
    ledger['summary'] = summarize(ledger)
    return added, changed
