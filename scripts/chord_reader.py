#!/usr/bin/env python3
"""Run the Chord Reader ML v3 development CLI from a source checkout."""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from steel_guitar_rag.chord_reader.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
