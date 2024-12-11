import os

os.environ["GITHUB_REPO_URL"] = (
    "https://github.com/zackees/torrent-test"  # Small, fake and fast.
)

import shutil
import unittest

from torrent_worker_coordinator.integration_test_env import (
    request_torrent_list_all,
    run_server_in_thread,
)
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

        shutil.rmtree(DATA_DIR, ignore_errors=True)

    @unittest.skipIf(IS_RENDER, "Why is this running on render?")
    def test_download_cycle(self) -> None:
        """Test the basic GET endpoint."""
        with run_server_in_thread():
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
