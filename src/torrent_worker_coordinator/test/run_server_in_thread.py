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

import uvicorn
from uvicorn.main import Config

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
def run_server_in_thread(host: str, port: int, timeout: int = TIMEOUT):
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
        while time.time() - start_time < timeout:
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
