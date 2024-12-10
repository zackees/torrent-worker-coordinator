#! /bin/bash
uvicorn --host 0.0.0.0 --port 80 --workers 1 --forwarded-allow-ips=* torrent_worker_coordinator.app:app
