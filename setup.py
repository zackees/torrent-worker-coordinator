"""
Setup file.
"""

from setuptools import setup

URL = "https://github.com/zackees/torrent-worker-coordinator"
KEYWORDS = "Torrent Worker Coordinator"


if __name__ == "__main__":
    setup(
        maintainer="Zachary Vorhies",
        keywords=KEYWORDS,
        url=URL,
        package_data={"": ["assets/example.txt"]},
        include_package_data=True)

