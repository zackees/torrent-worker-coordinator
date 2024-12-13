from .app_schemas import InfoResponse, TorrentListResponse, TorrentResponse
from .client import Client, ClientException
from .test.test_app import TestApp

__version__ = "1.0.17"


class Api:
    @staticmethod
    def client(
        host: str,
        port: int,
        api_key: str,
    ) -> Client:
        client = Client(host=host, port=port, api_key=api_key)
        return client


class Test:
    @staticmethod
    def app(
        api_key: str | None = None,
    ) -> TestApp:
        app = TestApp(api_key=api_key)
        return app


__all__ = [
    "Api",
    "Test",
    "InfoResponse",
    "TorrentListResponse",
    "TorrentResponse",
    "ClientException",
]
