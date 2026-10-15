import json, os, random, shutil, subprocess, sys, textwrap
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import risk
import selection as sel

ROOT = os.path.join(os.path.dirname(__file__), '..')
node = shutil.which('node')
pytestmark = pytest.mark.skipif(node is None, reason='node not installed')


def run_node(code):
    out = subprocess.run([node, '-e', code], capture_output=True, text=True, cwd=ROOT, timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_js_sizing_matches_risk_py_on_random_inputs():
    rng = random.Random(1)
    cases = [(rng.choice([100000, 565000, 1e6, 2.5e6]), rng.choice([0.25, 0.5, 0.375]), rng.uniform(20, 9000), rng.uniform(0.5, 600), rng.choice([10, 25])) for _ in range(400)]
    js = run_node(f"const m=require('./plan_math.js'); console.log(JSON.stringify({json.dumps(cases)}.map(c=>m.sizeShares(c[0],c[1],c[2],c[3],c[4]))))")
    for (cap, rp, entry, sd, mp), got in zip(cases, js):
        assert got == risk.size_position(cap, rp / 100, entry, sd, mp / 100)['shares'], (cap, rp, entry, sd, mp)


def test_effective_risk_can_only_be_lowered():
    js = run_node("const m=require('./plan_math.js'); console.log(JSON.stringify([m.effectiveRisk('',0.5), m.effectiveRisk('0.25',0.5), m.effectiveRisk('2',0.5), m.effectiveRisk('abc',0.5), m.effectiveRisk(-1,0.5)]))")
    assert js == [0.5, 0.25, 0.5, 0.5, 0.5]
    js = run_node("const m=require('./plan_math.js'); console.log(JSON.stringify(Object.values(m.TIER_MULT).map(x=>x<=1)))")
    assert all(js)


def test_auto_select_respects_budget_sector_cap_ranking_and_holdings():
    code = textwrap.dedent("""
        const m = require('./plan_math.js');
        const c = (symbol, sector, level, rs) => ({symbol, sector, level, rs, entry: 100, stopDist: 5, riskMult: 1});
        const cands = [c('LOW1','A','low',99), c('HIGH1','A','high',50), c('HIGH2','A','high',90), c('HIGH3','A','high',10), c('MED1','B','medium',70), c('AVOID','C','avoid',99), c('HELD','D','high',99)];
        const base = {capital: 565000, riskPct: 0.5, maxOpenRiskPct: 1.5, maxPosPct: 25, maxPerSector: 2};
        const a = m.autoSelect(cands, base);
        const b = m.autoSelect(cands, Object.assign({}, base, {existingRisk: 4500, held: ['HELD']}));
        const c2 = m.autoSelect(cands, Object.assign({}, base, {maxOpenRiskPct: 5, maxPerSector: 1}));
        console.log(JSON.stringify({a, b, c2, order: m.rank(cands).map(x => x.symbol)}));
    """)
    r = run_node(code)
    assert r['order'] == ['HELD', 'HIGH2', 'HIGH1', 'HIGH3', 'MED1', 'LOW1', 'AVOID']          # conviction, then relative strength; avoid last
    assert r['a'] == ['HELD', 'HIGH2', 'HIGH1']                                               # 3 x 0.5% fills the 1.5% budget; sector A capped at 2 anyway
    assert r['b'] == ['HIGH2']                                                               # 4500 already open leaves one slot; HELD is skipped
    assert r['c2'] == ['HELD', 'HIGH2', 'MED1']                                               # one per sector; AVOID never chosen


def test_conviction_levels_and_avoid_override():
    five = {f'c{i}': True for i in range(5)}
    assert sel.conviction(five, False) == {'level': 'high', 'met': 5, 'of': 5}
    assert sel.conviction(dict(five, c0=False), False)['level'] == 'medium'
    assert sel.conviction(dict(five, c0=False, c1=False), False)['level'] == 'medium'
    assert sel.conviction(dict(five, c0=False, c1=False, c2=False), False)['level'] == 'low'
    assert sel.conviction(five, True)['level'] == 'avoid'


def stock(sym, level, rs, sector='Banks', trigger=100.0, stop=95.0):
    return {'symbol': sym, 'execution_ok': True, 'trigger': trigger, 'stop_loss': stop, 'price': 99.0, 'setup_type': 'TRENDING', 'signal_date': '2026-10-14',
            'ema_50': 94.0, 'ema_20': 98.0, 'rsi': 60.0, 'vol_ratio': 1.2, 'from_52w_high': -5.0, 'atr_pct': 3.0, 'stop_pct': 5.0, 'checks': [], 'spark': None,
            'position': {'shares': 1, 'invested': 100, 'risk_amount': 5}, 'in_stockedge': False,
            'selection': {'tier': 'standard', 'conviction': {'level': level, 'met': 3, 'of': 5}, 'conditions': {'x': True}, 'rs_rank_pct': rs, 'sector': sector, 'regime': 'bull',
                          'events': {'reasons': [], 'unverified': []}, 'risk_mult': 1.0, 'size_notes': []},
            'plan': None}


def render_with(stocks, prefs=None, ledger=None):
    harness = textwrap.dedent("""
        const fs = require('fs');
        const els = {}; const mk = id => els[id] || (els[id] = {id, hidden: false, innerHTML: '', textContent: '', className: '', style: {}, value: '', checked: false,
            addEventListener(){}, querySelectorAll(){ return []; }});
        const store = %s;
        global.localStorage = {getItem: k => store[k] ?? null, setItem: (k, v) => { store[k] = v; }};
        global.document = {getElementById: mk, addEventListener(){}, hidden: false};
        global.setInterval = () => {};
        global.PlanMath = require('./plan_math.js');
        const src = fs.readFileSync('common.js','utf8') + '\\n' + fs.readFileSync('desk.js','utf8') +
            '\\n;globalThis.__run = (d) => { desk.data = d.data; desk.rd = null; desk.ledger = d.ledger; render(); };';
        (0, eval)(src);
        const input = %s;
        __run(input);
        console.log(JSON.stringify({plans: els['plans'].innerHTML, alloc: els['alloc-panel'].innerHTML, sizing: els['sizing-panel'].innerHTML, cap: els['capital-note'].innerHTML}));
    """) % (json.dumps({'edge_desk_prefs_v1': json.dumps(prefs)} if prefs else {}),
            json.dumps({'data': {'risk_config': {'capital': 565000, 'risk_pct': 0.5, 'max_pos_pct': 25, 'max_open_risk_pct': 1.5, 'max_per_sector': 2},
                                  'stocks': stocks, 'market': None, 'total_scanned': 159, 'data_cutoff': '2026-10-14', 'strategy': {}, 'data_quality': {'status': 'TRUSTED'}},
                        'ledger': ledger}))
    return run_node(harness)


def test_desk_sorts_by_conviction_sizes_from_capital_and_builds_a_position_plan():
    stocks = [stock('LOWX', 'low', 99, 'IT'), stock('HIGHX', 'high', 60, 'Banks'), stock('MEDX', 'medium', 80, 'Autos & ancillaries')]
    r = render_with(stocks)
    assert r['plans'].index('HIGHX') < r['plans'].index('MEDX') < r['plans'].index('LOWX')
    assert 'High conviction' in r['plans'] and 'not a probability of profit' in r['plans']
    # 565000 x 0.5% / 5 = 565 shares; position value 56,500 (10%) is under the 25% cap
    assert '<b>565</b>' in r['plans'] and 'reference size' in r['plans']
    assert 'Position plan' in r['alloc'] and '3 positions' in r['alloc'] and 'does not raise the amount at stake' in r['alloc']


def test_custom_capital_and_lower_risk_resize_and_risk_cannot_be_raised():
    r = render_with([stock('HIGHX', 'high', 60)], prefs={'capital': '1000000', 'riskPct': '0.25', 'tierScale': False})
    assert '<b>500</b>' in r['plans'] and 'your size' in r['plans']                      # 1,000,000 x 0.25% / 5
    r = render_with([stock('HIGHX', 'high', 60)], prefs={'capital': '565000', 'riskPct': '3', 'tierScale': False})
    assert '<b>565</b>' in r['plans']                                                     # 3% request is clamped to the 0.5% limit
    r = render_with([stock('LOWX', 'low', 60)], prefs={'capital': '', 'riskPct': '', 'tierScale': True})
    assert '<b>282</b>' in r['plans']                                                     # low conviction: 50% of the risk budget


def test_open_positions_use_up_risk_budget_in_the_plan():
    led = {'signals': [{'status': 'open', 'symbol': 'HELD1', 'shares': 100, 'risk_amount': 4000.0, 'evidence_eligible': True},
                       {'status': 'open', 'symbol': 'OLD', 'shares': 100, 'risk_amount': 9999.0, 'evidence_eligible': False}]}
    r = render_with([stock('HIGHX', 'high', 60), stock('HIGHY', 'high', 70, 'IT'), stock('HIGHZ', 'high', 80, 'Autos & ancillaries')], ledger=led)
    assert '1 position<' in r['alloc'].replace('</b>', '<') and 'including' in r['alloc'] and '9,999' not in r['alloc'] and '9999' not in r['alloc']     # legacy open risk ignored
