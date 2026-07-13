from __future__ import annotations

from pathlib import Path
import subprocess
import sys


MIB = 1024 * 1024
DEFAULT_TRACKED_FILE_LIMIT = 2 * MIB
LEGACY_EXPLORER_FILE = Path("ui/e9-fretboard-explorer-data.js")
LEGACY_EXPLORER_LIMIT = 75 * MIB
EXPLORER_CHUNK_DIR = Path("ui/explorer-data-v1")
EXPLORER_CHUNK_LIMIT = 64 * 1024
EXPLORER_TOTAL_LIMIT = 2 * MIB


def tracked_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files", "-z"])
    return [Path(item.decode("utf-8")) for item in output.split(b"\0") if item]


def main() -> int:
    failures: list[str] = []
    for path in tracked_files():
        if not path.is_file():
            continue
        size = path.stat().st_size
        limit = LEGACY_EXPLORER_LIMIT if path == LEGACY_EXPLORER_FILE else DEFAULT_TRACKED_FILE_LIMIT
        if size > limit:
            failures.append(f"{path}: {size} bytes exceeds {limit}")

    chunks = sorted(EXPLORER_CHUNK_DIR.glob("*.json.gz"))
    if not chunks:
        failures.append(f"{EXPLORER_CHUNK_DIR}: no lazy Explorer chunks found")
    else:
        total = sum(path.stat().st_size for path in chunks)
        if total > EXPLORER_TOTAL_LIMIT:
            failures.append(f"{EXPLORER_CHUNK_DIR}: {total} bytes exceeds {EXPLORER_TOTAL_LIMIT}")
        for path in chunks:
            if path.stat().st_size > EXPLORER_CHUNK_LIMIT:
                failures.append(f"{path}: chunk exceeds {EXPLORER_CHUNK_LIMIT} bytes")

    if failures:
        print("Asset size budget failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"Asset size budget passed for {len(tracked_files())} tracked files and {len(chunks)} Explorer chunks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
