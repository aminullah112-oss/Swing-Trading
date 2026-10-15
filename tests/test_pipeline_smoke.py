"""End-to-end smoke test of the daily pipeline after the scan: paper.py -> health.py -> forward_report.py -> readiness.py -> remediation.py,
run in an empty directory with a stubbed price download. Verifies the artefacts agree and fail closed."""
import json, os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import events as evlog
import forward_report
import health
import paper
import readiness
import remediation
from test_ledger import flat, sig, results_for


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run_pipeline(df, results, monkeypatch):
    json.dump(results, open('results.json', 'w'))
    monkeypatch.setattr(paper, 'fetch_frames', lambda syms: {s: df for s in syms})
    paper.main()
    return json.load(open('ledger.json'))


def test_paper_run_writes_a_consistent_ledger_and_event_chain(workdir, monkeypatch):
    df = flat([(100.5, 102, 100, 101.5), (101, 101.5, 96, 98)])                  # triggers, then stops out
    res = dict(results_for(sig('AAA', df)), risk_config={'capital': 565000, 'risk_pct': 0.5, 'max_pos_pct': 25, 'max_open_risk_pct': 1.5},
               data_cutoff=str(df.index[-1].date()))
    res['data_cutoff'] = str(df.index[100].date())                               # the scan ran on the signal date
    led = run_pipeline(df, res, monkeypatch)
    rec = led['signals'][0]
    assert rec['status'] == 'closed' and rec['simulated'] is True and led['reconciliation']['ok'] is True
    assert led['provenance']['kind'] == 'ledger' and led['summary']['closed'] == 1
    ok, n, why = evlog.verify('events.jsonl')
    assert ok and n >= 3                                                         # recorded, opened, closed
    # re-running the same scan changes nothing (idempotent) and the log only grows by transitions that did not already happen
    before = open('events.jsonl').read()
    paper.main()
    assert open('events.jsonl').read().startswith(before)
    assert json.load(open('ledger.json'))['signals'][0]['status'] == 'closed' and len(json.load(open('ledger.json'))['signals']) == 1


def test_paper_run_refuses_to_proceed_on_a_tampered_event_log(workdir, monkeypatch):
    df = flat([(100.5, 102, 100, 101.5)])
    res = dict(results_for(sig('AAA', df)), data_cutoff=str(df.index[100].date()))
    run_pipeline(df, res, monkeypatch)
    lines = open('events.jsonl').read().splitlines()
    open('events.jsonl', 'w').write('\n'.join(lines[1:]) + '\n')                  # delete the first event
    with pytest.raises(SystemExit) as e:
        paper.main()
    assert e.value.code == 2


def test_untrusted_scan_adds_nothing_and_health_degrades(workdir, monkeypatch):
    df = flat([])
    bad = dict(results_for(sig('AAA', df)), actionable=False, stocks=[], data_quality={'status': 'UNTRUSTED', 'reasons': ['stale']},
               data_cutoff='2024-01-01', strategy={'x': 1}, risk_config={'capital': 565000, 'risk_pct': 0.5, 'max_pos_pct': 25, 'max_open_risk_pct': 1.5})
    led = run_pipeline(df, bad, monkeypatch)
    assert led['signals'] == [] and 'not trusted' in led['last_ingest']['blocked']
    with pytest.raises(SystemExit):                                              # a 2024 cutoff is also a stale-data FAIL
        health.main()
    h = json.load(open('health.json'))
    assert h['status'] in ('DEGRADED', 'FAIL') and h['permits']['new_entries'] is False
    readiness.main()
    r = json.load(open('readiness.json'))
    assert r['policy']['live_risk_pct_allowed'] == 0.0 and r['policy']['mode'] == 'PAPER ONLY'
    o1 = [g for g in r['gates'] if g['id'] == 'O1'][0]
    assert o1['earned'] == 0
    forward_report.main()
    remediation.main()
    assert os.path.exists('reports/forward.md') and os.path.exists('reports/remediation.md')
    assert json.load(open('reports/remediation.json'))['ceiling_after_reruns'] < 7


def test_paper_never_simulates_fills_on_the_unfinished_session(workdir, monkeypatch):
    """A partial bar dated after the expected session must not trigger or stop out a pending signal."""
    import pandas as pd
    import analysis
    df = flat([(100.5, 102, 100, 101.5)])                                        # a real entry-day bar for the signal
    live = df.index[-1] + pd.offsets.BDay(1)
    df.loc[live] = (101.5, 140, 80, 90, 1e6)                                      # wild partial 'today' bar
    monkeypatch.setattr(analysis, 'expected_last_session', lambda now_ist, close_hhmm=(16, 30), holidays=frozenset(): df.index[-2].date())
    res = dict(results_for(sig('AAA', flat([]))), data_cutoff=str(df.index[100].date()))
    led = run_pipeline(df, res, monkeypatch)
    rec = led['signals'][0]
    assert rec['status'] == 'open' and rec.get('exit_reason') is None and rec['entry_date'] == str(df.index[-2].date())     # not stopped by the 80 low
