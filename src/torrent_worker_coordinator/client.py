import httpx

from torrent_worker_coordinator.app_schemas import (
    InfoResponse,
    TorrentListResponse,
    TorrentResponse,
)
from torrent_worker_coordinator.settings import API_KEY
from torrent_worker_coordinator.test.run_server_in_thread import TIMEOUT


class Client:

    def __init__(self, port: int, api_key: str = API_KEY) -> None:
        self.port = port
        self.api_key = api_key
        self.endpoint_get = f"http://localhost:{self.port}/get"
        self.endpoint_protected = f"http://localhost:{self.port}/protected"
        self.endpoint_info = f"http://localhost:{self.port}/info"
        self.endpoint_list_torrents = f"http://localhost:{self.port}/torrent/list/all"
        self.endpoint_ready = f"http://localhost:{self.port}/ready"
        self.endpoint_torrent_take = f"http://localhost:{self.port}/torrent/take"

    def info(self) -> InfoResponse:
        """Test the info endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        response = httpx.get(self.endpoint_info, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        json = response.json()
        return InfoResponse(**json)

    def list_torrents(self) -> list[TorrentResponse]:
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

    def take_torrent(self, torrent_name: str, worker_name: str) -> TorrentResponse:
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

    def ready(self) -> bool:
        """Test the ready endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        # response = httpx.get(ENDPOINT_READY, headers=headers, timeout=TIMEOUT)
        response = httpx.get(self.endpoint_ready, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()["ready"]

    def log(self) -> str:
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

    def torrent_info(self, name: str) -> TorrentResponse:
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
        json = response.json()
        return TorrentResponse(**json)

    def download_torrent(self, torrent_name: str) -> bytes:
        """Test the torrent download endpoint."""
        headers = {
            "accept": "application/x-bittorrent",
            "api-key": self.api_key,
        }
        json = {"torrent_name": torrent_name}
        response = httpx.post(
            f"http://localhost:{self.port}/torrent/download",
            headers=headers,
            json=json,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.content

    def set_torrent_complete(
        self, torrent_name: str, worker_name: str
    ) -> TorrentResponse:
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
        json = response.json()
        return TorrentResponse(**json)

    def set_torrent_error(self, name: str, error_message: str) -> dict:
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

    def update_torrent(
        self, worker_name: str, torrent_name: str, progress: int
    ) -> TorrentResponse:
        """Test the torrent update endpoint."""
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        body = {
            "torrent_name": torrent_name,
            "worker_name": worker_name,
            "progress": progress,
        }
        response = httpx.post(
            f"http://localhost:{self.port}/torrent/update",
            headers=headers,
            json=body,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        out = response.json()
        return TorrentResponse(**out)

    def list_pending_torrents(
        self, order_by_oldest: bool = True
    ) -> list[TorrentResponse]:
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

    def list_active_torrents(self) -> list[TorrentResponse]:
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

    def list_completed_torrents(self) -> list[TorrentResponse]:
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
