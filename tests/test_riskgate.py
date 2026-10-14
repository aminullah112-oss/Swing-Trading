import ast, copy, glob, json, os, re, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import events as evlog
import execution_guard as eg
import riskgate as rg
import settings

ROOT = os.path.join(os.path.dirname(__file__), '..')


@pytest.fixture
def ks(tmp_path):
    p = tmp_path / 'ks.json'
    p.write_text(json.dumps({'engaged': False}))
    return str(p)


def order(**kw):
    o = {'symbol': 'AAA', 'side': 'buy', 'qty': 100, 'entry_price': 100.0, 'stop_price': 97.0, 'atr': 2.0, 'client_order_id': 'c1'}
    o.update(kw)
    return o


def state(**kw):
    s = {'equity': 565000.0, 'cash': 565000.0, 'open_positions': [], 'submitted_ids': [], 'health_status': 'OK', 'mode': 'paper',
         'state_reconciled': True, 'market': {'session_open': True, 'halted': []},
         'broker': {'connected': True, 'heartbeat_age_seconds': 5, 'consecutive_rejects': 0, 'consecutive_timeouts': 0},
         'quote': {'age_seconds': 3, 'ltp': 100.1, 'upper_circuit': 120.0, 'lower_circuit': 80.0},
         'liquidity': {'AAA': {'adv_shares': 1_000_000, 'adv_value': 1e8}}}
    s.update(kw)
    return s


def ok(o=None, s=None, ks=None):
    return rg.evaluate(o or order(), s or state(), ks)


def why(res, text):
    return any(text in r for r in res['reasons'])


def test_baseline_order_is_approved(ks):
    r = ok(ks=ks)
    assert r['approved'] and r['reasons'] == [] and r['limits']['per_trade_risk'] == {'value': 300.0, 'cap': 2825.0}


def test_risk_limits_are_the_audited_ones_and_not_raised():
    assert (settings.RISK_PCT, settings.MAX_POS_PCT, settings.MAX_OPEN_RISK) == (0.005, 0.25, 0.015)


@pytest.mark.parametrize('mut,text', [
    (lambda o, s: o.update(qty=1000), 'trade risk'),
    (lambda o, s: o.update(qty=1500, stop_price=99.9), 'position value'),
    (lambda o, s: s.update(open_positions=[{'symbol': 'B', 'qty': 1400, 'entry_price': 100, 'stop_price': 97},
                                           {'symbol': 'C', 'qty': 1400, 'entry_price': 100, 'stop_price': 97}]), 'aggregate open risk'),
    (lambda o, s: s.update(cash=1000), 'cash'),
    (lambda o, s: s['liquidity']['AAA'].update(adv_shares=1000), 'average daily volume'),
    (lambda o, s: s['liquidity']['AAA'].update(adv_value=1e5), 'average daily traded value'),
    (lambda o, s: s['liquidity'].pop('AAA'), 'no liquidity data'),
    (lambda o, s: s.update(submitted_ids=['c1']), 'duplicate order'),
    (lambda o, s: s.update(open_positions=[{'symbol': 'AAA', 'qty': 1, 'entry_price': 100, 'stop_price': 97}]), 'already has an open position'),
    (lambda o, s: s['quote'].update(age_seconds=900), 'stale'),
    (lambda o, s: s['quote'].pop('age_seconds'), 'stale'),
    (lambda o, s: s['quote'].update(ltp=110.0), 'differs from the order entry'),
    (lambda o, s: s['quote'].update(ltp=119.9), 'circuit'),
    (lambda o, s: s['quote'].pop('upper_circuit'), 'circuit limits unknown'),
    (lambda o, s: s['market'].update(session_open=False), 'not open'),
    (lambda o, s: s['market'].update(halted=['AAA']), 'halted'),
    (lambda o, s: s['broker'].update(connected=False), 'not connected'),
    (lambda o, s: s['broker'].update(heartbeat_age_seconds=600), 'heartbeat'),
    (lambda o, s: s['broker'].update(consecutive_rejects=3), 'consecutive broker rejections'),
    (lambda o, s: s['broker'].update(consecutive_timeouts=3), 'timeouts'),
    (lambda o, s: s.update(state_reconciled=False), 'reconciled'),
    (lambda o, s: s.update(health_status='DEGRADED'), 'health status'),
    (lambda o, s: s.update(health_status='FAIL'), 'health status'),
    (lambda o, s: o.update(stop_price=101.0), 'not below entry'),
    (lambda o, s: o.update(atr=0), 'ATR missing'),
    (lambda o, s: o.update(atr=60.0), 'gap-stressed loss'),
])
def test_each_control_rejects(mut, text, ks):
    o, s = order(), state()
    mut(o, s)
    r = ok(o, s, ks)
    assert not r['approved'] and why(r, text), r['reasons']


def test_unknown_or_missing_inputs_reject_never_pass(ks):
    for k in rg.REQUIRED_ORDER:
        o = order(); o.pop(k)
        assert not ok(o, ks=ks)['approved']
    for k in rg.REQUIRED_STATE:
        s = state(); s.pop(k)
        assert not ok(s=s, ks=ks)['approved']
    assert not ok(order(qty='abc'), ks=ks)['approved']
    assert not ok(order(qty=float('nan')), ks=ks)['approved']
    assert not ok(order(entry_price=-5), ks=ks)['approved']
    assert not ok(order(side='short'), ks=ks)['approved']
    assert not rg.evaluate(None, None)['approved']
    assert not ok(s=state(health_status=None), ks=ks)['approved']
    assert not ok(s=state(equity='x'), ks=ks)['approved']
    assert not ok(s=state(open_positions=[{'symbol': 'B'}]), ks=ks)['approved']       # malformed position: exception path


def test_kill_switch_missing_corrupt_or_engaged_blocks(tmp_path, ks):
    assert rg.kill_switch_engaged(str(tmp_path / 'nope.json'))
    bad = tmp_path / 'bad.json'; bad.write_text('{not json')
    assert rg.kill_switch_engaged(str(bad)) and not ok(ks=str(bad))['approved']
    on = tmp_path / 'on.json'; on.write_text('{"engaged": true}')
    assert why(ok(ks=str(on)), 'kill switch')
    assert not rg.kill_switch_engaged(ks)


def test_shipped_kill_switch_is_engaged_until_live_is_authorised():
    assert json.load(open(os.path.join(ROOT, 'kill_switch.json')))['engaged'] is True


def test_exits_are_never_blocked_by_entry_controls_but_cannot_exceed_the_position(ks):
    held = [{'symbol': 'AAA', 'qty': 100, 'entry_price': 100, 'stop_price': 97}]
    degraded = state(open_positions=held, health_status='FAIL')
    r = rg.evaluate(order(side='sell', qty=100, client_order_id='x'), degraded, ks)
    assert r['approved'] and r['kind'] == 'exit'
    r = rg.evaluate(order(side='sell', qty=150, client_order_id='x'), degraded, ks)
    assert not r['approved'] and why(r, 'exceeds the held position')
    assert not rg.evaluate(order(side='sell', client_order_id='x'), state(), ks)['approved']       # nothing held: no shorting


def test_cluster_limit_when_known(ks):
    held = [{'symbol': 'B', 'qty': 1, 'entry_price': 100, 'stop_price': 99, 'cluster': 'banks'},
            {'symbol': 'C', 'qty': 1, 'entry_price': 100, 'stop_price': 99, 'cluster': 'banks'}]
    assert why(ok(order(cluster='banks'), state(open_positions=held), ks), 'cluster')
    r = ok(order(), state(), ks)
    assert r['approved'] and any('cluster' in w for w in r['warnings'])


# ------------------------------------------------------------ execution guard
def test_live_mode_is_blocked_while_the_switch_is_off(tmp_path, ks):
    assert settings.LIVE_EXECUTION_ENABLED is False
    ev = str(tmp_path / 'e.jsonl')
    r = eg.submit(order(), state(), mode='live', events_path=ev, kill_switch_path=ks)
    assert r['status'] == 'blocked' and 'disabled' in r['reason']
    assert evlog.verify(ev)[0] and evlog.read(ev)[0]['type'] == 'order_blocked'


def test_live_mode_still_has_no_broker_even_if_the_switch_were_flipped(tmp_path, ks, monkeypatch):
    monkeypatch.setattr(settings, 'LIVE_EXECUTION_ENABLED', True)
    with pytest.raises(eg.LiveTradingDisabled):
        eg.submit(order(), state(), mode='live', events_path=str(tmp_path / 'e.jsonl'), kill_switch_path=ks)


def test_paper_orders_are_simulated_and_logged_not_sent(tmp_path, ks):
    ev = str(tmp_path / 'e.jsonl')
    r = eg.submit(order(), state(), events_path=ev, kill_switch_path=ks)
    assert r['status'] == 'simulated' and 'nothing was sent' in r['reason']
    e = evlog.read(ev)[0]
    assert e['type'] == 'order_simulated' and e['data']['simulated'] is True
    r2 = eg.submit(order(), state(submitted_ids=['c1']), events_path=ev, kill_switch_path=ks)
    assert r2['status'] == 'blocked' and evlog.verify(ev)[0]


# ------------------------------------------------------------ structural guarantees
def _imports(path):
    tree = ast.parse(open(path).read())
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out |= {a.name.split('.')[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module.split('.')[0])
    return out


def test_riskgate_is_independent_of_signal_generation():
    imps = _imports(os.path.join(ROOT, 'riskgate.py'))
    forbidden = {'strategy', 'screener', 'backtest', 'analysis', 'ledger', 'research', 'benchmarks', 'readiness', 'health',
                 'intraday', 'paper', 'pandas', 'numpy', 'yfinance', 'requests'}
    assert not (imps & forbidden), imps & forbidden
    assert imps <= {'json', 'math', 'os', 'settings'}, imps


def test_no_broker_or_network_code_in_the_repository():
    banned = re.compile(r'\b(kiteconnect|upstox|angelone|smartapi|fyers|dhan|zerodha|ib_insync|alpaca|place_order|placeorder|breeze)\b', re.I)
    offenders = []
    for f in glob.glob(os.path.join(ROOT, '*.py')):
        src = open(f).read()
        if banned.search(re.sub(r'#.*', '', src)) and os.path.basename(f) not in ('execution_guard.py',):
            offenders.append(os.path.basename(f))
    assert offenders == [], offenders
    guard = _imports(os.path.join(ROOT, 'execution_guard.py'))
    assert guard <= {'events', 'riskgate', 'settings'}, guard


def test_live_switch_is_not_environment_overridable():
    src = open(os.path.join(ROOT, 'settings.py')).read()
    line = [l for l in src.splitlines() if l.startswith('LIVE_EXECUTION_ENABLED')][0]
    assert 'environ' not in line and 'False' in line
