from torrent_worker_coordinator.settings import DATA_DIR, PROJECT_ROOT

# all
__all__ = [
    "DATA_DIR",
    "PROJECT_ROOT",
    "DATA_UPLOAD_DIR",
    "LOG_DIR",
    "GITHUB_REPO_PATH",
    "TORRENTS_PATH",
    "DB_PATH",
    "LOG_SYSTEM",
]
DATA_UPLOAD_DIR = DATA_DIR / "upload"
LOG_DIR = DATA_DIR / "logs"


GITHUB_REPO_PATH = DATA_DIR / "github"
TORRENTS_PATH = DATA_DIR / "torrents"
DB_PATH = DATA_DIR / "db.sqlite"
LOG_SYSTEM = LOG_DIR / "system.log"

DATA_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
