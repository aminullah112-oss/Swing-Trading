#!/usr/bin/env python3
"""Automated pre-trade checklist (replaces the manual daily routine in docs/OPERATOR_CHECKLIST.md).

Reads the artefacts the screen workflow just produced and answers one question: may any NEW paper entry be taken
today, and which of today's signals survive every check? Output: reports/pretrade.json and reports/pretrade.md.
Verdict GO means the checks passed, not that a trade is wise; NO-GO lists every blocking reason. Paper only: no orders
are placed and live execution stays disabled."""
import json
import os
import sys
from datetime import datetime, timezone

import analysis
import events as evlog
import health as hl
import ledger as lg
import prereg
import provenance as provn
import riskgate
import selection
import settings


def _load(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _c(cid, level, ok, msg):
    """level: 'block' (failing blocks all entries), 'warn' (reported only), 'info'."""
    return {'id': cid, 'level': level, 'ok': bool(ok), 'msg': msg}


def run_checks(ctx):
    res, led, health, now = ctx['results'], ctx['ledger'], ctx['health'], ctx['now']
    out = []
    dq = res.get('data_quality') or {}
    behind = res.get('sessions_behind')
    cur = bool(res.get('data_cutoff')) and res.get('data_cutoff') == res.get('expected_session') and behind == 0
    out.append(_c('P1', 'block', cur, f"scan data cutoff {res.get('data_cutoff')} vs expected session {res.get('expected_session')} ({behind} behind)"))
    sp = provn.problems(res.get('provenance'), 'scan', now)
    out.append(_c('P2', 'block', not sp, 'scan provenance current' if not sp else sp[0]))
    out.append(_c('P3', 'block', dq.get('status') == 'TRUSTED' and res.get('actionable') is True,
                  f"data quality {dq.get('status')}" + ('' if dq.get('status') == 'TRUSTED' else ': ' + '; '.join(dq.get('reasons', ['no verdict'])[:2]))))
    hs = health.get('status')
    out.append(_c('P4', 'block', hl.permits(hs)['new_entries'], f'health {hs}: new entries {"allowed" if hl.permits(hs)["new_entries"] else "NOT allowed"}'))
    ok, n, why = ctx['events']
    out.append(_c('P5', 'block', ok, f'event log verified ({n} events)' if ok else f'event log broken: {why}'))
    rec = led.get('reconciliation') or {}
    out.append(_c('P6', 'block', rec.get('ok') is True, 'ledger reconciles' if rec.get('ok') else
                  f"ledger reconciliation {'missing' if not rec else str(len(rec.get('issues', []))) + ' issue(s): ' + ', '.join(sorted({i['kind'] for i in rec.get('issues', [])}))}"))
    out.append(_c('P7', 'block', settings.LIVE_EXECUTION_ENABLED is False, 'live execution disabled (paper only)'))
    try:
        c0 = ctx['c0_hash'] == '5e7924a41b0ee220'
        pr = prereg.load()['_hash'] is not None
    except Exception as e:
        c0, pr = False, False
    out.append(_c('P8', 'block', c0 and pr, 'control C0 and pre-registration intact' if c0 and pr else 'C0 identity or pre-registration changed'))
    hol = ctx['holidays']
    out.append(_c('P9', 'warn', any(d.year == now.year for d in hol), f'holiday calendar has {sum(d.year == now.year for d in hol)} entries for {now.year}'
                  + ('' if any(d.year == now.year for d in hol) else ': add exchange holidays to market_holidays.json')))
    bp = provn.problems(ctx.get('report_provenance'), 'backtest', now)
    out.append(_c('P10', 'warn', not bp, 'backtest evidence current' if not bp else 'backtest evidence stale: ' + bp[0]))
    ks = riskgate.kill_switch_engaged(ctx.get('kill_switch_path'))
    out.append(_c('P11', 'info', True, 'kill switch ENGAGED (no real orders possible; paper tracking continues)' if ks else 'kill switch released'))
    return out


def screen_signals(ctx):
    """Per-signal checks against the same limits the risk gate uses. Returns (tradable, rejected[{symbol, reasons}])."""
    res, led = ctx['results'], ctx['ledger']
    cap = res.get('capital') or (res.get('risk_config') or {}).get('capital') or settings.CAPITAL
    live = [s for s in led.get('signals', []) if lg.counts_toward_limits(s)]          # legacy records hold no budget and block nothing
    active = {s['symbol'] for s in live if s['status'] in lg.ACTIVE}
    open_risk = sum(lg.eff_risk(s) for s in live if s['status'] == 'open' and s.get('taken'))
    sectors = selection.load_sectors()
    held = [s['symbol'] for s in live if s['status'] in lg.ACTIVE]
    tradable, rejected = [], []
    for r in res.get('stocks', []):
        why = []
        pos = r.get('position') or {}
        if r.get('actionable') is not True or r.get('provisional'):
            why.append('not an official-bar actionable signal')
        if not r.get('execution_ok'):
            why.append('execution checks blocked it')
        if r['symbol'] in active:
            why.append('symbol already has an active signal')
        sh, risk = pos.get('shares', 0), pos.get('risk_amount', 0.0)
        if not sh:
            why.append('zero shares fundable under the risk limits')
        else:
            if r['stop_loss'] >= r['trigger']:
                why.append('stop is not below the buy-stop')
            if risk > cap * settings.RISK_PCT * (1 + 1e-9):
                why.append('trade risk above the per-trade limit')
            if sh * r['trigger'] > cap * settings.MAX_POS_PCT * (1 + 1e-9):
                why.append('position above the 25% cap')
            if open_risk + risk > cap * settings.MAX_OPEN_RISK * (1 + 1e-9):
                why.append('aggregate open-risk budget would be exceeded')
        ok_sec, grp, n_open = selection.sector_ok(r['symbol'], held + [t['symbol'] for t in tradable], sectors)
        if not ok_sec:
            why.append(f'sector cap: {n_open} open positions already in {grp} (limit {settings.MAX_PER_SECTOR})')
        if why:
            rejected.append({'symbol': r['symbol'], 'reasons': why})
        else:
            open_risk += risk
            tradable.append({'symbol': r['symbol'], 'buy_stop': r['trigger'], 'stop': r['stop_loss'], 'shares': sh, 'risk_inr': risk,
                             'tier': (r.get('selection') or {}).get('tier'), 'sector': (r.get('selection') or {}).get('sector'), 'valid_for': str(analysis.next_session(datetime.fromisoformat(str(r['signal_date'])[:10]).date(), ctx['holidays']))})
    return tradable, rejected


def evaluate(ctx):
    checks = run_checks(ctx)
    blockers = [c for c in checks if c['level'] == 'block' and not c['ok']]
    tradable, rejected = ([], [{'symbol': '*', 'reasons': ['entries blocked: ' + '; '.join(c['msg'] for c in blockers)]}]) if blockers else screen_signals(ctx)
    verdict = 'NO-GO' if blockers else ('GO' if tradable else 'GO (no qualifying signals)')
    return {'verdict': verdict, 'generated': ctx['now'].isoformat(timespec='seconds'), 'checks': checks,
            'tradable': tradable, 'rejected': rejected, 'paper_only': True}


def markdown(rep):
    L = [f"# Pre-trade checklist: **{rep['verdict']}** (paper only)", '', f"Generated {rep['generated']}.", '', '| Check | Result | Detail |', '|---|---|---|']
    for c in rep['checks']:
        L.append(f"| {c['id']} {c['level']} | {'✅' if c['ok'] else ('❌' if c['level'] == 'block' else '⚠️')} | {c['msg']} |")
    L += ['', '## Entries allowed (valid for the next session only; buy-stop, then stop)' if rep['tradable'] else '## No entries allowed today', '']
    L += [f"- {t['symbol']} [{t.get('tier') or 'n/a'} · {t.get('sector') or 'sector n/a'}]: buy-stop {t['buy_stop']}, stop {t['stop']}, {t['shares']} shares, risk ₹{t['risk_inr']:.0f}, valid {t['valid_for']}" for t in rep['tradable']]
    if rep['rejected']:
        L += ['', '## Rejected', ''] + [f"- {r['symbol']}: {'; '.join(r['reasons'])}" for r in rep['rejected']]
    L += ['', 'A GO means the checks passed, not that the trade is wise. Paper only: no order is sent anywhere.']
    return '\n'.join(L)


def main():
    ctx = {'results': _load('results.json', {}), 'ledger': _load('ledger.json', lg.empty()), 'health': _load('health.json', {}),
           'events': evlog.verify('events.jsonl'), 'holidays': analysis.load_holidays(), 'c0_hash': provn.c0_hash(),
           'report_provenance': _load('reports/provenance.json'), 'now': datetime.now(timezone.utc)}
    rep = evaluate(ctx)
    os.makedirs('reports', exist_ok=True)
    with open('reports/pretrade.json', 'w') as f:
        json.dump(rep, f, indent=2, default=str)
    with open('reports/pretrade.md', 'w') as f:
        f.write(markdown(rep))
    print(markdown(rep))


if __name__ == '__main__':
    main()
