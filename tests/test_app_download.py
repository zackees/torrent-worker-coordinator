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

from torrent_worker_coordinator.app_schemas import TorrentResponse  # noqa: E402
from torrent_worker_coordinator.test.test_app import TestApp  # noqa: E402

IS_RENDER = any([key.startswith("RENDER_") for key in os.environ.keys()])


class ComplexAppTester(unittest.TestCase):
    """Example tester."""

    # before
    def setUp(self) -> None:
        """Setup test environment before each test."""
        if IS_RENDER:
            return  # don't delete the data store while running on render.com

    @unittest.skipIf(IS_RENDER, "Why is this running on render?")
    def test_download_cycle(self) -> None:
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
            out: TorrentResponse = app.take_torrent(
                torrent_name="test.torrent", worker_name="test_worker"
            )
            print(out)
            self.assertTrue(out.name == "test.torrent")

            torrents = app.list_torrents()
            self.assertEqual(
                1,
                len(torrents),
                f"Expected 1 torrent, got {len(torrents)}, which was {torrents}",
            )
            torrent = torrents[0]
            name = torrent.name
            status = torrent.status
            self.assertEqual("test.torrent", name)
            self.assertEqual("active", status)

            torrent = app.update_torrent(
                worker_name="test_worker", torrent_name="test.torrent", progress=50
            )
            self.assertEqual(50, torrent.progress)

            out = app.set_torrent_complete(
                torrent_name="test.torrent", worker_name="test_worker"
            )

            torrent_bytes = app.download_torrent(torrent_name="test.torrent")
            self.assertIsNotNone(torrent_bytes)
            pending_torrents = app.list_pending_torrents()
            self.assertEqual(0, len(pending_torrents))
            completed_torrents = app.list_completed_torrents()
            self.assertEqual(1, len(completed_torrents))


if __name__ == "__main__":
    unittest.main()
