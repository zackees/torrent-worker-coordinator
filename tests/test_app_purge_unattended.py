import os  # noqa: E402
import time  # noqa: E402
import unittest  # noqa: E402
from tempfile import NamedTemporaryFile  # noqa: E402

# isort: off
URL = f"sqlite:///{NamedTemporaryFile().name}"
environ = {
    "GITHUB_REPO_URL": "https://github.com/zackees/torrent-test",
    "DB_URL": URL,
}
os.environ.update(environ)
# isort: on

from torrent_worker_coordinator.models import get_db  # noqa: E402
from torrent_worker_coordinator.test.test_app import TestApp  # noqa: E402
from torrent_worker_coordinator.torrent_manager import TorrentManager  # noqa: E402

IS_RENDER = any([key.startswith("RENDER_") for key in os.environ.keys()])


class ComplexAppTester(unittest.TestCase):
    """Example tester."""

    # before
    def setUp(self) -> None:
        """Setup test environment before each test."""
        if IS_RENDER:
            return  # don't delete the data store while running on render.com

    def test_purge_unattended(self) -> None:
        """Test the basic GET endpoint."""
        with TestApp() as app:

            while app.ready() is False:
                time.sleep(0.1)

            torrents = app.list_torrents()
            self.assertEqual(
                1,
                len(torrents),
                f"Expected 1 torrent, got {len(torrents)}, which was {torrents}",
            )
            app.take_torrent(torrent_name="test.torrent", worker_name="test_worker")
            # update it to 50% progress
            torrent = app.update_torrent("test_worker", "test.torrent", 50)

            with get_db() as db:
                TorrentManager.recycle_unattended_torrents(db, max_age=1)
                torrents = app.list_torrents()
                self.assertEqual(1, len(torrents))
                torrent = torrents[0]
                self.assertTrue(torrent.status == "active")
                # recycle all torrents
                TorrentManager.recycle_unattended_torrents(db, max_age=0)
                torrents = app.list_torrents()
                self.assertEqual(1, len(torrents))
                torrent = torrents[0]
                self.assertTrue(torrent.status == "pending")


if __name__ == "__main__":
    unittest.main()
