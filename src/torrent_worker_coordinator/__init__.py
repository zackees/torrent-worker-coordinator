from .client import Client


class Api:
    @staticmethod
    def client(
        host: str,
        port: int,
        api_key: str,
    ) -> Client:
        client = Client(host=host, port=port, api_key=api_key)
        return client
