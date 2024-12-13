import subprocess
from pathlib import Path


def info_hash(path: Path) -> str:
    cmd_list = ["torf", "-i", str(path)]
    try:
        result = subprocess.run(cmd_list, capture_output=True, check=True, text=True)
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Error getting info hash, is it valid? {e}")
    info_hash = result.stdout.strip()
    needle: str | None = None
    for line in info_hash.splitlines():
        if "Info Hash" in line:
            needle = line
            break
    else:
        raise ValueError("Info Hash not found")
    h = needle.split("\t")[-1].strip()
    if len(h) != 40:
        raise ValueError(f"Invalid info hash: {h}")
    return h
