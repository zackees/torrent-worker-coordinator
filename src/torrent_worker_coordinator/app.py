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
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse

from torrent_worker_coordinator.log import get_log_reversed, make_logger
from torrent_worker_coordinator.settings import API_KEY, IS_TEST
from torrent_worker_coordinator.util import async_download
from torrent_worker_coordinator.version import VERSION

just_fix_windows_console()

STARTUP_DATETIME = datetime.now()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

log = make_logger(__name__)

APP_DISPLAY_NAME = "torrent_worker_coordinator"


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
def route_log() -> PlainTextResponse:
    """Gets the log file."""
    out = get_log_reversed(100).strip()
    if not out:
        out = "(Empty log file)"
    return PlainTextResponse(out)


@app.get("/protected")
async def protected_route(api_key: str = ApiKeyHeader) -> PlainTextResponse:
    """TODO - Add description."""
    if not is_authenticated(api_key):
        return PlainTextResponse("Not authenticated", status_code=401)
    return PlainTextResponse("Authenticated")


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
    }
    return JSONResponse(info)


@app.get("/torrent/{name}")
async def route_torrent_info(name: str, api_key: str = ApiKeyHeader) -> JSONResponse:
    """Get information about a specific torrent by name."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    # TODO: This is a placeholder - we need to implement actual torrent tracking
    # For now return a mock response
    torrent_info = {
        "name": name,
        "status": "not_implemented",
        "message": "Torrent tracking not yet implemented",
    }

    return JSONResponse(torrent_info)


@app.post("/torrent/{name}/take")
async def route_torrent_take(name: str, api_key: str = ApiKeyHeader) -> JSONResponse:
    """Attempt to take ownership of a torrent for processing."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    # TODO: Implement torrent claiming logic
    return JSONResponse(
        {
            "name": name,
            "status": "not_implemented",
            "message": "Torrent claiming not yet implemented",
        }
    )


@app.post("/torrent/{name}/on_complete")
async def route_torrent_complete(
    name: str, api_key: str = ApiKeyHeader
) -> JSONResponse:
    """Mark a torrent as completed."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    # TODO: Implement completion handling
    return JSONResponse(
        {
            "name": name,
            "status": "not_implemented",
            "message": "Completion handling not yet implemented",
        }
    )


@app.post("/torrent/{name}/on_error")
async def route_torrent_error(name: str, api_key: str = ApiKeyHeader) -> JSONResponse:
    """Report an error for a torrent."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    # TODO: Implement error handling
    return JSONResponse(
        {
            "name": name,
            "status": "not_implemented",
            "message": "Error handling not yet implemented",
        }
    )


@app.post("/torrent/{name}/on_update")
async def route_torrent_update(name: str, api_key: str = ApiKeyHeader) -> JSONResponse:
    """Update the status of a torrent."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    # TODO: Implement status update handling
    return JSONResponse(
        {
            "name": name,
            "status": "not_implemented",
            "message": "Status update handling not yet implemented",
        }
    )


@app.get("/torrent/list/all")
async def route_torrent_list_all(api_key: str = ApiKeyHeader) -> JSONResponse:
    """Get a list of all torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    # TODO: Implement torrent listing
    return JSONResponse(
        {"torrents": [], "message": "Torrent listing not yet implemented"}
    )


@app.get("/torrent/list/pending")
async def route_torrent_list_pending(api_key: str = ApiKeyHeader) -> JSONResponse:
    """Get a list of pending torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    # TODO: Implement pending torrent listing
    return JSONResponse(
        {"torrents": [], "message": "Pending torrent listing not yet implemented"}
    )


@app.get("/torrent/list/active")
async def route_torrent_list_active(api_key: str = ApiKeyHeader) -> JSONResponse:
    """Get a list of active torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    # TODO: Implement active torrent listing
    return JSONResponse(
        {"torrents": [], "message": "Active torrent listing not yet implemented"}
    )


@app.get("/torrent/list/completed")
async def route_torrent_list_completed(api_key: str = ApiKeyHeader) -> JSONResponse:
    """Get a list of completed torrents."""
    if not is_authenticated(api_key):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)

    # TODO: Implement completed torrent listing
    return JSONResponse(
        {"torrents": [], "message": "Completed torrent listing not yet implemented"}
    )


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
