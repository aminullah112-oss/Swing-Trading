"""Pre-registration: the hypotheses and acceptance criteria are fixed in a hash-pinned file BEFORE results exist.

experiments/PREREG_v1.json + PREREG_v1.sha256 are committed together before any experiment is run. The runner refuses
to run if the file no longer matches its recorded hash, so criteria cannot be edited after seeing results. A change
needs a NEW file (PREREG_v2) with its own hash and its own multiple-testing family; the old results stay on record."""
import hashlib
import json
import os

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'experiments')


class PreregMismatch(Exception):
    pass


def file_hash(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def load(version='PREREG_v1', directory=None):
    d = directory or DIR
    path = os.path.join(d, f'{version}.json')
    try:
        recorded = open(os.path.join(d, f'{version}.sha256')).read().strip()
    except OSError:
        raise PreregMismatch(f'{version}.sha256 missing: the pre-registration is not pinned')
    actual = file_hash(path)
    if actual != recorded:
        raise PreregMismatch(f'{version}.json was modified after registration ({actual[:12]} != {recorded[:12]}); create a new version instead')
    with open(path) as f:
        spec = json.load(f)
    spec['_hash'] = actual
    return spec


def alpha_per_test(spec):
    m = spec['multiple_testing']
    return m['alpha_family'] / m['n_tests']
