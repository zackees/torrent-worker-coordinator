from pydantic import BaseModel


class TorrentInfoRequest(BaseModel):
    """Request parameters for torrent info."""

    torrent_name: str


class TorrentCompleteRequest(BaseModel):
    """Request parameters for torrent completion."""

    torrent_name: str
    worker_name: str


class TorrentErrorRequest(BaseModel):
    """Request parameters for torrent error."""

    name: str
    error_message: str


class TorrentUpdateRequest(BaseModel):
    """Request parameters for torrent update."""

    torrent_name: str
    worker_name: str
    progress: int
    status_message: str


class TorrentTakeRequest(BaseModel):
    """Request body for taking a torrent."""

    worker_name: str
    torrent_name: str


class TorrentListPendingRequest(BaseModel):
    """Request parameters for torrent info."""

    order_by_oldest: bool


class TorrentDownloadRequest(BaseModel):
    """Request body for taking a torrent."""

    torrent_name: str


class TorrentResponse(BaseModel):
    """Response body for torrent info."""

    id: int
    name: str
    status: str
    worker_id: str | None
    created_at: str
    updated_at: str
    completed_at: str | None
    progress: int | None
    error_message: str | None
    last_update: str | None


class TorrentListResponse(BaseModel):
    """Response body for listing torrents."""

    torrents: list[TorrentResponse]
