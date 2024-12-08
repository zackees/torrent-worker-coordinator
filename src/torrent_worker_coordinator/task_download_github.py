import os
import shutil
import subprocess
from pathlib import Path

from torrent_worker_coordinator.asyncwrap import asyncwrap


def _clone_repository(path: Path, repo_url: str) -> None:
    """Clone the repository to the given path.

    Args:
        path: Directory to clone into
        repo_url: GitHub repository URL

    Raises:
        subprocess.CalledProcessError: If git command fails
    """

    prev_dir = Path.cwd()
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

        os.chdir(path)

        slug = Path(repo_url).name
        if slug.endswith(".git"):
            slug = slug[:-4]
        os.makedirs(slug, exist_ok=True)
        # os.chdir(slug)
        print(f"Now at {Path.cwd().resolve()}")
        print("Initializing git repository...")
        os.system("git init")
        print(f"Adding remote origin {repo_url}")
        os.system(f"git remote add origin {repo_url}")
        retries = 100
        for i in range(retries):
            print(f"git fetch origin, attempt {i + 1}/{retries}")
            rtn = os.system("git fetch origin")
            if rtn == 0:
                break

        print("git reset --hard origin/main")
        rtn = os.system("git reset --hard origin/main")
        if rtn != 0:
            print(f"Failed to clone repository: {slug}")
            raise RuntimeError("Failed to clone repository")

        print("Setting up upstream tracking...")
        rtn = os.system("git branch --set-upstream-to=origin/main main")
        if rtn != 0:
            # Create main branch first if it doesn't exist
            os.system("git checkout -b main")
            rtn = os.system("git branch --set-upstream-to=origin/main main")
            if rtn != 0:
                print("Failed to set upstream tracking branch")
                raise RuntimeError("Failed to set upstream tracking branch")
    finally:
        os.chdir(prev_dir)


def _update_repository(path: Path) -> None:
    """Update the repository at the given path.

    Args:
        path: Path to repository

    Raises:
        subprocess.CalledProcessError: If git command fails
    """
    try:
        cmd_str = subprocess.list2cmdline(["git", "fetch", "origin"])
        print(f"Running: {cmd_str} in {path}")
        subprocess.run(cmd_str, cwd=path, check=True, shell=True)
        cmd_str = subprocess.list2cmdline(["git", "reset", "--hard", "origin/main"])
        print(f"Running: {cmd_str} in {path}")
        subprocess.run(cmd_str, cwd=path, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to update repository: {e}")
        raise RuntimeError("Failed to update repository") from e


def sync_task_download_github(
    repo_url: str,
    path: Path,
    torrents_path: Path,
) -> None:
    """Clone or update the repository at the given path.

    Args:
        path: Directory for the repository
        repo_url: GitHub repository URL
    """
    if path.exists():
        print(f"Repository already exists at {path}. Updating...")
        _update_repository(path)
    else:
        print(f"Cloning repository to {path}...")
        _clone_repository(path, repo_url)

    os.makedirs(torrents_path, exist_ok=True)

    # os walk the repo and copy files to torrents_path
    for root, _, files in os.walk(path):
        for file in files:
            src = Path(root) / file
            dst = torrents_path / Path(root).name
            if src.is_file() and not dst.exists():
                print(f"Copying {src} to {dst}")
                shutil.copy(src, dst)


@asyncwrap
def task_download_github(repo_url: str, path: Path, torrents_path: Path) -> None:
    return sync_task_download_github(repo_url, path, torrents_path)
