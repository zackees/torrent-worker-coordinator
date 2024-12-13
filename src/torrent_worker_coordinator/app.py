"""
    app worker
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from hmac import compare_digest

import uvicorn  # type: ignore
from colorama import just_fix_windows_console
from fastapi import FastAPI, Header  # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)

from torrent_worker_coordinator.app_schemas import (
    InfoResponse,
    TorrentCompleteRequest,
    TorrentErrorRequest,
    TorrentInfoRequest,
    TorrentListActiveRequest,
    TorrentListPendingRequest,
    TorrentListResponse,
    TorrentResponse,
    TorrentTakeRequest,
    TorrentUpdateRequest,
)
from torrent_worker_coordinator.log import get_log_reversed, make_logger
from torrent_worker_coordinator.models import TorrentStatus, get_db
from torrent_worker_coordinator.paths import GITHUB_REPO_PATH, TORRENTS_PATH
from torrent_worker_coordinator.settings import (
    API_KEY,
    BACKGROUND_WORKER_INTERVAL,
    GITHUB_REPO_URL,
    IS_TEST,
    S3_CREDENTIALS,
    SKIP_GITHUB_DOWNLOADS,
)
from torrent_worker_coordinator.task_background import task_background
from torrent_worker_coordinator.task_populate_torrents import task_populate_torrents
from torrent_worker_coordinator.torrent_manager import TorrentManager

just_fix_windows_console()

STARTUP_DATETIME = datetime.now()

log = make_logger(__name__)

APP_DISPLAY_NAME = "torrent_worker_coordinator"

READY = False
GITHUB_DOWNLOADED = False


def _version() -> str:
    from torrent_worker_coordinator import __version__

    return __version__


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    global READY
    global GITHUB_DOWNLOADED
    _ = get_db()  # invoke to create the database
    log.info("Starting up torrent_worker_coordinator")

    # Start background task
    task = task_background(interval_seconds=BACKGROUND_WORKER_INTERVAL)  # type: ignore
    asyncio.create_task(task)

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
    yield


def app_description() -> str:
    """Get the app description."""
    lines = []
    lines.append("  * Version: " + _version())
    lines.append("  * Started at: " + STARTUP_DATETIME.isoformat() + " UTC")
    if IS_TEST:
        lines.append("  * Running in TEST mode")
        lines.append("  * API_KEY: " + API_KEY)
    else:
        lines.append("  * Running in PRODUCTION mode")
    return "\n".join(lines)


app = FastAPI(
    title=APP_DISPLAY_NAME,
    lifespan=lifespan,
    version=_version(),
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


@app.get("/info", response_model=InfoResponse)
async def route_info(api_key: str = ApiKeyHeader) -> InfoResponse:
    """Returns information about the service including version, startup time, and runtime mode."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)  # type: ignore

    try:
        out = InfoResponse(
            version=_version(),
            startup_time=STARTUP_DATETIME.isoformat(),
            mode="TEST" if IS_TEST else "PRODUCTION",
            app_name=APP_DISPLAY_NAME,
            github_downloaded=GITHUB_DOWNLOADED,
            ready=READY,
            s3=S3_CREDENTIALS,
        )
        return out
    except Exception as e:
        log.error("Error creating InfoResponse: %s", str(e))
        raise


@app.post("/torrent/info")
async def route_torrent_info(
    request: TorrentInfoRequest, api_key: str = ApiKeyHeader
) -> JSONResponse:
    """Get information about a specific torrent by name."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    with get_db() as db:
        torrent = TorrentManager.get_torrent(db, request.torrent_name)
        if not torrent:
            return JSONResponse({"error": "Torrent not found"}, status_code=404)

        return JSONResponse(torrent.to_dict())


@app.get("/torrent/download/{filename}")
async def route_torrent_download(filename: str) -> FileResponse:
    """Download a torrent by name."""
    with get_db() as db:
        torrent = TorrentManager.get_torrent(db, filename)
        if torrent is None:
            return JSONResponse({"error": "Torrent not found"}, status_code=404)  # type: ignore

        torrent_path = TORRENTS_PATH / filename
        if not os.path.exists(torrent_path):
            return JSONResponse(  # type: ignore
                {"error": "Torrent file not found, even though it should exist"},
                status_code=500,
            )

        return FileResponse(
            torrent_path,
            media_type="application/x-bittorrent",
            filename=torrent_path.name,
        )


@app.post("/torrent/take", response_model=TorrentResponse)
async def route_torrent_take(
    request: TorrentTakeRequest, api_key: str = ApiKeyHeader
) -> TorrentResponse:
    """Attempt to take ownership of a torrent for processing."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)  # type: ignore

    # db = get_db()
    with get_db() as db:
        torrent = TorrentManager.take_torrent(
            db=db,
            worker_name=request.worker_name,
            torrent_name=request.torrent_name,
        )
        if not torrent:
            torrent = TorrentManager.get_torrent(db, request.torrent_name)
            if not torrent:
                return JSONResponse(  # type: ignore
                    {"error": "Torrent not found"}, status_code=404
                )
            return JSONResponse(  # type: ignore
                {"error": "Torrent might have already been taken"}, status_code=409
            )

        return TorrentResponse(**torrent.to_dict())


@app.post("/torrent/complete", response_model=TorrentResponse)
async def route_torrent_complete(
    request: TorrentCompleteRequest,
    api_key: str = ApiKeyHeader,
) -> TorrentResponse:
    """Mark a torrent as completed."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)  # type: ignore

    with get_db() as db:
        torrent = TorrentManager.update_torrent_status(
            db, request.torrent_name, TorrentStatus.COMPLETED, progress=100
        )
        if not torrent:
            return JSONResponse({"error": "Torrent not found"}, status_code=404)  # type: ignore

        return TorrentResponse(**torrent.to_dict())


@app.post("/torrent/error")
async def route_torrent_error(
    request: TorrentErrorRequest, api_key: str = ApiKeyHeader
) -> JSONResponse:
    """Report an error for a torrent."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    with get_db() as db:
        torrent = TorrentManager.update_torrent_status(
            db,
            request.torrent_name,
            TorrentStatus.ERROR,
            error_message=request.error_message,
        )
        if not torrent:
            return JSONResponse({"error": "Torrent not found"}, status_code=404)

        return JSONResponse(torrent.to_dict())


@app.post("/torrent/update", response_model=TorrentResponse)
async def route_torrent_update(
    request: TorrentUpdateRequest, api_key: str = ApiKeyHeader
) -> TorrentResponse:
    """Update the status of a torrent."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)  # type: ignore

    with get_db() as db:
        torrent = TorrentManager.update_torrent_status(
            db,
            request.torrent_name,
            None,
            progress=request.progress,
        )
        if not torrent:
            return JSONResponse({"error": "Torrent not found"}, status_code=404)  # type: ignore

        # return JSONResponse(torrent.to_dict())
        out = TorrentResponse(**torrent.to_dict())
        return out


@app.post("/torrent/list/all", response_model=TorrentListResponse)
async def route_torrent_list_all(api_key: str = ApiKeyHeader) -> TorrentListResponse:
    """Get a list of all torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)  # type: ignore

    try:
        with get_db() as db:
            torrents = TorrentManager.get_all_torrents(db)
            list_of_dicts = [t.to_dict() for t in torrents]
            list_of_torrents: list[TorrentResponse] = []
            for t in list_of_dicts:
                try:
                    tr = TorrentResponse(**t)
                    list_of_torrents.append(tr)
                except Exception as e:
                    log.error("Error creating TorrentResponse: %s", str(e))
                    raise

            return TorrentListResponse(torrents=list_of_torrents)
    except Exception as e:
        msg = {"error": "Error getting torrents", "exception": str(e)}
        return JSONResponse(msg, status_code=500)  # type: ignore


@app.post("/torrent/list/pending", response_model=TorrentListResponse)
async def route_torrent_list_pending(
    request: TorrentListPendingRequest, api_key: str = ApiKeyHeader
) -> TorrentListResponse:
    """Get a list of pending torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)  # type: ignore

    with get_db() as db:
        torrents = TorrentManager.get_torrents_by_status(
            db, TorrentStatus.PENDING, order_by_oldest=request.order_by_oldest
        )
        out: list[TorrentResponse] = []
        for t in torrents:
            tr = TorrentResponse(**t.to_dict())
            out.append(tr)
        return TorrentListResponse(torrents=out)


@app.post("/torrent/list/active", response_model=TorrentListResponse)
async def route_torrent_list_active(
    request: TorrentListActiveRequest, api_key: str = ApiKeyHeader
) -> TorrentListResponse:
    """Get a list of active torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)  # type: ignore

    with get_db() as db:
        filter_by_worker = request.filter_by_worker_name
        order_by_oldest = request.order_by_oldest
        torrents = TorrentManager.get_torrents_by_status(
            db, TorrentStatus.ACTIVE, order_by_oldest, filter_by_worker
        )
        return TorrentListResponse(torrents=[t.to_dict() for t in torrents])


@app.post("/torrent/list/completed", response_model=TorrentListResponse)
async def route_torrent_list_completed(
    api_key: str = ApiKeyHeader,
) -> TorrentListResponse:
    """Get a list of completed torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)  # type: ignore

    with get_db() as db:
        torrents = TorrentManager.get_torrents_by_status(db, TorrentStatus.COMPLETED)
        return TorrentListResponse(torrents=[t.to_dict() for t in torrents])


# @app.post("/upload")
# async def route_upload(
#     datafile: UploadFile = File(...),
# ) -> PlainTextResponse:
#     """TODO - Add description."""
#     if datafile.filename is None:
#         return PlainTextResponse("No filename", status_code=400)
#     log.info("Upload called with file: %s", datafile.filename)
#     with TemporaryDirectory() as temp_dir:
#         temp_datapath: str = os.path.join(temp_dir, datafile.filename)
#         await async_download(datafile, temp_datapath)
#         await datafile.close()
#         log.info("Downloaded file %s to %s", datafile.filename, temp_datapath)
#         # shutil.move(temp_path, final_path)
#     return PlainTextResponse(f"Uploaded {datafile.filename} to {temp_datapath}")


def main() -> None:
    """Start the app."""
    import argparse
    import webbrowser  # pylint: disable=import-outside-toplevel

    parser = argparse.ArgumentParser(
        description="Start the torrent_worker_coordinator app"
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="Don't open the browser on startup"
    )
    parser.add_argument("--port", type=int, default=8080, help="Port to run the app on")
    args = parser.parse_args()

    port = args.port

    if not args.no_browser:
        webbrowser.open(f"http://localhost:{port}")
    uvicorn.run(
        "torrent_worker_coordinator.app:app", host="localhost", port=port, reload=True
    )


if __name__ == "__main__":
    main()
