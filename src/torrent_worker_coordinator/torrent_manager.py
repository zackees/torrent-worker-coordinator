from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session  # type: ignore

from torrent_worker_coordinator.log import make_logger
from torrent_worker_coordinator.models import Torrent, TorrentStatus

log = make_logger(__name__)


class TorrentManager:
    """Helper class for torrent database operations."""

    @staticmethod
    def get_torrent(db: Session, name: str) -> Optional[Torrent]:
        """Get a torrent by name."""
        return db.query(Torrent).filter(Torrent.name == name).first()

    @staticmethod
    def create_torrent(db: Session, name: str) -> Torrent:
        """Create a new torrent."""
        torrent = Torrent(name=name)
        try:
            db.add(torrent)
            db.commit()
            db.refresh(torrent)
            return torrent
        except SQLAlchemyError as e:
            db.rollback()
            log.error("Error creating torrent: %s", str(e))
            raise

    @staticmethod
    def create_if_missing(db: Session, name: str) -> Torrent:
        """Create a new torrent if it doesn't exist."""
        torrent = TorrentManager.get_torrent(db, name)
        if not torrent:
            torrent = TorrentManager.create_torrent(db, name)
        return torrent

    @staticmethod
    def get_all_torrents(db: Session) -> list[Torrent]:
        """Get all torrents."""
        return db.query(Torrent).all()

    @staticmethod
    def get_torrents_by_status(
        db: Session, status: TorrentStatus, order_by_oldest: bool = False
    ) -> list[Torrent]:
        """Get torrents by status."""
        if order_by_oldest:
            return (
                db.query(Torrent)
                .filter(Torrent.status == status)
                .order_by(Torrent.updated_at)
                .all()
            )
        return db.query(Torrent).filter(Torrent.status == status).all()

    @staticmethod
    def recycle_unattended_torrents(db: Session, max_age: float) -> None:
        """Purge unattended torrents."""
        oldest_allowed = datetime.utcnow() - timedelta(seconds=max_age)
        db.query(Torrent).filter(Torrent.status == TorrentStatus.ACTIVE).filter(
            Torrent.last_update < oldest_allowed
            if oldest_allowed is not None
            else False
        ).update(
            {"status": TorrentStatus.PENDING, "worker_id": None},
            synchronize_session=False,
        )
        db.commit()

    @staticmethod
    def take_torrent(db: Session, name: str, worker_name: str) -> Optional[Torrent]:
        """Attempt to take ownership of a torrent."""
        torrent = TorrentManager.get_torrent(db, name)
        if not torrent or torrent.status != TorrentStatus.PENDING:
            return None

        try:
            setattr(torrent, "status", TorrentStatus.ACTIVE)
            setattr(torrent, "worker_id", worker_name)
            db.commit()
            db.refresh(torrent)
            return torrent
        except SQLAlchemyError as e:
            db.rollback()
            log.error("Error taking torrent: %s", str(e))
            raise

    @staticmethod
    def update_torrent_status(
        db: Session,
        name: str,
        status: TorrentStatus | None,
        error_message: Optional[str] = None,
        progress: Optional[int] = None,
    ) -> Optional[Torrent]:
        """Update torrent status."""
        torrent = TorrentManager.get_torrent(db, name)
        if not torrent:
            return None

        try:
            if status is not None:
                setattr(torrent, "status", status)
            if error_message is not None:
                setattr(torrent, "error_message", error_message)
            if progress is not None:
                setattr(torrent, "progress", progress)
            utcnow = datetime.utcnow()
            setattr(torrent, "last_update", utcnow)
            if status == TorrentStatus.COMPLETED:
                setattr(torrent, "completed_at", datetime.utcnow())

            db.commit()
            db.refresh(torrent)
            return torrent
        except SQLAlchemyError as e:
            db.rollback()
            log.error("Error updating torrent: %s", str(e))
            raise
