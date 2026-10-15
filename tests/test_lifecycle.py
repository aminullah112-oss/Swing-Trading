import json, os, sys
from datetime import date
import pandas as pd
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import analysis
import events as ev
import ledger as lg
from test_ledger import flat, sig, results_for, S


def fresh(df, **kw):
    led = lg.empty()
    lg.add_signals(led, results_for(sig('AAA', df, **kw)))
    return led


# ------------------------------------------------------------ calendar expiry
def test_next_session_skips_weekends_and_holidays():
    assert analysis.next_session(date(2026, 10, 9)) == date(2026, 10, 12)                       # Fri -> Mon
    assert analysis.next_session(date(2026, 10, 9), {date(2026, 10, 12)}) == date(2026, 10, 13)  # Monday holiday


def test_expires_on_is_the_next_session_and_expired_signals_are_never_revived():
    df = flat([(100, 100.8, 99.5, 100.2), (100.2, 110, 100, 109)])           # day 1 never reaches 101; day 2 would trigger
    led = fresh(df)
    rec = led['signals'][0]
    assert rec['expires_on'] == str(df.index[S + 1].date()) and rec['simulated'] is True
    lg.update_status(led, {'AAA': df})
    assert rec['status'] == 'expired' and rec['expired_reason'] == 'trigger_not_hit' and 'entry_date' not in rec
    for _ in range(3):                                                        # later updates, even with the breakout, change nothing
        lg.update_status(led, {'AAA': df})
    assert rec['status'] == 'expired'
    with pytest.raises(lg.IllegalTransition):
        lg.transition(rec, 'open', 'attempted revival')


def test_missing_entry_session_bar_keeps_signal_pending_and_flags_it():
    df = flat([(100, 100.8, 99.5, 100.2), (100.2, 110, 100, 109)])
    gap = df.drop(df.index[S + 1])                                            # the entry session's bar is absent from the data
    led = fresh(df)
    lg.update_status(led, {'AAA': gap}, expected_session=df.index[-1].date())
    rec = led['signals'][0]
    assert rec['status'] == 'pending' and rec['needs_data'] is True
    r = lg.reconcile(led)
    assert any(i['kind'] == 'needs_data' for i in r['issues'])


def test_stale_data_beyond_entry_session_is_flagged_not_guessed():
    df = flat([])
    led = fresh(df)
    exp = pd.Timestamp(led['signals'][0]['expires_on']).date()
    lg.update_status(led, {'AAA': df}, expected_session=analysis.next_session(exp))
    assert led['signals'][0]['status'] == 'pending' and led['signals'][0]['needs_data'] is True
    r = lg.reconcile(led, expected_session=analysis.next_session(exp))
    assert any(i['kind'] in ('needs_data', 'overdue_pending') for i in r['issues'])


# ------------------------------------------------------------ transitions
def test_transition_table_rejects_illegal_moves():
    r = {'id': 'A|d', 'status': 'closed'}
    for new in ('open', 'pending', 'expired'):
        with pytest.raises(lg.IllegalTransition):
            lg.transition(r, new)
    r = {'id': 'A|d', 'status': 'open'}
    with pytest.raises(lg.IllegalTransition):
        lg.transition(r, 'expired')
    assert lg.transition({'id': 'A|d', 'status': 'pending'}, 'cancelled', 'operator') is True


# ------------------------------------------------------------ ingestion: idempotency, duplicates, replay, untrusted
def test_ingestion_is_idempotent_by_scan_and_by_signal_id():
    df = flat([])
    res = results_for(sig('AAA', df))
    led = lg.empty()
    assert lg.add_signals(led, res) == 1
    assert lg.add_signals(led, res) == 0                                      # same scan replayed
    assert len(led['signals']) == 1
    res2 = dict(res, scan_id='other')                                         # a new scan_id carrying the same signal id
    assert lg.add_signals(led, res2) == 0 and len(led['signals']) == 1 and led['duplicates_skipped'] == 1


def test_older_scan_is_blocked_as_replay():
    df = flat([])
    led = lg.empty()
    lg.add_signals(led, results_for(sig('AAA', df)))
    old = dict(results_for(sig('BBB', df)), scan_id='old', data_cutoff='2023-01-02')
    assert lg.add_signals(led, old) == 0 and 'replay' in led['last_ingest']['blocked']
    assert [s['symbol'] for s in led['signals']] == ['AAA']


def test_stale_signal_dates_and_busy_symbols_are_recorded_as_rejected():
    df = flat([])
    led = lg.empty()
    r = results_for(sig('AAA', df))
    stale = dict(sig('BBB', df), signal_date='2020-01-01')
    r['stocks'].append(stale)
    lg.add_signals(led, r)
    st = {s['symbol']: s for s in led['signals']}
    assert st['AAA']['status'] == 'pending'
    assert st['BBB']['status'] == 'rejected' and 'stale signal' in st['BBB']['reject_reason']
    led2 = lg.empty()                                                         # same symbol, different day, while the first is active
    lg.add_signals(led2, results_for(sig('AAA', df)))
    nxt = dict(sig('AAA', df), signal_date='2024-06-03')
    res = dict(results_for(nxt), scan_id='n2', data_cutoff='2024-06-03')
    lg.add_signals(led2, res)
    assert led2['signals'][1]['status'] == 'rejected' and 'already has an active' in led2['signals'][1]['reject_reason']


# ------------------------------------------------------------ fills
def test_partial_fill_limited_by_entry_day_liquidity():
    df = flat([(100.5, 102, 100, 101.5), (101.5, 103, 101, 102.5)])
    df.loc[df.index[S + 1], 'Volume'] = 400                                   # 5% participation -> 20 shares
    led = fresh(df, shares=100, risk=300.0)
    lg.update_status(led, {'AAA': df})
    rec = led['signals'][0]
    assert rec['status'] == 'open' and rec['filled_shares'] == 20 and rec['fill_ratio'] == 0.2
    assert lg.eff_shares(rec) == 20 and abs(lg.eff_risk(rec) - 60.0) < 1e-9


def test_no_liquidity_cancels_the_order():
    df = flat([(100.5, 102, 100, 101.5)])
    df.loc[df.index[S + 1], 'Volume'] = 10
    led = fresh(df)
    lg.update_status(led, {'AAA': df})
    assert led['signals'][0]['status'] == 'cancelled' and led['signals'][0]['cancel_reason'] == 'no_liquidity'


def test_gap_through_stop_is_recorded_with_loss_beyond_one_r():
    df = flat([(100.5, 102, 100, 101.5), (92, 93, 90, 91)])                   # next open gaps well below the 97 stop
    led = fresh(df)
    lg.update_status(led, {'AAA': df})
    rec = led['signals'][0]
    assert rec['status'] == 'closed' and rec['gap_through_stop'] is True and rec['r'] < -1.5 and rec['gap_loss_beyond_stop_r'] > 0.5


# ------------------------------------------------------------ event chain
def test_event_chain_detects_tampering(tmp_path):
    p = str(tmp_path / 'events.jsonl')
    for i in range(5):
        ev.append(p, 'x', f'ref{i}', {'i': i}, ts='2026-10-13T00:00:00+00:00')
    assert ev.verify(p) == (True, 5, None)
    lines = open(p).read().splitlines()
    open(p, 'w').write('\n'.join(lines[:2] + lines[3:]) + '\n')                # delete an event
    ok, _, why = ev.verify(p)
    assert not ok and 'sequence' in why
    d = json.loads(lines[2]); d['data']['i'] = 99                              # edit an event in place
    open(p, 'w').write('\n'.join(lines[:2] + [json.dumps(d)] + lines[3:]) + '\n')
    assert not ev.verify(p)[0]
    open(p, 'w').write('\n'.join([lines[1], lines[0]] + lines[2:]) + '\n')     # reorder
    assert not ev.verify(p)[0]


def test_append_only_prefix_check():
    assert ev.extends(b'abc\n', b'abc\ndef\n') and not ev.extends(b'abc\n', b'abd\ndef\n')


def test_lifecycle_is_logged_and_replay_matches_the_ledger(tmp_path):
    p = str(tmp_path / 'events.jsonl')
    df = flat([(100.5, 102, 100, 101.5), (101, 101.5, 96, 98)])
    led = lg.empty()
    lg.add_signals(led, results_for(sig('AAA', df)), events=p, ts='t0')
    lg.update_status(led, {'AAA': df}, events=p, ts='t1')
    rec = led['signals'][0]
    assert rec['status'] == 'closed' and [h['to'] for h in rec['history']] == ['pending', 'open', 'closed']
    assert ev.verify(p)[0]
    assert lg.replay_statuses(ev.read(p)) == {rec['id']: 'closed'}
    assert lg.reconcile(led, ev.read(p))['ok']
    rec['status'] = 'expired'                                                  # edit the ledger without an event
    kinds = {i['kind'] for i in lg.reconcile(led, ev.read(p))['issues']}
    assert 'event_mismatch' in kinds


def test_reconcile_finds_duplicates_and_active_conflicts():
    df = flat([])
    led = fresh(df)
    led['signals'].append(dict(led['signals'][0]))                              # duplicated record
    led['signals'].append(dict(led['signals'][0], id='AAA|2020-01-01', signal_date='2020-01-01'))   # second active AAA
    kinds = {i['kind'] for i in lg.reconcile(led)['issues']}
    assert {'duplicate_id', 'duplicate_active'} <= kinds


def test_legacy_records_are_migrated_once_kept_and_excluded_from_evidence(tmp_path):
    p = str(tmp_path / 'events.jsonl')
    led = lg.empty()
    led['version'] = 1
    led['signals'].append({'id': 'AAA|2026-10-12', 'symbol': 'AAA', 'signal_date': '2026-10-12', 'status': 'pending', 'scan_id': 's1', 'shares': 1, 'risk_amount': 1})
    assert lg.migrate(led, p, 't') == 1 and lg.migrate(led, p, 't') == 0      # idempotent
    r = led['signals'][0]
    assert r['legacy'] and r['evidence_eligible'] is False and r['expires_on'] == '2026-10-13' and led['version'] == lg.VERSION
    assert ev.verify(p) == (True, 1, None) and lg.reconcile(led, ev.read(p))['ok']


# ------------------------------------------------------------ legacy records, stale bookkeeping and unfinished-session fills
def test_legacy_records_hold_no_budget_block_no_symbol_and_are_not_taken():
    df = flat([(100.5, 102, 100, 101.5), (101.5, 103, 101, 102.5)])
    led = fresh(df)
    lg.update_status(led, {'AAA': df})
    rec = led['signals'][0]
    assert rec['status'] == 'open'
    rec.update(legacy=True, evidence_eligible=False)
    lg.mark_taken(led, 565000, 0.015)
    assert rec['taken'] is False and 'legacy' in rec['not_taken_reason']
    # the same symbol can get a fresh signal while the legacy position is still open
    res = dict(results_for(dict(sig('AAA', df), signal_date='2024-06-03')), scan_id='n2', data_cutoff='2024-06-03')
    assert lg.add_signals(led, res) == 1 and led['signals'][1]['status'] == 'pending'


def test_stale_bookkeeping_rejection_is_reinstated_while_the_entry_session_is_ahead():
    df = flat([])
    led = lg.empty()
    old = dict(sig('AAA', df))
    first = dict(results_for(sig('BBB', df)), expected_session='2024-06-03')          # BBB active
    lg.add_signals(led, first)
    again = dict(results_for(dict(old, symbol='BBB')), scan_id='s2', expected_session='2024-06-03')
    again['stocks'] = [dict(old, symbol='BBB', signal_date='2024-06-03')]
    again['data_cutoff'] = '2024-06-03'
    lg.add_signals(led, again)                                                         # rejected: BBB already active
    rej = [s for s in led['signals'] if s['status'] == 'rejected'][0]
    assert 'already has an active signal' in rej['reject_reason'] and rej['expires_on'] == '2024-06-04'
    rej_id = rej['id']
    led['signals'][0]['status'] = 'expired'                                            # the earlier BBB signal has since expired
    p = dict(again, scan_id='s3', expected_session='2024-06-03')
    assert lg.add_signals(led, p) == 1
    back = [s for s in led['signals'] if s['id'] == rej_id][0]
    assert back['status'] == 'pending' and back['history'][-1]['reason'].startswith('reinstated') and 'reject_reason' not in back
    assert lg.reconcile(led)['ok']
    # once the entry session has passed it must NOT be reinstated
    led2 = lg.empty()
    led2['signals'] = [dict(rej, status='rejected', reject_reason='symbol already has an active signal')]
    late = dict(again, scan_id='s9', expected_session='2024-06-04')
    assert lg.add_signals(led2, late) == 0 and led2['signals'][0]['status'] == 'rejected'


def test_fill_on_an_unfinished_session_is_voided_with_an_audit_trail(tmp_path):
    p = str(tmp_path / 'e.jsonl')
    df = flat([(100.5, 102, 100, 101.5), (101.5, 103, 101, 102.5)])
    led = fresh(df)
    lg.update_status(led, {'AAA': df}, events=p)
    assert led['signals'][0]['status'] == 'open'
    official = df.iloc[:-1]                                                            # the last bar was the unfinished session
    led['signals'][0]['entry_date'] = str(df.index[-1].date())
    lg.update_status(led, {'AAA': official}, events=p, ts='t')
    rec = led['signals'][0]
    assert rec['status'] == 'void' and 'unfinished' in rec['void_reason']
    assert [e['type'] for e in ev.read(p)][-1] == 'fill_voided' and lg.replay_statuses(ev.read(p))[rec['id']] == 'void'


def test_reconcile_does_not_flag_a_legacy_position_overlapping_a_current_signal():
    df = flat([])
    led = fresh(df)
    legacy = dict(led['signals'][0], id='AAA|2020-01-01', signal_date='2020-01-01', legacy=True, evidence_eligible=False, status='open')
    led['signals'].append(legacy)
    assert 'duplicate_active' not in {i['kind'] for i in lg.reconcile(led)['issues']}
    led['signals'].append(dict(led['signals'][0], id='AAA|2020-02-02', signal_date='2020-02-02'))          # two CURRENT active ones is still a defect
    assert 'duplicate_active' in {i['kind'] for i in lg.reconcile(led)['issues']}
