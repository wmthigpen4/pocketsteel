#!/usr/bin/env python3
"""Run the sealed exact runtime beat-cell Stage-1 development preflight."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from steel_guitar_rag.chord_reader.beat_cell_stage1 import main


if __name__ == "__main__":
    raise SystemExit(main())
