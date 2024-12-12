"""
Common code for integration tests.
"""

# flake8: noqa: E402
# pylint: disable=wrong-import-position,too-many-public-methods,unused-import,self-assigning-variable


import random

from torrent_worker_coordinator.client import Client
from torrent_worker_coordinator.settings import API_KEY
from torrent_worker_coordinator.test.run_server_in_thread import run_server_in_thread


def _get_next_port() -> int:

    random_port = random.randint(5000, 9000)
    return random_port


class TestApp(Client):
    __test__ = False  # Prevent discovery

    def __init__(self, port: int, api_key: str = API_KEY) -> None:
        super().__init__(host="localhost", port=_get_next_port(), api_key=api_key)
        self.api_key = api_key
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
