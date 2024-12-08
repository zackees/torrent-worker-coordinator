import unittest
from pathlib import Path

from torrent_worker_coordinator.models import TorrentManager, get_db
from torrent_worker_coordinator.paths import PROJECT_ROOT
from torrent_worker_coordinator.task_populate_torrents import (
    sync_task_populate_torrents,
)


class TestPopulateTorrents(unittest.TestCase):
    """Test suite for torrent population functionality using real GitHub repo."""

    TEST_REPO_URL = "https://github.com/zackees/zlibry"
    TEST_DIR = PROJECT_ROOT / Path(".cache/test_repos")
    TEST_TORRENTS_DIR = PROJECT_ROOT / Path(".cache/test_torrents")

    def setUp(self):
        """Setup test environment before each test."""
        self.TEST_DIR.mkdir(parents=True, exist_ok=True)
        self.TEST_TORRENTS_DIR.mkdir(parents=True, exist_ok=True)

    def test_populate_torrents(self):
        """Test populating torrents from the test repository."""
        # Run the populate task
        sync_task_populate_torrents(
            self.TEST_REPO_URL, self.TEST_DIR, self.TEST_TORRENTS_DIR
        )

        # Verify results in database
        all_torrents = TorrentManager.get_all_torrents(get_db())
        self.assertTrue(len(all_torrents) > 0, "Should have found some torrents")

        # Verify at least one torrent has expected fields populated
        first_torrent = all_torrents[0]
        self.assertIsNotNone(first_torrent.name)
        self.assertIsNotNone(first_torrent.status)
        self.assertIsNotNone(first_torrent.created_at)

        # Verify files were copied to torrents directory
        self.assertTrue(
            any(self.TEST_TORRENTS_DIR.iterdir()),
            "Torrents directory should contain files",
        )


if __name__ == "__main__":
    unittest.main()
