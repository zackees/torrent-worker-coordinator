"""
Common code for integration tests.
"""

# flake8: noqa: E402
# pylint: disable=wrong-import-position,too-many-public-methods,unused-import,self-assigning-variable

import contextlib
import os
import sys
import threading
import time
from pathlib import Path

import httpx
import uvicorn
from uvicorn.main import Config

from torrent_worker_coordinator.settings import API_KEY

HERE = Path(__file__).parent
PROJECT_ROOT = HERE.parent.parent

# Change set the DB_URL environment variable to a temporary sqlite database.
# This needs to be done before importing the app.
HERE = Path(os.path.dirname(os.path.abspath(__file__)))

# if debugger is attached
if sys.gettrace():
    TIMEOUT = 1000000
else:
    TIMEOUT = 20  # seconds


APP_NAME = "torrent_worker_coordinator.app:app"


# Surprisingly uvicorn does allow graceful shutdowns, making testing hard.
# This class is the stack overflow answer to work around this limitiation.
# Note: Running this in python 3.8 and below will cause the console to spew
# scary warnings during test runs:
#   ValueError: set_wakeup_fd only works in main thread
class ServerWithShutdown(uvicorn.Server):
    """Adds a shutdown method to the uvicorn server."""

    def install_signal_handlers(self):
        pass


@contextlib.contextmanager
def run_server_in_thread(host: str, port: int):
    """
    Useful for testing, this function brings up a server.
    It's a context manager so that it can be used in a with statement.
    """
    config = Config(
        APP_NAME,
        host=host,
        port=port,
        log_level="info",
        use_colors=True,
    )
    server = ServerWithShutdown(config=config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        start_time = time.time()
        while time.time() - start_time < TIMEOUT:
            if server.started:
                yield
                return
            time.sleep(0.1)
        raise TimeoutError(
            "Server did not start in time, was there an error in the app startup?"
        )
    finally:
        server.should_exit = True
        thread.join()


class TestApp:
    __test__ = False  # Prevent discovery

    def __init__(self, port: int, api_key: str = API_KEY) -> None:
        self.port = port
        self.api_key = api_key
        self.endpoint_get = f"http://localhost:{self.port}/get"
        self.endpoint_protected = f"http://localhost:{self.port}/protected"
        self.endpoint_info = f"http://localhost:{self.port}/info"
        self.endpoint_list_torrents = f"http://localhost:{self.port}/torrent/list/all"
        self.endpoint_ready = f"http://localhost:{self.port}/ready"
        self.endpoint_torrent_take = f"http://localhost:{self.port}/torrent/take"
        self.server_context = None

    def __enter__(self):
        # Start the server in a context
        self.server_context = run_server_in_thread("localhost", self.port)
        self.server_context.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Ensure the server is cleaned up properly
        if self.server_context:
            self.server_context.__exit__(exc_type, exc_value, traceback)
            self.server_context = None

    def request_get(self) -> dict:
        """Test the get method."""
        response = httpx.get(self.endpoint_get, timeout=TIMEOUT)
        return response.json()

    def request_protected(self) -> dict:
        """Test the get method."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        response = httpx.get(self.endpoint_protected, headers=headers, timeout=TIMEOUT)
        return response.json()

    def request_info(self) -> dict[str, str]:
        """Test the info endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        response = httpx.get(self.endpoint_info, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def request_torrent_list_all(self) -> dict:
        """Test the list_all endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        response = httpx.get(
            self.endpoint_list_torrents, headers=headers, timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()["torrents"]

    def request_torrent_take(self, torrent_name: str, worker_name: str) -> dict:
        """Test the take endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        body = {
            "worker_name": worker_name,
            "torrent_name": torrent_name,
        }
        response = httpx.post(
            self.endpoint_torrent_take,
            headers=headers,
            json=body,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def request_ready(self) -> dict:
        """Test the ready endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        # response = httpx.get(ENDPOINT_READY, headers=headers, timeout=TIMEOUT)
        response = httpx.get(self.endpoint_ready, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()["ready"]
