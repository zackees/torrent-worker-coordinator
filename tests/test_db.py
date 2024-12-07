import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from torrent_worker_coordinator.db import (
    query_torrents_finished,
    query_torrents_pending,
)
from torrent_worker_coordinator.models import Base, Torrent, TorrentStatus

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)


@pytest.fixture
def db_session():
    """Create a test database session."""

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_torrents(db_session: Session):
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
        db_session.add(torrent)
    db_session.commit()

    return torrents


def test_query_torrents_pending(db_session: Session, sample_torrents):
    """Test querying pending torrents."""
    pending_torrents = query_torrents_pending(db_session)

    assert len(pending_torrents) == 2
    assert all(t.status == TorrentStatus.PENDING for t in pending_torrents)
    assert set(t.name for t in pending_torrents) == {"pending1", "pending2"}


def test_query_torrents_finished(db_session: Session, sample_torrents):
    """Test querying completed torrents."""
    completed_torrents = query_torrents_finished(db_session)

    assert len(completed_torrents) == 2
    assert all(t.status == TorrentStatus.COMPLETED for t in completed_torrents)
    assert set(t.name for t in completed_torrents) == {"completed1", "completed2"}


def test_empty_queries(db_session: Session):
    """Test querying when no torrents exist."""
    pending_torrents = query_torrents_pending(db_session)
    completed_torrents = query_torrents_finished(db_session)

    assert len(pending_torrents) == 0
    assert len(completed_torrents) == 0
