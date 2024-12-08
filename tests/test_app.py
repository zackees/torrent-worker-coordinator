import unittest

from torrent_worker_coordinator.integration_test_env import (
    request_get,
    request_info,
    request_protected,
    request_torrent_list_all,
    run_server_in_thread,
)
from torrent_worker_coordinator.settings import API_KEY


class ExampleTester(unittest.TestCase):
    """Example tester."""

    def test_request_get(self) -> None:
        """Test querying pending torrents."""
        with run_server_in_thread():
            result = request_get()
            print(result)
            print()

    def test_request_protected(self) -> None:
        """Test querying pending torrents."""
        with run_server_in_thread():
            result = request_protected(API_KEY)
            print(result)
            print()

    def test_request_info(self) -> None:
        """Test querying pending torrents."""
        with run_server_in_thread():
            result = request_info(API_KEY)
            print(result)
            print()

    def test_request_torrent_list_all(self) -> None:
        """Test querying pending torrents."""
        with run_server_in_thread():
            result = request_torrent_list_all(API_KEY)
            print(result)
            print()


if __name__ == "__main__":
    unittest.main()
