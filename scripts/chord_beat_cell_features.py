#!/usr/bin/env python3
"""Publish the one preregistered beat-cell Stage-A feature set."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from steel_guitar_rag.chord_reader.beat_cell_examples import run_official_beat_cell_features


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv or ())
    if arguments:
        raise SystemExit("This command accepts no path, policy, or weakening flags.")
    artifact = run_official_beat_cell_features()
    print(
        json.dumps(
            {
                "artifactSha256": artifact["artifactSha256"],
                "trackCount": artifact["trackCount"],
                "cellCount": artifact["cellCount"],
                "cellDurationMilliseconds": artifact["cellDurationMilliseconds"],
            },
            allow_nan=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
