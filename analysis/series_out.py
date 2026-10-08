"""Monthly Fama-MacBeth slope series of an entry's headline regressor, saved for Romano-Wolf (SPEC D25;
analysis/exploratory_family.romano_wolf). Aggregates only: one slope per month, no firm data. File:
analysis/output/<dir>/series/<spec id>.json = {month: slope}, months as 'YYYY-MM' strings in time order."""
import json
from pathlib import Path

def save(out_dir, spec, name, periods, values):
    sid = (spec or {}).get('id') or name
    d = Path(out_dir) / 'series'; d.mkdir(parents=True, exist_ok=True)
    (d / f'{sid}.json').write_text(json.dumps({str(p): float(v) for p, v in zip(periods, values)}, indent=0))
    return d / f'{sid}.json'

def load(path):
    return json.loads(Path(path).read_text())
