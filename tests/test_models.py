import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from torrent_worker_coordinator.models import Base, TorrentManager, TorrentStatus


class TestTorrentManager(unittest.TestCase):
    def setUp(self):
        """Set up test database before each test."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

        connection = self.engine.connect()
        self.transaction = connection.begin()
        self.db_session = Session(bind=connection)

    def tearDown(self):
        """Clean up after each test."""
        self.db_session.close()
        self.transaction.rollback()
        self.engine.dispose()

    def test_create_torrent(self):
        """Test creating a new torrent."""
        torrent = TorrentManager.create_torrent(self.db_session, "test_torrent")
        self.assertEqual(torrent.name, "test_torrent")
        self.assertEqual(torrent.status, TorrentStatus.PENDING)
        self.assertIsNone(torrent.worker_id)
        self.assertIsInstance(torrent.created_at, datetime)
        self.assertIsInstance(torrent.updated_at, datetime)
        self.assertIsNone(torrent.completed_at)

    def test_get_torrent(self):
        """Test getting a torrent by name."""
        # Create a torrent first
        TorrentManager.create_torrent(self.db_session, "test_torrent")

        # Get the torrent
        torrent = TorrentManager.get_torrent(self.db_session, "test_torrent")
        self.assertIsNotNone(torrent)
        self.assertEqual(torrent.name, "test_torrent")

        # Try getting non-existent torrent
        non_existent = TorrentManager.get_torrent(self.db_session, "non_existent")
        self.assertIsNone(non_existent)

    def test_take_torrent(self):
        """Test taking ownership of a torrent."""
        # Create a torrent
        TorrentManager.create_torrent(self.db_session, "test_torrent")

        # Take the torrent
        torrent = TorrentManager.take_torrent(
            self.db_session, "test_torrent", "worker1"
        )
        self.assertIsNotNone(torrent)
        self.assertEqual(torrent.status, TorrentStatus.ACTIVE)
        self.assertEqual(torrent.worker_id, "worker1")

        # Try taking an already taken torrent
        result = TorrentManager.take_torrent(self.db_session, "test_torrent", "worker2")
        self.assertIsNone(result)

    def test_update_torrent_status(self):
        """Test updating torrent status."""
        # Create a torrent
        TorrentManager.create_torrent(self.db_session, "test_torrent")

        # Update status
        updated = TorrentManager.update_torrent_status(
            self.db_session,
            "test_torrent",
            TorrentStatus.ACTIVE,
            progress=50,
            last_update="Processing...",
        )
        self.assertEqual(updated.status, TorrentStatus.ACTIVE)
        self.assertEqual(updated.progress, 50)
        self.assertEqual(updated.last_update, "Processing...")

        # Update to completed
        completed = TorrentManager.update_torrent_status(
            self.db_session, "test_torrent", TorrentStatus.COMPLETED
        )
        self.assertEqual(completed.status, TorrentStatus.COMPLETED)
        self.assertIsNotNone(completed.completed_at)

    def test_get_torrents_by_status(self):
        """Test getting torrents by status."""
        # Create some torrents with different statuses
        TorrentManager.create_torrent(self.db_session, "pending1")
        TorrentManager.create_torrent(self.db_session, "pending2")

        active = TorrentManager.create_torrent(self.db_session, "active1")
        TorrentManager.update_torrent_status(
            self.db_session, "active1", TorrentStatus.ACTIVE
        )

        completed = TorrentManager.create_torrent(self.db_session, "completed1")
        TorrentManager.update_torrent_status(
            self.db_session, "completed1", TorrentStatus.COMPLETED
        )

        # Test filtering
        pending = TorrentManager.get_torrents_by_status(
            self.db_session, TorrentStatus.PENDING
        )
        self.assertEqual(len(pending), 2)

        active = TorrentManager.get_torrents_by_status(
            self.db_session, TorrentStatus.ACTIVE
        )
        self.assertEqual(len(active), 1)

        completed = TorrentManager.get_torrents_by_status(
            self.db_session, TorrentStatus.COMPLETED
        )
        self.assertEqual(len(completed), 1)

    def test_get_all_torrents(self):
        """Test getting all torrents."""
        # Create some torrents
        TorrentManager.create_torrent(self.db_session, "torrent1")
        TorrentManager.create_torrent(self.db_session, "torrent2")
        TorrentManager.create_torrent(self.db_session, "torrent3")

        torrents = TorrentManager.get_all_torrents(self.db_session)
        self.assertEqual(len(torrents), 3)

    def test_torrent_to_dict(self):
        """Test the to_dict method of Torrent."""
        torrent = TorrentManager.create_torrent(self.db_session, "test_torrent")
        torrent_dict = torrent.to_dict()

        self.assertIsInstance(torrent_dict, dict)
        self.assertEqual(torrent_dict["name"], "test_torrent")
        self.assertEqual(torrent_dict["status"], TorrentStatus.PENDING.value)
        self.assertIn("created_at", torrent_dict)
        self.assertIn("updated_at", torrent_dict)


if __name__ == "__main__":
    unittest.main()
