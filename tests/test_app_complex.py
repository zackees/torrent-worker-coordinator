import os
import shutil
import time
import unittest

# isort: off
os.environ.update(
    {
        "GITHUB_REPO_URL": "https://github.com/zackees/torrent-test",
        "DB_URL": "sqlite:///.cache/test.db",
    }
)
# isort: on

from torrent_worker_coordinator.integration_test_env import (
    request_ready,
    request_torrent_list_all,
    run_server_in_thread,
)
from torrent_worker_coordinator.models import Base, TorrentManager, engine, get_db
from torrent_worker_coordinator.paths import DATA_DIR
from torrent_worker_coordinator.settings import API_KEY

IS_RENDER = any([key.startswith("RENDER_") for key in os.environ.keys()])


class ComplexAppTester(unittest.TestCase):
    """Example tester."""

    # before
    def setUp(self) -> None:
        """Setup test environment before each test."""
        if IS_RENDER:
            return  # don't delete the data store while running on render.com

        Base.metadata.drop_all(engine)  # Clear any existing tables
        Base.metadata.create_all(engine)  # Create fresh tables

        # Add a test torrent
        with get_db() as db:
            TorrentManager.create_torrent(db, "test_torrent.torrent")

        shutil.rmtree(DATA_DIR, ignore_errors=True)

    @unittest.skipIf(IS_RENDER, "Why is this running on render?")
    def test_download_cycle(self) -> None:
        """Test the basic GET endpoint."""
        with run_server_in_thread():

            while request_ready(API_KEY)["ready"] is False:
                time.sleep(0.1)

            torrents = request_torrent_list_all(API_KEY)["torrents"]
            self.assertEqual(
                1,
                len(torrents),
                f"Expected 1 torrent, got {len(torrents)}, which was {torrents}",
            )

            for torrent in torrents:
                print(torrent)
            print()


if __name__ == "__main__":
    unittest.main()
