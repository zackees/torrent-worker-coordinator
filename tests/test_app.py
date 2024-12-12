import os
import unittest

# isort: off
from tempfile import NamedTemporaryFile  # noqa: E402

URL = f"sqlite:///{NamedTemporaryFile().name}"
environ = {
    "GITHUB_REPO_URL": "https://github.com/zackees/torrent-test",
    "DB_URL": URL,
}
os.environ.update(environ)
# isort: on


from torrent_worker_coordinator.test.test_app import TestApp  # noqa: E402

IS_RENDER = any([key.startswith("RENDER_") for key in os.environ.keys()])

PORT = 4446

_next

class AppTester(unittest.TestCase):
    """Example tester."""

    def test_info(self) -> None:
        """Test the info endpoint returns version and ready status."""
        with TestApp(PORT + 2) as app:
            result = app.info()
            # self.assertIn("version", result)
            # self.assertIn("ready", result)
            version = result.version
            ready = result.ready
            self.assertIsNotNone(version)
            self.assertTrue(ready)
            print(result)
            print()

    def test_list_torrents(self) -> None:
        """Test retrieving the full torrent list."""
        with TestApp(PORT + 3) as app:
            result = app.list_torrents()
            print(result)
            print()

    def test_ready(self) -> None:
        """Test the ready status endpoint."""
        with TestApp(PORT + 4) as app:
            result = app.ready()
            print(result)
            print()


if __name__ == "__main__":
    unittest.main()
