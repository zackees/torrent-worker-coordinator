import os
import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

# isort: off
HERE = Path(__file__).parent
PROJECT_ROOT = HERE.parent

URL = f"sqlite:///{NamedTemporaryFile().name}"
environ = {
    "GITHUB_REPO_URL": "https://github.com/zackees/torrent-test",
    "DB_URL": URL,
    "DATA_DIR": str(PROJECT_ROOT / ".cache" / "3"),
}
os.environ.update(environ)
# isort: on


from torrent_worker_coordinator.test.test_app import TestApp  # noqa: E402

IS_RENDER = any([key.startswith("RENDER_") for key in os.environ.keys()])


class AppTester(unittest.TestCase):
    """Example tester."""

    def test_info(self) -> None:
        """Test the info endpoint returns version and ready status."""
        with TestApp() as app:
            result = app.info()
            version = result.version
            ready = result.ready
            self.assertIsNotNone(version)
            self.assertTrue(ready)
            print(result)
            print()

    def test_list_torrents(self) -> None:
        """Test retrieving the full torrent list."""
        with TestApp() as app:
            result = app.list_torrents()
            print(result)
            print()

    def test_ready(self) -> None:
        """Test the ready status endpoint."""
        with TestApp() as app:
            result = app.ready()
            print(result)
            print()

    def test_torrent_info(self) -> None:
        """Test retrieving torrent info."""
        with TestApp() as app:
            result = app.torrent_info("1.torrent")
            print(result)
            print()


if __name__ == "__main__":
    unittest.main()
