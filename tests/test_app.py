import os
import unittest

# isort: off
os.environ.update(
    {
        "GITHUB_REPO_URL": "https://github.com/zackees/torrent-test",
        "DB_URL": "sqlite:///.cache/test2.db",
    }
)
# isort: on


from torrent_worker_coordinator.integration_test_env import (
    request_get,
    request_info,
    request_protected,
    request_ready,
    request_torrent_list_all,
    run_server_in_thread,
)
from torrent_worker_coordinator.models import Base, engine
from torrent_worker_coordinator.settings import API_KEY

IS_RENDER = any([key.startswith("RENDER_") for key in os.environ.keys()])


class AppTester(unittest.TestCase):
    """Example tester."""

    def setUp(self) -> None:
        """Setup test environment before each test."""
        if IS_RENDER:
            return  # don't delete the data store while running on render.com

        Base.metadata.drop_all(engine)  # Clear any existing tables
        Base.metadata.create_all(engine)  # Create fresh tables

        # Add a test torrent
        # with get_db() as db:
        #    TorrentManager.create_torrent(db, "test_torrent.torrent")

    def test_request_get(self) -> None:
        """Test the basic GET endpoint."""
        with run_server_in_thread():
            result = request_get()
            print(result)
            print()

    def test_request_protected(self) -> None:
        """Test the protected endpoint requiring API key."""
        with run_server_in_thread():
            result = request_protected(API_KEY)
            print(result)
            print()

    def test_request_info(self) -> None:
        """Test the info endpoint returns version and ready status."""

        with run_server_in_thread():
            result = request_info(API_KEY)
            self.assertIn("version", result)
            self.assertIn("ready", result)
            print(result)
            print()

    def test_request_torrent_list_all(self) -> None:
        """Test retrieving the full torrent list."""
        with run_server_in_thread():
            result = request_torrent_list_all(API_KEY)
            print(result)
            print()

    def test_request_ready(self) -> None:
        """Test the ready status endpoint."""
        with run_server_in_thread():
            result = request_ready(API_KEY)
            print(result)
            print()


if __name__ == "__main__":
    unittest.main()
