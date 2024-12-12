import os
import shutil
import subprocess
from pathlib import Path

from torrent_worker_coordinator.asyncwrap import asyncwrap


def _exec(cmd: str) -> int:
    """Execute a command in the shell.

    Args:
        cmd: Command to execute
    """
    # return subprocess.run(cmd, shell=True, check=True).returncode
    cp: subprocess.CompletedProcess = subprocess.run(cmd, shell=True)
    return cp.returncode


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
        _exec("git init")
        print(f"Adding remote origin {repo_url}")
        _exec(f"git remote add origin {repo_url}")
        retries = 100
        for i in range(retries):
            print(f"git fetch origin, attempt {i + 1}/{retries}")
            rtn = _exec("git fetch origin")
            if rtn == 0:
                break

        print("git reset --hard origin/main")
        rtn = _exec("git reset --hard origin/main")
        if rtn != 0:
            print(f"Failed to clone repository: {slug}")
            raise RuntimeError("Failed to clone repository")

        print("Setting up upstream tracking...")
        rtn = _exec("git branch --set-upstream-to=origin/main main")
        if rtn != 0:
            # Create main branch first if it doesn't exist
            _exec("git checkout -b main")
            rtn = _exec("git branch --set-upstream-to=origin/main main")
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
        cmd_str = subprocess.list2cmdline(["cd", path, "&&", "git", "fetch", "origin"])
        print(f"Running: {cmd_str} in {path}")
        subprocess.run(cmd_str, check=True, shell=True)
        cmd_str = subprocess.list2cmdline(
            ["cd", path, "&&", "git", "reset", "--hard", "origin/main"]
        )
        print(f"Running: {cmd_str} in {path}")
        subprocess.run(cmd_str, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to update repository: {e}")
        raise RuntimeError("Failed to update repository") from e


def sync_task_download_github(
    repo_url: str,
    path: Path,
    torrents_path: Path,
) -> list[Path]:
    """Clone or update the repository at the given path.

    Args:
        path: Directory for the repository
        repo_url: GitHub repository URL
    """
    if path.exists() and (path / ".git").exists():
        # print(f"Repository already exists at {path}. Updating...")
        # _update_repository(path)
        print("Repository already exists. Skipping update.")
    else:
        print(f"Cloning repository to {path}...")
        _clone_repository(path, repo_url)

    os.makedirs(torrents_path, exist_ok=True)

    list_paths: list[Path] = []
    for root, dirs, files in os.walk(path):
        # protect against git
        if ".git" in root:
            continue
        # dirs
        for dir in dirs:
            if ".git" in dir:
                continue
        for file in files:
            if ".git" in file:
                continue
            list_paths.append(Path(root) / file)

    # first filter - no git
    # second filter - only .torrent files
    list_paths = [
        x for x in list_paths if ".git" not in x.parts and x.name.endswith(".torrent")
    ]

    # # os walk the repo and copy files to torrents_path
    # for root, _, files in os.walk(path):
    #     root_path = Path(root)
    #     #print(f"Checking {root_path}")
    #     if ".git" in root_path.parts:
    #         continue

    #     for file in files:

    #         src_path = Path(Path(root) / file)

    #         if ".git" in src_path.parts:
    #             continue

    #         if not src_path.name.endswith(".torrent"):
    #             continue
    #         print(f"Checking {src_path}")
    #         dst = torrents_path / root_path.name
    #         if src_path.is_file() and not dst.exists():
    #             print(f"Copying {src_path} to {dst}")
    #             shutil.copy(str(src_path), dst)

    print(list_paths)

    # now copy the files
    for src_path in list_paths:
        dst = torrents_path / src_path.name
        if src_path.is_file() and not dst.exists():
            print(f"Copying {src_path} to {dst}")
            shutil.copy(str(src_path), dst)

    out: list[Path] = []
    for root, _, files in os.walk(torrents_path):
        for file in files:
            out.append(Path(root) / file)
    out = sorted(out)
    return out


@asyncwrap
def task_download_github(repo_url: str, path: Path, torrents_path: Path) -> list[Path]:
    return sync_task_download_github(repo_url, path, torrents_path)
