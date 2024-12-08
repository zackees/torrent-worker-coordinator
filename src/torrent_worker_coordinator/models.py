from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker  # type: ignore

from torrent_worker_coordinator.log import make_logger
from torrent_worker_coordinator.paths import DB_PATH

DB_URL = f"sqlite:///{DB_PATH}"

log = make_logger(__name__)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


class TorrentStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"


class Torrent(Base):
    __tablename__ = "torrents"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    status: Column[TorrentStatus] = Column(  # type: ignore
        SQLEnum(TorrentStatus), nullable=False, default=TorrentStatus.PENDING  # type: ignore
    )
    worker_id = Column(String, nullable=True)  # ID of worker processing this torrent

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at = Column(DateTime, nullable=True)

    # Status tracking
    progress = Column(Integer, nullable=True)  # Progress percentage 0-100
    error_message = Column(String, nullable=True)
    last_update = Column(String, nullable=True)  # For status updates

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "worker_id": self.worker_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "progress": self.progress,
            "error_message": self.error_message,
            "last_update": self.last_update,
        }


# Database setup
engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


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
    def get_torrents_by_status(db: Session, status: TorrentStatus) -> list[Torrent]:
        """Get torrents by status."""
        return db.query(Torrent).filter(Torrent.status == status).all()

    @staticmethod
    def take_torrent(db: Session, name: str, worker_id: str) -> Optional[Torrent]:
        """Attempt to take ownership of a torrent."""
        torrent = TorrentManager.get_torrent(db, name)
        if not torrent or torrent.status != TorrentStatus.PENDING:
            return None

        try:
            setattr(torrent, "status", TorrentStatus.ACTIVE)
            setattr(torrent, "worker_id", worker_id)
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
        status: TorrentStatus,
        error_message: Optional[str] = None,
        progress: Optional[int] = None,
        last_update: Optional[str] = None,
    ) -> Optional[Torrent]:
        """Update torrent status."""
        torrent = TorrentManager.get_torrent(db, name)
        if not torrent:
            return None

        try:
            setattr(torrent, "status", status)
            if error_message is not None:
                setattr(torrent, "error_message", error_message)
            if progress is not None:
                setattr(torrent, "progress", progress)
            if last_update is not None:
                setattr(torrent, "last_update", last_update)
            if status == TorrentStatus.COMPLETED:
                setattr(torrent, "completed_at", datetime.utcnow())

            db.commit()
            db.refresh(torrent)
            return torrent
        except SQLAlchemyError as e:
            db.rollback()
            log.error("Error updating torrent: %s", str(e))
            raise
