import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import forward_report as fr
import ledger as lg
import provenance
import settings
import strategy
from test_ledger import flat, sig, results_for, S
from test_readiness_health import led_with


def test_forward_report_lists_every_signal_fate_and_excludes_legacy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    df = flat([(100, 100.8, 99.5, 100.2)])                                    # expires
    led = lg.empty()
    lg.add_signals(led, results_for(sig('AAA', df)))
    lg.add_signals(led, dict(results_for(sig('BBB', df, shares=0, risk=0.0)), scan_id='s2'))
    lg.update_status(led, {'AAA': df, 'BBB': df})
    lg.mark_taken(led, 565000, 0.015)
    led['signals'].append({'id': 'OLD|2020-01-01', 'symbol': 'OLD', 'signal_date': '2020-01-01', 'status': 'pending', 'evidence_eligible': False,
                           'shares': 1, 'risk_amount': 1.0, 'plan_risk': 1.0})
    led['summary'] = lg.summarize(led)
    rep = fr.build(led, [], 565000)
    assert rep['signals_total'] == 3 and rep['evidence_eligible'] == 2 and rep['legacy_excluded'] == 1
    assert rep['by_status'].get('expired') == 2 and rep['all_fills_simulated'] is True
    assert 'entry session passed without a trigger' in rep['not_taken_reasons']
    md = fr.markdown(rep)
    assert 'simulated' in md and 'No entered, eligible signals yet' in md and '0 of 100 needed' in md


def test_not_taken_reason_when_open_risk_budget_binds():
    led = led_with(0, 0, n_open=6, taken=False)
    for r in led['signals']:
        r.update(shares=1000, risk_amount=3000.0)
    lg.mark_taken(led, 565000, 0.015)
    taken = [r for r in led['signals'] if r['taken']]
    assert 0 < len(taken) < 6
    assert any('open-risk budget' in (r.get('not_taken_reason') or '') for r in led['signals'] if not r['taken'])


def test_forward_paper_uses_the_realistic_cost_model_and_c0_identity_is_unchanged():
    cfg = strategy.realistic_config()
    assert (cfg.cost_buy_bps, cfg.cost_sell_bps) == (settings.COST_BUY_BPS, settings.COST_SELL_BPS) and cfg.participation_cap == settings.LIQUIDITY_PARTICIPATION_CAP
    assert provenance.c0_hash() == '5e7924a41b0ee220'
    legacy = strategy.backtest_config()
    assert legacy.cost_buy_bps is None and legacy.participation_cap is None
