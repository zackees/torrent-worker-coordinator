"""
Common code for integration tests.
"""

# flake8: noqa: E402
# pylint: disable=wrong-import-position,too-many-public-methods,unused-import,self-assigning-variable


import httpx

from torrent_worker_coordinator.app_schemas import (
    InfoResponse,
    TorrentListResponse,
    TorrentResponse,
)
from torrent_worker_coordinator.settings import API_KEY
from torrent_worker_coordinator.test.run_server_in_thread import (
    TIMEOUT,
    run_server_in_thread,
)


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

    def request_info(self) -> InfoResponse:
        """Test the info endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        response = httpx.get(self.endpoint_info, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        json = response.json()
        return InfoResponse(**json)

    def request_torrent_list_all(self) -> list[TorrentResponse]:
        """Test the list_all endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        response = httpx.get(
            self.endpoint_list_torrents, headers=headers, timeout=TIMEOUT
        )
        response.raise_for_status()
        json = response.json()
        return TorrentListResponse(**json).torrents

    def request_torrent_take(
        self, torrent_name: str, worker_name: str
    ) -> TorrentResponse:
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
        json = response.json()
        return TorrentResponse(**json)

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

    def request_log(self) -> str:
        """Test the log endpoint."""
        headers = {
            "accept": "text/plain",
            "api-key": self.api_key,
        }
        response = httpx.get(
            f"http://localhost:{self.port}/log", headers=headers, timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.text

    def request_torrent_info(self, name: str) -> dict:
        """Test the torrent info endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        params = {"name": name}
        response = httpx.get(
            f"http://localhost:{self.port}/torrent/info",
            headers=headers,
            params=params,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def request_torrent_download(self, torrent_name: str) -> bytes:
        """Test the torrent download endpoint."""
        headers = {
            "accept": "application/x-bittorrent",
            "api-key": self.api_key,
        }
        params = {"torrent_name": torrent_name}
        response = httpx.get(
            f"http://localhost:{self.port}/torrent/download",
            headers=headers,
            params=params,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.content

    def request_torrent_complete(self, torrent_name: str, worker_name: str) -> dict:
        """Test the torrent complete endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        body = {"torrent_name": torrent_name, "worker_name": worker_name}
        response = httpx.post(
            f"http://localhost:{self.port}/torrent/complete",
            headers=headers,
            json=body,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def request_torrent_error(self, name: str, error_message: str) -> dict:
        """Test the torrent error endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        body = {"name": name, "error_message": error_message}
        response = httpx.post(
            f"http://localhost:{self.port}/torrent/error",
            headers=headers,
            json=body,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def request_torrent_update(
        self, name: str, progress: int, status_message: str
    ) -> dict:
        """Test the torrent update endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        body = {"name": name, "progress": progress, "status_message": status_message}
        response = httpx.post(
            f"http://localhost:{self.port}/torrent/update",
            headers=headers,
            json=body,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    def request_torrent_list_pending(self, order_by_oldest) -> list[TorrentResponse]:
        """Test the pending torrents list endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        body = {"order_by_oldest": order_by_oldest}
        response = httpx.post(
            f"http://localhost:{self.port}/torrent/list/pending",
            headers=headers,
            timeout=TIMEOUT,
            json=body,
        )
        response.raise_for_status()
        return TorrentListResponse(**response.json()).torrents

    def request_torrent_list_active(self) -> list[TorrentResponse]:
        """Test the active torrents list endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        response = httpx.get(
            f"http://localhost:{self.port}/torrent/list/active",
            headers=headers,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return TorrentListResponse(**response.json()).torrents

    def request_torrent_list_completed(self) -> list[TorrentResponse]:
        """Test the completed torrents list endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        response = httpx.get(
            f"http://localhost:{self.port}/torrent/list/completed",
            headers=headers,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return TorrentListResponse(**response.json()).torrents
