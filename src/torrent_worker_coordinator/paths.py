import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent.parent

_IS_RENDER_COM = False

for key, _ in os.environ.items():
    if key.startswith("RENDER_"):
        _IS_RENDER_COM = True
        break

DATA_DIR = PROJECT_ROOT / "data" if not _IS_RENDER_COM else Path("/var/data")

GITHUB_REPO_PATH = DATA_DIR / "github"
TORRENTS_PATH = DATA_DIR / "torrents"
DB_PATH = DATA_DIR / "db.sqlite"
