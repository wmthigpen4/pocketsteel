#!/usr/bin/env python3
"""Run the fixed half-bar-cell development Stage-1 preflight."""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from steel_guitar_rag.chord_reader.half_bar_stage1 import main


if __name__ == "__main__":
    raise SystemExit(main())
