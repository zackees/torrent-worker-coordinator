import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from torrent_worker_coordinator.task_populate_torrents import (
    sync_task_populate_torrents,
    task_populate_torrents,
)


class TestPopulateTorrents(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock(spec=Session)
        self.test_paths = [Path("test1.torrent"), Path("test2.torrent")]
        self.repo_url = "https://github.com/test/repo"
        self.path = Path("test_path")
        self.torrents_path = Path("test_torrents")

    @patch(
        "torrent_worker_coordinator.task_populate_torrents.sync_task_download_github"
    )
    @patch("torrent_worker_coordinator.task_populate_torrents.TorrentManager")
    async def test_task_populate_torrents(self, mock_torrent_manager, mock_download):
        # Configure mock to return test paths
        mock_download.return_value = self.test_paths

        # Execute
        await task_populate_torrents(
            self.mock_db, self.repo_url, self.path, self.torrents_path
        )

        # Verify
        mock_download.assert_called_once_with(
            self.repo_url, self.path, self.torrents_path
        )
        self.assertEqual(
            mock_torrent_manager.create_if_missing.call_count, len(self.test_paths)
        )
        for test_path in self.test_paths:
            mock_torrent_manager.create_if_missing.assert_any_call(
                self.mock_db, test_path.name
            )

    @patch(
        "torrent_worker_coordinator.task_populate_torrents.sync_task_download_github"
    )
    @patch("torrent_worker_coordinator.task_populate_torrents.TorrentManager")
    def test_sync_task_populate_torrents(self, mock_torrent_manager, mock_download):
        # Configure mock to return test paths
        mock_download.return_value = self.test_paths

        # Execute
        sync_task_populate_torrents(
            self.mock_db, self.repo_url, self.path, self.torrents_path
        )

        # Verify
        mock_download.assert_called_once_with(
            self.repo_url, self.path, self.torrents_path
        )
        self.assertEqual(
            mock_torrent_manager.create_if_missing.call_count, len(self.test_paths)
        )
        for test_path in self.test_paths:
            mock_torrent_manager.create_if_missing.assert_any_call(
                self.mock_db, test_path.name
            )


if __name__ == "__main__":
    unittest.main()
