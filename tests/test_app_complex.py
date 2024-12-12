import os  # noqa: E402
import time  # noqa: E402
import unittest  # noqa: E402
from tempfile import NamedTemporaryFile  # noqa: E402


def make_port(string_to_hash: str) -> int:
    """Make a port number from a string."""
    # return int(crypt.crypt(string_to_hash, "salt")[0:5])  // this isn't right
    hash_value = hash(string_to_hash)
    return int(str(hash_value)[1:6])


# isort: off
PORT = make_port(__file__)
URL = f"sqlite:///{NamedTemporaryFile().name}"
environ = {
    "GITHUB_REPO_URL": "https://github.com/zackees/torrent-test",
    "DB_URL": URL,
}
os.environ.update(environ)
# isort: on

from torrent_worker_coordinator.integration_test_env import TestApp  # noqa: E402

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

            while app.request_ready() is False:
                time.sleep(0.1)

            torrents = app.request_torrent_list_all()
            self.assertEqual(
                1,
                len(torrents),
                f"Expected 1 torrent, got {len(torrents)}, which was {torrents}",
            )
            out: dict = app.request_torrent_take(
                torrent_name="test.torrent", worker_name="test_worker"
            )
            self.assertTrue(out["name"] == "test.torrent")

            torrents = app.request_torrent_list_all()
            self.assertEqual(
                1,
                len(torrents),
                f"Expected 1 torrent, got {len(torrents)}, which was {torrents}",
            )
            torrent = torrents[0]
            name = torrent["name"]
            status = torrent["status"]
            self.assertEqual("test.torrent", name)
            self.assertEqual("active", status)


if __name__ == "__main__":
    unittest.main()
