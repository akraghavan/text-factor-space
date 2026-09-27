"""Single source of truth for data locations. Override the repo root with TFS_ROOT; data always lives in <root>/data (gitignored)."""
import os
from pathlib import Path
ROOT = Path(os.environ.get("TFS_ROOT", Path(__file__).resolve().parents[1]))
DATA = ROOT / "data"
RAW, INTERIM, PROCESSED = DATA / "raw", DATA / "interim", DATA / "processed"
for p in (RAW, INTERIM, PROCESSED):
    p.mkdir(parents=True, exist_ok=True)
SEC_UA = os.environ.get("SEC_USER_AGENT", "")  # SEC fair access: set to "Your Name your@email" before scraping
if not SEC_UA:
    SEC_UA = "text-factor-space research (set SEC_USER_AGENT)"
