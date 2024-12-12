from .client import Client


class Api:
    @staticmethod
    def client(
        host: str,
        port: int,
        api_key: str,
    ) -> Client:
        client = Client(host, port, api_key)
        return client
