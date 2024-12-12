import os
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from typing import Generator

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker  # type: ignore

from torrent_worker_coordinator.log import make_logger
from torrent_worker_coordinator.paths import DB_PATH

DEFAULT_DB_URL = f"sqlite:///{DB_PATH}"

DB_URL = os.getenv("DB_URL", DEFAULT_DB_URL)

print(f"DB_URL: {DB_URL}")
print("CWD:", os.getcwd())

log = make_logger(__name__)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


engine = create_engine(
    DB_URL,
    echo=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    data = get_db.__dict__
    initialized = data.get("initialized", False)
    if not initialized:
        data["initialized"] = True
        Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
