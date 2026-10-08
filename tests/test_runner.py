"""src/runner.py (SPEC §10.1) on a throwaway git repo: unregistered specs refused, guarded specs refused before the
freeze and when edited after it, diagnostic and exploratory specs run, every attempt logged, BH count from the log.
Also validates the real specs.yaml."""
import json, os, subprocess, sys
from pathlib import Path
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import runner

REG = """version: 1
prereg: PREREG.md
specs:
  - {id: D1, element: X, family: diagnostic, hypothesis: none, statistic: s, predicted_sign: none, period: na, prereg: X, entry: "script:job.py"}
  - {id: X1, element: X, family: exploratory, hypothesis: h, statistic: s, predicted_sign: '+', period: test, prereg: X, entry: "script:job.py"}
  - {id: H1, element: X, family: confirmatory, hypothesis: h, statistic: s, predicted_sign: '+', period: full, prereg: X, entry: "script:job.py"}
  - {id: P1, element: X, family: primary, hypothesis: h, statistic: s, predicted_sign: '+', period: full, prereg: X, entry: pending}
"""
DRAFT = "# Pre-registration\n> **DRAFT, NOT FROZEN**\n**Frozen at commit:** `TODO`\n"

def git(root, *a): subprocess.run(['git', *a], cwd=root, check=True, capture_output=True)

@pytest.fixture
def repo(tmp_path):
    (tmp_path / 'specs.yaml').write_text(REG); (tmp_path / 'PREREG.md').write_text(DRAFT)
    (tmp_path / 'job.py').write_text("open('ran.txt','a').write('x')\n")
    git(tmp_path, 'init', '-q'); git(tmp_path, '-c', 'user.email=t@t', '-c', 'user.name=t', 'add', '.')
    git(tmp_path, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 'init')
    return tmp_path

def log(root): return [json.loads(l) for l in (root / 'runs.log').read_text().splitlines()]

def freeze(root):
    h = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True).stdout.strip()
    (root / 'PREREG.md').write_text(f"# Pre-registration\n**Frozen at commit:** `{h}` on 2026-10-01\n")
    git(root, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qam', 'freeze')

def test_unregistered_refused(repo):
    assert runner.run('NOPE', root=repo) == 2 and log(repo)[-1]['status'] == 'refused'

def test_diagnostic_and_exploratory_run_and_log(repo, monkeypatch):
    monkeypatch.chdir(repo)
    assert runner.run('D1', root=repo) == 0 and runner.run('X1', root=repo) == 0
    assert [r['status'] for r in log(repo)] == ['ok', 'ok'] and runner.count(root=repo) == (1, ['X1'])

def test_confirmatory_refused_before_freeze(repo):
    assert runner.run('H1', root=repo) == 2 and 'before the PREREG freeze' in log(repo)[-1]['reason']

def test_confirmatory_runs_after_freeze_and_refuses_edits(repo, monkeypatch):
    monkeypatch.chdir(repo); freeze(repo)
    assert runner.run('H1', root=repo) == 0
    (repo / 'specs.yaml').write_text(REG.replace('statistic: s, predicted_sign: \'+\', period: full, prereg: X, entry: "script:job.py"}',
                                                 'statistic: CHANGED, predicted_sign: \'+\', period: full, prereg: X, entry: "script:job.py"}'))
    assert runner.run('H1', root=repo) == 2 and 'uncommitted' in log(repo)[-1]['reason']
    git(repo, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qam', 'edit after freeze')
    assert runner.run('H1', root=repo) == 2 and 'freeze commit' in log(repo)[-1]['reason']

def test_pending_entry_refused(repo, monkeypatch):
    monkeypatch.chdir(repo); freeze(repo)
    assert runner.run('P1', root=repo) == 3 and 'pending' in log(repo)[-1]['reason']

def test_real_registry_valid():
    d, specs, conf = runner.load_registry(Path(__file__).resolve().parents[1] / 'specs.yaml')
    assert sorted(conf) == ['C_H1_dense_bbar', 'E_H3_bow_peermom_test']
    # after the freeze only `entry` may differ from the frozen registry (01cb5cc)
    import subprocess, yaml
    old = subprocess.run(['git', 'show', '01cb5cc4bab2fe05c7b16690bac4015e17a499f6:specs.yaml'], capture_output=True, text=True,
                         cwd=Path(__file__).resolve().parents[1])
    if old.returncode == 0:
        frozen = {s['id']: s for s in yaml.safe_load(old.stdout)['specs']}
        for i in conf + ['B_primary_alignment_share']:
            assert runner._frozen_fields(frozen[i]) == runner._frozen_fields(specs[i])

def test_filling_a_pending_entry_is_allowed_after_freeze(repo, monkeypatch):
    """The code pointer may go from 'pending' to real code after the freeze; nothing else may change."""
    monkeypatch.chdir(repo); freeze(repo)
    (repo / 'specs.yaml').write_text(REG.replace('prereg: X, entry: pending}', 'prereg: X, entry: "script:job.py"}'))
    git(repo, '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qam', 'write P1 code')
    assert runner.run('P1', root=repo) == 0

def test_dirty_code_refused_for_guarded(repo, monkeypatch):
    monkeypatch.chdir(repo); freeze(repo)
    (repo / 'job.py').write_text("open('ran.txt','a').write('y')\n")
    assert runner.run('H1', root=repo) == 2 and 'uncommitted' in log(repo)[-1]['reason']
