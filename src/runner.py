"""Specification runner (SPEC §10.1; docs/PREREG.md). The only way to execute a registered analysis.

  python src/runner.py list                 every registered spec (id, family, element, entry)
  python src/runner.py run <spec_id>        run one spec; refuses anything not in specs.yaml
  python src/runner.py count                distinct exploratory specs run (the m for Benjamini-Hochberg)
  python src/runner.py check                validate specs.yaml and report the PREREG freeze state

Rules enforced:
  1. Unregistered id -> refused (exit 2), and the refusal is logged.
  2. family confirmatory or primary -> refused unless docs/PREREG.md is frozen (a 40-hex commit in "Frozen at commit",
     no DRAFT box), the tracked tree has no uncommitted changes (runs.log excepted: the runner appends to it), so every
     guarded result is tied to an exact code commit, and the spec in specs.yaml equals its entry at the freeze commit in
     every field except `entry`. `entry` is the pointer to the code, frozen as 'pending' because the code could only be
     written after the freeze; hypothesis, statistic, sign, period, network, family and element stay locked.
  3. Every attempt (ok, error, refused) is appended to runs.log as one JSON line: time (UTC), spec id, family, element,
     git commit, dirty flag, PREREG frozen flag and commit, status, reason, duration, and the small result summary the
     entry returns (aggregates only, never data rows). runs.log is append-only and committed.
Entries: 'script:<path>' runs the file as __main__ (runpy); '<module>:<function>' imports the module from src/ or
analysis/ and calls function(spec) -> dict; 'pending' means the analysis code does not exist yet (refused as error).
The runner computes nothing itself."""
import sys, os, json, time, subprocess, runpy, importlib, datetime, re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {'confirmatory', 'primary', 'exploratory', 'diagnostic'}
REQUIRED = ['id', 'element', 'family', 'hypothesis', 'statistic', 'predicted_sign', 'period', 'prereg', 'entry']
GUARDED = {'confirmatory', 'primary'}

def _git(*args, root=ROOT):
    r = subprocess.run(['git', *args], cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None

def load_registry(path):
    d = yaml.safe_load(Path(path).read_text())
    specs = d.get('specs') or []
    errs = []
    ids = [s.get('id') for s in specs]
    for s in specs:
        miss = [k for k in REQUIRED if k not in s]
        if miss: errs.append(f"{s.get('id')}: missing {miss}")
        if s.get('family') not in FAMILIES: errs.append(f"{s.get('id')}: family {s.get('family')!r}")
        if str(s.get('predicted_sign')) not in {'+', '-', 'none'}: errs.append(f"{s.get('id')}: predicted_sign {s.get('predicted_sign')!r}")
    dup = {i for i in ids if ids.count(i) > 1}
    if dup: errs.append(f'duplicate ids {sorted(dup)}')
    conf = [s['id'] for s in specs if s.get('family') == 'confirmatory']
    if errs: raise ValueError('specs.yaml invalid: ' + '; '.join(errs))
    return d, {s['id']: s for s in specs}, conf

def freeze_state(prereg_path):
    """(frozen: bool, commit or None). Frozen = a 40-hex hash after 'Frozen at commit' and no DRAFT box."""
    t = Path(prereg_path).read_text()
    m = re.search(r'\*\*Frozen at commit:\*\*\s*`([0-9a-f]{40})`', t)
    draft = 'DRAFT, NOT FROZEN' in t
    return (bool(m) and not draft), (m.group(1) if m else None)

def _dirty(paths, root):
    out = _git('status', '--porcelain', '--', *paths, root=root)
    return bool(out)

def _frozen_fields(spec):
    return {k: v for k, v in (spec or {}).items() if k != 'entry'}

def _entry_at(commit, spec_id, registry_rel, root):
    txt = _git('show', f'{commit}:{registry_rel}', root=root)
    if txt is None: return None
    old = {s['id']: s for s in (yaml.safe_load(txt).get('specs') or [])}
    return old.get(spec_id)

def _log(log_path, rec):
    with open(log_path, 'a') as fh: fh.write(json.dumps(rec, default=str) + '\n')

def run(spec_id, registry='specs.yaml', log='runs.log', root=ROOT):
    root = Path(root); reg_path = root / registry; log_path = root / log
    d, specs, _ = load_registry(reg_path)
    prereg = root / d.get('prereg', 'docs/PREREG.md')
    frozen, fcommit = freeze_state(prereg)
    commit = _git('rev-parse', 'HEAD', root=root)
    rec = {'time': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), 'spec': spec_id,
           'commit': commit, 'dirty': _dirty([], root), 'prereg_frozen': frozen, 'freeze_commit': fcommit}
    def refuse(reason, code=2):
        rec.update(status='refused', reason=reason); _log(log_path, rec); print('REFUSED:', reason); return code
    if spec_id not in specs: return refuse(f'{spec_id!r} is not registered in {registry}')
    s = specs[spec_id]; rec.update(family=s['family'], element=s['element'])
    if s['family'] in GUARDED:
        if not frozen: return refuse(f"{s['family']} spec before the PREREG freeze")
        dirty = [l for l in (_git('status', '--porcelain', '--untracked-files=no', root=root) or '').splitlines() if not l.endswith(log)]
        if dirty: return refuse('uncommitted changes to tracked files (commit the code first): ' + '; '.join(l.strip() for l in dirty[:5]))
        frozen_spec = _entry_at(fcommit, spec_id, registry, root)
        if frozen_spec is None or _frozen_fields(frozen_spec) != _frozen_fields(s): return refuse('the spec differs from its entry at the freeze commit')
    entry = str(s['entry'])
    if entry == 'pending': return refuse('entry is pending (analysis code not written yet)', code=3)
    t0 = time.time()
    try:
        if entry.startswith('script:'):
            runpy.run_path(str(root / entry[len('script:'):]), run_name='__main__'); result = None
        else:
            mod, fn = entry.split(':')
            for p in (root / 'src', root / 'analysis', root):
                if str(p) not in sys.path: sys.path.insert(0, str(p))
            result = getattr(importlib.import_module(mod), fn)(s)
        rec.update(status='ok', result=result)
    except SystemExit as e:
        rec.update(status='ok' if not e.code else 'error', reason=f'SystemExit({e.code})')
    except Exception as e:
        rec.update(status='error', reason=f'{type(e).__name__}: {e}')
    rec['seconds'] = round(time.time() - t0, 1); _log(log_path, rec)
    print(f"{rec['status'].upper()}: {spec_id} ({rec['seconds']} s)")
    return 0 if rec['status'] == 'ok' else 1

def count(log='runs.log', root=ROOT):
    """Distinct exploratory specs with at least one status 'ok' run: the m for Benjamini-Hochberg."""
    p = Path(root) / log
    if not p.exists(): return 0, []
    ids = sorted({r['spec'] for r in map(json.loads, p.read_text().splitlines()) if r.get('family') == 'exploratory' and r.get('status') == 'ok'})
    return len(ids), ids

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] not in {'list', 'run', 'count', 'check'}: print(__doc__); sys.exit(1)
    if a[0] == 'list':
        _, specs, _ = load_registry(ROOT / 'specs.yaml')
        for s in specs.values(): print(f"{s['id']:30s} {s['family']:13s} {s['element']}  {s['entry']}")
    elif a[0] == 'check':
        d, specs, conf = load_registry(ROOT / 'specs.yaml'); fr, fc = freeze_state(ROOT / d['prereg'])
        from collections import Counter
        print(f"specs.yaml valid: {len(specs)} specs {dict(Counter(s['family'] for s in specs.values()))}; confirmatory {conf}; "
              f"PREREG frozen: {fr} (commit {fc})")
    elif a[0] == 'count':
        n, ids = count(); print(n, ids)
    else:
        sys.exit(run(a[1]))
