import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ledger as lg
import forward_report as fr


def rec(i, status, **kw):
    d = {'id': f'S{i}|d', 'symbol': f'S{i}', 'signal_date': 'd', 'status': status, 'setup': 'TRENDING', 'shares': 1, 'risk_amount': 1.0}
    d.update(kw)
    return d


def test_every_status_gets_one_class_and_tallies_add_up():
    led = lg.empty()
    led['signals'] = [rec(1, 'closed', r=1.8, exit_reason='ema50'), rec(2, 'closed', r=-1.0, exit_reason='stop'),
                      rec(3, 'closed', r=-1.9, exit_reason='gap_stop'), rec(4, 'closed', r=-0.3, exit_reason='ema50'),
                      rec(5, 'closed', r=0.4, exit_reason='time'), rec(6, 'open', unrealized_r=0.7), rec(7, 'open', unrealized_r=-0.2),
                      rec(8, 'expired'), rec(9, 'pending'), rec(10, 'rejected'), rec(11, 'cancelled'), rec(12, 'void'),
                      rec(13, 'closed', r=5.0, exit_reason='ema50', evidence_eligible=False)]
    oc = lg.outcomes(led)
    n = {k: v['n'] for k, v in oc['classes'].items()}
    assert n == {'won': 2, 'stopped': 2, 'exited_loss': 1, 'open_profit': 1, 'open_loss': 1, 'never_triggered': 1, 'waiting': 1, 'not_tradable': 3}
    assert oc['legacy_excluded'] == 1 and sum(n.values()) == 12
    assert oc['entered'] == 7 and oc['closed'] == 5 and oc['closed_win_rate'] == 0.4
    assert oc['entered_in_profit_rate'] == round(3 / 7, 3) and oc['trigger_rate'] == round(7 / 8, 3)
    assert oc['classes']['stopped']['avg_r'] == -1.45 and oc['by_setup']['TRENDING'] == {'entered': 7, 'good': 3, 'hit_rate': round(3 / 7, 3)}
    assert lg.summarize(led)['outcomes']['entered'] == 7


def test_empty_ledger_and_report_text():
    led = lg.empty(); led['summary'] = lg.summarize(led)
    oc = led['summary']['outcomes']
    assert oc['closed_win_rate'] is None and oc['trigger_rate'] is None
    led['signals'] = [rec(1, 'closed', r=2.0, exit_reason='ema50', exit_date='2026-01-01', entry_date='2025-12-01')]; led['summary'] = lg.summarize(led)
    md = fr.markdown(fr.build(led, [], 565000))
    assert 'How the filtered stocks fared' in md and 'Won: closed in profit: 1' in md
