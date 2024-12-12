from pathlib import Path

from torrent_worker_coordinator.asyncwrap import asyncwrap
from torrent_worker_coordinator.models import get_db
from torrent_worker_coordinator.task_download_github import sync_task_download_github
from torrent_worker_coordinator.torrent_manager import TorrentManager


def sync_task_populate_torrents(
    repo_url: str,
    path: Path,
    torrents_path: Path,
) -> None:
    paths: list[Path] = sync_task_download_github(repo_url, path, torrents_path)
    with get_db() as db:
        for path in paths:
            TorrentManager.create_if_missing(db, path.name)


@asyncwrap
def task_populate_torrents(repo_url: str, path: Path, torrents_path: Path) -> None:
    return sync_task_populate_torrents(repo_url, path, torrents_path)
