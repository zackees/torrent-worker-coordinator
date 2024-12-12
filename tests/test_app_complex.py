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

from torrent_worker_coordinator.integration_test_env import (  # noqa: E402
    request_ready,
    request_torrent_list_all,
    request_torrent_take,
    run_server_in_thread,
)
from torrent_worker_coordinator.settings import API_KEY  # noqa: E402

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

            out = request_torrent_take(
                API_KEY, torrent_name="test.torrent", worker_name="test_worker"
            )
            print(out)


if __name__ == "__main__":
    unittest.main()
