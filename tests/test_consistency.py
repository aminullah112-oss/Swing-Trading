import json, os, sys
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import health as hl
import ledger as lg
import provenance as provn
import readiness as rd
import settings
from test_readiness_health import ctx, led_with, by_id, RES, ATT_ALL, NOW, UNI_WINS, GRID, hctx, lvl, fills

GOOD_DQ = {'status': 'TRUSTED', 'official_coverage': 1.0, 'quarantined': {}, 'reasons': []}


def fresh_prov(**kw):
    return dict(provn.make('backtest'), generated_at=NOW.isoformat(), **kw)


# ---------------------------------------------------------------- stale backtest evidence earns nothing
def test_missing_provenance_blocks_backtest_credit():
    g = by_id(rd.evaluate(ctx(lg.empty(), rprov=None)))
    assert g['B1']['status'] == 'stale' and g['B1']['earned'] == 0 and g['B1']['evidence_state'] == 'blocked_defect'
    assert g['U1']['status'] == 'stale' and 'no provenance' in g['U1']['detail'] + g['B1']['detail']
    assert rd.policy(list(g.values()), {}, {'status': 'OK'})['score'] < 1.5


def test_config_or_universe_change_makes_evidence_stale():
    p = fresh_prov(evidence_hash='deadbeefdeadbeef')
    g = by_id(rd.evaluate(ctx(lg.empty(), rprov=p)))
    assert g['B1']['status'] == 'stale' and 'evidence_hash' in g['B1']['detail']
    p2 = fresh_prov(universe_hash='0000')
    assert by_id(rd.evaluate(ctx(lg.empty(), rprov=p2)))['U1']['status'] == 'stale'


def test_old_evidence_is_stale():
    old = dict(provn.make('backtest'), generated_at=(NOW - timedelta(days=provn.BACKTEST_MAX_AGE_DAYS + 5)).isoformat())
    assert by_id(rd.evaluate(ctx(lg.empty(), rprov=old)))['B1']['status'] == 'stale'


def test_report_edited_after_stamping_is_detected():
    p = fresh_prov(source_ids={'grid': 'aaaa', 'benchmarks': 'bbbb'})
    c = ctx(lg.empty(), rprov=p)
    c['report_ids'] = {'grid': 'aaaa', 'benchmarks': 'CHANGED'}
    g = by_id(rd.evaluate(c))
    assert g['B1']['status'] == 'stale' and 'benchmarks changed since it was stamped' in g['B1']['detail']
    c['report_ids'] = {'grid': 'aaaa', 'benchmarks': 'bbbb'}
    assert by_id(rd.evaluate(c))['B1']['status'] == 'pass'


# ---------------------------------------------------------------- forward gates ignore legacy records
def test_legacy_signals_do_not_count_toward_forward_gates():
    led = led_with(150, 0.6, months=9)
    for r in led['signals']:
        r['evidence_eligible'] = False
    led['summary'] = lg.summarize(led)
    assert led['summary']['closed'] == 150 and led['summary']['closed_eligible'] == 0
    g = by_id(rd.evaluate(ctx(led)))
    assert g['F1']['status'] == 'fail' and g['F2']['status'] == 'fail' and g['F3']['status'] == 'insufficient'
    assert lg.forward_returns(led)[0].size == 0


# ---------------------------------------------------------------- health states gate readiness
def test_degraded_health_gives_no_ops_credit_and_blocks_live():
    g = by_id(rd.evaluate(ctx(lg.empty(), health='DEGRADED')))
    assert g['O1']['status'] == 'fail' and g['O1']['earned'] == 0
    full = rd.evaluate(ctx(led_with(150, 0.6, months=9), att=ATT_ALL, fills=fills(40, 5, 5), health='DEGRADED'))
    pol = rd.policy(full, ATT_ALL, {'status': 'DEGRADED'})
    assert pol['live_risk_pct_allowed'] == 0.0 and pol['mode'] == 'PAPER ONLY' and 'DEGRADED' in pol['reasons'][0]


def test_untrusted_scan_data_fails_the_ops_gate_even_if_health_says_ok():
    res = dict(RES, data_quality={'status': 'UNTRUSTED', 'reasons': ['only 0% of symbols have an official daily bar']})
    g = by_id(rd.evaluate(ctx(lg.empty(), res=res, health='OK')))
    assert g['O1']['status'] == 'fail' and 'UNTRUSTED' in g['O1']['detail']


def test_health_state_permissions_fail_closed():
    assert hl.permits('OK')['new_entries'] and hl.permits('WARN')['new_entries']
    assert not hl.permits('DEGRADED')['new_entries'] and hl.permits('DEGRADED')['manage_exits']
    assert not hl.permits('FAIL')['new_entries'] and not hl.permits('FAIL')['manage_exits']
    assert hl.permits(None) == hl.permits('FAIL') and hl.permits('whatever') == hl.permits('FAIL')


def test_health_levels_map_to_four_states():
    mk = lambda lv: [{'id': 'x', 'level': lv, 'msg': ''}]
    assert [hl.overall(mk(l)) for l in ('ok', 'warn', 'degraded', 'fail')] == ['OK', 'WARN', 'DEGRADED', 'FAIL']


def test_health_degrades_on_untrusted_data_unreconciled_ledger_and_missing_verdict():
    res = dict(RES, data_quality={'status': 'UNTRUSTED', 'reasons': ['stale']})
    c = hl.run_checks(hctx(res=res))
    assert lvl(c, 'H10') == 'degraded' and hl.overall(c) == 'DEGRADED'
    assert lvl(hl.run_checks(hctx(res=dict(RES, data_quality=GOOD_DQ))), 'H10') == 'ok'
    assert lvl(hl.run_checks(hctx()), 'H10') == 'degraded'                           # no verdict at all = not trusted
    led = lg.empty(); led['reconciliation'] = {'ok': False, 'issues': [{'kind': 'needs_data', 'ref': 'A|d', 'detail': ''}]}
    assert lvl(hl.run_checks(hctx(led=led)), 'H11') == 'degraded'


def test_tampered_event_log_is_a_health_fail():
    c = dict(hctx(), events=(False, 3, 'event 4: broken chain link'))
    ch = hl.run_checks(c)
    assert lvl(ch, 'H12') == 'fail' and hl.overall(ch) == 'FAIL'
    assert lvl(hl.run_checks(dict(hctx(), events=(True, 10, None))), 'H12') == 'ok'


def test_live_switch_enabled_is_a_health_fail_and_blocks_policy(monkeypatch):
    assert lvl(hl.run_checks(hctx()), 'H14') == 'ok'
    monkeypatch.setattr(settings, 'LIVE_EXECUTION_ENABLED', True)
    assert lvl(hl.run_checks(hctx()), 'H14') == 'fail'
    full = rd.evaluate(ctx(led_with(150, 0.6, months=9), att=ATT_ALL, fills=fills(40, 5, 5)))
    pol = rd.policy(full, ATT_ALL, {'status': 'OK'})
    assert pol['live_risk_pct_allowed'] == 0.0 and 'LIVE_EXECUTION_ENABLED' in pol['reasons'][0]


# ---------------------------------------------------------------- cross-artefact consistency
def test_inconsistent_artefacts_block_the_ops_gate():
    c = ctx(lg.empty())
    c['artifact_ids'] = {'results': 'r2', 'ledger': 'l1'}
    c['health'] = {'status': 'OK', 'provenance': {'source_ids': {'results': 'r1', 'ledger': 'l1'}}}
    g = by_id(rd.evaluate(c))
    assert g['O1']['status'] == 'blocked' and 'health.json' in g['O1']['detail'] and g['O1']['evidence_state'] == 'blocked_defect'
    c['health'] = {'status': 'OK', 'provenance': {'source_ids': {'results': 'r2', 'ledger': 'l1'}}}
    assert by_id(rd.evaluate(c))['O1']['status'] == 'pass'


def test_ledger_built_from_other_scan_is_flagged():
    led = lg.empty(); led['signals'] = [{'id': 'x'}]; led['provenance'] = {'source_ids': {'results': 'old'}}
    c = ctx(led)
    c['artifact_ids'] = {'results': 'new', 'ledger': 'l'}
    assert any('different results.json' in x for x in rd.consistency(c))


def test_gate_weights_are_unchanged():
    w = {g[0]: g[2] for g in rd.GATES}
    assert w == {'B1': 0.5, 'U1': 1.0, 'B2': 1.5, 'F1': 1.0, 'F2': 1.0, 'F3': 1.5, 'F4': 1.0, 'E1': 1.0, 'S1': 0.5, 'O1': 0.5, 'R1': 0.5}
    assert (rd.MIN_CLOSED, rd.MIN_DAYS, rd.MIN_FILLS) == (100, 182, 30)


def test_evidence_state_classification():
    assert rd.evidence_state('F1', 'fail') == 'pending_time' and rd.evidence_state('F3', 'fail') == 'failed'
    assert rd.evidence_state('B2', 'manual') == 'unverifiable' and rd.evidence_state('B1', 'stale') == 'blocked_defect'
    assert rd.evidence_state('E1', 'insufficient') == 'pending_time' and rd.evidence_state('U1', 'insufficient') == 'blocked_defect'


# ---------------------------------------------------------------- B2 needs the objective point-in-time test, not just a flag
def test_b2_requires_attestation_and_a_passing_pit_acceptance():
    fail = {'passed': False, 'status': 'fail', 'reasons': ['none of the 12 departed stocks has price history']}
    none = {'passed': False, 'status': 'no_pit_universe', 'reasons': ['no point-in-time membership file']}
    g = by_id(rd.evaluate(ctx(lg.empty(), att=ATT_ALL, pit=fail)))['B2']
    assert g['status'] == 'fail' and g['earned'] == 0 and 'departed stocks' in g['detail']
    g = by_id(rd.evaluate(ctx(lg.empty(), att=ATT_ALL, pit=None)))['B2']
    assert g['status'] == 'fail' and g['earned'] == 0                                  # attested but never tested: no credit
    g = by_id(rd.evaluate(ctx(lg.empty(), pit=none)))['B2']
    assert g['status'] == 'manual' and 'survivorship bias remains' in g['detail']
    assert by_id(rd.evaluate(ctx(lg.empty(), att=ATT_ALL)))['B2']['status'] == 'pass'
    assert by_id(rd.evaluate(ctx(lg.empty(), att=ATT_ALL, rprov=None)))['B2']['status'] == 'fail'    # stale backtest evidence: no B2 either
