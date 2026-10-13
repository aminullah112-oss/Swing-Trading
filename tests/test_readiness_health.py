import os, sys
from datetime import datetime, timezone, timedelta
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ledger as lg
import readiness as rd
import health as hl

NOW = datetime(2027, 6, 1, tzinfo=timezone.utc)
GRID = [{'label': rd.LIVE_LABEL, 'promising': True, 'G1': True, 'G2': True, 'G3': True, 'design_avg_r': 0.2,
         'holdout_port_cagr': 7.5, 'holdout_port_maxdd': -14.8}]
UNI_LOSES = {'holdout': {'equal_weight': {'cagr_pct': 17.0, 'max_drawdown_pct': -20.6}}}     # 0.83 vs strategy 0.51
UNI_WINS = {'holdout': {'equal_weight': {'cagr_pct': 5.0, 'max_drawdown_pct': -20.0}}}       # 0.25
RES = {'risk_config': {'capital': 565000, 'risk_pct': 0.5, 'max_pos_pct': 25, 'max_open_risk_pct': 1.5},
       'data_cutoff': '2027-05-31', 'strategy': {'x': 1}, 'symbols_processed': 158, 'total_scanned': 160, 'total_passed': 5}
ATT_NO = {}
ATT_ALL = {'survivorship_free_backtest_passed': True, 'market_stress_observed': True, 'capital_confirmed': True}


def led_with(n_closed, mean_r, months=9, n_open=0, started='2026-10-14', taken=False, shares=100):
    rng = np.random.default_rng(0)
    led = lg.empty(); led['started'] = started
    for i in range(n_closed + n_open):
        m = i % months
        d = (datetime(2026, 10, 14) + timedelta(days=30 * m + (i % 20))).date()
        closed = i < n_closed
        rec = {'id': f'S{i}|{d}', 'symbol': f'S{i}', 'signal_date': str(d), 'entry_date': str(d), 'entry': 100.0,
               'plan_risk': 3.0, 'shares': shares, 'risk_amount': 300.0, 'status': 'closed' if closed else 'open', 'taken': taken}
        if closed:
            r = float(rng.normal(mean_r, 1.0))
            rec.update({'exit_date': str(d + timedelta(days=10)), 'exit': 100 + 3 * r, 'r': r, 'pnl_inr': r * 3.0 * shares, 'days_held': 10})
        else:
            rec.update({'unrealized_r': 0.5, 'days_held': 5})
        led['signals'].append(rec)
    led['summary'] = lg.summarize(led)
    return led


def ctx(led, att=ATT_NO, uni=UNI_WINS, fills=(), health='OK', res=RES):
    return {'ledger': led, 'results': res, 'grid': GRID, 'universe': uni, 'attest': att, 'fills': list(fills),
            'health': {'status': health}, 'now': NOW}


def by_id(gates):
    return {g['id']: g for g in gates}


def test_points_sum_to_ten():
    assert abs(sum(g[2] for g in rd.GATES) - 10.0) < 1e-9


def test_today_scores_low_and_is_paper_only():
    g = rd.evaluate(ctx(lg.empty(), uni=None))
    pol = rd.policy(g, ATT_NO, {'status': 'OK'})
    assert pol['score'] == 1.5 and pol['mode'] == 'PAPER ONLY' and pol['live_risk_pct_allowed'] == 0.0


def test_universe_gate_fails_when_buy_and_hold_wins():
    assert by_id(rd.evaluate(ctx(lg.empty(), uni=UNI_LOSES)))['U1']['status'] == 'fail'
    assert by_id(rd.evaluate(ctx(lg.empty(), uni=UNI_WINS)))['U1']['status'] == 'pass'
    assert by_id(rd.evaluate(ctx(lg.empty(), uni=None)))['U1']['status'] == 'insufficient'


def test_attestations_default_to_no_credit():
    g = by_id(rd.evaluate(ctx(lg.empty())))
    assert g['B2']['status'] == 'manual' and g['S1']['status'] == 'manual' and g['B2']['earned'] == 0
    g = by_id(rd.evaluate(ctx(lg.empty(), att=ATT_ALL)))
    assert g['B2']['status'] == 'pass' and g['S1']['status'] == 'pass'


def test_forward_gates_need_volume_and_time_then_judge_expectancy():
    small = by_id(rd.evaluate(ctx(led_with(40, 0.5, months=3))))
    assert small['F1']['status'] == 'fail' and small['F3']['status'] == 'insufficient'
    good = by_id(rd.evaluate(ctx(led_with(150, 0.6, months=9))))
    assert good['F1']['status'] == 'pass' and good['F2']['status'] == 'pass'
    assert good['F3']['status'] == 'pass' and good['F4']['status'] == 'pass'
    bad = by_id(rd.evaluate(ctx(led_with(150, -0.3, months=9))))
    assert bad['F3']['status'] == 'fail' and bad['F4']['status'] == 'fail'


def fills(n, entry_bps, exit_bps=None):
    rows = []
    for i in range(n):
        f = {'planned_entry': 100.0, 'actual_entry': 100.0 * (1 + entry_bps / 1e4)}
        if exit_bps is not None:
            f.update({'planned_exit': 100.0, 'actual_exit': 100.0 * (1 - exit_bps / 1e4)})
        rows.append(f)
    return rows


def test_live_fill_gate():
    assert by_id(rd.evaluate(ctx(lg.empty(), fills=fills(40, 5, 5))))['E1']['status'] == 'pass'
    assert by_id(rd.evaluate(ctx(lg.empty(), fills=fills(40, 40, 5))))['E1']['status'] == 'fail'
    assert by_id(rd.evaluate(ctx(lg.empty(), fills=fills(40, 5, 40))))['E1']['status'] == 'fail'
    assert by_id(rd.evaluate(ctx(lg.empty(), fills=fills(10, 5))))['E1']['status'] == 'insufficient'


def test_policy_tiers_and_overrides():
    full = ctx(led_with(150, 0.6, months=9), att=ATT_ALL, fills=fills(40, 5, 5))
    g = rd.evaluate(full)
    pol = rd.policy(g, ATT_ALL, {'status': 'OK'})
    assert pol['score'] >= 8 and pol['live_risk_pct_allowed'] == 0.5, pol
    # same evidence but the capital attestation is missing -> paper only
    att = dict(ATT_ALL, capital_confirmed=False)
    assert rd.policy(rd.evaluate(ctx(led_with(150, 0.6), att=att, fills=fills(40, 5, 5))), att, {'status': 'OK'})['live_risk_pct_allowed'] == 0.0
    # kill switch / health FAIL overrides everything
    assert rd.policy(g, ATT_ALL, {'status': 'FAIL'})['live_risk_pct_allowed'] == 0.0
    # fill-test tier: forward gates pass, no survivorship-free test, no fills yet
    mid = rd.evaluate(ctx(led_with(150, 0.6), att={'capital_confirmed': True}, uni=UNI_WINS))
    pol = rd.policy(mid, {'capital_confirmed': True}, {'status': 'OK'})
    assert pol['mode'].startswith('FILL TEST') and pol['live_risk_pct_allowed'] == 0.1, pol


# ---------------- health -----------------
def hctx(led=None, res=None, grid=GRID):
    return {'ledger': led or lg.empty(), 'results': res or dict(RES), 'grid': grid, 'now': NOW}


def lvl(checks, cid):
    return next((c['level'] for c in checks if c['id'] == cid), None)


def test_health_freshness_and_coverage():
    assert lvl(hl.run_checks(hctx()), 'H1') == 'ok'
    assert lvl(hl.run_checks(hctx(res=dict(RES, data_cutoff='2027-05-25'))), 'H1') == 'warn'
    assert lvl(hl.run_checks(hctx(res=dict(RES, data_cutoff='2027-05-10'))), 'H1') == 'fail'
    assert lvl(hl.run_checks(hctx(res=dict(RES, symbols_processed=120))), 'H2') == 'warn'
    assert lvl(hl.run_checks(hctx(res={'risk_config': {}})), 'H1') == 'fail'


def test_health_ledger_integrity_and_staleness():
    led = led_with(3, 0.1)
    led['signals'].append(dict(led['signals'][0]))                      # duplicate id
    assert lvl(hl.run_checks(hctx(led)), 'H4') == 'fail'
    led = lg.empty(); led['updated'] = '2027-05-31T00:00:00+00:00'; led['last_update_ok'] = False
    assert lvl(hl.run_checks(hctx(led)), 'H3') == 'fail'
    led = lg.empty(); led['updated'] = '2027-05-20T00:00:00+00:00'; led['last_update_ok'] = True
    assert lvl(hl.run_checks(hctx(led)), 'H3') == 'fail'                # >7 days stale
    led = lg.empty(); led['signals'] = [{'id': 'A|2027-05-01', 'symbol': 'A', 'signal_date': '2027-05-01', 'status': 'pending'}]
    assert lvl(hl.run_checks(hctx(led)), 'H4') == 'fail'                # pending far too long


def test_health_edge_decay():
    assert lvl(hl.run_checks(hctx(led_with(80, -0.5, months=9))), 'H7') == 'fail'
    assert lvl(hl.run_checks(hctx(led_with(80, 0.6, months=9))), 'H7') == 'ok'
    assert 'needs 30' in next(c['msg'] for c in hl.run_checks(hctx(led_with(5, -1))) if c['id'] == 'H7')


def test_drawdown_kill_switch_on_taken_signals():
    capital = RES['risk_config']['capital']
    led = led_with(40, 0.0, taken=True, shares=100)
    for s in led['signals']:                                            # every taken trade loses 1R ~ ₹300 -> make it big
        s['r'] = -1.0; s['pnl_inr'] = -capital * 0.0025                 # 40 x 0.25% = 10% drawdown
    assert lvl(hl.run_checks(hctx(led)), 'H8') == 'fail'
    for s in led['signals'][20:]:
        s['pnl_inr'] = 0.0                                              # ~5% -> warn
    assert lvl(hl.run_checks(hctx(led)), 'H8') == 'warn'
    for s in led['signals']:
        s['pnl_inr'] = 10.0
    assert lvl(hl.run_checks(hctx(led)), 'H8') == 'ok'


def test_overall_is_worst_level_and_config_check():
    assert hl.overall([{'level': 'ok'}, {'level': 'warn'}]) == 'WARN'
    assert hl.overall([{'level': 'ok'}, {'level': 'fail'}, {'level': 'warn'}]) == 'FAIL'
    assert hl.overall([]) == 'OK'
    bad = dict(RES, risk_config=dict(RES['risk_config'], risk_pct=2.0))
    assert lvl(hl.run_checks(hctx(res=bad)), 'H9') == 'fail'


def test_health_flags_data_lag_and_names_missing_symbols():
    behind = dict(RES, sessions_behind=1, expected_session='2027-06-01')
    c = hl.run_checks(hctx(res=behind))
    assert lvl(c, 'H1b') == 'warn' and 'holiday' in next(x['msg'] for x in c if x['id'] == 'H1b')
    assert lvl(hl.run_checks(hctx(res=dict(RES, sessions_behind=6, expected_session='2027-06-01'))), 'H1b') == 'fail'
    assert lvl(hl.run_checks(hctx(res=dict(RES, sessions_behind=0))), 'H1b') is None
    miss = hl.run_checks(hctx(res=dict(RES, symbols_processed=157, total_scanned=160, missing_symbols=['AAA', 'BBB', 'CCC'])))
    assert 'AAA, BBB, CCC' in next(x['msg'] for x in miss if x['id'] == 'H2')


def test_data_lag_fails_the_operations_gate_and_costs_a_point():
    lag_health = {'status': 'WARN', 'checks': [{'id': 'H1b', 'level': 'warn', 'msg': 'behind'}]}
    g = by_id(rd.evaluate(ctx(lg.empty(), uni=None, health='WARN')))
    assert g['O1']['status'] == 'pass'                                  # WARN for another reason is fine
    c = ctx(lg.empty(), uni=None); c['health'] = lag_health
    g = by_id(rd.evaluate(c))
    assert g['O1']['status'] == 'fail' and g['O1']['earned'] == 0
    assert rd.policy(list(g.values()), ATT_NO, lag_health)['score'] == 1.0   # B1 + R1 only


def test_three_sessions_behind_is_a_health_fail():
    assert lvl(hl.run_checks(hctx(res=dict(RES, sessions_behind=2, expected_session='2027-06-01'))), 'H1b') == 'warn'
    assert lvl(hl.run_checks(hctx(res=dict(RES, sessions_behind=3, expected_session='2027-06-01'))), 'H1b') == 'fail'
