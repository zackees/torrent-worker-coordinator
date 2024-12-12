from sqlalchemy.orm import Session

from torrent_worker_coordinator.models import TorrentStatus
from torrent_worker_coordinator.torrent_manager import TorrentManager


def query_torrents_pending(db: Session) -> list:
    """
    Query all torrents with PENDING status.

    Args:
        db: SQLAlchemy database session

    Returns:
        List of Torrent objects with PENDING status
    """
    return TorrentManager.get_torrents_by_status(
        db, TorrentStatus.PENDING, order_by_oldest=True
    )


def query_torrents_finished(db: Session) -> list:
    """
    Query all torrents with COMPLETED status.

    Args:
        db: SQLAlchemy database session

    Returns:
        List of Torrent objects with COMPLETED status
    """
    return TorrentManager.get_torrents_by_status(
        db, TorrentStatus.COMPLETED, order_by_oldest=False
    )
