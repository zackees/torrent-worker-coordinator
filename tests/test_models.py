from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from torrent_worker_coordinator.models import Base, TorrentManager, TorrentStatus

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(engine):
    """Create test database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def test_create_torrent(db_session):
    """Test creating a new torrent."""
    torrent = TorrentManager.create_torrent(db_session, "test_torrent")
    assert torrent.name == "test_torrent"
    assert torrent.status == TorrentStatus.PENDING
    assert torrent.worker_id is None
    assert isinstance(torrent.created_at, datetime)
    assert isinstance(torrent.updated_at, datetime)
    assert torrent.completed_at is None


def test_get_torrent(db_session):
    """Test getting a torrent by name."""
    # Create a torrent first
    TorrentManager.create_torrent(db_session, "test_torrent")

    # Get the torrent
    torrent = TorrentManager.get_torrent(db_session, "test_torrent")
    assert torrent is not None
    assert torrent.name == "test_torrent"

    # Try getting non-existent torrent
    non_existent = TorrentManager.get_torrent(db_session, "non_existent")
    assert non_existent is None


def test_take_torrent(db_session):
    """Test taking ownership of a torrent."""
    # Create a torrent
    TorrentManager.create_torrent(db_session, "test_torrent")

    # Take the torrent
    torrent = TorrentManager.take_torrent(db_session, "test_torrent", "worker1")
    assert torrent is not None
    assert torrent.status == TorrentStatus.ACTIVE
    assert torrent.worker_id == "worker1"

    # Try taking an already taken torrent
    result = TorrentManager.take_torrent(db_session, "test_torrent", "worker2")
    assert result is None


def test_update_torrent_status(db_session):
    """Test updating torrent status."""
    # Create a torrent
    TorrentManager.create_torrent(db_session, "test_torrent")

    # Update status
    updated = TorrentManager.update_torrent_status(
        db_session,
        "test_torrent",
        TorrentStatus.ACTIVE,
        progress=50,
        last_update="Processing...",
    )
    assert updated.status == TorrentStatus.ACTIVE
    assert updated.progress == 50
    assert updated.last_update == "Processing..."

    # Update to completed
    completed = TorrentManager.update_torrent_status(
        db_session, "test_torrent", TorrentStatus.COMPLETED
    )
    assert completed.status == TorrentStatus.COMPLETED
    assert completed.completed_at is not None


def test_get_torrents_by_status(db_session):
    """Test getting torrents by status."""
    # Create some torrents with different statuses
    TorrentManager.create_torrent(db_session, "pending1")
    TorrentManager.create_torrent(db_session, "pending2")

    active = TorrentManager.create_torrent(db_session, "active1")
    TorrentManager.update_torrent_status(db_session, "active1", TorrentStatus.ACTIVE)

    completed = TorrentManager.create_torrent(db_session, "completed1")
    TorrentManager.update_torrent_status(
        db_session, "completed1", TorrentStatus.COMPLETED
    )

    # Test filtering
    pending = TorrentManager.get_torrents_by_status(db_session, TorrentStatus.PENDING)
    assert len(pending) == 2

    active = TorrentManager.get_torrents_by_status(db_session, TorrentStatus.ACTIVE)
    assert len(active) == 1

    completed = TorrentManager.get_torrents_by_status(
        db_session, TorrentStatus.COMPLETED
    )
    assert len(completed) == 1


def test_get_all_torrents(db_session):
    """Test getting all torrents."""
    # Create some torrents
    TorrentManager.create_torrent(db_session, "torrent1")
    TorrentManager.create_torrent(db_session, "torrent2")
    TorrentManager.create_torrent(db_session, "torrent3")

    torrents = TorrentManager.get_all_torrents(db_session)
    assert len(torrents) == 3


def test_torrent_to_dict(db_session):
    """Test the to_dict method of Torrent."""
    torrent = TorrentManager.create_torrent(db_session, "test_torrent")
    torrent_dict = torrent.to_dict()

    assert isinstance(torrent_dict, dict)
    assert torrent_dict["name"] == "test_torrent"
    assert torrent_dict["status"] == TorrentStatus.PENDING.value
    assert "created_at" in torrent_dict
    assert "updated_at" in torrent_dict
