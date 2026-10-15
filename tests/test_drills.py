"""Failure-injection drills: damage a real artefact and check the system stops instead of carrying on.
docs/DRILLS.md maps every failure mode to the test that proves it; these are the end-to-end ones on real files."""
import json, os, shutil, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import events as evlog
import pretrade as pt
import prereg
from test_pretrade import ctx, blockers

ROOT = os.path.join(os.path.dirname(__file__), '..')


def test_flipping_one_byte_in_the_shipped_event_log_is_detected(tmp_path):
    src = os.path.join(ROOT, 'events.jsonl')
    assert evlog.verify(src)[0] is True
    raw = open(src, 'rb').read()
    i = raw.index(b'"type"') + 9
    bad = tmp_path / 'events.jsonl'
    bad.write_bytes(raw[:i] + (b'X' if raw[i:i + 1] != b'X' else b'Y') + raw[i + 1:])
    ok, _, why = evlog.verify(str(bad))
    assert ok is False and why


def test_deleting_an_event_from_the_middle_breaks_the_chain(tmp_path):
    src = os.path.join(ROOT, 'events.jsonl')
    lines = open(src).read().splitlines(True)
    assert len(lines) > 5
    bad = tmp_path / 'events.jsonl'
    bad.write_text(''.join(lines[:3] + lines[4:]))
    assert evlog.verify(str(bad))[0] is False


def test_empty_or_unreadable_scan_results_mean_no_go_never_a_default_go():
    c = ctx(); c['results'] = {}
    rep = pt.evaluate(c)
    assert rep['verdict'] == 'NO-GO' and rep['tradable'] == [] and {'P1', 'P3'} <= blockers(rep)


def test_ledger_without_a_reconciliation_is_not_trusted():
    c = ctx(); c['ledger'].pop('reconciliation')
    rep = pt.evaluate(c)
    assert rep['verdict'] == 'NO-GO' and 'P6' in blockers(rep)


def test_a_modified_preregistration_blocks_the_checklist_and_every_runner(tmp_path):
    for v in ('PREREG_v1', 'PREREG_v2', 'PREREG_v3'):
        d = tmp_path / v
        d.mkdir()
        for ext in ('json', 'sha256'):
            shutil.copy(os.path.join(ROOT, 'experiments', f'{v}.{ext}'), d / f'{v}.{ext}')
        spec = json.load(open(d / f'{v}.json')); spec['purpose'] = 'edited after the fact'
        json.dump(spec, open(d / f'{v}.json', 'w'), indent=1)
        try:
            prereg.load(v, directory=str(d)); raised = False
        except prereg.PreregMismatch:
            raised = True
        assert raised, v


def test_a_missing_pin_file_is_a_failure_not_a_pass(tmp_path):
    shutil.copy(os.path.join(ROOT, 'experiments', 'PREREG_v3.json'), tmp_path / 'PREREG_v3.json')
    try:
        prereg.load('PREREG_v3', directory=str(tmp_path)); raised = False
    except prereg.PreregMismatch:
        raised = True
    assert raised
