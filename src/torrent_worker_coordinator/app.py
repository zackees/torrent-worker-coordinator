"""
    app worker
"""

import os
from datetime import datetime
from hmac import compare_digest
from tempfile import TemporaryDirectory

import uvicorn  # type: ignore
from colorama import just_fix_windows_console
from fastapi import FastAPI, File, Header, UploadFile  # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)

from torrent_worker_coordinator.log import get_log_reversed, make_logger
from torrent_worker_coordinator.models import TorrentManager, TorrentStatus, get_db
from torrent_worker_coordinator.paths import GITHUB_REPO_PATH, TORRENTS_PATH
from torrent_worker_coordinator.settings import (
    API_KEY,
    GITHUB_REPO_URL,
    IS_TEST,
    S3_CREDENTIALS,
    SKIP_GITHUB_DOWNLOADS,
)
from torrent_worker_coordinator.task_populate_torrents import task_populate_torrents
from torrent_worker_coordinator.util import async_download
from torrent_worker_coordinator.version import VERSION

just_fix_windows_console()

STARTUP_DATETIME = datetime.now()

log = make_logger(__name__)

APP_DISPLAY_NAME = "torrent_worker_coordinator"

READY = False
GITHUB_DOWNLOADED = False


def app_description() -> str:
    """Get the app description."""
    lines = []
    lines.append("  * Version: " + VERSION)
    lines.append("  * Started at: " + STARTUP_DATETIME.isoformat() + " UTC")
    if IS_TEST:
        lines.append("  * Running in TEST mode")
        lines.append("  * API_KEY: " + API_KEY)
    else:
        lines.append("  * Running in PRODUCTION mode")
    return "\n".join(lines)


app = FastAPI(
    title=APP_DISPLAY_NAME,
    version=VERSION,
    redoc_url=None,
    license_info={
        "name": "Private program, do not distribute",
    },
    description=app_description(),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if IS_TEST:
    ApiKeyHeader = Header(None)
else:
    ApiKeyHeader = Header(...)


def is_authenticated(api_key: str | None) -> bool:
    """Checks if the request is authenticated."""
    if IS_TEST:
        return True
    if api_key is None:
        return False
    out = compare_digest(api_key, API_KEY)
    if not out:
        log.warning("Invalid API key attempted: %s", api_key)
    return out


# on startup
@app.on_event("startup")
async def startup_event() -> None:
    """Startup event."""
    global READY
    global GITHUB_DOWNLOADED
    log.info("Starting up torrent_worker_coordinator")
    if SKIP_GITHUB_DOWNLOADS:
        log.info("Skipping downloads on startup")
    elif GITHUB_REPO_URL is None:
        log.info("No github repo specified")
    else:
        log.info("Downloading github repos")
        await task_populate_torrents(
            repo_url=GITHUB_REPO_URL, path=GITHUB_REPO_PATH, torrents_path=TORRENTS_PATH
        )
        GITHUB_DOWNLOADED = True
    READY = True


@app.get("/", include_in_schema=False)
async def index() -> RedirectResponse:
    """By default redirect to the fastapi docs."""
    return RedirectResponse(url="/docs", status_code=302)


@app.get("/get")
async def log_file() -> JSONResponse:
    """TODO - Add description."""
    return JSONResponse({"hello": "world"})


# get the log file
@app.get("/log")
def route_log(api_key: str = ApiKeyHeader) -> PlainTextResponse:
    """Gets the log file."""
    if not is_authenticated(api_key):
        return JSONResponse("Not authenticated", status_code=401)  # type: ignore
    out = get_log_reversed(100).strip()
    if not out:
        out = "(Empty log file)"
    return PlainTextResponse(out)


@app.get("/ready")
async def ready() -> JSONResponse:
    """Check if the service is ready."""
    return JSONResponse({"ready": READY})


@app.get("/protected")
async def protected_route(api_key: str = ApiKeyHeader) -> JSONResponse:
    """TODO - Add description."""
    if not is_authenticated(api_key):
        return JSONResponse("Not authenticated", status_code=401)
    return JSONResponse("Authenticated")


@app.get("/info")
async def route_info(api_key: str = ApiKeyHeader) -> JSONResponse:
    """Returns information about the service including version, startup time, and runtime mode."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    info = {
        "version": VERSION,
        "startup_time": STARTUP_DATETIME.isoformat(),
        "mode": "TEST" if IS_TEST else "PRODUCTION",
        "app_name": APP_DISPLAY_NAME,
        "github_downloaded": GITHUB_DOWNLOADED,
        "ready": READY,
        "s3": S3_CREDENTIALS,
    }
    return JSONResponse(info)


@app.get("/torrent/{name}")
async def route_torrent_info(name: str, api_key: str = ApiKeyHeader) -> JSONResponse:
    """Get information about a specific torrent by name."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    db = get_db()
    torrent = TorrentManager.get_torrent(db, name)
    if not torrent:
        return JSONResponse({"error": "Torrent not found"}, status_code=404)

    return JSONResponse(torrent.to_dict())


@app.get("/torrent/{name}/download")
async def route_torrent_download(
    name: str, api_key: str = ApiKeyHeader
) -> FileResponse:
    """Download a torrent by name."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)  # type: ignore

    db = get_db()
    torrent = TorrentManager.get_torrent(db, name)
    if torrent is None:
        return JSONResponse({"error": "Torrent not found"}, status_code=404)  # type: ignore

    torrent_path = TORRENTS_PATH / name
    if not os.path.exists(torrent_path):
        return JSONResponse(  # type: ignore
            {"error": "Torrent file not found, even though it should exist"},
            status_code=500,
        )

    return FileResponse(
        torrent_path, media_type="application/x-bittorrent", filename=torrent_path.name
    )


@app.post("/torrent/{name}/take")
async def route_torrent_take(
    name: str, worker_id: str, api_key: str = ApiKeyHeader
) -> JSONResponse:
    """Attempt to take ownership of a torrent for processing."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    db = get_db()
    torrent = TorrentManager.take_torrent(db, name, worker_id)
    if not torrent:
        return JSONResponse(
            {"error": "Torrent not found or already taken"}, status_code=404
        )

    return JSONResponse(torrent.to_dict())


@app.post("/torrent/{name}/on_complete")
async def route_torrent_complete(
    name: str, api_key: str = ApiKeyHeader
) -> JSONResponse:
    """Mark a torrent as completed."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    db = get_db()
    torrent = TorrentManager.update_torrent_status(
        db, name, TorrentStatus.COMPLETED, progress=100
    )
    if not torrent:
        return JSONResponse({"error": "Torrent not found"}, status_code=404)

    return JSONResponse(torrent.to_dict())


@app.post("/torrent/{name}/on_error")
async def route_torrent_error(
    name: str, error_message: str, api_key: str = ApiKeyHeader
) -> JSONResponse:
    """Report an error for a torrent."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    db = get_db()
    torrent = TorrentManager.update_torrent_status(
        db, name, TorrentStatus.ERROR, error_message=error_message
    )
    if not torrent:
        return JSONResponse({"error": "Torrent not found"}, status_code=404)

    return JSONResponse(torrent.to_dict())


@app.post("/torrent/{name}/on_update")
async def route_torrent_update(
    name: str, progress: int, status_message: str, api_key: str = ApiKeyHeader
) -> JSONResponse:
    """Update the status of a torrent."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    db = get_db()
    torrent = TorrentManager.update_torrent_status(
        db, name, TorrentStatus.ACTIVE, progress=progress, last_update=status_message
    )
    if not torrent:
        return JSONResponse({"error": "Torrent not found"}, status_code=404)

    return JSONResponse(torrent.to_dict())


@app.get("/torrent/list/all")
async def route_torrent_list_all(api_key: str = ApiKeyHeader) -> JSONResponse:
    """Get a list of all torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    db = get_db()
    torrents = TorrentManager.get_all_torrents(db)
    return JSONResponse({"torrents": [t.to_dict() for t in torrents]})


@app.get("/torrent/list/pending")
async def route_torrent_list_pending(api_key: str = ApiKeyHeader) -> JSONResponse:
    """Get a list of pending torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    db = get_db()
    torrents = TorrentManager.get_torrents_by_status(db, TorrentStatus.PENDING)
    return JSONResponse({"torrents": [t.to_dict() for t in torrents]})


@app.get("/torrent/list/active")
async def route_torrent_list_active(api_key: str = ApiKeyHeader) -> JSONResponse:
    """Get a list of active torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    db = get_db()
    torrents = TorrentManager.get_torrents_by_status(db, TorrentStatus.ACTIVE)
    return JSONResponse({"torrents": [t.to_dict() for t in torrents]})


@app.get("/torrent/list/completed")
async def route_torrent_list_completed(api_key: str = ApiKeyHeader) -> JSONResponse:
    """Get a list of completed torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    db = get_db()
    torrents = TorrentManager.get_torrents_by_status(db, TorrentStatus.COMPLETED)
    return JSONResponse({"torrents": [t.to_dict() for t in torrents]})


@app.post("/upload")
async def route_upload(
    datafile: UploadFile = File(...),
) -> PlainTextResponse:
    """TODO - Add description."""
    if datafile.filename is None:
        return PlainTextResponse("No filename", status_code=400)
    log.info("Upload called with file: %s", datafile.filename)
    with TemporaryDirectory() as temp_dir:
        temp_datapath: str = os.path.join(temp_dir, datafile.filename)
        await async_download(datafile, temp_datapath)
        await datafile.close()
        log.info("Downloaded file %s to %s", datafile.filename, temp_datapath)
        # shutil.move(temp_path, final_path)
    return PlainTextResponse(f"Uploaded {datafile.filename} to {temp_datapath}")


def main() -> None:
    """Start the app."""
    import webbrowser  # pylint: disable=import-outside-toplevel

    port = 8080

    webbrowser.open(f"http://localhost:{port}")
    uvicorn.run(
        "torrent_worker_coordinator.app:app", host="localhost", port=port, reload=True
    )


if __name__ == "__main__":
    main()
