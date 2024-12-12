import httpx

from torrent_worker_coordinator.app_schemas import (
    InfoResponse,
    TorrentListResponse,
    TorrentResponse,
)
from torrent_worker_coordinator.settings import API_KEY, CLIENT_SERVER_URL
from torrent_worker_coordinator.test.run_server_in_thread import TIMEOUT


def _init_host(host: str | None) -> str:
    if host is None:
        return CLIENT_SERVER_URL
    if host.startswith("http"):
        return host.split("://")[-1]
    return host


class Client:

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        api_key: str | None = None,
    ) -> None:
        self.host = _init_host(host)
        self.port = port or 80
        self.api_key = api_key or API_KEY
        self.endpoint_get = self._make_endpoint("get")
        self.endpoint_protected = self._make_endpoint("protected")
        self.endpoint_info = self._make_endpoint("info")
        self.endpoint_list_torrents = self._make_endpoint("torrent/list/all")
        self.endpoint_ready = self._make_endpoint("ready")
        self.endpoint_torrent_take = self._make_endpoint("torrent/take")

    def _make_endpoint(self, path: str) -> str:
        if self.port == 80:
            host = f"http://{self.host}"
        else:
            host = f"http://{self.host}:{self.port}"
        return f"{host}/{path}"

    def _post_json(self, endpoint: str, json: dict) -> dict:
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        response = httpx.post(
            endpoint,
            headers=headers,
            json=json,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        json = response.json()
        return json

    def _download(self, endpoint: str, json: dict | None = None) -> bytes:
        headers = {
            "accept": "application/x-bittorrent",
            "api-key": self.api_key,
        }
        response = httpx.post(
            endpoint,
            headers=headers,
            timeout=TIMEOUT,
            json=json,
        )
        response.raise_for_status()
        return response.content

    def info(self) -> InfoResponse:
        """Test the info endpoint."""
        json = self.get_json("info")
        return InfoResponse(**json)

    def list_torrents(self) -> list[TorrentResponse]:
        """Test the list_all endpoint."""
        json = self._post_json(self.endpoint_list_torrents, {})
        return TorrentListResponse(**json).torrents

    def take_torrent(self, worker_name: str, torrent_name: str) -> TorrentResponse:
        """Test the take endpoint."""
        url = self.endpoint_torrent_take
        body = {"worker_name": worker_name, "torrent_name": torrent_name}
        json = self._post_json(
            url,
            body,
        )
        return TorrentResponse(**json)

    def ready(self) -> bool:
        """Test the ready endpoint."""
        return self.info().ready

    def log(self) -> str:
        """Test the log endpoint."""
        headers = {
            "accept": "text/plain",
            "api-key": self.api_key,
        }
        url = self._make_endpoint("log")
        response = httpx.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text

    def get_json(self, path: str) -> dict:
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
        }
        url = self._make_endpoint(path)
        response = httpx.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def torrent_info(self, name: str) -> TorrentResponse:
        """Test the torrent info endpoint."""
        json = self._post_json(self._make_endpoint("torrent/info"), {"name": name})
        return TorrentResponse(**json)

    def download_torrent(self, torrent_name: str) -> bytes:
        """Test the torrent download endpoint."""
        out = self._download(
            self._make_endpoint("torrent/download"),
            {"torrent_name": torrent_name},
        )
        return out

    def set_torrent_complete(
        self, torrent_name: str, worker_name: str
    ) -> TorrentResponse:
        """Test the torrent complete endpoint."""
        json = self._post_json(
            self._make_endpoint("torrent/complete"),
            {"torrent_name": torrent_name, "worker_name": worker_name},
        )
        return TorrentResponse(**json)

    def set_torrent_error(self, name: str, error_message: str) -> dict:
        """Test the torrent error endpoint."""
        json = self._post_json(
            self._make_endpoint("torrent/error"),
            {"name": name, "error_message": error_message},
        )
        return json

    def update_torrent(
        self, worker_name: str, torrent_name: str, progress: int
    ) -> TorrentResponse:
        """Test the torrent update endpoint."""
        out = self._post_json(
            self._make_endpoint("torrent/update"),
            {
                "torrent_name": torrent_name,
                "worker_name": worker_name,
                "progress": progress,
            },
        )
        return TorrentResponse(**out)

    def list_pending_torrents(
        self, order_by_oldest: bool = True
    ) -> list[TorrentResponse]:
        """Test the pending torrents list endpoint."""
        json = self._post_json(
            self._make_endpoint("torrent/list/pending"),
            {"order_by_oldest": order_by_oldest},
        )
        return TorrentListResponse(**json).torrents

    def list_active_torrents(self) -> list[TorrentResponse]:
        """Test the active torrents list endpoint."""
        json = self.get_json("torrent/list/active")
        return TorrentListResponse(**json).torrents

    def list_completed_torrents(self) -> list[TorrentResponse]:
        """Test the completed torrents list endpoint."""
        url = self._make_endpoint("torrent/list/completed")
        json = self._post_json(url, {})
        return TorrentListResponse(**json).torrents
