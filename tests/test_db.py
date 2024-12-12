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

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from torrent_worker_coordinator.db import (  # noqa: E402
    query_torrents_finished,
    query_torrents_pending,
)
from torrent_worker_coordinator.models import Base, Torrent, TorrentStatus  # noqa: E402


class TestDatabase(unittest.TestCase):
    def setUp(self):
        """Set up test database before each test."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.db_session = TestingSessionLocal()

    def tearDown(self):
        """Clean up after each test."""
        self.db_session.close()

    def create_sample_torrents(self):
        """Create sample torrents with different statuses."""
        torrents = [
            Torrent(name="pending1", status=TorrentStatus.PENDING),
            Torrent(name="pending2", status=TorrentStatus.PENDING),
            Torrent(name="active1", status=TorrentStatus.ACTIVE),
            Torrent(name="completed1", status=TorrentStatus.COMPLETED),
            Torrent(name="completed2", status=TorrentStatus.COMPLETED),
            Torrent(name="error1", status=TorrentStatus.ERROR),
        ]

        for torrent in torrents:
            self.db_session.add(torrent)
        self.db_session.commit()

        return torrents

    def test_query_torrents_pending(self):
        """Test querying pending torrents."""
        self.create_sample_torrents()
        pending_torrents = query_torrents_pending(self.db_session)

        self.assertEqual(len(pending_torrents), 2)
        self.assertTrue(
            all(t.status == TorrentStatus.PENDING for t in pending_torrents)
        )
        self.assertEqual(
            set(t.name for t in pending_torrents), {"pending1", "pending2"}
        )

    def test_query_torrents_finished(self):
        """Test querying completed torrents."""
        self.create_sample_torrents()
        completed_torrents = query_torrents_finished(self.db_session)

        self.assertEqual(len(completed_torrents), 2)
        self.assertTrue(
            all(t.status == TorrentStatus.COMPLETED for t in completed_torrents)
        )
        self.assertEqual(
            set(t.name for t in completed_torrents), {"completed1", "completed2"}
        )

    def test_empty_queries(self):
        """Test querying when no torrents exist."""
        pending_torrents = query_torrents_pending(self.db_session)
        completed_torrents = query_torrents_finished(self.db_session)

        self.assertEqual(len(pending_torrents), 0)
        self.assertEqual(len(completed_torrents), 0)


if __name__ == "__main__":
    unittest.main()
