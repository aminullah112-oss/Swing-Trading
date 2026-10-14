import os, sys
from datetime import date
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import corpevents as ce
import pretrade as pt
import selection as sel
import settings
import universe
from test_pretrade import ctx, stock
from test_scan_fail_closed import make_bulk, run_scan  # noqa: F401
import screener as sc

REC = {'from_52w_high': -5.0, 'avg_value_cr': 20.0, 'atr_pct': 3.0}


# ------------------------------------------------------------ sectors
def test_every_universe_symbol_has_a_sector_and_unknowns_never_share_a_bucket():
    sectors = sel.load_sectors()
    u = universe.load('U159_v2')
    assert [s for s in u['symbols'] if s not in sectors] == []
    assert sectors['ETERNAL'] == sectors['ZOMATO'] and sectors['TMPV'] == sectors['TATAMOTORS']
    assert sel.sector_of('NEWCO1', sectors) != sel.sector_of('NEWCO2', sectors)


def test_sector_cap_counts_existing_and_new_positions():
    sec = {'A': 'Banks', 'B': 'Banks', 'C': 'Banks', 'D': 'IT'}
    assert sel.sector_ok('C', ['A', 'D'], sec)[0] is True
    ok, g, n = sel.sector_ok('C', ['A', 'B'], sec)
    assert (ok, g, n) == (False, 'Banks', 2) and settings.MAX_PER_SECTOR == 2
    assert sel.sector_ok('X', ['A', 'B'], sec)[0] is True                       # unmapped symbol is its own bucket


# ------------------------------------------------------------ rank, regime, tier, size
def trend(n, drift, seed):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end='2026-10-13', periods=n)
    return pd.DataFrame({'Close': 100 * np.cumprod(1 + drift + 0.01 * rng.standard_normal(n))}, index=idx)


def test_rank_orders_by_vol_adjusted_momentum_and_needs_253_bars():
    frames = {'UP': trend(400, 0.003, 1), 'FLAT': trend(400, 0.0, 2), 'DOWN': trend(400, -0.003, 3), 'SHORT': trend(200, 0.003, 4)}
    r = sel.rank_universe(frames)
    assert r['UP'] > r['FLAT'] > r['DOWN'] and r['UP'] == 1.0 and np.isnan(r['SHORT'])
    assert np.isnan(sel.momentum(frames['SHORT']))


def test_regime():
    up = pd.Series(np.linspace(100, 200, 300)); down = pd.Series(np.linspace(200, 100, 300))
    assert sel.regime(up) == 'bull' and sel.regime(down) == 'bear' and sel.regime(None) == 'unknown' and sel.regime(up.iloc[:50]) == 'unknown'


def test_tier_requires_every_condition_and_avoid_beats_everything():
    t, c = sel.tier(REC, 0.9, 'bull', False)
    assert t == 'preferred' and all(c.values())
    for rec, rank, reg in ((dict(REC, from_52w_high=-15.0), 0.9, 'bull'), (dict(REC, avg_value_cr=2.0), 0.9, 'bull'), (dict(REC, atr_pct=5.0), 0.9, 'bull'),
                           (REC, 0.5, 'bull'), (REC, 0.9, 'bear'), (REC, None, 'bull'), (REC, float('nan'), 'bull')):
        assert sel.tier(rec, rank, reg, False)[0] == 'standard'
    assert sel.tier(REC, 0.9, 'bull', True)[0] == 'avoid'


def test_size_multiplier_only_shrinks_and_regime_halving_is_off(monkeypatch):
    assert sel.size_multiplier(dict(REC, atr_pct=3.0), 'bear') == (1.0, [])            # regime halving failed its test: off
    m, notes = sel.size_multiplier(dict(REC, atr_pct=5.0), 'bull')
    assert m == 0.75 and 'size x0.75' in notes[0]
    monkeypatch.setattr(settings, 'VOL_SCALE_ENABLED', False)
    assert sel.size_multiplier(dict(REC, atr_pct=5.0), 'bull')[0] == 1.0
    monkeypatch.setattr(settings, 'REGIME_HALVING_ENABLED', True)
    assert sel.size_multiplier(REC, 'bear')[0] == 0.5
    assert settings.REGIME_HALVING_ENABLED is True                                       # (patched here only)


def test_position_scaling_shrinks_risk():
    rec = {'trigger': 100.0, 'stop_loss': 96.0}
    full, half = sc.position(dict(rec)), sc.position(dict(rec), 0.0, 0.5, ['x'])
    assert half['shares'] <= full['shares'] / 2 + 1 and half['size_notes'] == ['x']
    assert sc.position(dict(rec), 0.0, 5.0)['shares'] == full['shares']                  # a multiplier above 1 is ignored


# ------------------------------------------------------------ events
def test_manual_events_block_inside_the_window_only(tmp_path):
    p = tmp_path / 'cal.json'
    p.write_text('{"updated": "2026-10-13", "events": [{"symbol": "TCS", "date": "2026-10-16", "kind": "earnings", "note": "Q2"}, '
                 '{"symbol": "INFY", "date": "2026-11-30", "kind": "ex_date"}, {"symbol": "BAD", "date": "oops"}], "asm_gsm": ["SUZLON"]}')
    man = ce.load_manual(str(p))
    ban = {'status': 'ok', 'symbols': {'IDEA'}}
    sig = date(2026, 10, 13)
    a = ce.assess('TCS', sig, man, ban)
    assert a['blocked'] and 'results on 2026-10-16 (3 session(s) away): Q2' in a['reasons'][0] and a['unverified'] == []
    assert not ce.assess('INFY', sig, man, ban)['blocked']                              # far away
    assert ce.assess('SUZLON', sig, man, ban)['blocked'] and 'ASM/GSM' in ce.assess('SUZLON', sig, man, ban)['reasons'][0]
    assert ce.assess('IDEA', sig, man, ban)['reasons'] == ['in the F&O ban list']
    assert not ce.assess('TCS', date(2026, 10, 17), man, ban)['blocked']                # event already passed
    assert len(man['events']) == 2                                                      # the malformed row is skipped


def test_unknowns_are_flagged_not_treated_as_clear():
    man = ce.load_manual('/nonexistent.json')
    a = ce.assess('XYZ', date(2026, 10, 13), man, {'status': 'unavailable', 'symbols': set()})
    assert not a['blocked'] and len(a['unverified']) == 3
    a2 = ce.assess('XYZ', date(2026, 10, 13), dict(man, updated='2026-10-13'), {'status': 'ok', 'symbols': set()}, earnings_date=date(2026, 10, 15))
    assert a2['blocked'] and 'from yfinance: confirm' in a2['reasons'][0]


def test_ban_list_parsing_and_fetch_failure_modes():
    assert ce.parse_ban('Securities in Ban For Trade Date 13-OCT-2026:\n1,IDEA\n2,SAIL\n') == {'IDEA', 'SAIL'}
    assert ce.parse_ban('') == set()
    ok = ce.fetch_ban(date(2026, 10, 13), downloader=lambda url: '1,IDEA\n')
    assert ok['status'] == 'ok' and ok['symbols'] == {'IDEA'}
    def boom(url):
        raise OSError('403')
    assert ce.fetch_ban(date(2026, 10, 13), downloader=boom)['status'] == 'unavailable'
    assert ce.fetch_ban(date(2026, 10, 13))['status'] == 'disabled'                     # conftest sets EDGE_EVENTS=0


# ------------------------------------------------------------ through the scanner and the pre-trade list
def test_scan_attaches_selection_and_blocks_known_events(run_scan, monkeypatch):
    bulk = make_bulk()
    r0 = run_scan(bulk)
    assert r0['stocks'], 'fixture must produce signals'
    for s in r0['stocks']:
        x = s['selection']
        assert x['tier'] in ('preferred', 'standard') and x['sector'] and 'hypothesis' in x['status']
        assert x['events']['unverified'] and s['position']['size_notes'] == x['size_notes']
    victim = r0['stocks'][0]['symbol']
    monkeypatch.setattr(sc.corpevents, 'load_manual', lambda *a, **k: {'events': [{'symbol': victim, 'date': date(2026, 10, 15), 'kind': 'earnings', 'note': 'Q2'}],
                                                                       'asm_gsm': [], 'updated': '2026-10-13'})
    r1 = run_scan(bulk)
    v = [s for s in r1['stocks'] if s['symbol'] == victim][0]
    assert v['selection']['tier'] == 'avoid' and v['execution_ok'] is False
    assert any(c['id'] == 'events' and c['status'] == 'block' for c in v['checks'])


def test_pretrade_enforces_the_sector_cap(monkeypatch):
    monkeypatch.setattr(sel, 'load_sectors', lambda *a, **k: {'A': 'Banks', 'B': 'Banks', 'C': 'Banks', 'D': 'Banks', 'E': 'IT'})
    c = ctx([stock(n) for n in 'ABCDE'])
    c['ledger']['signals'] = []
    rep = pt.evaluate(c)
    assert [t['symbol'] for t in rep['tradable']] == ['A', 'B', 'E']
    why = {r['symbol']: ' '.join(r['reasons']) for r in rep['rejected']}
    assert 'sector cap' in why['C'] and 'sector cap' in why['D']
    c['ledger']['signals'] = [{'id': 'Z|d', 'symbol': 'A', 'status': 'open', 'shares': 1, 'risk_amount': 1, 'taken': False}]
    assert [t['symbol'] for t in pt.evaluate(c)['tradable']] == ['B', 'E']             # one Banks slot already held
