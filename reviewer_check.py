#!/usr/bin/env python3
"""WARP-128 reviewer verification runner (Python 3.11+, standard library).

From the extracted code archive:
    python reviewer_check.py --verify
    python reviewer_check.py --smoke
    python reviewer_check.py --extended
    python reviewer_check.py --noise

Each executable suite runs in a disposable copy of the source tree; archived
reference CSVs and experiment logs are not overwritten. Logs remain in the
reviewer_results/ directory, excluded from source integrity checks.
"""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / 'REVIEWER_SOURCE_MANIFEST.json'


def git_blob_hash(path):
    data = path.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def verify_inventory():
    m = json.loads(MANIFEST.read_text(encoding='utf-8'))
    missing, different = [], []
    for item in m['files']:
        rel = item['path']
        path = ROOT / rel
        if not path.is_file():
            missing.append(rel)
        elif path.stat().st_size != item['size'] or git_blob_hash(path) != item['git_blob_sha1']:
            different.append(rel)
    print('Frozen source commit:', m['source_commit'])
    print('Tracked base-snapshot files:', len(m['files']))
    print('Missing:', len(missing), '; changed:', len(different))
    for path in missing:
        print('MISSING:', path)
    for path in different:
        print('MODIFIED:', path)
    if missing or different:
        raise AssertionError('Source archive does not match its frozen research snapshot')
    print('PASS: every pinned research file matches its Git blob checksum')


def check_noise_csv():
    base = ROOT / 'data' / 'toywarp8'
    with (base / 'QISKIT_NOISE_FINAL_RAW.csv').open(newline='') as f:
        raw = list(csv.DictReader(f))
    with (base / 'QISKIT_NOISE_FINAL_SUMMARY.csv').open(newline='') as f:
        summaries = list(csv.DictReader(f))
    assert len(raw) == 36, f'Expected 36 raw experiments, got {len(raw)}'
    assert len(summaries) == 12, f'Expected 12 summary rows, got {len(summaries)}'
    groups = defaultdict(list)
    for row in raw:
        k = (row['scenario'], int(row['iterations']))
        groups[k].append(row)
    z = 1.959963984540054
    for summary in summaries:
        key = (summary['scenario'], int(summary['iterations']))
        rows = groups[key]
        assert sorted(int(x.get('seed', x.get('requested_seed'))) for x in rows) == [101, 202, 303], key
        assert all('effective_seed' not in x or x['effective_seed'] == x['requested_seed'] for x in rows), key
        assert all(int(x['shots']) == 4096 for x in rows), key
        n = sum(int(x['shots']) for x in rows)
        correct = sum(int(x['correct']) for x in rows)
        p = correct / n
        denom = 1 + z*z/n
        center = (p + z*z/(2*n)) / denom
        radius = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom
        lo, hi = center-radius, center+radius
        assert math.isclose(p, float(summary['pooled_success']), abs_tol=1e-13), key
        assert math.isclose(lo, float(summary['wilson95_low']), abs_tol=1e-13), key
        assert math.isclose(hi, float(summary['wilson95_high']), abs_tol=1e-13), key
        assert int(summary['depth']) == int(rows[0]['depth']), key
        reps = [float(x) for x in summary['replicates'].split(';')]
        assert all(abs(a-int(x['correct'])/4096) < 1e-11 for a,x in zip(reps, rows)), key
        R = 1 if p >= 0.99 else math.ceil(math.log(0.01)/math.log(1-p))
        assert R == int(summary['R99']) and R*key[1] == int(summary['total_iter_99']), key
    assert len(groups) == 12
    print('PASS: 36 raw Toy-WARP observations independently reconstruct all 12 summary rows')
    print('PASS: pooled probabilities, 95% Wilson intervals, restart counts and depths')


def check_archived_data():
    for rel in ['data/RESULTS.txt', 'data/RESOURCE_MODELS_V2.csv',
                'data/COMPONENT_NOISE.csv', 'data/FINITE_SHOT_1024.csv',
                'data/GATELEVEL_GROVER_DEMO.json',
                'validation/cross_cipher/cross_cipher_occupancy.csv',
                'validation/cross_cipher/two_pair_uniqueness.csv',
                'validation/sbox_optimality/SBOX_MITM_CERTIFICATE.txt',
                'validation/warp_core/INDEPENDENT_AUDIT_OUTPUT.txt']:
        assert (ROOT / rel).is_file(), rel
    with (ROOT/'validation/cross_cipher/two_pair_uniqueness.csv').open(newline='') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    for row in rows:
        assert int(row['intersection_size']) == 1
        assert row['intersection_keys'] == row['true_key']
    print('PASS: recorded Mini-AES and S-AES two-pair intersections retain only the true key')
    check_noise_csv()


def run_experiment_suite(level):
    if sys.version_info < (3, 11):
        raise RuntimeError('Python 3.11 or newer is required')
    out = ROOT / 'reviewer_results'
    out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='warp-review-') as tmp:
        stage = Path(tmp) / 'warp-research'
        shutil.copytree(ROOT, stage, ignore=shutil.ignore_patterns('reviewer_results', '.git', '.venv', '__pycache__'))
        env = dict(os.environ)
        env['PYTHONPATH'] = os.pathsep.join([str(stage/'src'), str(stage/'experiments'),
                                              str(stage/'validation/cross_cipher')])
        tasks = [
            ('python_syntax', [sys.executable, '-m', 'compileall', '-q', 'src', 'tests', 'experiments', 'validation']),
            ('warp_phase6', [sys.executable, 'tests/verify_phase6.py']),
            ('balanced_comparator', [sys.executable, 'tests/verify_depth_optimized.py']),
            ('sparse_support', [sys.executable, 'tests/verify_sparse_support.py']),
            ('independent_warp', [sys.executable, 'validation/warp_core/independent_warp_numerical_audit.py']),
            ('toywarp_reference', [sys.executable, 'experiments/toywarp8_reference.py']),
            ('saes_reference', [sys.executable, 'validation/cross_cipher/saes_reference.py']),
            ('depth_resources', [sys.executable, 'experiments/resource_models_v2.py']),
            ('toywarp_qiskit', [sys.executable, 'experiments/toywarp8_qiskit_end_to_end.py']),
        ]
        if shutil.which('g++'):
            tasks.insert(1, ('sbox_compile', ['g++', '-O3', '-std=c++17',
               'validation/sbox_optimality/sbox_nct_mitm_certificate.cpp', '-o', str(stage/'sbox_certificate')]))
            tasks.insert(2, ('sbox_certificate', [str(stage/'sbox_certificate')]))
        else:
            print('WARNING: g++ not found; cannot rerun the C++ optimality search')
        if level in ('extended', 'noise'):
            tasks.extend([
                ('full_cross_cipher_occupancy', [sys.executable, 'validation/cross_cipher/cross_cipher_collision_audit.py']),
                ('local_components_qiskit', [sys.executable, 'experiments/qiskit_local_components.py']),
                ('gatelevel_and_component_noise', [sys.executable, 'experiments/run_phase6.py']),
                ('early_stop', [sys.executable, 'experiments/early_stop_tradeoff.py']),
            ])
        if level == 'noise':
            tasks.append(('replicated_qiskit_noise', [sys.executable, 'experiments/toywarp8_noise_final.py']))
        summary = []
        for name, argv in tasks:
            print('RUN:', name, flush=True)
            completed = subprocess.run(argv, cwd=stage, env=env, text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       check=False)
            (out/(name+'.log')).write_text(completed.stdout, encoding='utf-8')
            summary.append({'name':name,'returncode':completed.returncode,
                            'command':' '.join(argv),'log':f'reviewer_results/{name}.log'})
            print('PASS' if completed.returncode == 0 else 'FAIL', name, flush=True)
            if completed.returncode:
                print(completed.stdout[-3500:])
                break
        (out/'status.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        if any(x['returncode'] != 0 for x in summary):
            raise SystemExit('One or more checks failed; see reviewer_results/*.log')
        print(f'PASS: {len(summary)} execution stages; logs under {out}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group()
    g.add_argument('--verify', action='store_true', help='Check all frozen files and recorded data (default)')
    g.add_argument('--smoke', action='store_true', help='Run clean source/data checks and key executable tests')
    g.add_argument('--extended', action='store_true', help='Also run slow cross-cipher simulations')
    g.add_argument('--noise', action='store_true', help='Also regenerate complete replicated Qiskit noise campaign')
    a = p.parse_args()
    verify_inventory()
    check_archived_data()
    if a.smoke or a.extended or a.noise:
        run_experiment_suite('noise' if a.noise else 'extended' if a.extended else 'smoke')
    else:
        print('To execute tests: python reviewer_check.py --smoke')


if __name__ == '__main__':
    main()
