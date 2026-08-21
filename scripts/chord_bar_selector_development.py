#!/usr/bin/env python3
"""Run the sealed development-only chord-bar selector experiment stages."""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from steel_guitar_rag.chord_reader.selector_development import main


if __name__ == "__main__":
    raise SystemExit(main())
