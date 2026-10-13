#!/usr/bin/env python3
"""Pipeline and edge health monitoring. Runs daily after the scan and ledger update.

Levels: ok < warn < fail. Overall status is the worst level. A FAIL exits non-zero so the GitHub
Actions run goes red (GitHub emails you) and the workflow opens an issue. The kill-switch
thresholds are fixed here, in advance, so they can't be argued away during a drawdown.

Edge-decay and drawdown checks use the paper ledger now and will apply to live fills later.
"""
import json, os, sys
from datetime import datetime, timezone

import numpy as np

import ledger as lg
import readiness as rd
import research as rs

FRESH_WARN_DAYS = 4         # calendar days since the last market bar (covers weekend + one holiday)
FRESH_FAIL_DAYS = 7
LAG_FAIL_SESSIONS = 5       # sessions behind the expected last session
LEDGER_STALE_DAYS = 3
COVERAGE_WARN = 0.95
PENDING_MAX_DAYS = 7        # a signal must resolve (trigger or expire) within a few sessions
NO_SIGNAL_WARN_DAYS = 21    # calendar days without any new signal while scans keep running
FLOOD_FRACTION = 0.35       # > 35% of the universe signalling at once smells like bad data
KILL_DD_WARN = 5.0          # % of capital, taken-signal paper/live equity (closed + open marked)
KILL_DD_FAIL = 8.0
DECAY_MIN_CLOSED_WARN = 30
DECAY_MIN_CLOSED_FAIL = 60


def _c(cid, level, msg):
    return {'id': cid, 'level': level, 'msg': msg}


def _days_since(datestr, now):
    return (now.date() - datetime.fromisoformat(str(datestr)[:10]).date()).days


def taken_equity(ledger, capital):
    """Equity curve (in % of capital) of 'taken' signals: realised at exit dates, plus open positions marked."""
    pts = []
    for r in ledger['signals']:
        if r.get('taken') and r['status'] == 'closed':
            pts.append((r['exit_date'], r.get('pnl_inr', 0.0)))
    pts.sort()
    eq, cum = [0.0], 0.0
    for _, p in pts:
        cum += p
        eq.append(cum)
    unreal = sum(r.get('unrealized_r', 0.0) * r['plan_risk'] * r['shares']
                 for r in ledger['signals'] if r.get('taken') and r['status'] == 'open')
    eq.append(cum + unreal)
    eq = np.array(eq) / capital * 100
    peak = np.maximum.accumulate(eq)
    return float((peak - eq).max()) if len(eq) else 0.0, float(eq[-1])


def run_checks(ctx):
    led, res, grid = ctx['ledger'], ctx.get('results') or {}, ctx.get('grid')
    now = ctx.get('now') or datetime.now(timezone.utc)
    out = []

    # --- scan freshness and coverage
    cutoff = res.get('data_cutoff')
    if not cutoff or not res.get('strategy'):
        out.append(_c('H1', 'fail', 'results.json missing or from the pre-v4 scanner'))
    else:
        age = _days_since(cutoff, now)
        lvl = 'fail' if age > FRESH_FAIL_DAYS else 'warn' if age > FRESH_WARN_DAYS else 'ok'
        out.append(_c('H1', lvl, f'market data through {cutoff} ({age} days old)'))
        behind = res.get('sessions_behind')
        if behind:
            out.append(_c('H1b', 'fail' if behind >= LAG_FAIL_SESSIONS else 'warn',
                          f"data ends {cutoff} but the last completed session should be {res.get('expected_session')} "
                          f"({behind} session(s) behind): an exchange holiday, or the data vendor is lagging. If it was a "
                          f"trading day, 'valid for the next session' buy levels refer to a session that already traded"))
        cov = res.get('symbols_processed', 0) / max(res.get('total_scanned', 1), 1)
        miss = res.get('missing_symbols') or []
        out.append(_c('H2', 'warn' if cov < COVERAGE_WARN else 'ok',
                      f"{res.get('symbols_processed')}/{res.get('total_scanned')} symbols had data ({cov:.0%})"
                      + (f"; no data for: {', '.join(miss)}" if miss else '')))
        flood = res.get('total_passed', 0) / max(res.get('total_scanned', 1), 1)
        if flood > FLOOD_FRACTION:
            out.append(_c('H5', 'warn', f"{res.get('total_passed')} signals ({flood:.0%} of universe) at once; check for a data glitch"))

    # --- ledger freshness and integrity
    if led.get('updated'):
        age = _days_since(led['updated'], now)
        ok = led.get('last_update_ok') is not False
        lvl = 'fail' if (not ok or age > LEDGER_STALE_DAYS + 4) else 'warn' if age > LEDGER_STALE_DAYS else 'ok'
        out.append(_c('H3', lvl, f"ledger updated {age} days ago; last price update {'ok' if ok else 'FAILED'}"))
    else:
        out.append(_c('H3', 'warn', 'ledger has never been updated'))

    sigs = led.get('signals', [])
    ids = [s['id'] for s in sigs]
    problems = []
    if len(ids) != len(set(ids)):
        problems.append('duplicate signal ids')
    for s in sigs:
        if s['status'] == 'closed' and any(k not in s for k in ('exit_date', 'exit', 'r')):
            problems.append(f"{s['id']} closed without exit fields")
        if s['status'] == 'pending' and _days_since(s['signal_date'], now) > PENDING_MAX_DAYS:
            problems.append(f"{s['id']} pending for >{PENDING_MAX_DAYS} days (price update stuck?)")
        if s['status'] == 'open' and s.get('days_held', 0) > 130:
            problems.append(f"{s['id']} open for {s['days_held']} sessions (max hold is 120)")
    out.append(_c('H4', 'fail' if problems else 'ok', '; '.join(problems[:5]) if problems else f'{len(sigs)} signals, integrity ok'))

    # --- signal drought
    if sigs and res.get('data_cutoff'):
        last_sig = max(s['signal_date'] for s in sigs)
        gap = _days_since(last_sig, now)
        started = led.get('started')
        running = _days_since(started, now) if started else 0
        if running > NO_SIGNAL_WARN_DAYS and gap > NO_SIGNAL_WARN_DAYS:
            out.append(_c('H6', 'warn', f'no new signal for {gap} days; quiet market or a broken filter?'))

    # --- edge decay on the forward record (paper now, live fills later)
    closed = (led.get('summary') or {}).get('closed', 0)
    rs_, months = lg.forward_returns(led)
    row = rd.live_variant(grid)
    if closed >= DECAY_MIN_CLOSED_WARN and len(rs_) >= 2:
        ci = rs.cluster_ci_mean(rs_, months, alpha=0.05)
        mean = float(rs_.mean())
        if closed >= DECAY_MIN_CLOSED_FAIL and ci and ci[1] < 0:
            out.append(_c('H7', 'fail', f'forward expectancy significantly negative: mean {mean:+.3f}R, CI [{ci[0]:+.3f}, {ci[1]:+.3f}]'))
        elif row and ci and ci[1] < row['design_avg_r']:
            out.append(_c('H7', 'warn', f"forward mean {mean:+.3f}R (CI upper {ci[1]:+.3f}) is below the backtest design figure {row['design_avg_r']:+.3f}R"))
        else:
            out.append(_c('H7', 'ok', f'forward mean {mean:+.3f}R over {len(rs_)} signals; no decay detected'))
    else:
        out.append(_c('H7', 'ok', f'edge-decay check needs {DECAY_MIN_CLOSED_WARN}+ closed signals (have {closed})'))

    # --- drawdown kill switch on taken signals
    capital = (res.get('risk_config') or {}).get('capital') or ctx.get('capital')
    if capital and sigs:
        dd, now_pct = taken_equity(led, capital)
        lvl = 'fail' if dd >= KILL_DD_FAIL else 'warn' if dd >= KILL_DD_WARN else 'ok'
        msg = f'taken-signal equity drawdown {dd:.1f}% of capital (now {now_pct:+.1f}%)'
        if lvl == 'fail':
            msg += f' >= {KILL_DD_FAIL:g}% kill switch: STOP trading and review before resuming'
        out.append(_c('H8', lvl, msg))

    # --- config sanity
    cfg = res.get('risk_config') or {}
    if cfg:
        bad = [k for k, lim in (('risk_pct', 1.0), ('max_open_risk_pct', 3.0), ('max_pos_pct', 25.0)) if cfg.get(k, 99) > lim]
        out.append(_c('H9', 'fail' if bad else 'ok', f"risk limits exceed safe bounds: {bad}" if bad else 'risk limits within bounds'))
    return out


def overall(checks):
    order = {'ok': 0, 'warn': 1, 'fail': 2}
    worst = max((order[c['level']] for c in checks), default=0)
    return {0: 'OK', 1: 'WARN', 2: 'FAIL'}[worst]


def _load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def main():
    ctx = {'ledger': _load('ledger.json', lg.empty()), 'results': _load('results.json', {}), 'grid': _load('reports/grid.json')}
    checks = run_checks(ctx)
    status = overall(checks)
    rep = {'status': status, 'generated': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'checks': checks}
    with open('health.json.tmp', 'w') as f:
        json.dump(rep, f, indent=2)
    os.replace('health.json.tmp', 'health.json')
    icon = {'ok': '✅', 'warn': '⚠️', 'fail': '❌'}
    print(f'HEALTH: {status}')
    for c in checks:
        print(f"  {icon[c['level']]} {c['id']}: {c['msg']}")
    if status == 'FAIL':
        sys.exit(2)


if __name__ == '__main__':
    main()
