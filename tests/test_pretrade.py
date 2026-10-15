import os, sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ledger as lg
import pretrade as pt
import provenance as provn

NOW = datetime(2026, 10, 14, 13, tzinfo=timezone.utc)


def stock(sym='AAA', **kw):
    s = {'symbol': sym, 'signal_date': '2026-10-13', 'actionable': True, 'execution_ok': True, 'trigger': 100.0, 'stop_loss': 96.0,
         'position': {'shares': 500, 'risk_amount': 2000.0}}
    s.update(kw)
    return s


def ctx(stocks=None, **over):
    res = {'data_cutoff': '2026-10-13', 'expected_session': '2026-10-13', 'sessions_behind': 0, 'actionable': True, 'capital': 565000,
           'data_quality': {'status': 'TRUSTED'}, 'provenance': provn.make('scan'), 'stocks': [stock()] if stocks is None else stocks}
    led = lg.empty(); led['reconciliation'] = {'ok': True, 'issues': []}
    c = {'results': res, 'ledger': led, 'health': {'status': 'OK'}, 'events': (True, 3, None), 'holidays': set(), 'c0_hash': '5e7924a41b0ee220',
         'report_provenance': None, 'now': datetime.now(timezone.utc), 'kill_switch_path': 'nope.json'}
    c.update(over)
    return c


def blockers(rep):
    return {c['id'] for c in rep['checks'] if c['level'] == 'block' and not c['ok']}


def test_clean_day_is_go_with_the_signal_and_validity():
    rep = pt.evaluate(ctx())
    assert rep['verdict'] == 'GO' and not blockers(rep) and rep['paper_only']
    t = rep['tradable'][0]
    assert t['symbol'] == 'AAA' and t['valid_for'] == '2026-10-14'
    assert 'GO' in pt.markdown(rep)


def test_every_blocker_gives_no_go_and_no_entries():
    cases = {
        'P1': lambda c: c['results'].update(sessions_behind=1),
        'P2': lambda c: c['results'].pop('provenance'),
        'P3': lambda c: c['results'].update(actionable=False, data_quality={'status': 'UNTRUSTED', 'reasons': ['x']}),
        'P4': lambda c: c.update(health={'status': 'DEGRADED'}),
        'P5': lambda c: c.update(events=(False, 2, 'broken')),
        'P6': lambda c: c['ledger'].update(reconciliation={'ok': False, 'issues': [{'kind': 'needs_data'}]}),
        'P8': lambda c: c.update(c0_hash='other'),
    }
    for pid, mut in cases.items():
        c = ctx(); mut(c)
        rep = pt.evaluate(c)
        assert rep['verdict'] == 'NO-GO' and pid in blockers(rep) and rep['tradable'] == [], pid


def test_live_switch_blocks(monkeypatch):
    import settings
    monkeypatch.setattr(settings, 'LIVE_EXECUTION_ENABLED', True)
    assert 'P7' in blockers(pt.evaluate(ctx()))


def test_signal_level_rejections_with_reasons():
    c = ctx([stock('PROV', actionable=False), stock('NOEX', execution_ok=False), stock('ZERO', position={'shares': 0, 'risk_amount': 0}),
             stock('RISKY', position={'shares': 500, 'risk_amount': 9000.0}), stock('BADSTOP', stop_loss=101.0),
             stock('BIG', position={'shares': 2000, 'risk_amount': 2000.0})])
    rep = pt.evaluate(c)
    why = {r['symbol']: ' '.join(r['reasons']) for r in rep['rejected']}
    assert rep['verdict'] == 'GO (no qualifying signals)' and rep['tradable'] == []
    assert 'official-bar' in why['PROV'] and 'execution' in why['NOEX'] and 'zero shares' in why['ZERO']
    assert 'per-trade limit' in why['RISKY'] and 'not below' in why['BADSTOP'] and '25% cap' in why['BIG']


def test_aggregate_open_risk_and_active_symbols_limit_entries():
    big = lambda n: stock(n, position={'shares': 500, 'risk_amount': 2500.0})
    c = ctx([big('A'), big('B'), big('C'), big('D'), big('E')])
    c['ledger']['signals'] = [{'id': 'Z|d', 'symbol': 'D', 'status': 'pending', 'shares': 1, 'risk_amount': 1}]
    rep = pt.evaluate(c)
    assert [t['symbol'] for t in rep['tradable']] == ['A', 'B', 'C']             # 3 x 2500 = 7500 <= 8475; a fourth would reach 10000
    why = {r['symbol']: r['reasons'][0] for r in rep['rejected']}
    assert 'active signal' in why['D'] and 'open-risk budget' in why['E']


def test_todays_own_pending_signals_are_candidates_not_competition():
    c = ctx([stock('A', signal_date='2026-10-14'), stock('B', signal_date='2026-10-14')])
    c['ledger']['signals'] = [{'id': 'A|2026-10-13', 'symbol': 'A', 'signal_date': '2026-10-13', 'status': 'pending', 'shares': 1, 'risk_amount': 1}]      # older pending: stands
    c['ledger']['signals'] += [{'id': 'B|2026-10-14', 'symbol': 'B', 'signal_date': '2026-10-14', 'status': 'pending', 'shares': 1, 'risk_amount': 1}]      # today's own record
    c['results'].update(data_cutoff='2026-10-14', expected_session='2026-10-14')
    rep = pt.evaluate(c)
    assert [t['symbol'] for t in rep['tradable']] == ['B']
    assert 'active signal' in ' '.join(next(r for r in rep['rejected'] if r['symbol'] == 'A')['reasons'])
