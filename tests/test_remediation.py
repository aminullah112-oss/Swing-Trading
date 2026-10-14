import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import readiness as rd
import remediation as rm
import ledger as lg
from test_readiness_health import ctx


def test_matrix_covers_every_gate_and_never_promises_unsupported_points():
    g = rd.evaluate(ctx(lg.empty(), rprov=None))
    pol = rd.policy(g, {}, {'status': 'OK'})
    rep = rm.build({'gates': g, 'policy': pol})
    assert [r['id'] for r in rep['gates']] == [x[0] for x in rd.GATES]
    by = {r['id']: r for r in rep['gates']}
    assert by['B1']['state'] == 'blocked_defect' and by['F2']['state'] == 'pending_time' and by['S1']['state'] == 'unverifiable'
    assert by['R1']['state'] == 'passed'
    # U1 is never counted toward the near-term ceiling; time/event gates are never counted either
    assert rep['ceiling_after_reruns'] == round(0.5 + 0.5 + 0.5, 2) and rep['ceiling_after_reruns'] < 7
    assert all(by[i]['weight'] == dict((x[0], x[2]) for x in rd.GATES)[i] for i in by)             # weights untouched
    assert 'U1 excluded' in rep['u1_note'] and 'Score now' in rm.markdown(rep)


def test_reports_cannot_be_stamped_outside_the_backtest_workflow(monkeypatch, tmp_path):
    import stamp_reports as st
    monkeypatch.delenv('GITHUB_WORKFLOW', raising=False)
    monkeypatch.chdir(tmp_path)
    assert st.main() == 2 and not (tmp_path / 'reports' / 'provenance.json').exists()
    monkeypatch.setenv('GITHUB_WORKFLOW', 'Backtest')
    assert st.main() == 1                                  # in the workflow, but required reports are missing: still refuses
