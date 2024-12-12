import os
import threading
import time
from queue import Queue

import uvicorn

# from androidmonitor_backend.testing.db_test_env import db_test_env_init
from uvicorn.main import Config

APP_NAME = "torrent_worker_coordinator.app:app"
HOST = "localhost"
PORT = 4424  # Arbitrarily chosen.

TIMEOUT = 10

# CLIENT_API_KEYS = CLIENT_API_KEYS
# current_datetime = current_datetime  #

URL = f"http://{HOST}:{PORT}"


class ServerWithShutdown(uvicorn.Server):
    """Adds a shutdown method to the uvicorn server."""

    def install_signal_handlers(self):
        pass


def trampoline(queue: Queue, env: dict[str, str] | None = None):
    if env:
        for key, value in env.items():
            os.environ[key] = value

    config = Config(
        APP_NAME,
        host=HOST,
        port=PORT,
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
                queue.put(True)

            time.sleep(0.1)
            # raise TimeoutError(
            "Server did not start in time, was there an error in the app startup?"
        # )
        import warnings

        warnings.warn(
            "Server did not start in time, was there an error in the app startup?"
        )
        queue.put(False)
    finally:
        queue.get()
        server.should_exit = True
        thread.join()
