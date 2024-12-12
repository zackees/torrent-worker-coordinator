from .client import Client
from .test.test_app import TestApp


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
