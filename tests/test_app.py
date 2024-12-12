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


from torrent_worker_coordinator.integration_test_env import TestApp  # noqa: E402

IS_RENDER = any([key.startswith("RENDER_") for key in os.environ.keys()])

PORT = 4446


class AppTester(unittest.TestCase):
    """Example tester."""

    def test_request_get(self) -> None:
        """Test the basic GET endpoint."""
        with TestApp(PORT) as app:
            result = app.request_get()
            print(result)
            print()

    def test_request_protected(self) -> None:
        """Test the protected endpoint requiring API key."""
        with TestApp(PORT + 1) as app:
            result = app.request_protected()
            print(result)
            print()

    def test_request_info(self) -> None:
        """Test the info endpoint returns version and ready status."""
        with TestApp(PORT + 2) as app:
            result = app.request_info()
            self.assertIn("version", result)
            self.assertIn("ready", result)
            print(result)
            print()

    def test_request_torrent_list_all(self) -> None:
        """Test retrieving the full torrent list."""
        with TestApp(PORT + 3) as app:
            result = app.request_torrent_list_all()
            print(result)
            print()

    def test_request_ready(self) -> None:
        """Test the ready status endpoint."""
        with TestApp(PORT + 4) as app:
            result = app.request_ready()
            print(result)
            print()


if __name__ == "__main__":
    unittest.main()
