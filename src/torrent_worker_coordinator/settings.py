"""
Settings
"""

import os
import secrets
from pathlib import Path

DEFAULT_API_KEY = "a8d4ef6c3ae1c2517dcb9a5dda2500ac"

_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent.parent


LOG_SIZE = 512 * 1024
LOG_HISTORY = 20
LOGGING_FMT = (
    "%(levelname)s %(asctime)s %(filename)s:%(lineno)s (%(funcName)s) - %(message)s"
)
LOGGING_USE_GZIP = True
UPLOAD_CHUNK_SIZE = 1024 * 64
IS_TEST = os.getenv("IS_TEST", "0") == "1"
API_KEY = os.getenv("API_KEY", secrets.token_hex(16))

GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", None)
SKIP_GITHUB_DOWNLOADS = os.environ.get("SKIP_GITHUB_DOWNLOADS", "0") == "1"


IS_RENDER_COM = False

for key, _ in os.environ.items():
    if key.startswith("RENDER_"):
        IS_RENDER_COM = True
        break


DEFAULT_DATA_DIR = PROJECT_ROOT / ".cache" if not IS_RENDER_COM else Path("/var/data")
DATA_DIR = Path(os.getenv("DATA_DIR", DEFAULT_DATA_DIR))

S3_BUCKET = os.getenv("S3_BUCKET", "UNSET")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "UNSET")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "UNSET")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "UNSET")

S3_CREDENTIALS: dict[str, str] = {
    "bucket": S3_BUCKET,
    "access_key_id": S3_ACCESS_KEY_ID,
    "secret_access_key": S3_SECRET_ACCESS_KEY,
    "endpoint_url": S3_ENDPOINT_URL,
}


os.makedirs(DATA_DIR, exist_ok=True)
