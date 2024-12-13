import unittest
from pathlib import Path

from torrent_worker_coordinator.info_hash import info_hash

HERE = Path(__file__).parent
TEST_DIR = HERE / "test_data"
BUNNY_TORRENT = TEST_DIR / "bunny.torrent"
assert BUNNY_TORRENT.exists()


class InfoHashTester(unittest.TestCase):

    def test_info_hash(self):
        h = info_hash(BUNNY_TORRENT)
        self.assertEqual(h, "af8f10f30bf9aefecf3686922bfa0d5bd290a395")


if __name__ == "__main__":
    unittest.main()
