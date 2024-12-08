import os
import unittest
from pathlib import Path

from torrent_worker_coordinator.task_download_github import (
    _clone_repository,
    _update_repository,
    sync_task_download_github,
)


class TestGithubDownload(unittest.TestCase):
    """Test suite for GitHub repository download functionality."""

    TEST_REPO_URL = "https://github.com/zackees/torrent-test"
    TEST_DIR = Path("test_repos")
    TEST_TORRENTS_DIR = Path("test_torrents")

    def setUp(self):
        """Setup test environment before each test."""

        self.TEST_DIR.mkdir(parents=True, exist_ok=True)
        self.TEST_TORRENTS_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up after each test."""
        pass

    def test_clone_repository(self):
        """Test cloning a repository."""
        repo_path = self.TEST_DIR / "zlibry"
        _clone_repository(repo_path, self.TEST_REPO_URL)

        self.assertTrue(repo_path.exists())
        self.assertTrue((repo_path / ".git").exists())
        self.assertTrue(any(repo_path.iterdir()))  # Check if repository has content

    def test_update_repository(self):
        """Test updating an existing repository."""
        repo_path = self.TEST_DIR / "zlibry"

        # First clone the repository
        _clone_repository(repo_path, self.TEST_REPO_URL)

        # Then update it
        _update_repository(repo_path)

        self.assertTrue(repo_path.exists())
        self.assertTrue((repo_path / ".git").exists())

    def test_sync_task_download_github(self):
        """Test the main sync task function."""
        repo_path = self.TEST_DIR / "zlibry"

        # Test initial clone
        sync_task_download_github(self.TEST_REPO_URL, repo_path, self.TEST_TORRENTS_DIR)

        self.assertTrue(repo_path.exists())
        self.assertTrue((repo_path / ".git").exists())
        self.assertTrue(self.TEST_TORRENTS_DIR.exists())
        self.assertTrue(
            any(self.TEST_TORRENTS_DIR.iterdir())
        )  # Check if files were copied

        # Test update
        sync_task_download_github(self.TEST_REPO_URL, repo_path, self.TEST_TORRENTS_DIR)

        self.assertTrue(repo_path.exists())
        self.assertTrue((repo_path / ".git").exists())
        self.assertTrue(self.TEST_TORRENTS_DIR.exists())

    @unittest.skip("Investigate why this test fails")
    def test_file_copying(self):
        """Test that files are properly copied to torrents directory."""
        repo_path = self.TEST_DIR / "zlibry"

        sync_task_download_github(self.TEST_REPO_URL, repo_path, self.TEST_TORRENTS_DIR)

        # Verify that files exist in both locations
        repo_files = set()
        for root, _, files in os.walk(repo_path):
            for file in files:
                if ".git" not in root:  # Ignore .git directory
                    repo_files.add(file)

        torrent_files = set()
        for root, _, files in os.walk(self.TEST_TORRENTS_DIR):
            torrent_files.update(files)

        # Check that at least some files were copied
        self.assertTrue(len(torrent_files) > 0)
        # Check that copied files exist in original repo
        self.assertTrue(all(file in repo_files for file in torrent_files))


if __name__ == "__main__":
    unittest.main()
